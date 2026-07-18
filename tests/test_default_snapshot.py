"""
test_default_snapshot.py -- a golden SNAPSHOT of the shipped default switchboard's numbers.

This is the "well-known result" test. With config/formulation_criteria.yaml at its shipped
defaults, the funnel is exactly the numbers in EXPECTED below.

>>> IF YOU INTENTIONALLY CHANGE THE DEFAULT SWITCHBOARD, THIS TEST IS DESIGNED TO FAIL. <<<
That failure is the safety feature working: it proves your edit took effect and shows the new
result. The workflow when it fails after a deliberate change:
    1. Confirm test_real_invariants.py STILL PASSES  (structure intact -> no coding bug).
    2. Eyeball the new numbers -- are they what you intended the change to do?
    3. If yes, update EXPECTED below to lock in the new baseline (and note why in a commit).
If it fails when you did NOT change the config, something is wrong -- investigate before trusting output.

Skips if the gold card is not built, or if the switchboard's criteria set differs from the
shipped default (then the snapshot is N/A, but the invariants in test_real_invariants.py still apply).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build"))
import heuristic_shortlist as H          # noqa: E402

# The shipped default criteria set (by name + mode). If this changes, the snapshot is N/A.
DEFAULT_CRITERIA = [
    ("non_hemolytic", "gate"),
    ("amr_not_mdr", "gate"),
    ("grows_in_scfm", "rank"),
    ("beats_pa", "rank"),
]

# The exact funnel for the shipped defaults (verified 2026-07-18 against the preliminary card).
# Update ONLY when you intentionally change the default switchboard (see module docstring).
EXPECTED = {
    "candidates": 739,
    "pass_gates": 317,        # shortlist + shortlist_unscreened
    "ranked": 87,             # status == shortlist
    "unscreened": 230,        # status == shortlist_unscreened
    "excluded": 422,          # status == excluded
    "fail_non_hemolytic": 336,
    "fail_amr_not_mdr": 215,
}


class TestDefaultSnapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(H.GOLD_CARD):
            raise unittest.SkipTest("gold card not built -- run `bash build/run_all.sh` first")
        cls.cfg = H.load_criteria()
        cls.actual_criteria = [(c["name"], c.get("mode")) for c in cls.cfg.get("criteria", [])]
        pool = H.select_pool(list(H.read_delimited(H.GOLD_CARD, ",")), cls.cfg)
        cls.pool_n = len(pool)
        cls.rows, cls.cols, cls.evals, cls.gates, cls.order, cls.primary = H.assemble(pool, cls.cfg)

    def setUp(self):
        if self.actual_criteria != DEFAULT_CRITERIA:
            self.skipTest("switchboard differs from shipped default -- snapshot N/A "
                          "(structural invariants in test_real_invariants.py still apply)")

    def _count(self, status):
        return sum(1 for r in self.rows if r["status"] == status)

    def test_candidate_pool_size(self):
        self.assertEqual(self.pool_n, EXPECTED["candidates"])

    def test_funnel_counts(self):
        self.assertEqual(self._count("shortlist"), EXPECTED["ranked"])
        self.assertEqual(self._count("shortlist_unscreened"), EXPECTED["unscreened"])
        self.assertEqual(self._count("excluded"), EXPECTED["excluded"])
        self.assertEqual(self._count("shortlist") + self._count("shortlist_unscreened"),
                         EXPECTED["pass_gates"])

    def test_per_gate_failure_counts(self):
        fail = {g["name"]: sum(1 for e in self.evals if g["name"] in e["failed"]) for g in self.gates}
        self.assertEqual(fail["non_hemolytic"], EXPECTED["fail_non_hemolytic"])
        self.assertEqual(fail["amr_not_mdr"], EXPECTED["fail_amr_not_mdr"])


if __name__ == "__main__":
    unittest.main()
