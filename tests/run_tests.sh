#!/usr/bin/env bash
# =============================================================================
# run_tests.sh -- the safety net for the unified-sheet decision engine.
#
# RUN THIS EVERY TIME YOU CHANGE:
#     - config/formulation_criteria.yaml   (the switchboard: gates / ranking)
#     - config/thresholds.yaml             (how column values are computed)
#     - anything under build/              (the pipeline code)
#
# Why: this is a science-critical pipeline. When we change the rules, the output
# must change because of the RULES, not because of a bug. These tests confirm the
# engine logic is correct so any change in the result is intentional, not an error.
#
# Exit code is nonzero if ANY test fails.  Usage:  bash tests/run_tests.sh
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."          # project root (imports + gold-card path resolve absolutely)
PY="${PY:-python}"

echo "== unified-sheet test suite =="
echo "   (unit + golden are data-free; real-invariants + snapshot need the card built)"
echo
"$PY" -m unittest discover -s tests -p 'test_*.py' -v
