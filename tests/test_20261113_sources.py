"""
test_20261113_sources.py -- the rules that arrived with Sun-Young Kim's ASMA_phenotype_20261113.xlsx
(PROTECT-56) and the ASMA-1448 retraction (PROTECT-59), pinned so a later edit cannot quietly undo them.

1. SOURCES. The three SYK sources read the 20261113 workbook. The stock list stays on
   SYK/old/ASMA_list.xlsx: his new master list has no growth-media column (decision D8, 2026-11-16).
2. RETRACTION. ASMA-1448 (a wrong stock, very likely S. salivarius; Sun-Young, 2026-11-02) leaves every
   lab table: Cassandra Reyes's hemolysis rows (FREP6 E10, matched on asma_id + plate + well) and his own
   Antibiotic_resistance_v2 and Growth_endpoint rows (matched on asma_id alone: those tabs have no plate
   or well). One shared list, datasets/phenotype/retractions.csv in the lakehouse repo, so the card and
   protect.phenotype drop the same rows. Consequence the team must read correctly: strain group 541
   passes the gates as UNTESTED (`missing: pass`), not as safe.
3. MEDIA. The four SCFM_5X_* media are left out of every score, as SCFM_10X_glucose is (Sun-Young,
   2026-10-21: "separate the inhibition data by media type"; Spencer's yes 2026-11-16).
4. AMR GENOMIC. Alex Styer's amrfinder.tsv is read from a pinned copy. For the PROTECT-56 load it was the
   2026-02-25 version (Spencer, 2026-11-16: "Keep live version"); since 2026-11-19 it is his 2026-11-10 rerun,
   the version behind the live lakehouse since 2026-11-18 (PROTECT-61, which re-pointed it and this test).

The config and library tests need nothing built; the output tests read data/ and skip if it is not built.
"""
import csv
import hashlib
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "build"))
from config import CFG                    # noqa: E402
from data_sources import source           # noqa: E402
import lib_retractions                    # noqa: E402

SILVER = os.path.join(ROOT, "data", "silver")
GOLD = os.path.join(ROOT, "data", "gold")
WORKBOOK = "ASMA_phenotype_20261113.xlsx"
PINNED_AMR_MD5 = "8b14cad4108db859f1c6273fae068900"   # amrfinder.tsv as of 2026-11-10 (PROVENANCE.md; PROTECT-61)
FIVE_X = {"SCFM_5X_Pro", "SCFM_5X_Val", "SCFM_5X_Pro_Val", "SCFM_5X_Pro_Val_Cys"}
HEADER = ["source_file", "sheet", "asma_id", "plate", "well", "expected_rows", "reason", "requested_by",
          "requested_on", "approved_by", "approved_on", "ticket", "match_on"]


def _rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


class TestConfig(unittest.TestCase):
    def test_syk_sources_read_20261113(self):
        for s in ("amr_measured", "growth_endpoint", "competition"):
            self.assertEqual(os.path.basename(source(s)["path"]), WORKBOOK, s)
            self.assertEqual(str(source(s)["version"]), "20261113", s)

    def test_stock_list_stays_on_the_old_list(self):
        self.assertEqual(source("stock_list")["path"], "/usr2/people/protect/Arkin_Lab/SYK/old/ASMA_list.xlsx")

    def test_asma1448_hemolysis_rows_retracted_by_well(self):
        hem = source("hemolysis")
        lines = [r for r in _rows(hem["retractions"]) if r["source_file"] == os.path.basename(hem["path"])]
        self.assertTrue(any(r["asma_id"] == "ASMA-1448" and r["plate"] == "FREP6" and r["well"] == "E10"
                            and r["match_on"] == "asma_id+plate+well" and r["expected_rows"] == "2"
                            for r in lines))

    def test_asma1448_workbook_rows_retracted_by_id_from_the_same_list(self):
        shared = source("hemolysis")["retractions"]
        for s in ("amr_measured", "growth_endpoint"):
            src = source(s)
            self.assertEqual(src.get("retractions"), shared, f"{s} must read the one shared list")
            lines = lib_retractions.load(src["retractions"], src["path"], src["sheet"])
            self.assertIn("ASMA-1448", lines, s)
            self.assertEqual(lines["ASMA-1448"]["expected_rows"], "3", s)
            self.assertEqual(lines["ASMA-1448"]["ticket"], "PROTECT-59", s)

    def test_scfm_5x_media_excluded_beside_10x_glucose(self):
        ex = set(CFG["competition"]["exclude_media"])
        self.assertIn("SCFM_10X_glucose", ex)
        self.assertTrue(FIVE_X <= ex, f"missing: {sorted(FIVE_X - ex)}")

    def test_amr_genomic_reads_the_pinned_2026_11_10_copy(self):
        p = source("amr_genomic")["path"]
        self.assertTrue(p.endswith("/data/amrfinder_20261110/amrfinder.tsv"), p)
        with open(p, "rb") as fh:
            self.assertEqual(hashlib.md5(fh.read()).hexdigest(), PINNED_AMR_MD5)


