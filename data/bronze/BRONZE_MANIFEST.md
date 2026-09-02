# Bronze Manifest — the raw sources behind our silver & gold

**What this is:** a pointer list. "Bronze" = the raw, original data files as their owners maintain them.
We do **NOT copy** these into the project (they're big and owned by others) — we record their **exact server
address**, who owns them, and which silver/gold outputs they feed. If a path here ever breaks, that's the
first thing to check.

**Convention:** raw (bronze, pointed-to here) → cleaned (silver, `../silver/`) → combined (gold, `../gold/`).
Everything keys on the canonical `ASMA_id` (see `build/lib_ids.py`).

> **Machine-readable companion:** `config/data_sources.yaml` is the registry the build actually reads (each
> source's exact path, version, on/off switch, and the gold columns it provides). This doc is the human-readable
> narrative; the YAML is the source of truth the builders load. Keep them consistent.

Last updated: 2026-09-02. Preliminary flags reflect owner notes at that date — verify against the live file.

---

## SAFETY gate

| Source file (exact address) | Owner | What it holds | Feeds |
|---|---|---|---|
| `…/current_tasks_8_2026/cassie_hemolysis_data_inventory/data/hemolysis/ASMArep_HemolysisResultsSummary_FollowUps_08122026.xlsx` | Cassandra Reyes (departed 2026-08-13) | α/β hemolysis at 24/48/72 h per isolate (base sheet, 1,638 rows) **plus a `Follow Up Results` sheet: 144 re-screen rows / 143 isolates, run 2026-07-21 and 07-28, carrying freezer `Vial_box_id` / `Vial_location_id`** | `silver_hemolysis` |
| ~~`/usr2/people/protect/Arkin_Lab/hilzinger/hemolysis/ASMArep_HemolysisResultsSummary_063026_ASMAid.xlsx`~~ | Cassandra Reyes (via Jake) | **SUPERSEDED 2026-08-12** by the row above, which contains this sheet byte-identically. Retained for audit. | — |
| `/usr2/people/protect/Arkin_Lab/hilzinger/hemolysis/cassie rep plate_well_sorted.xlsx` | Cassandra Reyes | Rep-plate w/ curated Strain Group / Representative / Genus / Species (306 rows) | interim taxonomy (now superseded by Alex's gtdbtk/mash below) |
| `/usr2/people/protect/Arkin_Lab/hilzinger/hemolysis/HemolysisScreenPlateManifests.xlsx` | Cassandra Reyes | Plate→well layout maps | provenance only |
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260828.xlsx` → sheet `Antibiotic_resistance_v2` | Sun-Young Kim (he/him) | Measured abx growth-under-drug for 6 antibiotics + ΔOD600 QC (~2,350 rows) | `silver_amr_measured` |
| `/usr2/people/alex.styer/protect/ASMA/amrfinder.tsv` | Alex Styer | Predicted AMR genes, one row per gene per isolate (~34k rows) | `silver_amr_genomic` |
| `/usr2/people/alex.styer/protect/ASMA/metaVF.tsv` | Alex Styer | Predicted virulence factors (sibling of AMR; optional safety input) | `silver_amr_genomic` (virulence add-on) |

## VIABILITY gate

| Source | Owner | Holds | Feeds |
|---|---|---|---|
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260828.xlsx` → sheet `Growth_endpoint` | SYK | SCFM_72 / SCFM_mucin_0.5_72 grow-no-grow + BHIS/No_Carbon controls (~2,361 rows) | `silver_growth_endpoint` |
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260828.xlsx` → sheet `Growth_Curve_single_96` | SYK | 96-well single-carbon growth curves, cyc=10 min (~1,537 rows) | `silver_growth_curves` |

## COMPETITION gate

| Source | Owner | Holds | Feeds |
|---|---|---|---|
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260828.xlsx` → sheet `Competition` (**Standard conditions only**) | SYK | Inhibition of PA reporter by 1–5-member SynComs (28,928 rows, measured 2026-09-02) | `silver_competition` + `formulations` |

## TISSUE gate  *(2026-07-21 — Gwyneth's airway-tissue model; PRELIMINARY, supplementary, NON-gating)*

Built from **Gwyneth's OWN computed analysis workbooks** (her co-culture statistics files + M21 LY workbook),
hand-extracted with row-level provenance into two curated tables. Her data is **private** (ACL: Spencer + Gwyn).
Full audit trail (every number → her file/sheet): `docs/tissue_provenance_and_method.md`; coverage gaps:
`docs/tissue_gaps_for_gwyn.md`; ADR: `docs/decisions/tissue_stat_sheet_decisions.md`.
**To add a study:** append rows to the two CSVs (same columns + provenance), bump `version` in
`config/data_sources.yaml`, re-run. Source workbooks live under `gahr/data_grab_7_21_26*/`.

| Source (exact address) | Owner | What it holds | Feeds |
|---|---|---|---|
| `gahr/CURATED/tissue_results/tissue_efficacy_v1.csv` | Gwyneth Hutchinson | per (study × tissue × formulation) % PA suppression on tissue, from her computed mCherry analyses (6 rows, 3 studies) | `silver_tissue` → `tissue` |
| `gahr/CURATED/tissue_results/tissue_barrier_v1.csv` | Gwyneth Hutchinson | per (study × tissue × strain) control-subtracted Lucifer-Yellow barrier change, monoculture (9 rows, 3 studies) | `silver_tissue` → `tissue_damage` |

## IDENTITY / TAXONOMY  *(← the unblock: Alex's manifest, confirmed 2026-07-15)*

| Source | Owner | Holds | Feeds |
|---|---|---|---|
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_list.xlsx` | SYK | Canonical isolate universe + stock location (3,972 rows) | `identity_spine` (rows) |
| `/usr2/people/alex.styer/protect/ASMA/gtdbtk/gtdbtk-summary.tsv` | Alex Styer | GTDB taxonomy; `sample_id` = ASMA_id → `classification` lineage (~5,719 assembly rows; dedup per isolate) | `identity_spine` (species/genus) |
| `/usr2/people/alex.styer/protect/ASMA/mash/clusters.csv` | Alex Styer | **Canonical strain groups**: genome(ASMA_id) → cluster + is_representative (4,371 rows) | `identity_spine` (strain grain + representative) |
| `/usr2/people/alex.styer/protect/ASMA/gtdbtk/assembly-manifest.tsv` | Alex Styer | `genome_id` (`ASMA-###__assembler`) → `sample_id` (ASMA_id) | ID reconciliation reference |
| `/usr2/people/alex.styer/protect/ASMA/fastani/ani-clusters.csv` | Alex Styer | Alternate strain groups (>99% ANI) + rep list | cross-check for strain grain |

## METABOLIC  *(Alex's lane — later)*

| Source | Owner | Holds | Feeds |
|---|---|---|---|
| `/usr2/people/alex.styer/protect/ASMA/gapmind-carbon-rules.tsv`, `gapmind-aa-rules.tsv`, `gapmind-manifest.tsv`, `c-sources.xlsx` | Alex Styer | In-silico metabolic capabilities + suggested partners | `silver_gapmind` (Alex) |

## RELEVANCE  *(BUILT 2026-07-18: airway abundance + PA co-occurrence + MIND metabolic competitor)*

Use Emma's **`20260728_final_dataset_clean/`** only, and within it **`MIND_152/`, not `MIND/`** (updated
2026-09-02). Her `README_RERUN.md`: that directory is a full mirror of `final_dataset_clean/` re-run end to
end on the updated cohort, **161 raw / 152 paired / 47 patients** (previously 159 / 149 / 45).
**Do not use `final_dataset_clean/`: it is mixed-vintage**, holding a 152-sample count table beside SparCC
(2026-06-22) and MIND (2026-06-26) outputs computed on the 149-sample cohort and never refreshed.
**Trap:** the new directory contains BOTH `MIND/` (copied across unchanged, 149-sample, 860 rows) and
`MIND_152/` (re-run 2026-08-05, 152-sample, 895 rows). Keeping the old relative path while changing the
directory silently keeps the old numbers. `custom_database/` is a sibling of both dated dirs, so it is
unaffected. The directory is still being worked in (files modified 2026-09-01); ask Emma before treating
it as frozen. All Emma data
joins to our strains via **cluster_95 ids (which ARE our ASMA genomes); PA = cluster 737**. ADR:
`docs/decisions/relevance_emma_decisions.md`. (Original scoping: `docs/emma_metagenomics_integration_plan.md`.)

| Source (exact path) | Owner | Holds | Feeds |
|---|---|---|---|
| `Zengler_Lab/Emma/custom_database/genome_to_cluster_95.map` + `genome_to_species_full.map` | Emma | cluster_95 id <-> ASMA / species (keyed by our ASMA ids) | `silver_emma_map` (the join backbone) |
| `Zengler_Lab/Emma/20260728_final_dataset_clean/multiomics_paired_depthfiltered_raw.tsv` (cluster x 152 metaG + 152 metaRS, raw counts; byte-identical to the copy in the old dir) | Emma | airway abundance, DNA + RNA | `silver_airway_abundance` -> `abundance_/prevalence_metag`, `_metars` |
| `Zengler_Lab/Emma/20260728_final_dataset_clean/sparcc_PApos/out_metaG/median_correlation.tsv` + `pvalues.tsv` (recomputed 2026-07-28; note `pvalues.tsv` is the SAME SIZE in both dirs but different content, compare by checksum) | Emma | SparCC co-occurrence with PA (PA-positive samples) | `silver_pa_cooccurrence` -> `pa_cooccurrence` (+`_p`) |
| `Zengler_Lab/Emma/20260728_final_dataset_clean/**MIND_152**/data/MIND_PA_competitors_per_sample.tsv` (895 rows) | Emma | MIND metabolic-competitor prediction (focal PA=737) | `silver_pa_metabolic_competitor` -> `pa_metabolic_competitor` |

## NOT YET ON SERVER (can't be bronze until delivered)
- **Mouse** — Fatemeh (local). | **BSL-1 list** — Gwyn (still local).
- *(Tissue landed 2026-07-21 — see the TISSUE gate above. Still `needs_review`; more M21 studies pending from Gwyn.)*

---

### Reference
- Alex's own manifest (authoritative for the genomics files above): `/usr2/people/alex.styer/protect/MANIFEST.md`
- Our data catalog (discovery layer): `/usr2/people/protect/protect-data-manifest/`
