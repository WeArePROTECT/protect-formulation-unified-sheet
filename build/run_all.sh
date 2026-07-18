#!/usr/bin/env bash
# run_all.sh — build the unified sheet end-to-end, in order.
# Run from anywhere: `bash run_all.sh`.  Stops on the first real error (set -e).
# Note: NumPy prints cosmetic "_ARRAY_API not found" warnings on parquet write — harmless.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-python}"

echo "== 1. roster (identity spine) =="
"$PY" identity_spine.py

echo "== 2. silver stat sheets =="
"$PY" silver_hemolysis.py
"$PY" silver_amr_measured.py
"$PY" silver_amr_genomic.py
"$PY" silver_competition.py           # COMPETITION — also writes the formulations table
"$PY" silver_growth_endpoint.py       # VIABILITY — SCFM grow/no-grow + mucin lift
# "$PY" silver_growth_curves.py       # VIABILITY — growth rate/lag (todo)

echo "== 3. gold card =="
"$PY" gold_unified_sheet.py           # strain-level decision card (.csv/.parquet/.xlsx)

echo "== 4. formulation shortlist =="
"$PY" heuristic_shortlist.py          # config-driven gates + ranking (config/formulation_criteria.yaml)

echo "== done. outputs in ../data/{reference,silver,gold} =="
echo "   tip: if you changed a threshold or the switchboard, verify with  bash tests/run_tests.sh"
