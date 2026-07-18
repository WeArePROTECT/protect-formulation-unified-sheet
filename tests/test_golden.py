"""
test_golden.py -- end-to-end engine behavior on a SYNTHETIC dataset with a hand-computed
answer. Because we control every input, we know the exact right output, so any logic bug in
gates / ranking / tie-breaking / fallback / missing-data / tiering shows up here.

CONFIG-INDEPENDENT and data-free: uses fabricated strains + an in-memory config, so it runs
anywhere (no build needed) and must always pass. Drives the pure H.assemble(rows, cfg).
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build"))
import heuristic_shortlist as H          # noqa: E402

FIELDS = ["strain_group", "representative_asma_id", "genus", "species", "n_isolates",
          "is_candidate", "hemolysis_beta", "amr_resistance_count_prov", "grows_scfm",
          "comp_best_team_pa", "comp_best_solo_pa"]


def strain(**kw):
    r = {f: "" for f in FIELDS}
    r["n_isolates"] = "1"
    r.update(kw)
    return r


# 8 fabricated strains chosen to exercise every branch. Expected outcome noted per row.
SYNTH = [
    strain(strain_group="S1", is_candidate="True", hemolysis_beta="N", amr_resistance_count_prov="0",
           grows_scfm="Y", comp_best_team_pa="90"),                       # pass; rank by 90,Y
    strain(strain_group="S2", is_candidate="True", hemolysis_beta="N", amr_resistance_count_prov="0",
           grows_scfm="N", comp_best_team_pa="90"),                       # pass; ties S1 on 90 but N -> below S1
    strain(strain_group="S3", is_candidate="True", hemolysis_beta="N", amr_resistance_count_prov="1",
           grows_scfm="Y", comp_best_team_pa="80"),                       # pass; 80
    strain(strain_group="S4", is_candidate="True", hemolysis_beta="Y", amr_resistance_count_prov="0",
           grows_scfm="Y", comp_best_team_pa="95"),                       # EXCLUDED: hemolytic (best comp, still out)
    strain(strain_group="S5", is_candidate="True", hemolysis_beta="N", amr_resistance_count_prov="3",
           grows_scfm="Y", comp_best_team_pa="85"),                       # EXCLUDED: MDR (>2)
    strain(strain_group="S6", is_candidate="True", hemolysis_beta="N", amr_resistance_count_prov="0",
           grows_scfm="Y", comp_best_team_pa="", comp_best_solo_pa="70"),  # pass; uses SOLO fallback = 70
    strain(strain_group="S7", is_candidate="True", hemolysis_beta="N", amr_resistance_count_prov="0",
           grows_scfm="Y", comp_best_team_pa="", comp_best_solo_pa=""),    # pass gates, UNSCREENED (no comp)
    strain(strain_group="S8", is_candidate="False", hemolysis_beta="N", amr_resistance_count_prov="0",
           grows_scfm="Y", comp_best_team_pa="99"),                       # filtered out: not a candidate
]

CFG = {
    "candidates_only": True,
    "criteria": [
        {"name": "non_hemolytic", "column": "hemolysis_beta", "mode": "gate",
         "pass_when": "== N", "missing": "pass"},
        {"name": "amr_not_mdr", "column": "amr_resistance_count_prov", "mode": "gate",
         "pass_when": "<= 2", "missing": "pass"},
        {"name": "grows_in_scfm", "column": "grows_scfm", "mode": "rank",
         "higher_is_better": True, "missing": "rank_last"},
        {"name": "beats_pa", "column": "comp_best_team_pa", "column_fallback": "comp_best_solo_pa",
         "mode": "rank", "higher_is_better": True, "missing": "rank_last"},
    ],
    "ranking": {"order": ["beats_pa", "grows_in_scfm"], "unscreened_tier": True},
}


def build(cfg):
    pool = H.select_pool(SYNTH, cfg)
    out_rows, out_cols, evals, gates, order, primary = H.assemble(pool, cfg)
    return {r["strain_group"]: r for r in out_rows}, out_rows


class TestGoldenDefault(unittest.TestCase):
    def setUp(self):
        self.by, self.rows = build(CFG)

    def test_non_candidate_filtered_out(self):
        self.assertNotIn("S8", self.by)
        self.assertEqual(len(self.rows), 7)

    def test_exact_ranked_order_and_positions(self):
        # hand-computed: sort by beats_pa desc, ties broken by grows_scfm desc
        #   S1(90,Y) > S2(90,N) > S3(80,Y) > S6(70,Y)
        ranked = [r["strain_group"] for r in self.rows if r["status"] == "shortlist"]
        self.assertEqual(ranked, ["S1", "S2", "S3", "S6"])
        self.assertEqual([self.by[s]["rank"] for s in ["S1", "S2", "S3", "S6"]], [1, 2, 3, 4])

    def test_tie_broken_by_secondary_key(self):
        # S1 and S2 both have beats_pa=90; the SCFM grower (S1) must rank above the non-grower (S2)
        self.assertLess(self.by["S1"]["rank"], self.by["S2"]["rank"])

    def test_gate_failures_excluded_with_reason(self):
        self.assertEqual(self.by["S4"]["status"], "excluded")
        self.assertIn("non_hemolytic", self.by["S4"]["gates_failed"])
        self.assertEqual(self.by["S5"]["status"], "excluded")
        self.assertIn("amr_not_mdr", self.by["S5"]["gates_failed"])

    def test_strong_competitor_still_excluded_by_safety(self):
        # S4 has the BEST competition (95) but is hemolytic -> must not be on the shortlist
        self.assertEqual(self.by["S4"]["rank"], None)

    def test_solo_fallback_recorded(self):
        self.assertEqual(self.by["S6"]["status"], "shortlist")
        self.assertEqual(self.by["S6"]["source_beats_pa"], "comp_best_solo_pa")
        self.assertEqual(str(self.by["S6"]["value_beats_pa"]), "70")

    def test_unscreened_strain_tiered_not_dropped(self):
        self.assertEqual(self.by["S7"]["status"], "shortlist_unscreened")
        self.assertIsNone(self.by["S7"]["rank"])
        self.assertEqual(self.by["S7"]["value_beats_pa"], "")


class TestGoldenSwitchesBite(unittest.TestCase):
    """Prove that flipping a switch changes the result in the exact predicted way."""

    def test_flip_viability_to_hard_gate(self):
        cfg = copy.deepcopy(CFG)
        for c in cfg["criteria"]:
            if c["name"] == "grows_in_scfm":
                c["mode"] = "gate"
                c["pass_when"] = "== Y"
        by, rows = build(cfg)
        # S2 (grows N) now fails the viability gate and drops off
        self.assertEqual(by["S2"]["status"], "excluded")
        self.assertIn("grows_in_scfm", by["S2"]["gates_failed"])
        self.assertEqual([r["strain_group"] for r in rows if r["status"] == "shortlist"],
                         ["S1", "S3", "S6"])

    def test_missing_fail_policy_excludes_untested(self):
        # add a competition gate with missing:fail -> the unscreened strain S7 is now excluded
        cfg = copy.deepcopy(CFG)
        cfg["criteria"].append({"name": "has_comp", "column": "comp_best_team_pa",
                                "column_fallback": "comp_best_solo_pa", "mode": "gate",
                                "pass_when": ">= 0", "missing": "fail"})
        by, _ = build(cfg)
        self.assertEqual(by["S7"]["status"], "excluded")
        self.assertIn("has_comp", by["S7"]["gates_failed"])

    def test_candidates_only_false_admits_non_candidate(self):
        cfg = copy.deepcopy(CFG)
        cfg["candidates_only"] = False
        by, _ = build(cfg)
        self.assertIn("S8", by)                       # the pathogen-flagged strain is now scored
        self.assertEqual(by["S8"]["rank"], 1)         # comp 99 -> tops the ranking


if __name__ == "__main__":
    unittest.main()
