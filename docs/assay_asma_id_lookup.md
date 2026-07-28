# `assay_asma_id_lookup` — how it was made and where it came from

**What this is:** a lookup table at **`data/gold/assay_asma_id_lookup.csv`** mapping each strain group to the
actual ASMA isolate used in the wet-lab phenotype assays (growth, in-vitro AMR, hemolysis), shown next to the
genomic representative isolate. Built for Sun-Young Kim (requested 2026-07-27) so the team can pull the correct,
experimentally-validated, **arrayed** stock for each strain group when finalizing the candidate list.

> **Status: INTERIM / stopgap.** The same `assay_asma_id` value is planned to become a first-class column on the
> gold sheet itself (and will be documented in `docs/gold_data_dictionary.md` + an ADR at that point). Once that
> lands, this standalone file and doc can be retired.

## Why it exists
The gold sheet shows `representative_asma_id`, the genomically-correct representative of each strain group (from
Alex's whole-genome clustering). But the wet-lab assays were frequently run on a **different isolate of the same
strain group**, the one with an arrayed stock. As of 2026-07-27, the assay isolate differs from the genomic
representative in **299 of the 717** assayed groups. Knowing the actual assay isolate makes it much easier to go
back to the correct, reliably-workable stock.

## Where the data came from (sources)
It is derived entirely from tables already produced by this project's pipeline (rebuild them with
`bash build/run_all.sh`). No new external source was introduced.

| Input file (in this project) | What it provides here | Ultimately sourced from (owner) |
|---|---|---|
| `data/reference/identity_isolates.csv` | isolate -> strain-group membership | Alex Styer's mash clustering + GTDB (`identity_spine.py`) |
| `data/reference/identity_strains.csv` | strain group -> `representative_asma_id`, `species` | same (Alex) |
| `data/silver/silver_hemolysis.csv` | which isolates were run in the **hemolysis** assay | Cassandra Reyes' blood-agar screen (via Jake), `silver_hemolysis.py` |
| `data/silver/silver_amr_measured.csv` | which isolates were run in the **measured-AMR** assay | Sun-Young Kim's antibiotic panel, `silver_amr_measured.py` |
| `data/silver/silver_growth_endpoint.csv` | which isolates were run in the **SCFM growth** assay | Sun-Young Kim's growth screen, `silver_growth_endpoint.py` |

The exact **raw** server paths behind those silver/reference tables are registered in `config/data_sources.yaml`
and described in `data/bronze/BRONZE_MANIFEST.md`.

## Exactly how it was built (method)
For each strain group:
1. Get its member isolates from `identity_isolates`.
2. For each of the three phenotype assays, find which of those members appear in that assay's silver table
   (presence in the table = that isolate was run in that assay).
3. `assay_asma_id` = the isolate(s) **common to all the present assays** (the set intersection). In practice this
   is the single arrayed isolate used across the trio.
4. Attach `representative_asma_id` and `species` from `identity_strains` for the side-by-side comparison.

Groups with none of the three assays are omitted. No thresholds or judgement calls are involved; it is a pure
membership intersection.

## Columns
| Column | Meaning |
|---|---|
| `strain_group` | internal strain-group id (the join key) |
| `species` | GTDB species of the group |
| `representative_asma_id` | the genomic representative isolate (the one shown on the gold sheet today) |
| `assay_asma_id` | the isolate used for the wet-lab assays (semicolon-joined if the group used more than one) |
| `assays_present` | which of `growth` / `amr` / `hemolysis` were run (e.g. `growth+amr+hemolysis` when all three) |
| `note` | flags the edge cases (see below) |

## Coverage and edge cases (verified 2026-07-27)
- **717** strain groups have at least one of the three assays (rows in the file).
- **660** have a single consistent isolate across all three assays (the clean case; `note` blank).
- **19** used two isolates across the assays; both are shown semicolon-joined and flagged in `note`.
- **38** have only some of the three assays so far; `note` says which (`only growth+amr assayed so far`, etc.).
- **0** had no common isolate, so every assayed group resolves to at least one real ASMA id.
- `assay_asma_id` differs from `representative_asma_id` in **299** groups (the reason the lookup is useful).

## How to reproduce it exactly
Rebuild the inputs (`bash build/run_all.sh`), then run this from the project root. It is read-only apart from
writing the one CSV.

```python
import csv
from collections import defaultdict

def rows(p): return list(csv.DictReader(open(p)))
def num(a):
    try: return int(a.split('-')[1])
    except: return 0

grp_members = defaultdict(list)
for r in rows('data/reference/identity_isolates.csv'):
    grp_members[r['strain_group']].append(r['asma_id'])
strn = {r['strain_group']: r for r in rows('data/reference/identity_strains.csv')}

def assayed(p): return {r['asma_id'] for r in rows(p)}
hemo = assayed('data/silver/silver_hemolysis.csv')
amr  = assayed('data/silver/silver_amr_measured.csv')
grow = assayed('data/silver/silver_growth_endpoint.csv')

out = []
for g, mems in grp_members.items():
    ms = set(mems); h = ms & hemo; a = ms & amr; gr = ms & grow
    pres = [(nm, s) for nm, s in [('growth', gr), ('amr', a), ('hemolysis', h)] if s]
    if not pres:
        continue
    common = set.intersection(*[s for _, s in pres]); ids = sorted(common, key=num)
    assays = '+'.join(nm for nm, _ in pres); all3 = bool(h and a and gr); note = ''
    if len(ids) > 1:
        note = f'{len(ids)} validated isolates for this group'
    elif len(ids) == 0:
        note = f'assays used different isolates (hemo={sorted(h,key=num)}, amr={sorted(a,key=num)}, growth={sorted(gr,key=num)})'
    if not all3 and not note:
        note = f'only {assays} assayed so far'
    s = strn.get(g, {})
    out.append({'strain_group': g, 'species': s.get('species', ''),
                'representative_asma_id': s.get('representative_asma_id', ''),
                'assay_asma_id': ';'.join(ids), 'assays_present': assays, 'note': note})

out.sort(key=lambda r: num(r['assay_asma_id'].split(';')[0]) if r['assay_asma_id'] else 0)
cols = ['strain_group', 'species', 'representative_asma_id', 'assay_asma_id', 'assays_present', 'note']
with open('data/gold/assay_asma_id_lookup.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
```
