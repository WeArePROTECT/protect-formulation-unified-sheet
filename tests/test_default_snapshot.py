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

# The exact funnel for the shipped defaults.
# Update ONLY when you intentionally change the default switchboard, OR when a data source is
# deliberately swapped to a newer version (see module docstring).
#
# REBASELINED 2026-08-12 -- hemolysis data swapped 063026 -> 08122026.
#   Cassie Reyes delivered a second round of follow-up re-screens on her last day. The new file is
#   a strict superset: base sheet byte-identical, plus a `Follow Up Results` sheet resolving
#   isolates whose original read was unreliable. Merge policy `union` (config/data_sources.yaml).
#   The switchboard itself is UNCHANGED. test_real_invariants.py passed throughout, so the
#   movement is data, not a coding bug.
#
#   Among the 739 candidates, the beta call moved:
#       Y     336 -> 358   (+22 newly confirmed beta-hemolytic, now fail the safety gate)
#       N     288 -> 305   (+17 newly confirmed clean)
#       blank 115 ->  76   (-39 resolved; 22 + 17 = 39, reconciles exactly)
#   Note `fail_non_hemolytic` counts affirmative Y only; a blank is non-evaluable, not a failure.
#
#   Previous baseline (063026, verified 2026-07-18):
#       pass_gates 317 | ranked 87 | unscreened 230 | excluded 422 | fail_non_hemolytic 336
#
# REBASELINED AGAIN 2026-08-13 -- followup_policy union -> followup_wins.
#   Cassie Reyes, the assay owner, answered the open merge-policy question before leaving:
#   "I would trust the rescreen call over the original call. If it was followed up on in the
#    rescreen, it is because I didn't trust the original call for some reason."
#   Data and switchboard both UNCHANGED; only the merge policy moved. test_real_invariants.py
#   passed throughout.
#
#   9 strain groups flipped beta Y -> N, so among the 739 candidates:
#       Y     358 -> 349   N  305 -> 314   blank 76 (unchanged)
#   Of those 9: 3 still fail amr_not_mdr (sg 773, 670, 49), 3 pass gates with competition data
#   (sg 612, 75, 80) so ranked +3, and 3 pass gates without it so unscreened +3.
#
#   Baseline under 'union' (2026-08-13 midday):
#       pass_gates 299 | ranked 82 | unscreened 217 | excluded 440 | fail_non_hemolytic 358
#
# REBASELINED AGAIN 2026-09-02 -- SYK workbook 20260714 -> 20260828, and Emma's relevance sources
# repointed to her full re-run directory. Done as part of PROTECT-15 (lakehouse push), so that the
# bronze tables going on the lakehouse and the gold card built from them cite one source generation.
#   SYK   : ASMA_phenotype_20260714.xlsx -> ASMA_phenotype_20260828.xlsx
#           (Competition 27,667 -> 28,928 rows; sheet names unchanged, verified before the run)
#   Emma  : final_dataset_clean/ -> 20260728_final_dataset_clean/, and MIND/ -> MIND_152/.
#           Her README_RERUN.md: the new dir is a full mirror re-run end to end on the updated
#           cohort, 161 raw / 152 paired / 47 patients (was 159 / 149 / 45). The old dir is
#           mixed-vintage: a 152-sample count table sitting next to 149-sample SparCC and MIND
#           outputs that were never refreshed. Within the NEW dir, MIND/ was copied across
#           unchanged and still holds 149-sample results; MIND_152/ is the 2026-08-05 re-run.
#   The switchboard itself is UNCHANGED. test_real_invariants.py passed throughout.
#
#   The movement is entirely one thing: 11 strains that passed both gates but had never been
#   screened against PA now have a competition result. Verified by diffing the old card against
#   the new one before replacing it:
#       unscreened -> ranked : 11  (sg 17, 239, 247, 284, 413, 427, 518, 619, 620, 647, 736)
#       ranked -> unscreened :  0
#       any other status move:  0
#       strains whose gate_non_hemolytic value changed: 0
#       strains whose gate_amr_not_mdr    value changed: 0
#   So pass_gates, excluded, and both gate-failure counts are all unchanged, and ranked +11 is
#   exactly offset by unscreened -11. The three strongest new entries are Enterobacter hormaechei_B
#   (69.9), Neisseria mucosa_A (23.7) and Klebsiella grimontii (21.3); note the latter two genera
#   already carry BSL-2 flags, so this is data arriving, not a recommendation.
#
#   Other tables moved in VALUE without moving the funnel, which is why the gate counts held:
#   silver_amr_measured, silver_growth_endpoint (SYK revised numbers between July and August) and
#   silver_pa_cooccurrence (all 313 rows, SparCC recomputed on 152 samples). None crossed a
#   threshold. silver_amr_genomic changed in exactly one column, total_elements, in exactly 943
#   rows -- that is the separate no-hit-placeholder fix in commit 7402feb, not a data swap.
#
#   Previous baseline (20260714 + final_dataset_clean, verified 2026-08-13):
#       pass_gates 305 | ranked 85 | unscreened 220 | excluded 434 | fail_non_hemolytic 349
#
# REBASELINED AGAIN 2026-10-01 -- SYK workbook 20260828 -> 20260929 (his Month 24 update), plus
# three rules that came with it (tests/test_m24_sources.py pins each one). PROTECT-29, PROTECT-34.
#   SYK   : ASMA_phenotype_20260828.xlsx -> ASMA_phenotype_20260929.xlsx (he asked for 0929 or
#           later). Competition 28,928 -> 30,536 rows; ASMA-4467 removed at source.
#   Rules : (1) ASMA-4467's 2 hemolysis rows dropped via the shared retractions.csv (wrong strain
#           in FREP5 well B9); (2) SCFM_10X_glucose wells left out of every score
#           (competition.exclude_media); (3) the PA reporter set read from config, 19 not 5.
#   The switchboard itself is UNCHANGED. test_real_invariants.py passed throughout.
#
#   Verified by diffing the old card against the new one before replacing it:
#       status moves: exactly ONE -- sg 259 (Streptococcus vaginalis, ASMA-4467)
#                     excluded -> shortlist_unscreened, both gates FAIL/pass -> untested.
#                     It has NO hemolysis result now, and `missing: pass` lets it through as
#                     UNTESTED; read it as "safety unknown", not "safe", until SYK re-tests.
#       gate value moves: only sg 259's two.
#       value_beats_pa moves (no status change): sg 284 -0.2 -> 19.7, sg 647 -7.2 -> 38.1,
#                     sg 580 0.2 -> 24.5, sg 482 -7.2 -> 26.3 (new team results with ASMA-3643);
#                     sg 583 (ASMA-4486) 37.0 -> 22.0 after a new replicate run.
#   Rule (2) is why ranked did NOT move: without it sg 11 (ASMA-1228) entered the ranked list at
#   #97 on 10x-glucose wells alone, and sg 770 blended both media in one score.
#
#   Previous baseline (20260828, verified 2026-09-02):
#       pass_gates 305 | ranked 96 | unscreened 209 | excluded 434 | fail_non_hemolytic 349
EXPECTED = {
    "candidates": 739,
    "pass_gates": 306,        # shortlist + shortlist_unscreened (was 305; +1 = sg 259)
    "ranked": 96,             # status == shortlist            UNCHANGED (see rule 2 above)
    "unscreened": 210,        # status == shortlist_unscreened (was 209; +1 = sg 259, untested)
    "excluded": 433,          # status == excluded             (was 434; -1 = sg 259)
    "fail_non_hemolytic": 348,  # (was 349; sg 259's retracted beta-hemolysis call)
    "fail_amr_not_mdr": 215,    # UNCHANGED
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
