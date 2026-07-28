"""
test_bsl.py -- the biosafety-level column (bsl_level), from the authoritative interim reference.

bsl_level is populated from data/reference/species_bsl.csv (risk groups from published registries, cited per
row): species match, then genus fallback, then the species_safety fallback. It is INTERIM and NON-gating.
Method + caveats: docs/decisions/bsl_stat_sheet_decisions.md.

Guarantees:
  - REFERENCE WELL-FORMED: each row's risk_group and bsl_level are valid and agree; classified rows cite a source.
  - VALID ON CARD: every bsl_level on the card is one of {"", "1", "2", "3"}.
  - NO FABRICATION: every card bsl_level is exactly what the builder's own lookup produces (traces to source).
  - SAFETY ANCHOR: the certain BSL-2 pathogens are not blanked or downgraded.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build"))
import gold_unified_sheet as G     # noqa: E402
import heuristic_shortlist as H     # noqa: E402  (reuse read_delimited)

ROOT = os.path.dirname(HERE)
BSL_REF = os.path.join(ROOT, "data", "reference", "species_bsl.csv")
GOLD = os.path.join(ROOT, "data", "gold", "gold_unified_sheet.csv")

VALID_BSL = {"", "1", "2", "3"}
RG_TO_BSL = {"1": "1", "2": "2", "3": "3", "review": ""}


@unittest.skipUnless(os.path.exists(BSL_REF), "species_bsl.csv not present")
class TestBslReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(H.read_delimited(BSL_REF, ","))

    def test_rows_well_formed(self):
        self.assertGreater(len(self.rows), 0, "species_bsl.csv is empty")
        for r in self.rows:
            self.assertIn(r["rank"], ("species", "genus"), msg=f"bad rank: {r}")
            rg = (r["risk_group"] or "").strip()
            bsl = (r["bsl_level"] or "").strip()
            self.assertIn(rg, ("1", "2", "3", "review"), msg=f"bad risk_group: {r}")
            self.assertIn(bsl, VALID_BSL, msg=f"bad bsl_level: {r}")
            self.assertEqual(bsl, RG_TO_BSL[rg], msg=f"risk_group and bsl_level disagree: {r}")
            self.assertEqual(" " in r["species"].strip(), r["rank"] == "species",
                             msg=f"rank does not match the name shape (species names have a space): {r}")

    def test_classified_rows_cite_a_source(self):
        for r in self.rows:
            if (r["bsl_level"] or "").strip():          # a real BSL number must be sourced
                self.assertTrue((r["source"] or "").strip(), msg=f"classified row has no source: {r}")


@unittest.skipUnless(os.path.exists(GOLD) and os.path.exists(BSL_REF), "card / ref not built")
class TestBslOnCard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(H.read_delimited(GOLD, ","))
        cls.bs, cls.bg = G.load_bsl_ref()
        cls.ss, cls.sg = G.load_safety_ref()

    def test_values_valid(self):
        for r in self.rows:
            self.assertIn((r.get("bsl_level") or "").strip(), VALID_BSL,
                          msg=f"{r['strain_group']} has an invalid bsl_level {r.get('bsl_level')!r}")

    def test_no_fabrication_traces_to_source(self):
        # every card bsl must equal the builder's own lookup: species_bsl -> genus fallback -> safety fallback
        for r in self.rows:
            sp, ge = r.get("species") or None, r.get("genus")
            expected = G.bsl_for(sp, ge, self.bs, self.bg) or G.classify(sp, ge, self.ss, self.sg)[2]
            self.assertEqual((r.get("bsl_level") or ""), expected,
                             msg=f"{r['strain_group']} bsl_level not reproducible from the reference")

    def test_certain_pathogens_not_downgraded(self):
        anchors = {"Pseudomonas aeruginosa", "Staphylococcus aureus", "Klebsiella pneumoniae"}
        seen = {G.norm_species(r.get("species") or ""): (r.get("bsl_level") or "")
                for r in self.rows if G.norm_species(r.get("species") or "") in anchors}
        for sp in anchors & set(seen):
            self.assertIn(seen[sp], ("2", "3"), msg=f"{sp} downgraded to {seen[sp]!r} (must stay BSL-2+)")


if __name__ == "__main__":
    unittest.main()
