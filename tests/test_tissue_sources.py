"""
test_tissue_sources.py -- the TISSUE layer (Gwyneth's airway-tissue model).

Tissue numbers are hand-extracted from Gwyneth's computed workbooks into two curated source tables, so the most
important guarantee is TRACEABILITY: every value on the card must exist in her source, no fabrication, no mangled
rollup. Provenance + method: docs/tissue_provenance_and_method.md.

  - GOLDEN: the aggregation + member-parsing helpers on tiny inputs with hand-computed answers.
  - REAL INVARIANTS: silver_tissue (ids normalized + unique; values numeric; an efficacy value is backed by >=1 row).
  - SOURCE INTEGRITY: every silver tissue value equals a value in Gwyneth's source efficacy/barrier tables.
  - GOLD JOIN INTEGRITY: every tissue / tissue_damage on the card comes from a silver_tissue row.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build"))
import silver_tissue as T          # noqa: E402
import data_sources as DS          # noqa: E402
import heuristic_shortlist as H     # noqa: E402  (reuse read_delimited)

SILVER = os.path.join(os.path.dirname(HERE), "data", "silver")
GOLD = os.path.join(os.path.dirname(HERE), "data", "gold", "gold_unified_sheet.csv")
TISS = os.path.join(SILVER, "silver_tissue.csv")


class TestHelpers(unittest.TestCase):
    def test_agg(self):
        self.assertEqual(T._agg([1, 2, 3], "max"), 3)
        self.assertEqual(T._agg([1, 2, 3], "min"), 1)
        self.assertEqual(T._agg([1, 2, 3], "mean"), 2)
        self.assertEqual(T._agg([1, 2, 9], "median"), 2)
        self.assertIsNone(T._agg([], "max"))

    def test_members(self):
        self.assertEqual(T._members("ASMA-2260+ASMA-3643"), ["ASMA-2260", "ASMA-3643"])
        self.assertEqual(T._members("ASMA_1981"), ["ASMA-1981"])   # normalizes underscore form
        self.assertEqual(T._members(""), [])


class TestSilverInvariants(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(TISS), "silver_tissue not built")
    def test_ids_and_values(self):
        rows = list(H.read_delimited(TISS, ","))
        ids = [r["asma_id"] for r in rows]
        self.assertTrue(all(a.startswith("ASMA-") for a in ids))
        self.assertEqual(len(ids), len(set(ids)), "duplicate asma_id in silver_tissue")
        for r in rows:
            for c in ("tissue_pa_reduction", "tissue_barrier_delta"):
                if r[c] not in ("", "None"):
                    float(r[c])
            if r["tissue_pa_reduction"] not in ("", "None"):
                self.assertGreaterEqual(int(r["n_tissue_efficacy_rows"]), 1)


class TestSourceIntegrity(unittest.TestCase):
    """Every tissue number must trace to Gwyneth's curated source table (no fabrication)."""
    @unittest.skipUnless(os.path.exists(TISS), "silver_tissue not built")
    def test_values_come_from_her_source(self):
        src = DS.source("tissue")
        root, (eff, bar) = src["path"], src["files"]
        eff_vals = {round(float(r["pa_suppression_pct"]), 1)
                    for r in H.read_delimited(os.path.join(root, eff), ",") if r["pa_suppression_pct"]}
        bar_vals = {round(float(r["barrier_delta_pct_ctrlsub"]), 2)
                    for r in H.read_delimited(os.path.join(root, bar), ",") if r["barrier_delta_pct_ctrlsub"]}
        n_pa = n_bar = 0
        for r in H.read_delimited(TISS, ","):
            if r["tissue_pa_reduction"] not in ("", "None"):
                self.assertIn(round(float(r["tissue_pa_reduction"]), 1), eff_vals,
                              f"{r['asma_id']} tissue value not present in Gwyneth's efficacy source")
                n_pa += 1
            if r["tissue_barrier_delta"] not in ("", "None"):
                self.assertIn(round(float(r["tissue_barrier_delta"]), 2), bar_vals,
                              f"{r['asma_id']} barrier value not present in Gwyneth's barrier source")
                n_bar += 1
        self.assertGreater(n_pa, 0, "no efficacy values traced -- source empty or unbuilt")
        self.assertGreater(n_bar, 0, "no barrier values traced")


class TestGoldJoin(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(GOLD) and os.path.exists(TISS), "card / silver_tissue not built")
    def test_gold_from_silver(self):
        pa = {r["tissue_pa_reduction"] for r in H.read_delimited(TISS, ",")}
        bar = {r["tissue_barrier_delta"] for r in H.read_delimited(TISS, ",")}
        n = 0
        for r in H.read_delimited(GOLD, ","):
            if r.get("tissue") not in ("", "None", None):
                self.assertIn(r["tissue"], pa, f"{r['strain_group']} tissue not from silver")
                n += 1
            if r.get("tissue_damage") not in ("", "None", None):
                self.assertIn(r["tissue_damage"], bar, f"{r['strain_group']} tissue_damage not from silver")
        self.assertGreater(n, 0, "no strains carried tissue -- join produced nothing")


if __name__ == "__main__":
    unittest.main()
