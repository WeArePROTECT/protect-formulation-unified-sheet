# Tests — the safety net for the decision engine

This is a **science-critical** pipeline: the formulations it ranks will be made and tested in real labs.
So the one rule is: **when we change the rules, the output must change because of the rules, not because of a
bug.** These tests exist to guarantee that. They verify the *engine logic* is correct, so any change you see
in the shortlist is the settings talking, never a coding error.

## ▶ When to run them (please do this every time)
**Run `bash tests/run_tests.sh` every time you change any of these**, before trusting the new output:
- `config/formulation_criteria.yaml` — the switchboard (gates, ranking, missing-data policy)
- `config/thresholds.yaml` — how each column's value is computed (AMR cutoff, SCFM cutoff, …)
- anything under `build/` — the pipeline code itself

Rebuild the data first if you changed a threshold that feeds the card: `bash build/run_all.sh`, then run the tests.

## How to run
```bash
bash tests/run_tests.sh                 # everything, verbose
python -m unittest discover -s tests    # same, quieter
python -m unittest tests.test_golden    # one file
```

## What each file is (and what a failure means)

| File | What it checks | Needs the card built? | If it fails… |
|---|---|---|---|
| `test_units.py` | The pure functions (ID normalizer, comparators, ranking key, fallback). | No | **A real bug.** These must always pass. |
| `test_golden.py` | The whole engine on a **synthetic** dataset with a hand-computed answer (exact ranked order, tie-breaks, gate exclusions, solo fallback, unscreened tier, and that flipping a switch changes the result as predicted). | No | **A real bug** in gates/ranking/tiering. |
| `test_real_invariants.py` | **Structural invariants on the real output that hold for ANY config** (ranks contiguous, no shortlisted strain failed a gate, every excluded strain failed one, counts partition, ranked rows monotonic by the primary key). | Yes | **A real bug** — the code is wrong regardless of the numbers. |
| `test_default_snapshot.py` | The **exact funnel numbers** for the *shipped default* switchboard (739 candidates → 317 pass → 87 ranked …). | Yes | Expected **iff you intentionally changed the default config** — see below. |

The first three are **config-independent**: they must be green no matter how you set the switches. They are
the ones that actually protect you when you re-dial thresholds.

## The snapshot workflow (the one test designed to fail)
`test_default_snapshot.py` pins the numbers for the shipped defaults. If you **intentionally** change the
default switchboard, it will fail — that is the safety feature working, showing your change took effect. When
it fails after a deliberate change:
1. Confirm **`test_real_invariants.py` still passes** → structure intact → no coding bug, just different numbers.
2. Eyeball the new numbers — are they what your change was supposed to do?
3. If yes, update `EXPECTED` in `test_default_snapshot.py` to lock in the new baseline, and say why in the commit.

If the snapshot fails when you did **not** change anything, stop and investigate — something is off.

> Note: if a scientist edits the switchboard to *their* real thresholds, the snapshot test simply **skips**
> (it only applies to the shipped default criteria set). The invariant tests keep running and keep protecting them.

## Conventions
- Stdlib `unittest` only (no pandas, no pytest) — matches the rest of the project.
- Each file puts `build/` on `sys.path` and imports `heuristic_shortlist` + `lib_ids`.
- Synthetic tests use fabricated ASMA ids and made-up numbers — **no real ASMA data lives in this repo.**
