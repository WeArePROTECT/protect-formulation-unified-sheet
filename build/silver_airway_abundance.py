#!/usr/bin/env python3
"""
silver_airway_abundance.py -- RELEVANCE: how common/abundant each cluster is in patient airways.

Source : Emma multiomics_paired_depthfiltered_raw.tsv (cluster_95 x 149 metaG + 149 metaRS sample
         columns, raw counts; final_dataset_clean, see data_sources.yaml).
Meaning: metaG = DNA (who is PRESENT), metaRS = RNA (who is ACTIVE). Two different, both-useful reads.
         Per cluster, for each omic:
           prevalence           = fraction of samples where the cluster is present (count > 0)
           abundance (mean rel.) = mean over samples of the cluster's share of that sample's total
                                   counts, expressed as a percent of the community.
Output : one row per cluster_95. Joined to our strains (via silver_emma_map) in the gold card.
Decisions: docs/decisions/relevance_emma_decisions.md
"""
import os
from collections import Counter, defaultdict
from statistics import mean
from lib_ids import read_delimited, write_table
from data_sources import source, is_enabled

SOURCE = "airway_abundance"
HERE = os.path.dirname(os.path.abspath(__file__))
SILVER = os.path.join(os.path.dirname(HERE), "data", "silver")
OUT = os.path.join(SILVER, "silver_airway_abundance")
SRC = source(SOURCE)["path"]
COLS = ["cluster_95", "emma_species", "prevalence_metag", "abundance_metag",
        "prevalence_metars", "abundance_metars", "n_samples_metag", "n_samples_metars"]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def col_totals(rows, cols):
    """Per-sample (column) totals for an omic, so counts can be turned into relative abundance."""
    tot = {c: 0.0 for c in cols}
    for r in rows:
        for c in cols:
            v = num(r.get(c))
            if v:
                tot[c] += v
    return tot


def metrics(row, cols, totals):
    """One cluster's (prevalence, mean-relative-abundance %) over an omic's sample columns."""
    rels, present = [], 0
    for c in cols:
        v = num(row.get(c))
        if v is None:
            continue
        if v > 0:
            present += 1
            if totals[c] > 0:
                rels.append(v / totals[c])
    prevalence = round(present / len(cols), 4) if cols else None
    abundance = round(mean(rels) * 100, 5) if rels else 0.0   # mean % of the community
    return prevalence, abundance


def load_cluster_species():
    """cluster_95 -> dominant emma_species, from silver_emma_map (if built) -- for a readable label."""
    path = os.path.join(SILVER, "silver_emma_map.csv")
    if not os.path.exists(path):
        return {}
    by = defaultdict(Counter)
    for r in read_delimited(path, ","):
        if r.get("emma_species"):
            by[r["cluster_95"]][r["emma_species"]] += 1
    return {c: cnt.most_common(1)[0][0] for c, cnt in by.items()}


def main():
    if not is_enabled(SOURCE):
        print(f"silver_airway_abundance -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    os.makedirs(SILVER, exist_ok=True)

    rows = list(read_delimited(SRC, "\t"))
    if not rows:
        print("silver_airway_abundance -> no data rows found"); return
    header = list(rows[0].keys())
    metag = [c for c in header if c.endswith("_metaG")]
    metars = [c for c in header if c.endswith("_metaRS")]

    tot_g, tot_s = col_totals(rows, metag), col_totals(rows, metars)
    cluster_species = load_cluster_species()
    out = []
    for r in rows:
        cid = r.get("cluster_id")
        pg, ag = metrics(r, metag, tot_g)
        ps, as_ = metrics(r, metars, tot_s)
        out.append({"cluster_95": cid, "emma_species": cluster_species.get(cid, ""),
                    "prevalence_metag": pg, "abundance_metag": ag,
                    "prevalence_metars": ps, "abundance_metars": as_,
                    "n_samples_metag": len(metag), "n_samples_metars": len(metars)})
    out.sort(key=lambda r: -(r["prevalence_metag"] or 0))
    n = write_table(out, COLS, OUT)

    pa = next((r for r in out if r["cluster_95"] == "737"), None)
    print(f"silver_airway_abundance -> {n} clusters | samples: {len(metag)} metaG, {len(metars)} metaRS")
    if pa:
        print(f"    PA (cluster 737): metaG prevalence {pa['prevalence_metag']}, "
              f"mean abundance {pa['abundance_metag']}% ; metaRS prevalence {pa['prevalence_metars']}")


if __name__ == "__main__":
    main()
