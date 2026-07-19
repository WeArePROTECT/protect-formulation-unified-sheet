"""
test_emma_sources.py -- the RELEVANCE layer (Emma metagenomics): abundance math, the cluster<->ASMA
backbone, and the gold join.

  - GOLDEN: the prevalence / relative-abundance math on a tiny synthetic table with a hand-computed answer.
  - REAL INVARIANTS: silver_emma_map (ASMA ids normalized, PA=737 has members) and silver_airway_abundance
    (prevalence in [0,1], abundance >= 0, PA present) -- skip if not built.
  - JOIN INTEGRITY: every abundance value on the gold card actually comes from a cluster in the source table
    (guards against a mangled/mismatched join fabricating numbers).
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build"))
import silver_airway_abundance as SA    # noqa: E402
import silver_pa_cooccurrence as PC     # noqa: E402
import heuristic_shortlist as H          # noqa: E402  (reuse its read_delimited)

SILVER = os.path.join(os.path.dirname(HERE), "data", "silver")
GOLD = os.path.join(os.path.dirname(HERE), "data", "gold", "gold_unified_sheet.csv")
EMMA_MAP = os.path.join(SILVER, "silver_emma_map.csv")
ABUND = os.path.join(SILVER, "silver_airway_abundance.csv")
COOC = os.path.join(SILVER, "silver_pa_cooccurrence.csv")
METAB = os.path.join(SILVER, "silver_pa_metabolic_competitor.csv")


class TestAbundanceMath(unittest.TestCase):
    # two samples, three clusters; column totals SA=100, SB=100 (both)
    ROWS = [
        {"cluster_id": "X", "SA_metaG": "90", "SB_metaG": "0"},
        {"cluster_id": "Y", "SA_metaG": "10", "SB_metaG": "100"},
    ]
    COLS = ["SA_metaG", "SB_metaG"]

    def test_col_totals(self):
        self.assertEqual(SA.col_totals(self.ROWS, self.COLS), {"SA_metaG": 100.0, "SB_metaG": 100.0})

    def test_metrics_hand_computed(self):
        tot = SA.col_totals(self.ROWS, self.COLS)
        # X present in 1/2 samples -> prevalence 0.5 ; rel = [90/100] -> mean 0.9 -> 90.0%
        self.assertEqual(SA.metrics(self.ROWS[0], self.COLS, tot), (0.5, 90.0))
        # Y present in 2/2 -> prevalence 1.0 ; rel = [0.1, 1.0] -> mean 0.55 -> 55.0%
        self.assertEqual(SA.metrics(self.ROWS[1], self.COLS, tot), (1.0, 55.0))

    def test_absent_cluster_is_zero_not_error(self):
        tot = SA.col_totals(self.ROWS, self.COLS)
        absent = {"cluster_id": "Z", "SA_metaG": "0", "SB_metaG": "0"}
        self.assertEqual(SA.metrics(absent, self.COLS, tot), (0.0, 0.0))


class TestEmmaMap(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(EMMA_MAP), "silver_emma_map not built")
    def test_ids_normalized_and_unique(self):
        rows = list(H.read_delimited(EMMA_MAP, ","))
        ids = [r["asma_id"] for r in rows]
        self.assertTrue(all(a.startswith("ASMA-") for a in ids))
        self.assertEqual(len(ids), len(set(ids)), "duplicate asma_id in silver_emma_map")

    @unittest.skipUnless(os.path.exists(EMMA_MAP), "silver_emma_map not built")
    def test_pa_cluster_737_has_asma_members(self):
        rows = list(H.read_delimited(EMMA_MAP, ","))
        pa = [r["asma_id"] for r in rows if r["cluster_95"] == "737"]
        self.assertGreater(len(pa), 0, "PA cluster 737 has no ASMA members")


class TestAbundanceTable(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(ABUND), "silver_airway_abundance not built")
    def test_ranges_and_pa_present(self):
        rows = list(H.read_delimited(ABUND, ","))
        clusters = {r["cluster_95"] for r in rows}
        self.assertIn("737", clusters, "PA cluster 737 missing from abundance table")
        for r in rows:
            for col in ("prevalence_metag", "prevalence_metars"):
                p = float(r[col])
                self.assertTrue(0.0 <= p <= 1.0, f"{col}={p} out of [0,1] for cluster {r['cluster_95']}")
            for col in ("abundance_metag", "abundance_metars"):
                self.assertGreaterEqual(float(r[col]), 0.0)


class TestGoldJoinIntegrity(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(GOLD) and os.path.exists(ABUND), "card/abundance not built")
    def test_gold_abundance_values_come_from_source(self):
        # Every populated (prevalence, abundance) pair on the card must exist as some cluster's row in
        # the abundance table -- so the strain -> cluster join can't invent or mismatch a value.
        src = {(r["prevalence_metag"], r["abundance_metag"]) for r in H.read_delimited(ABUND, ",")}
        n_checked = 0
        for r in H.read_delimited(GOLD, ","):
            if r.get("abundance_metag") not in ("", "None", None):
                self.assertIn((r["prevalence_metag"], r["abundance_metag"]), src,
                              msg=f"strain {r['strain_group']} has abundance not present in the source table")
                n_checked += 1
        self.assertGreater(n_checked, 0, "no strains carried abundance -- join produced nothing")


class TestCooccurrenceParsing(unittest.TestCase):
    def test_focal_row_extraction(self):
        import tempfile
        content = "#OTU ID\tA\tB\t737\nA\t1\t0.5\t-0.3\nB\t0.5\t1\t0.2\n737\t-0.3\t0.2\t1\n"
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as fh:
            fh.write(content)
            path = fh.name
        try:
            self.assertEqual(PC.focal_row(path, "737"), {"A": "-0.3", "B": "0.2", "737": "1"})
        finally:
            os.unlink(path)


class TestCooccurrenceTable(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(COOC), "silver_pa_cooccurrence not built")
    def test_ranges_and_pa_self_excluded(self):
        rows = list(H.read_delimited(COOC, ","))
        self.assertNotIn("737", {r["cluster_95"] for r in rows})     # PA's self-correlation dropped
        for r in rows:
            c = float(r["pa_cooccurrence"])
            self.assertTrue(-1.0 <= c <= 1.0, f"corr {c} out of [-1,1]")
            if r["pa_cooccurrence_p"] not in ("", "None"):
                self.assertTrue(0.0 <= float(r["pa_cooccurrence_p"]) <= 1.0)

    @unittest.skipUnless(os.path.exists(GOLD) and os.path.exists(COOC), "card/cooccurrence not built")
    def test_gold_cooccurrence_values_come_from_source(self):
        src = {r["pa_cooccurrence"] for r in H.read_delimited(COOC, ",")}
        n = 0
        for r in H.read_delimited(GOLD, ","):
            if r.get("pa_cooccurrence") not in ("", "None", None):
                self.assertIn(r["pa_cooccurrence"], src, msg=f"{r['strain_group']} cooccurrence not in source")
                n += 1
        self.assertGreater(n, 0, "no strains carried co-occurrence -- join produced nothing")


class TestMetabolicTable(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(METAB), "silver_pa_metabolic_competitor not built")
    def test_scores_and_sample_counts(self):
        rows = list(H.read_delimited(METAB, ","))
        self.assertGreater(len(rows), 0)
        for r in rows:
            self.assertGreaterEqual(int(r["n_samples"]), 1)
            self.assertIsInstance(float(r["pa_metabolic_competitor"]), float)


if __name__ == "__main__":
    unittest.main()
