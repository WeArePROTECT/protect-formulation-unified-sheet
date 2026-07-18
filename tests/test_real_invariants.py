"""
test_real_invariants.py -- structural invariants on the REAL current output.

These properties must hold for ANY valid switchboard, so they stay green even after you
re-dial the thresholds. That is the point: they verify the ENGINE is correct (no coding
bug) independent of what the settings are. THIS is the file to trust when you change a
setting -- if an invariant breaks, the code is wrong, not just the numbers.

Reads the built gold card; if it is not present, the tests skip with instructions (run
`bash build/run_all.sh` first). No real ASMA numbers are asserted here -- only structure.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build"))
import heuristic_shortlist as H          # noqa: E402


class TestRealInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(H.GOLD_CARD):
            raise unittest.SkipTest("gold card not built -- run `bash build/run_all.sh` first")
        cls.cfg = H.load_criteria()
        pool = H.select_pool(list(H.read_delimited(H.GOLD_CARD, ",")), cls.cfg)
        cls.pool_n = len(pool)
        cls.rows, cls.cols, cls.evals, cls.gates, cls.order, cls.primary = H.assemble(pool, cls.cfg)
        cls.gate_names = [g["name"] for g in cls.gates]

    def test_status_values_are_valid(self):
        allowed = {"shortlist", "shortlist_unscreened", "excluded"}
        self.assertTrue(all(r["status"] in allowed for r in self.rows))

    def test_every_pool_row_appears_exactly_once(self):
        self.assertEqual(len(self.rows), self.pool_n)
        self.assertEqual(len({r["strain_group"] for r in self.rows}), self.pool_n)

    def test_counts_partition(self):
        c = {s: sum(1 for r in self.rows if r["status"] == s)
             for s in ("shortlist", "shortlist_unscreened", "excluded")}
        self.assertEqual(sum(c.values()), self.pool_n)

    def test_ranks_are_contiguous_1_to_n(self):
        ranked = [r for r in self.rows if r["status"] == "shortlist"]
        self.assertEqual([r["rank"] for r in ranked], list(range(1, len(ranked) + 1)))

    def test_only_shortlist_rows_have_a_rank(self):
        self.assertTrue(all(r["rank"] is None for r in self.rows if r["status"] != "shortlist"))

    def test_no_shortlisted_strain_failed_a_gate(self):
        for r in self.rows:
            if r["status"] in ("shortlist", "shortlist_unscreened"):
                for gn in self.gate_names:
                    self.assertNotEqual(r.get(f"gate_{gn}"), "FAIL",
                                        msg=f"{r['strain_group']} on shortlist but failed {gn}")

    def test_every_excluded_strain_failed_at_least_one_gate(self):
        for r in self.rows:
            if r["status"] == "excluded":
                self.assertTrue(any(r.get(f"gate_{gn}") == "FAIL" for gn in self.gate_names),
                                msg=f"{r['strain_group']} excluded but no gate FAIL")
                self.assertNotEqual(r["gates_failed"].strip(), "")

    def test_ranked_rows_monotonic_by_primary_key(self):
        # Independent re-derivation: read the primary VALUE column back and check monotonicity
        # in the configured direction -- catches a broken sort without trusting sort_key.
        if not self.order:
            self.skipTest("no ranking configured")
        crit = next(c for c in self.cfg["criteria"] if c["name"] == self.primary)
        higher = crit.get("higher_is_better", True)
        vals = []
        for r in self.rows:
            if r["status"] == "shortlist":
                v = H.rank_value(r.get(f"value_{self.primary}"))
                self.assertIsNotNone(v, msg=f"ranked row {r['strain_group']} has no primary value")
                vals.append(v)
        pairs = list(zip(vals, vals[1:]))
        ok = all(a >= b for a, b in pairs) if higher else all(a <= b for a, b in pairs)
        self.assertTrue(ok, msg="ranked rows are not monotonic by the primary ranking key")

    def test_unscreened_rows_have_no_primary_value(self):
        if not self.order:
            self.skipTest("no ranking configured")
        for r in self.rows:
            if r["status"] == "shortlist_unscreened":
                self.assertEqual(r.get(f"value_{self.primary}"), "",
                                 msg=f"{r['strain_group']} unscreened but has a primary value")


if __name__ == "__main__":
    unittest.main()
