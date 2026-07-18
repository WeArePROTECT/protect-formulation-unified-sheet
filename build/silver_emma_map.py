#!/usr/bin/env python3
"""
silver_emma_map.py -- RELEVANCE backbone: Emma's numeric cluster_95 id <-> our ASMA id / species.

Emma's metagenomic tables (abundance, SparCC co-occurrence, MIND) are keyed by numeric cluster_95
ids, not names. Emma built her reference DB from OUR ASMA genome collection, so each cluster's member
genomes ARE our ASMA isolates -- which lets us join her cluster-level data straight to our strains.

Source : Emma custom_database/ genome_to_cluster_95.map + genome_to_species_full.map (data_sources.yaml).
Meaning: PA = cluster 737 (its members are our ASMA genomes). The AB reporter genome (ABREPORTER)
         maps to 738 and is dropped as non-ASMA by the canonical normalizer.
Output : one row per ASMA genome in Emma's DB -> asma_id, cluster_95, emma_species.
Decisions: docs/decisions/relevance_emma_decisions.md
"""
import os
from lib_ids import normalize_asma_id, write_table
from data_sources import source, is_enabled

SOURCE = "emma_cluster_map"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_emma_map")
_SRC = source(SOURCE)
BASE = _SRC["path"]
CLUSTER_MAP = os.path.join(BASE, "genome_to_cluster_95.map")
SPECIES_MAP = os.path.join(BASE, "genome_to_species_full.map")
PA_CLUSTER = "737"
COLS = ["asma_id", "cluster_95", "emma_species", "genome_accession"]


def read_pairs(path):
    """Yield (col0, col1) from a headerless TAB-separated map file."""
    with open(path) as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[0]:
                yield parts[0], parts[1]


def main():
    if not is_enabled(SOURCE):
        print(f"silver_emma_map -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    species = {g: s for g, s in read_pairs(SPECIES_MAP)}
    rows, seen, pa_asma = [], set(), []
    for genome, cluster in read_pairs(CLUSTER_MAP):
        aid = normalize_asma_id(genome)          # ABREPORTER etc. -> None (dropped as non-ASMA)
        if not aid or aid in seen:
            continue
        seen.add(aid)
        rows.append({"asma_id": aid, "cluster_95": cluster,
                     "emma_species": species.get(genome, ""), "genome_accession": genome})
        if cluster == PA_CLUSTER:
            pa_asma.append(aid)
    rows.sort(key=lambda r: int(r["asma_id"].split("-")[1]))
    n = write_table(rows, COLS, OUT)
    tail = "..." if len(pa_asma) > 6 else ""
    print(f"silver_emma_map -> {n} ASMA genomes mapped to cluster_95 ids")
    print(f"    PA (cluster {PA_CLUSTER}) ASMA genomes: {len(pa_asma)} -> {', '.join(pa_asma[:6])}{tail}")


if __name__ == "__main__":
    main()
