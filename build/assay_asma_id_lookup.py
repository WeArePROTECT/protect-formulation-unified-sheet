#!/usr/bin/env python3
"""
assay_asma_id_lookup.py — per strain group, the arrayed isolate actually used in the wet-lab assays.

The detailed companion to the gold card's `assay_asma_id` column: it adds `assays_present` and an
edge-case `note`. Method and history: docs/assay_asma_id_lookup.md.

WHY THIS IS A BUILD STEP (2026-10-01). Until then this table was made once, on 2026-07-27, by a script
pasted into that doc, and never regenerated. Every later rebuild refreshed the card's column but left
this file frozen at July, and the 2026-09-03 lakehouse push shipped it as protect.curated
.assay_asma_id_lookup. It surfaced when ASMA-4467 was retracted (PROTECT-34): the card dropped it as
strain group 259's assay isolate, the July file still named it. Same logic as the doc's script,
now run by build/run_all.sh after the silver tables it reads, and pinned against the card by
tests/test_m24_sources.py.
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
OUT = os.path.join(DATA, "gold", "assay_asma_id_lookup.csv")
COLS = ["strain_group", "species", "representative_asma_id", "assay_asma_id", "assays_present", "note"]


def rows(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(fh))


def num(a):
    try:
        return int(a.split("-")[1])
    except (IndexError, ValueError):
        return 0


def main():
    grp_members = defaultdict(list)
    for r in rows(os.path.join(DATA, "reference", "identity_isolates.csv")):
        grp_members[r["strain_group"]].append(r["asma_id"])
    strn = {r["strain_group"]: r for r in rows(os.path.join(DATA, "reference", "identity_strains.csv"))}

    def assayed(name):
        return {r["asma_id"] for r in rows(os.path.join(DATA, "silver", name))}

    hemo = assayed("silver_hemolysis.csv")
    amr = assayed("silver_amr_measured.csv")
    grow = assayed("silver_growth_endpoint.csv")

    out = []
    for g, mems in grp_members.items():
        ms = set(mems)
        h, a, gr = ms & hemo, ms & amr, ms & grow
        pres = [(nm, s) for nm, s in [("growth", gr), ("amr", a), ("hemolysis", h)] if s]
        if not pres:
            continue
        common = set.intersection(*[s for _, s in pres])
        ids = sorted(common, key=num)
        assays = "+".join(nm for nm, _ in pres)
        all3 = bool(h and a and gr)
        note = ""
        if len(ids) > 1:
            note = f"{len(ids)} validated isolates for this group"
        elif len(ids) == 0:
            note = (f"assays used different isolates (hemo={sorted(h, key=num)}, "
                    f"amr={sorted(a, key=num)}, growth={sorted(gr, key=num)})")
        if not all3 and not note:
            note = f"only {assays} assayed so far"
        s = strn.get(g, {})
        out.append({"strain_group": g, "species": s.get("species", ""),
                    "representative_asma_id": s.get("representative_asma_id", ""),
                    "assay_asma_id": ";".join(ids), "assays_present": assays, "note": note})

    out.sort(key=lambda r: num(r["assay_asma_id"].split(";")[0]) if r["assay_asma_id"] else 0)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(out)
    multi = sum(1 for r in out if ";" in r["assay_asma_id"])
    diff = sum(1 for r in out if r["assay_asma_id"] and r["assay_asma_id"] != r["representative_asma_id"])
    print(f"assay_asma_id_lookup -> {len(out)} assayed strain groups | {multi} with two isolates | "
          f"{diff} differ from the genomic representative")


if __name__ == "__main__":
    main()
