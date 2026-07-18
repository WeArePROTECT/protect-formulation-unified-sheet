#!/usr/bin/env python3
"""
silver_amr_measured.py — SAFETY: measured antibiotic resistance (wet-lab).

Source : SYK ASMA_phenotype_20260714.xlsx  ->  sheet Antibiotic_resistance_v2.
Meaning: each *_profile = how well the isolate still grew under that drug, as a % of its
         untreated growth. HIGH % = shrugs off the drug (resistant); LOW % = killed (susceptible).
QC     : SYK's rule — if the untreated control barely grew (Untreat ΔOD600 < 0.1) we can't
         trust that replicate, so we drop it.
Output : one row per ASMA_id, drug %s averaged over QC-passing replicates, plus a PROVISIONAL
         resistance count. The 50% cutoff is a placeholder for the biologists to set — we store
         the raw %s so any cutoff can be re-derived later.
"""
import os
from collections import defaultdict
from statistics import mean
from lib_ids import normalize_asma_id, read_xlsx_sheet, write_table
from config import CFG
from data_sources import source, is_enabled

SOURCE = "amr_measured"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_amr_measured")
_SRC = source(SOURCE)
SRC = _SRC["path"]
SHEET = _SRC.get("sheet")
DRUGS = ["Ampicillin", "Ciprofloxacin", "Chloramphenicol", "Tetracycline", "Gentamicin", "Erythromycin"]
# Thresholds are TEAM-OWNED — see config/thresholds.yaml. Raw %s are kept so any cutoff re-derives.
QC_MIN = CFG["safety"]["amr_measured"]["qc_min_delta_od"]
RESIST_CUTOFF = float(CFG["safety"]["amr_measured"]["resistance_cutoff_pct"])
COLS = (["asma_id"] + [f"{d.lower()}_profile" for d in DRUGS]
        + ["qc_pass", "n_reps_qc", "resistance_count_prov", "assay", "panel", "source_file"])


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    if not is_enabled(SOURCE):
        print(f"silver_amr_measured -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    agg = defaultdict(lambda: {**{d: [] for d in DRUGS}, "n": 0})
    for row in read_xlsx_sheet(SRC, SHEET):
        aid = normalize_asma_id(row.get("ASMA_id"))
        if not aid:
            continue
        qc = num(row.get("Untreat_day3-day0_OD600"))
        if qc is None or qc < QC_MIN:        # fails growth QC -> drop this replicate
            continue
        a = agg[aid]
        a["n"] += 1
        for d in DRUGS:
            val = num(row.get(f"{d}_profile"))
            if val is not None:
                a[d].append(val)

    rows = []
    for aid, a in agg.items():
        rec = {"asma_id": aid, "qc_pass": a["n"] > 0, "n_reps_qc": a["n"],
               "assay": "antibiotic_resistance", "panel": "v2 (Amp/Cipro/Chlor/Tet/Gent/Eryth)",
               "source_file": os.path.basename(SRC)}
        rc = 0
        for d in DRUGS:
            m = round(mean(a[d]), 1) if a[d] else None
            rec[f"{d.lower()}_profile"] = m
            if m is not None and m >= RESIST_CUTOFF:
                rc += 1
        rec["resistance_count_prov"] = rc
        rows.append(rec)
    rows.sort(key=lambda r: int(r["asma_id"].split("-")[1]))
    n = write_table(rows, COLS, OUT)
    print(f"silver_amr_measured -> {n} isolates (QC-passing) | provisional 'resistant' = >={RESIST_CUTOFF}% relative growth")


if __name__ == "__main__":
    main()
