#!/usr/bin/env python3
"""
silver_amr_genomic.py — SAFETY: antibiotic-resistance genes in the genome.

Source : Alex amrfinder.tsv (AMRFinderPlus; one row per predicted element per isolate).
Meaning: a second, independent read on resistance — counts resistance genes found in the DNA.
         Complements the wet-lab measured AMR. `Type == AMR` picks true resistance genes
         (the file also lists STRESS/VIRULENCE elements, which we exclude from the AMR count).
Output : one row per ASMA_id — how many AMR genes, how many distinct drug classes, and the
         class list.
"""
import os
from collections import defaultdict
from lib_ids import normalize_asma_id, read_delimited, write_table
from data_sources import source, is_enabled

SOURCE = "amr_genomic"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_amr_genomic")
SRC = source(SOURCE)["path"]
COLS = ["asma_id", "amr_gene_count", "amr_class_count", "amr_classes",
        "total_elements", "assay", "tool", "source_file"]


def main():
    if not is_enabled(SOURCE):
        print(f"silver_amr_genomic -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    agg = defaultdict(lambda: {"amr": 0, "classes": set(), "total": 0})
    for row in read_delimited(SRC):
        aid = normalize_asma_id(row.get("ASMA_id"))
        if not aid:
            continue
        a = agg[aid]
        a["total"] += 1
        if str(row.get("Type", "")).strip().upper() == "AMR":
            a["amr"] += 1
            cls = str(row.get("Class") or "").strip()
            if cls:
                a["classes"].add(cls)

    rows = []
    for aid, a in agg.items():
        rows.append({
            "asma_id": aid, "amr_gene_count": a["amr"], "amr_class_count": len(a["classes"]),
            "amr_classes": ";".join(sorted(a["classes"])), "total_elements": a["total"],
            "assay": "amr_genomic", "tool": "AMRFinderPlus", "source_file": os.path.basename(SRC),
        })
    rows.sort(key=lambda r: int(r["asma_id"].split("-")[1]))
    n = write_table(rows, COLS, OUT)
    with_amr = sum(1 for r in rows if r["amr_gene_count"] > 0)
    print(f"silver_amr_genomic -> {n} isolates | with >=1 AMR gene: {with_amr}")


if __name__ == "__main__":
    main()
