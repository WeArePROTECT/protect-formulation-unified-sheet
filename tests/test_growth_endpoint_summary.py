"""
test_growth_endpoint_summary.py -- how an isolate's replicate growth wells collapse to one number.

The team's setting viability.replicate_aggregation (config/thresholds.yaml) says how
build/silver_growth_endpoint.py summarises an isolate's blank-subtracted wells, per condition (SCFM,
SCFM+mucin, the BHIS rich-media check and the no-carbon control). MEDIAN since 2026-11-24 (Spencer's
decision L, PROTECT-60 and PROTECT-76): with 3 wells a strain grows only if at least 2 of them do; the
mean, the rule before, let one odd well decide. Everything around the summary is unchanged and pinned
here too: each well minus the MEAN of its date's BLANK wells, floored at 0; the 0.1 OD cutoff; a call is
inconclusive (blank) if the strain did not grow in rich media; a grower must beat the no-carbon control.

1. Synthetic (no data needed): made-up wells with a hand-computed answer under each rule. No real ASMA
   data lives in this repo; the ids and numbers are invented.
2. Real output (skips if the table is not built or the workbook is not reachable): every isolate in
   data/silver/silver_growth_endpoint.csv re-derived from Sun-Young's raw wells under the configured rule,
   without the builder's code. Fails if the table was built under another rule (rebuild after a change).
"""
import csv
import os
import sys
import unittest
from collections import defaultdict
from statistics import mean, median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "build"))
from config import CFG                              # noqa: E402
import silver_growth_endpoint as G                  # noqa: E402

SILVER = os.path.join(ROOT, "data", "silver", "silver_growth_endpoint.csv")
CUT, QC = 0.1, 0.1          # the shipped cutoffs, passed explicitly so these tests do not move with the config
DAY = "2026-01-05"
BLANK_OD = 0.05             # every BLANK well on DAY reads this, in every condition


def well(aid, scfm=None, mucin=None, bhis=None, nocarb=None, date=DAY):
    """One row of the Growth_endpoint sheet, raw (before the blank is subtracted)."""
    return {"ASMA_id": aid, "Assay_start_date": date, "SCFM_72": scfm, "SCFM_mucin_0.5_72": mucin,
            "BHIS_72": bhis, "No_Carbon_72": nocarb}


def raw(corrected):
    """A raw reading that comes out at `corrected` once DAY's blank is subtracted."""
    return corrected + BLANK_OD


BLANKS = [well("BLANK", BLANK_OD, BLANK_OD, BLANK_OD, BLANK_OD) for _ in range(2)]


def isolate(aid, scfm, bhis=0.8, nocarb=0.0, mucin=None):
    """Wells for one isolate from blank-subtracted values: scfm (and mucin) are per-well lists."""
    mucin = mucin or [None] * len(scfm)
    return [well(aid, raw(s), None if m is None else raw(m), raw(bhis), raw(nocarb)) for s, m in zip(scfm, mucin)]


def build(rows, how):
    return {r["asma_id"]: r for r in G.summarize(rows, how, CUT, QC, "synthetic.xlsx")}


