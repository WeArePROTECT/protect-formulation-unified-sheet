#!/usr/bin/env python3
"""
silver_pa_metabolic_competitor.py -- RELEVANCE: is a species a PREDICTED metabolic competitor of PA?

Source : Emma MIND/data/MIND_PA_competitors_per_sample.tsv (MIND metabolic model; columns
         sample, focal_species, competitor, competition_score; focal 737 = PA; final_dataset_clean).
Meaning: a MODEL PREDICTION (not a wet-lab measurement) of how strongly each cluster competes with PA for
         metabolites, per patient sample. We summarize per competitor cluster: mean score across the samples
         that flagged it, and how many samples flagged it. Label it as predicted, distinct from measured data.
Output : one row per competitor cluster_95 -> pa_metabolic_competitor (mean score), n_samples, max_score.
Decisions: docs/decisions/relevance_emma_decisions.md
"""
import os
from collections import defaultdict
from statistics import mean
from lib_ids import read_delimited, write_table
from data_sources import source, is_enabled

SOURCE = "pa_metabolic_competitor"
PA_FOCAL = "737"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_pa_metabolic_competitor")
BASE = source(SOURCE)["path"]
SRC = os.path.join(BASE, "MIND_PA_competitors_per_sample.tsv")
COLS = ["cluster_95", "pa_metabolic_competitor", "n_samples", "max_score"]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    if not is_enabled(SOURCE):
        print(f"silver_pa_metabolic_competitor -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    scores = defaultdict(list)
    for r in read_delimited(SRC, "\t"):
        if str(r.get("focal_species")).strip() != PA_FOCAL:
            continue
        comp = str(r.get("competitor")).strip()
        s = num(r.get("competition_score"))
        if comp and s is not None:
            scores[comp].append(s)

    rows = []
    for cid, ss in scores.items():
        rows.append({"cluster_95": cid, "pa_metabolic_competitor": round(mean(ss), 4),
                     "n_samples": len(ss), "max_score": round(max(ss), 4)})
    rows.sort(key=lambda r: -r["pa_metabolic_competitor"])
    n = write_table(rows, COLS, OUT)
    top = ", ".join(f"{r['cluster_95']}({r['pa_metabolic_competitor']})" for r in rows[:3])
    print(f"silver_pa_metabolic_competitor -> {n} predicted PA competitor clusters (focal PA={PA_FOCAL})")
    if rows:
        print(f"    strongest predicted competitors: {top}")


if __name__ == "__main__":
    main()
