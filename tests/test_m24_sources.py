"""
test_m24_sources.py -- the three rules that arrived with Sun-Young Kim's Month 24 workbook
(ASMA_phenotype_20260929.xlsx), pinned so a later edit cannot quietly undo them.

1. RETRACTION. ASMA-4467's hemolysis rows (FREP5 well B9) are dropped: the stock in that well was
   the wrong strain (Sun-Young, 2026-09-25 and 2026-09-28; PROTECT-34). The list lives in the
   lakehouse repo, datasets/phenotype/retractions.csv, so the card and protect.phenotype drop the
   same rows. Consequence the team must read correctly: with no hemolysis result, strain group
   259 (S. vaginalis) passes the safety gates as UNTESTED (`missing: pass`), not as safe.
2. MEDIA. Wells grown in SCFM_10X_glucose are not a standard condition even when labelled
   Standard_A (Sun-Young, 2026-09-28). Without this rule ASMA-1228 (group 11) was ranked on
   10x-glucose wells alone and group 770 mixed two media in one score (measured 2026-10-01).
3. PA REPORTERS. The set of reporters that are P. aeruginosa comes from config, and includes the
   14 clinical reporters added for Month 24. Before 2026-10-01 it was five names in code.
4. ASSAY LOOKUP. data/gold/assay_asma_id_lookup.csv is rebuilt every run and agrees with the card.

The config tests need nothing built; the output tests read data/ and skip if it is not built.
"""
import csv
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "build"))
from config import CFG                    # noqa: E402
from data_sources import source           # noqa: E402

SILVER = os.path.join(ROOT, "data", "silver")
GOLD = os.path.join(ROOT, "data", "gold")
NEW_PA = {"ASMA-35_Reporter", "ASMA-130_Reporter", "ASMA-168_Reporter", "ASMA-274_Reporter",
          "ASMA-425_Reporter", "ASMA-1298_Reporter", "ASMA-1341_Reporter", "ASMA-1667_Reporter",
          "ASMA-2330_Reporter", "ASMA-2358_Reporter", "ASMA-2888_Reporter", "ASMA-3066_Reporter",
          "ASMA-4151_Reporter", "ASMA-4963_Reporter"}


def _rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


class TestM24Config(unittest.TestCase):
    def test_pa_reporters_include_the_month24_panel(self):
        pa = set(CFG["competition"]["pa_reporters"])
        self.assertTrue(NEW_PA <= pa, f"missing: {sorted(NEW_PA - pa)}")
        self.assertIn(CFG["competition"]["headline_reporter"], pa)
        self.assertEqual(len(pa), 19)

    def test_10x_glucose_is_excluded(self):
        self.assertIn("SCFM_10X_glucose", CFG["competition"]["exclude_media"])

    def test_hemolysis_retractions_configured(self):
        path = source("hemolysis").get("retractions")
        self.assertTrue(path and os.path.exists(path), f"retractions file missing: {path}")
        lines = [r for r in _rows(path)
                 if r["source_file"] == os.path.basename(source("hemolysis")["path"])]
        self.assertTrue(any(r["asma_id"] == "ASMA-4467" and r["plate"] == "FREP5"
                            and r["well"] == "B9" for r in lines))

    def test_builder_reads_config_not_a_hand_typed_set(self):
        import silver_competition as S
        self.assertEqual(S.PA_ALL, set(CFG["competition"]["pa_reporters"]))
        self.assertEqual(S.EXCLUDE_MEDIA, set(CFG["competition"]["exclude_media"]))


class TestM24Outputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        need = [os.path.join(SILVER, "silver_hemolysis.csv"),
                os.path.join(SILVER, "silver_competition.csv"),
                os.path.join(GOLD, "formulation_shortlist.csv")]
        if not all(os.path.exists(p) for p in need):
            raise unittest.SkipTest("outputs not built -- run `bash build/run_all.sh` first")
        cls.hem = {r["asma_id"]: r for r in _rows(need[0])}
        cls.comp = {r["asma_id"]: r for r in _rows(need[1])}
        cls.short = {r["strain_group"]: r for r in _rows(need[2])}

    def test_retracted_isolate_has_no_hemolysis_call(self):
        self.assertNotIn("ASMA-4467", self.hem)

    def test_group_259_reads_untested_not_safe(self):
        r = self.short["259"]
        self.assertEqual(r["status"], "shortlist_unscreened")
        self.assertEqual(r["gate_non_hemolytic"], "untested")
        self.assertEqual(r["gate_amr_not_mdr"], "untested")

    def test_assay_lookup_is_rebuilt_and_matches_the_card(self):
        # Until 2026-10-01 the lookup was a one-off from 2026-07-27 that no build refreshed; the
        # card dropped ASMA-4467 as group 259's assay isolate while the lookup still named it.
        lookup = {r["strain_group"]: r for r in _rows(os.path.join(GOLD, "assay_asma_id_lookup.csv"))}
        card = {r["strain_group"]: r for r in _rows(os.path.join(GOLD, "gold_unified_sheet.csv"))}
        self.assertNotIn("259", lookup)
        self.assertEqual(set(lookup), {g for g, r in card.items() if r["assay_asma_id"]})
        wrong = [g for g in lookup if lookup[g]["assay_asma_id"] != card[g]["assay_asma_id"]]
        self.assertEqual(wrong, [])

    def test_no_headline_score_from_10x_glucose_wells(self):
        # ASMA-1228's only standard wells against the headline reporter are 10x-glucose wells.
        r = self.comp.get("ASMA-1228")
        if r is not None:
            self.assertEqual(r["best_solo_inhib_pa"], "")
            self.assertEqual(r["n_formulations_pa"], "0")


if __name__ == "__main__":
    unittest.main()