class TestTheSetting(unittest.TestCase):
    def test_shipped_default_is_median(self):
        # Decision L, 2026-11-24 (Spencer, "for now"; the science is to be checked with Gwyn). If the team
        # changes it on purpose, change this line and say why in the commit.
        self.assertEqual(CFG["viability"]["replicate_aggregation"], "median")
        self.assertEqual(G.REPLICATES, "median")

    def test_only_median_or_mean_are_accepted(self):
        rows = BLANKS + isolate("ASMA-900001", [0.2, 0.2, 0.2])
        for bad in ("max", "Median", "", None, "average"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                G.summarize(rows, bad, CUT, QC, "synthetic.xlsx")


class TestOneOddWell(unittest.TestCase):
    """The case decision L is about: 2 of 3 wells stay flat, one shoots up."""

    rows = BLANKS + isolate("ASMA-900001", scfm=[0.03, 0.50, 0.03])

    def test_median_does_not_let_one_well_decide(self):
        r = build(self.rows, "median")["ASMA-900001"]
        self.assertAlmostEqual(r["scfm_od"], 0.03, places=9)
        self.assertEqual(r["grows_scfm"], "N")

    def test_mean_did(self):
        r = build(self.rows, "mean")["ASMA-900001"]
        self.assertAlmostEqual(r["scfm_od"], 0.187, places=9)       # (0.03 + 0.50 + 0.03) / 3 = 0.1867
        self.assertEqual(r["grows_scfm"], "Y")

    def test_two_of_three_growing_wells_is_a_grower(self):
        rows = BLANKS + isolate("ASMA-900002", scfm=[0.03, 0.15, 0.40])
        r = build(rows, "median")["ASMA-900002"]
        self.assertAlmostEqual(r["scfm_od"], 0.15, places=9)
        self.assertEqual(r["grows_scfm"], "Y")


class TestReplicateCounts(unittest.TestCase):
    def test_two_wells_median_equals_mean(self):
        rows = BLANKS + isolate("ASMA-900003", scfm=[0.06, 0.16], mucin=[0.30, 0.10])
        med, avg = build(rows, "median")["ASMA-900003"], build(rows, "mean")["ASMA-900003"]
        self.assertEqual(med, avg)
        self.assertAlmostEqual(med["scfm_od"], 0.11, places=9)
        self.assertAlmostEqual(med["scfm_mucin_od"], 0.20, places=9)
        self.assertEqual((med["grows_scfm"], med["n_reps"]), ("Y", 2))

    def test_six_wells_median_is_the_middle_pair(self):
        rows = BLANKS + isolate("ASMA-900004", scfm=[0.95, 0.02, 0.05, 0.03, 0.06, 0.04])
        r = build(rows, "median")["ASMA-900004"]
        self.assertAlmostEqual(r["scfm_od"], 0.045, places=9)       # (0.04 + 0.05) / 2
        self.assertEqual((r["grows_scfm"], r["n_reps"]), ("N", 6))
        r = build(rows, "mean")["ASMA-900004"]
        self.assertAlmostEqual(r["scfm_od"], 0.192, places=9)       # 1.15 / 6 = 0.1917
        self.assertEqual(r["grows_scfm"], "Y")

    def test_one_well(self):
        rows = BLANKS + isolate("ASMA-900005", scfm=[0.12])
        self.assertEqual(build(rows, "median")["ASMA-900005"], build(rows, "mean")["ASMA-900005"])


class TestUnchangedAroundTheSummary(unittest.TestCase):
    def test_blank_is_still_the_mean_of_the_dates_blank_wells(self):
        d = "2026-02-02"
        blanks = [well("BLANK", b, b, b, b, date=d) for b in (0.02, 0.04, 0.12)]   # mean 0.06, median 0.04
        rows = blanks + [well("ASMA-900006", 0.22, 0.22, 0.90, 0.06, date=d) for _ in range(3)]
        r = build(rows, "median")["ASMA-900006"]
        self.assertAlmostEqual(r["scfm_od"], 0.16, places=9)        # 0.22 - 0.06, not 0.22 - 0.04
        self.assertAlmostEqual(r["no_carbon_od"], 0.0, places=9)

    def test_a_date_without_blanks_falls_back_to_all_blanks(self):
        rows = BLANKS + [well("ASMA-900007", raw(0.2), None, raw(0.8), raw(0.0), date="2026-03-03")]
        self.assertAlmostEqual(build(rows, "median")["ASMA-900007"]["scfm_od"], 0.2, places=9)

    def test_each_well_is_floored_at_zero_before_the_summary(self):
        rows = BLANKS + [well("ASMA-900008", s, None, raw(0.8), raw(0.0)) for s in (0.01, 0.02, raw(0.26))]
        self.assertAlmostEqual(build(rows, "median")["ASMA-900008"]["scfm_od"], 0.0, places=9)
        self.assertAlmostEqual(build(rows, "mean")["ASMA-900008"]["scfm_od"], 0.087, places=9)   # 0.26 / 3

    def test_no_growth_in_rich_media_means_inconclusive(self):
        rows = BLANKS + isolate("ASMA-900009", scfm=[0.4, 0.4, 0.4], bhis=0.05)
        r = build(rows, "median")["ASMA-900009"]
        self.assertFalse(r["qc_grew"])
        self.assertIsNone(r["grows_scfm"])

    def test_the_rule_also_summarises_the_rich_media_check(self):
        rows = BLANKS + [well("ASMA-900010", raw(0.3), None, raw(b), raw(0.0)) for b in (0.02, 0.03, 0.60)]
        self.assertIsNone(build(rows, "median")["ASMA-900010"]["grows_scfm"])     # 1 of 3 grew in BHIS
        self.assertEqual(build(rows, "mean")["ASMA-900010"]["grows_scfm"], "Y")    # mean BHIS 0.217

    def test_a_grower_must_beat_the_no_carbon_control(self):
        rows = BLANKS + [well("ASMA-900011", raw(0.15), None, raw(0.8), raw(n)) for n in (0.0, 0.0, 0.50)]
        self.assertEqual(build(rows, "median")["ASMA-900011"]["grows_scfm"], "Y")   # control median 0
        self.assertEqual(build(rows, "mean")["ASMA-900011"]["grows_scfm"], "N")     # control mean 0.167

    def test_the_cutoff_is_inclusive(self):
        rows = BLANKS + isolate("ASMA-900012", scfm=[0.05, 0.10, 0.30])
        self.assertEqual(build(rows, "median")["ASMA-900012"]["grows_scfm"], "Y")

    def test_mucin_lift_is_the_difference_of_the_two_summaries(self):
        rows = BLANKS + isolate("ASMA-900013", scfm=[0.02, 0.04, 0.90], mucin=[0.30, 0.50, 0.40])
        r = build(rows, "median")["ASMA-900013"]
        self.assertAlmostEqual(r["mucin_lift"], 0.36, places=9)     # 0.40 - 0.04
        self.assertEqual((r["grows_scfm"], r["grows_scfm_mucin"]), ("N", "Y"))

    def test_non_asma_rows_are_ignored(self):
        rows = BLANKS + isolate("ASMA-900014", [0.2]) + [well("PA14_KEH108_Reporter", 0.9, 0.9, 0.9, 0.0)]
        self.assertEqual(sorted(build(rows, "median")), ["ASMA-900014"])


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


@unittest.skipUnless(os.path.exists(SILVER) and os.path.exists(G.SRC), "table not built or workbook not reachable")
class TestBuiltTableFollowsTheSetting(unittest.TestCase):
    """Re-derive every isolate from the raw wells without the builder's code, under the configured rule."""

    @classmethod
    def setUpClass(cls):
        from lib_ids import normalize_asma_id, read_xlsx_sheet
        rule = {"median": median, "mean": mean}[CFG["viability"]["replicate_aggregation"]]
        conds = {"scfm_od": "SCFM_72", "scfm_mucin_od": "SCFM_mucin_0.5_72", "bhis_od": "BHIS_72",
                 "no_carbon_od": "No_Carbon_72"}
        rows = list(read_xlsx_sheet(G.SRC, G.SHEET))
        blanks, everyday = defaultdict(list), defaultdict(list)
        for r in rows:
            if str(r.get("ASMA_id")).strip().upper() == "BLANK":
                for c in conds.values():
                    if _f(r.get(c)) is not None:
                        blanks[(str(r.get("Assay_start_date")), c)].append(_f(r.get(c)))
                        everyday[c].append(_f(r.get(c)))
        wells = defaultdict(lambda: defaultdict(list))
        for r in rows:
            aid = normalize_asma_id(r.get("ASMA_id"))
            for c in conds.values():
                v = _f(r.get(c))
                if aid and v is not None:
                    b = blanks.get((str(r.get("Assay_start_date")), c)) or everyday[c]
                    wells[aid][c].append(max(0.0, v - mean(b)))
        cls.want = {aid: {col: round(rule(w[c]), 3) if w[c] else None for col, c in conds.items()}
                    for aid, w in wells.items()}
        with open(SILVER, newline="") as fh:
            cls.built = list(csv.DictReader(fh))
        cls.cut = CFG["viability"]["scfm_grow_min_od"]
        cls.qc = CFG["viability"]["qc_rich_media_min_od"]

    def test_every_od_is_the_configured_summary_of_its_wells(self):
        self.assertGreater(len(self.built), 700)
        for r in self.built:
            for col, v in self.want[r["asma_id"]].items():
                got = _f(r[col])
                self.assertEqual(got is None, v is None, msg=(r["asma_id"], col))
                if v is not None:
                    self.assertAlmostEqual(got, v, places=9, msg=(r["asma_id"], col))

    def test_every_call_follows_from_those_ods(self):
        for r in self.built:
            w = self.want[r["asma_id"]]
            qc_grew = w["bhis_od"] is not None and w["bhis_od"] >= self.qc
            for col, od in (("grows_scfm", w["scfm_od"]), ("grows_scfm_mucin", w["scfm_mucin_od"])):
                if od is None or not qc_grew:
                    want = ""
                else:
                    nc = w["no_carbon_od"]
                    want = "Y" if od >= self.cut and (nc is None or od > nc) else "N"
                self.assertEqual(r[col], want, msg=(r["asma_id"], col))


if __name__ == "__main__":
    unittest.main()