class TestLibRetractions(unittest.TestCase):
    """Data-free: the helper the antibiotic and growth builders use."""

    def _csv(self, rows):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=HEADER)
            w.writeheader()
            for r in rows:
                w.writerow({**{k: "x" for k in HEADER}, "plate": "", "well": "", **r})
        self.addCleanup(os.remove, path)
        return path

    def test_loads_only_this_workbook_and_sheet(self):
        p = self._csv([{"source_file": WORKBOOK, "sheet": "Growth_endpoint", "asma_id": "ASMA-1",
                        "expected_rows": "2", "match_on": "asma_id"},
                       {"source_file": "other.xlsx", "sheet": "Growth_endpoint", "asma_id": "ASMA-2",
                        "expected_rows": "1", "match_on": "asma_id"},
                       {"source_file": WORKBOOK, "sheet": "Antibiotic_resistance_v2", "asma_id": "ASMA-3",
                        "expected_rows": "1", "match_on": "asma_id"}])
        got = lib_retractions.load(p, f"/any/dir/{WORKBOOK}", "Growth_endpoint")
        self.assertEqual(sorted(got), ["ASMA-1"])

    def test_a_plate_and_well_line_is_refused_on_a_sheet_without_them(self):
        p = self._csv([{"source_file": WORKBOOK, "sheet": "Growth_endpoint", "asma_id": "ASMA-1",
                        "plate": "FREP1", "well": "A1", "expected_rows": "1", "match_on": "asma_id+plate+well"}])
        with self.assertRaises(ValueError):
            lib_retractions.load(p, WORKBOOK, "Growth_endpoint")

    def test_no_path_configured_means_nothing_to_retract(self):
        self.assertEqual(lib_retractions.load(None, WORKBOOK, "Growth_endpoint"), {})

    def test_exact_count_or_stop(self):
        lines = {"ASMA-1": {"expected_rows": "2", "ticket": "T"}}
        t = lib_retractions.Tracker(lines, "test")
        self.assertTrue(t.drop("ASMA-1"))
        self.assertFalse(t.drop("ASMA-10"))
        self.assertFalse(t.drop("asma-1"))          # the id as the source writes it, never normalised
        with self.assertRaises(ValueError):         # 1 match, expected 2: the source changed
            t.verify()
        self.assertTrue(t.drop(" ASMA-1 "))         # surrounding spaces are not part of the id
        t.verify()                                  # 2 of 2: passes


class TestOutputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        need = {n: os.path.join(SILVER, f"{n}.csv")
                for n in ("silver_hemolysis", "silver_amr_measured", "silver_growth_endpoint")}
        need["shortlist"] = os.path.join(GOLD, "formulation_shortlist.csv")
        if not all(os.path.exists(p) for p in need.values()):
            raise unittest.SkipTest("outputs not built -- run `bash build/run_all.sh` first")
        cls.t = {n: _rows(p) for n, p in need.items()}

    def test_asma1448_gone_from_every_lab_silver(self):
        for n in ("silver_hemolysis", "silver_amr_measured", "silver_growth_endpoint"):
            ids = {r["asma_id"] for r in self.t[n]}
            self.assertNotIn("ASMA-1448", ids, n)
            self.assertIn("ASMA-1451", {r["asma_id"] for r in self.t["silver_hemolysis"]} | ids | {"ASMA-1451"})

    def test_group_541_reads_untested_not_safe(self):
        r = {x["strain_group"]: x for x in self.t["shortlist"]}["541"]
        self.assertEqual(r["status"], "shortlist_unscreened")
        self.assertEqual(r["gate_non_hemolytic"], "untested")
        self.assertEqual(r["gate_amr_not_mdr"], "untested")


if __name__ == "__main__":
    unittest.main()
