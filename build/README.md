# Build — how the unified sheet is assembled (in pieces)

Data arrives from different people at different times, so we **build incrementally**. Every assay keys on
`ASMA_id` at **isolate grain**, so each piece is independent — we build each stat sheet as its data lands,
then roll everything up to **strain grain** (780 strain groups) for the final card. Nothing built now is wasted.

## Naming convention (data-engineering + human-readable)
Files are named **`<layer>_<content>.py`** — no numeric prefixes. The layer tells you the stage; the content
tells you what it is. Run-order lives here (the table below) and in `run_all.sh`, not in the filenames.
- `lib_ids.py` — shared helpers (the canonical ID cleaner + IO).
- `identity_*` — the roster (reference tables).
- `silver_*` — one cleaned stat sheet per assay.
- `formulations` / `gold_*` — combine steps.
- **Versioning:** code history is tracked by **git** (no `_v2.py` copies). **Data outputs** may be dated/versioned.

## Pipeline (run order + status)

| Script | Produces | Status |
|---|---|---|
| `identity_spine.py` | `identity_isolates` (4,365) + `identity_strains` (780 = decision grain) | ✅ done |
| `silver_hemolysis.py` | per-isolate hemolysis (SAFETY) | ✅ done |
| `silver_amr_measured.py` | per-isolate measured antibiotic resistance (SAFETY) | ✅ done |
| `silver_amr_genomic.py` | per-isolate AMR-gene load (SAFETY) | ✅ done |
| `silver_competition.py` | per-strain PA knock-down + synergy (COMPETITION) + the `formulations` table | ✅ done · decisions in `docs/decisions/competition_stat_sheet_decisions.md` |
| `gold_unified_sheet.py` | strain-level decision card (`.xlsx` + `.csv`/`.parquet`) | ✅ done · decisions in `docs/decisions/gold_unified_sheet_decisions.md` |
| `silver_growth_endpoint.py` | SCFM ± mucin grow/no-grow (VIABILITY) | ✅ done · decisions in `docs/decisions/viability_stat_sheet_decisions.md` |
| `silver_growth_curves.py` | derived growth rate/lag (VIABILITY) | ⬜ unblocked |
| `heuristic_shortlist.py` | strawman gates → ranked shortlist | 🔒 after team buy-in |

Legend: ✅ done · ⬜ buildable now · 🔒 gated on buy-in.

## Grain: isolate → strain
`silver_*` tables are at **isolate grain** (one row per ASMA_id). `gold_unified_sheet.py` maps each isolate to
its strain group via `identity_isolates`, then aggregates to **strain grain** (worst-case for safety, best-case
for competition). Most assays were run on the strain's representative isolate, so the mapping is usually 1:1.

## Conventions
- **IDs:** everything through `lib_ids.normalize_asma_id` → canonical `ASMA-<int>`. Reporter/blank tokens dropped.
- **No pandas** (NumPy 1.x/2.x ABI noise → cosmetic `_ARRAY_API` stderr spam; files still write). openpyxl to read; `.csv` + `.parquet` out.
- **Every silver table carries assay/method/source columns** so joins never compare mismatched experiments.
- **Provisional thresholds are labeled `_prov`** and store the raw values — the biologists set the real cutoffs.
- **Thresholds are team-owned:** every cutoff/policy is in `config/thresholds.yaml` (read via `build/config.py`),
  never hard-coded. Safety/candidacy classification is in `data/reference/species_safety.csv` (interim -> Gwyn's
  BSL-1 list). See `docs/decisions/thresholds_are_team_owned.md`.

## Run
`bash run_all.sh` (from `build/`) runs the whole pipeline in order. Outputs land in `../data/{reference,silver,gold}`.

## Sources
All raw inputs are pointed to (not copied) in `../data/bronze/BRONZE_MANIFEST.md`.
