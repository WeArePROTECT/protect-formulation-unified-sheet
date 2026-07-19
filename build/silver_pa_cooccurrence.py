#!/usr/bin/env python3
"""
silver_pa_cooccurrence.py -- RELEVANCE: does a species co-occur with PA in real patient airways?

Source : Emma sparcc_PApos/out_metaG/ median_correlation.tsv + pvalues.tsv (SparCC network computed on
         PA-POSITIVE samples; axes are numeric cluster_95 ids; final_dataset_clean, see data_sources.yaml).
Meaning: SparCC correlation between each cluster and PA (cluster 737). NEGATIVE = anti-correlated with PA
         (tends to be present when PA is absent -> a natural displacer); POSITIVE = tends to co-occur with PA.
         This is real-world EVIDENCE, not proof of competition -- it complements the in-vitro competition gate.
Output : one row per cluster_95 -> pa_cooccurrence (correlation), pa_cooccurrence_p (significance).
Decisions: docs/decisions/relevance_emma_decisions.md
"""
import os
from lib_ids import write_table
from data_sources import source, is_enabled

SOURCE = "pa_cooccurrence"
PA_CLUSTER = "737"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_pa_cooccurrence")
BASE = source(SOURCE)["path"]
CORR = os.path.join(BASE, "median_correlation.tsv")
PVAL = os.path.join(BASE, "pvalues.tsv")
COLS = ["cluster_95", "pa_cooccurrence", "pa_cooccurrence_p"]


def focal_row(path, focal):
    """Return {cluster_id: value_str} for the `focal` cluster's row of a symmetric matrix TSV."""
    with open(path) as fh:
        cols = fh.readline().rstrip("\n").split("\t")[1:]
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if parts and parts[0] == focal:
                return dict(zip(cols, parts[1:]))
    return {}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    if not is_enabled(SOURCE):
        print(f"silver_pa_cooccurrence -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    corr = focal_row(CORR, PA_CLUSTER)
    pval = focal_row(PVAL, PA_CLUSTER)
    if not corr:
        print(f"silver_pa_cooccurrence -> PA cluster {PA_CLUSTER} not found in {os.path.basename(CORR)}; skipping")
        return

    rows = []
    for cid, c in corr.items():
        if cid == PA_CLUSTER:                       # skip PA's self-correlation (= 1)
            continue
        cv = num(c)
        if cv is None:
            continue
        pv = num(pval.get(cid))
        rows.append({"cluster_95": cid, "pa_cooccurrence": round(cv, 4),
                     "pa_cooccurrence_p": round(pv, 4) if pv is not None else None})
    rows.sort(key=lambda r: r["pa_cooccurrence"])   # most anti-correlated (displacers) first
    n = write_table(rows, COLS, OUT)

    anti = [r for r in rows if r["pa_cooccurrence"] < 0]
    top = ", ".join(f"{r['cluster_95']}({r['pa_cooccurrence']})" for r in rows[:3])
    print(f"silver_pa_cooccurrence -> {n} clusters vs PA (cluster {PA_CLUSTER})")
    print(f"    anti-correlated with PA (candidate displacers): {len(anti)}")
    print(f"    most anti-correlated: {top}")


if __name__ == "__main__":
    main()
