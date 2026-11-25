#!/usr/bin/env python3
"""
silver_amr_genomic.py — SAFETY: antibiotic-resistance genes in the genome.

Source : Alex amrfinder.tsv (AMRFinderPlus; one row per predicted element per isolate).
Meaning: a second, independent read on resistance — counts resistance genes found in the DNA.
         Complements the wet-lab measured AMR. `Type == AMR` picks true resistance genes
         (the file also lists STRESS/VIRULENCE elements, which we exclude from the AMR count).
Output : one row per ASMA_id — how many AMR genes, how many distinct drug classes, and the
         class list.

2026-11-19 (PROTECT-61), for Alex's AMRFinderPlus rerun of 2026-11-10:
  * The "screened, nothing found" row now carries FOUR FILLED provenance columns (assembly_type,
    assembler, amrfinder_organism, run_mode). The no-hit test ignores them; before this, it found
    none of the 945 such rows and counted each as one element (an isolate with nothing read 1).
  * POINT MUTATIONS (Subtype POINT, e.g. gyrA_S83L) are new in that run. Whether they count toward
    amr_gene_count is the team-owned switch safety.amr_genomic.count_point_mutations in
    config/thresholds.yaml. They always count toward total_elements, which counts every element.
"""
import os
from collections import defaultdict
from lib_ids import normalize_asma_id, read_delimited, write_table
from data_sources import source, is_enabled
from config import CFG

SOURCE = "amr_genomic"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_amr_genomic")
SRC = source(SOURCE)["path"]
COLS = ["asma_id", "amr_gene_count", "amr_class_count", "amr_classes",
        "total_elements", "assay", "tool", "source_file"]
# Columns Alex's compile adds to every row since 2026-11-10. They describe WHAT was screened (the
# assembly and how AMRFinder ran), so they are filled even on a "screened, nothing found" row and
# must not count against it being one.
PROVENANCE = ("assembly_type", "assembler", "amrfinder_organism", "run_mode")


def is_no_hit_placeholder(row):
    """True for a 'screened, zero hits found' row — not an element that was found.

    Alex records an isolate that ran through the tool and came back empty as one row
    whose every AMRFinder field is the literal string 'NA' (asma_id aside, and, since his
    2026-11-10 compile, the four PROVENANCE columns, which are filled). It is a coverage
    marker, not a hit, so it must not count toward `total_elements` (which otherwise
    reads 1 for an isolate that has nothing). The isolate still gets an output row —
    screened-and-clean is a real, different answer from never-screened (absent).
    (Same convention in the sibling metaVF.tsv, if we ever add the virulence add-on.)
    """
    values = [v for k, v in row.items() if k != "ASMA_id" and k not in PROVENANCE]
    return bool(values) and all(str(v).strip() == "NA" for v in values)


def is_point_mutation(row):
    return str(row.get("Subtype", "")).strip().upper() == "POINT"


def aggregate(rows, count_point_mutations):
    """{asma_id: {"amr", "classes", "total"}} from the source rows (one place, so the tests reuse it)."""
    agg = defaultdict(lambda: {"amr": 0, "classes": set(), "total": 0})
    for row in rows:
        aid = normalize_asma_id(row.get("ASMA_id"))
        if not aid:
            continue
        a = agg[aid]                      # touch: keeps screened-but-empty isolates in the output
        if is_no_hit_placeholder(row):
            continue                      # screened, nothing found -> contributes no elements
        a["total"] += 1
        if str(row.get("Type", "")).strip().upper() == "AMR":
            if is_point_mutation(row) and not count_point_mutations:
                continue                  # an element, but not a gene (the team's switch)
            a["amr"] += 1
            cls = str(row.get("Class") or "").strip()
            if cls:
                a["classes"].add(cls)
    return agg


def main():
    if not is_enabled(SOURCE):
        print(f"silver_amr_genomic -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    count_points = bool(CFG["safety"]["amr_genomic"]["count_point_mutations"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    agg = aggregate(read_delimited(SRC), count_points)

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
    print(f"silver_amr_genomic -> {n} isolates | with >=1 AMR gene: {with_amr} | "
          f"point mutations {'COUNTED' if count_points else 'not counted'} as genes")


if __name__ == "__main__":
    main()
