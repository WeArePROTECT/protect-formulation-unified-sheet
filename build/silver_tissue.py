#!/usr/bin/env python3
"""
silver_tissue.py — TISSUE: does a formulation reduce PA on airway tissue (efficacy), and does a strain
                    harm the epithelial barrier (safety)?

Source : Gwyneth Hutchinson's OWN computed tissue analyses (her co-culture statistics workbooks + M21 LY
         workbooks), hand-extracted with full provenance into two curated, fully-sourced tables:
           tissue_efficacy_v1.csv  — one row per (study x tissue x formulation): % PA suppression on tissue
           tissue_barrier_v1.csv   — one row per (study x tissue x strain monoculture): control-subtracted
                                     Lucifer-Yellow barrier change (percentage-passage points)
         Every row carries the exact source file + sheet + derivation.
         Provenance, method, coverage, and KNOWN GAPS: docs/tissue_provenance_and_method.md  <- read this.
Design decisions: docs/decisions/tissue_stat_sheet_decisions.md

!! PRELIMINARY. Gwyneth's tissue program is mid-analysis; this covers only the studies she has computed so far
   (a subset of her competition studies). It is a supplementary, NON-gating confirmation layer on the sheet.

Rollup (team-owned knobs in config/thresholds.yaml -> tissue:):
  efficacy  -> best PA suppression as a formulation member  (like competition: a strain gets its strongest team)
  safety    -> worst monoculture barrier change per strain  (conservative: flag any barrier disruption)

Output:
  silver_tissue : one row per STRAIN (asma_id) -> tissue_pa_reduction (efficacy) + tissue_barrier_delta (safety)
                  + the winning formulation / study and evidence counts, for the gold card and full traceability.
"""
import os
from statistics import mean, median
from collections import defaultdict
from lib_ids import normalize_asma_id, read_delimited, write_table
from config import CFG
from data_sources import source, is_enabled

SOURCE = "tissue"
HERE = os.path.dirname(os.path.abspath(__file__))
SILVER = os.path.join(os.path.dirname(HERE), "data", "silver")

_T = CFG.get("tissue", {})
PA_AGG = _T.get("pa_reduction_aggregation", "max")     # efficacy: how a strain's formulations combine
DMG_AGG = _T.get("barrier_aggregation", "max")         # safety: how a strain's monoculture barrier rows combine

STRAIN_COLS = ["asma_id", "tissue_pa_reduction", "tissue_pa_best_formulation", "tissue_pa_best_study",
               "tissue_pa_best_tissue", "n_tissue_efficacy_rows",
               "tissue_barrier_delta", "tissue_barrier_worst_study", "tissue_barrier_worst_tissue",
               "n_tissue_barrier_rows", "assay", "source"]


def _key(aid):
    return int(aid.split("-")[1])


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _members(s):
    return [m for m in (normalize_asma_id(x) for x in str(s or "").split("+")) if m]


def _agg(vals, how):
    if not vals:
        return None
    if how == "mean":
        return mean(vals)
    if how == "median":
        return median(vals)
    if how == "min":
        return min(vals)
    return max(vals)                          # default best/worst-case


def main():
    if not is_enabled(SOURCE):
        print(f"silver_tissue -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    src = source(SOURCE)
    root, files = src["path"], src.get("files", [])
    eff_path = os.path.join(root, files[0]) if files else ""
    bar_path = os.path.join(root, files[1]) if len(files) > 1 else ""
    if not (os.path.exists(eff_path) and os.path.exists(bar_path)):
        print(f"silver_tissue -> source files not found under {root}; skipping (tissue columns stay blank)")
        return
    os.makedirs(SILVER, exist_ok=True)

    # ---- EFFICACY: a strain gets the PA suppression of every formulation it is a member of ----
    eff_vals = defaultdict(list)               # asma -> [pa_suppression across its formulations]
    eff_top = {}                               # asma -> (best value, formulation, study, tissue)
    for r in read_delimited(eff_path, ","):
        v = _num(r.get("pa_suppression_pct"))
        if v is None:
            continue
        for X in _members(r.get("members_asma")):
            eff_vals[X].append(v)
            if X not in eff_top or v > eff_top[X][0]:
                eff_top[X] = (v, r.get("formulation", ""), r.get("study", ""), r.get("tissue", ""))

    # ---- SAFETY: a strain's own monoculture barrier change on tissue ----
    bar_vals = defaultdict(list)               # asma -> [control-subtracted barrier delta]
    bar_top = {}                               # asma -> (worst/max value, study, tissue)
    for r in read_delimited(bar_path, ","):
        X = normalize_asma_id(r.get("strain_asma"))
        v = _num(r.get("barrier_delta_pct_ctrlsub"))
        if v is None or not X:
            continue
        bar_vals[X].append(v)
        if X not in bar_top or v > bar_top[X][0]:      # max = most leaky = worst-case for safety
            bar_top[X] = (v, r.get("study", ""), r.get("tissue", ""))

    rows = []
    for X in sorted(set(eff_vals) | set(bar_vals), key=_key):
        pa = _agg(eff_vals.get(X, []), PA_AGG)
        bar = _agg(bar_vals.get(X, []), DMG_AGG)
        rows.append({
            "asma_id": X,
            "tissue_pa_reduction": round(pa, 1) if pa is not None else None,
            "tissue_pa_best_formulation": eff_top[X][1] if X in eff_top else None,
            "tissue_pa_best_study": eff_top[X][2] if X in eff_top else None,
            "tissue_pa_best_tissue": eff_top[X][3] if X in eff_top else None,
            "n_tissue_efficacy_rows": len(eff_vals.get(X, [])),
            "tissue_barrier_delta": round(bar, 2) if bar is not None else None,
            "tissue_barrier_worst_study": bar_top[X][1] if X in bar_top else None,
            "tissue_barrier_worst_tissue": bar_top[X][2] if X in bar_top else None,
            "n_tissue_barrier_rows": len(bar_vals.get(X, [])),
            "assay": "tissue_coculture",
            "source": "CURATED/tissue_results/{tissue_efficacy_v1,tissue_barrier_v1}.csv",
        })
    n = write_table(rows, STRAIN_COLS, os.path.join(SILVER, "silver_tissue"))

    with_pa = sum(1 for r in rows if r["tissue_pa_reduction"] is not None)
    with_bar = sum(1 for r in rows if r["tissue_barrier_delta"] is not None)
    print(f"silver_tissue -> {n} strains with tissue data  [efficacy_agg={PA_AGG}, barrier_agg={DMG_AGG}]")
    print(f"    strains with a PA-suppression % (efficacy): {with_pa}")
    print(f"    strains with a barrier change (safety)    : {with_bar}")
    print(f"    PRELIMINARY — Gwyneth's own computed numbers, partial coverage. See docs/tissue_provenance_and_method.md")


if __name__ == "__main__":
    main()
