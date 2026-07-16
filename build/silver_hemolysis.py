#!/usr/bin/env python3
"""
silver_hemolysis.py — SAFETY: does the isolate break down red blood cells?

Source : Cassie's ASMArep_HemolysisResultsSummary_063026_ASMAid.xlsx (see BRONZE_MANIFEST).
Meaning: beta-hemolysis (fully lyses blood cells) is the primary "could harm the patient"
         proxy Adam named; alpha is partial. Values in the file are Y / N / (blank = not determined).
Output : one row per ASMA_id (isolate grain). Replicates/timepoints collapsed conservatively —
         a strain counts as hemolytic if it showed hemolysis in ANY replicate at ANY timepoint.
"""
import os
from collections import defaultdict
from lib_ids import normalize_asma_id, read_xlsx_sheet, write_table

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_hemolysis")
SRC = "/usr2/people/protect/Arkin_Lab/hilzinger/hemolysis/ASMArep_HemolysisResultsSummary_063026_ASMAid.xlsx"
SHEET = "ASMArep_HemolysisResultsSummary"
BETA = ["24: Beta Hemolysis?", "48: Beta Hemolysis?", "72: Beta Hemolysis?"]
ALPHA = ["24: Alpha Hemolysis?", "48: Alpha Hemolysis?", "72: Alpha Hemolysis?"]
COLS = ["asma_id", "grew", "beta_hemolytic", "alpha_hemolytic", "hemolysis_concern",
        "n_reps", "assay", "method", "source_file"]


def any_yes(vals):
    """Y if any value is Y; else N if any is N; else None (not determined)."""
    v = [str(x).strip().upper() for x in vals if x is not None and str(x).strip().lower() not in ("", "none")]
    return "Y" if "Y" in v else ("N" if "N" in v else None)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    agg = defaultdict(lambda: {"grew": [], "beta": [], "alpha": [], "n": 0})
    for row in read_xlsx_sheet(SRC, SHEET):
        aid = normalize_asma_id(row.get("ASMA_ID") or row.get("ASMA_id"))
        if not aid:
            continue
        a = agg[aid]
        a["n"] += 1
        a["grew"].append(row.get("Growth?"))
        a["beta"] += [row.get(c) for c in BETA]
        a["alpha"] += [row.get(c) for c in ALPHA]

    rows = []
    for aid, a in agg.items():
        beta = any_yes(a["beta"])
        rows.append({
            "asma_id": aid, "grew": any_yes(a["grew"]),
            "beta_hemolytic": beta, "alpha_hemolytic": any_yes(a["alpha"]),
            "hemolysis_concern": beta == "Y", "n_reps": a["n"],
            "assay": "hemolysis", "method": "blood agar (ASMArep plate)",
            "source_file": os.path.basename(SRC),
        })
    rows.sort(key=lambda r: int(r["asma_id"].split("-")[1]))
    n = write_table(rows, COLS, OUT)
    conc = sum(1 for r in rows if r["hemolysis_concern"])
    print(f"silver_hemolysis -> {n} isolates | beta-hemolytic (safety concern): {conc} | clear/other: {n - conc}")


if __name__ == "__main__":
    main()
