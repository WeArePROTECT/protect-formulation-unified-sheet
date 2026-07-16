#!/usr/bin/env python3
"""
identity_spine.py — the roster (row backbone of the unified sheet).

Builds TWO reference tables, both keyed on the canonical ASMA_id:
  1. identity_isolates — one row per isolate: its strain group, whether it's the
     group's representative, its species, and stock location. Used to attribute any
     assay (run on any isolate) to its strain.
  2. identity_strains  — one row per STRAIN GROUP (the decision-sheet grain): the
     representative isolate, species, and how many isolates the group holds.

Sources (all on-server; see data/bronze/BRONZE_MANIFEST.md):
  - stock universe : SYK  ASMA_list.xlsx
  - species        : Alex gtdbtk/gtdbtk-summary.tsv   (sample_id = ASMA_id -> classification)
  - strain groups  : Alex mash/clusters.csv           (canonical: genome -> cluster + is_representative)

Run:  python identity_spine.py
Out:  ../data/reference/identity_isolates.{csv,parquet}
      ../data/reference/identity_strains.{csv,parquet}
"""
import os
from collections import Counter, defaultdict

from lib_ids import normalize_asma_id, read_xlsx_sheet, read_delimited, parse_gtdb_lineage, write_table

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(os.path.dirname(HERE), "data", "reference")

STOCK_LIST = "/usr2/people/protect/Arkin_Lab/SYK/ASMA_list.xlsx"
GTDBTK = "/usr2/people/alex.styer/protect/ASMA/gtdbtk/gtdbtk-summary.tsv"
MASH = "/usr2/people/alex.styer/protect/ASMA/mash/clusters.csv"

ISO_COLS = ["asma_id", "strain_group", "is_representative", "genus", "species",
            "gtdb_classification", "in_stock", "stock_location", "stock_location_well", "growth_media"]
STR_COLS = ["strain_group", "representative_asma_id", "genus", "species",
            "n_isolates", "n_isolates_stocked"]


def load_stock():
    stock = {}
    for row in read_xlsx_sheet(STOCK_LIST):
        aid = normalize_asma_id(row.get("ASMA_id"))
        if aid and aid not in stock:
            stock[aid] = {"stock_location": row.get("stock_location"),
                          "stock_location_well": row.get("stock_location_well"),
                          "growth_media": row.get("growth_media")}
    return stock


def load_taxonomy():
    """gtdbtk-summary.tsv -> {asma_id: (genus, species, classification)} (first non-empty per id)."""
    tax = {}
    for row in read_delimited(GTDBTK):
        aid = normalize_asma_id(row.get("sample_id"))
        if not aid or aid in tax:
            continue
        cls = (row.get("classification") or "").strip()
        if not cls:
            continue
        genus, species = parse_gtdb_lineage(cls)
        tax[aid] = (genus, species, cls)
    return tax


def load_clusters():
    """mash/clusters.csv -> {asma_id: (strain_group, is_representative)}."""
    clusters = {}
    for row in read_delimited(MASH, delimiter=","):
        aid = normalize_asma_id(row.get("genome"))
        if not aid:
            continue
        clusters[aid] = (row.get("cluster"),
                         str(row.get("is_representative", "")).strip().lower() == "yes")
    return clusters


def main():
    os.makedirs(REF, exist_ok=True)
    stock = load_stock()
    tax = load_taxonomy()
    clusters = load_clusters()

    # ---- identity_isolates: base = the clustered (strain-grouped) universe ----
    iso_rows = []
    for aid in sorted(clusters, key=lambda x: int(x.split("-")[1])):
        grp, is_rep = clusters[aid]
        genus, species, cls = tax.get(aid, (None, None, None))
        st = stock.get(aid)
        iso_rows.append({
            "asma_id": aid, "strain_group": grp, "is_representative": is_rep,
            "genus": genus, "species": species, "gtdb_classification": cls,
            "in_stock": st is not None,
            "stock_location": st["stock_location"] if st else None,
            "stock_location_well": st["stock_location_well"] if st else None,
            "growth_media": st["growth_media"] if st else None,
        })

    # ---- identity_strains: one row per strain group ----
    by_group = defaultdict(list)
    for r in iso_rows:
        by_group[r["strain_group"]].append(r)

    str_rows = []
    for grp, members in by_group.items():
        rep = next((m for m in members if m["is_representative"]), members[0])
        # species: prefer representative's; else the most common non-empty in the group
        species = rep["species"]
        if not species:
            sp = Counter(m["species"] for m in members if m["species"])
            species = sp.most_common(1)[0][0] if sp else None
        genus = rep["genus"] or (parse_gtdb_lineage(None)[0])
        str_rows.append({
            "strain_group": grp, "representative_asma_id": rep["asma_id"],
            "genus": genus, "species": species,
            "n_isolates": len(members),
            "n_isolates_stocked": sum(1 for m in members if m["in_stock"]),
        })
    str_rows.sort(key=lambda r: (-r["n_isolates"], str(r["strain_group"])))

    n_iso = write_table(iso_rows, ISO_COLS, os.path.join(REF, "identity_isolates"))
    n_str = write_table(str_rows, STR_COLS, os.path.join(REF, "identity_strains"))

    # ---- summary ----
    iso_species = sum(1 for r in iso_rows if r["species"])
    iso_stocked = sum(1 for r in iso_rows if r["in_stock"])
    str_species = sum(1 for r in str_rows if r["species"])
    top = Counter(r["genus"] for r in str_rows if r["genus"]).most_common(8)
    print(f"\nidentity_isolates -> {n_iso} isolates (the strain-grouped universe)")
    print(f"    with species     : {iso_species} ({100*iso_species//max(n_iso,1)}%)")
    print(f"    in stock list    : {iso_stocked} ({100*iso_stocked//max(n_iso,1)}%)")
    print(f"identity_strains  -> {n_str} strains (ONE row per strain group = the decision grain)")
    print(f"    with species     : {str_species} ({100*str_species//max(n_str,1)}%)")
    print(f"    top genera       : {', '.join(f'{g}:{c}' for g, c in top)}")
    print(f"\nwritten to {REF}/")


if __name__ == "__main__":
    main()
