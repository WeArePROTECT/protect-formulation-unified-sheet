# Bronze Manifest — the raw sources behind our silver & gold

**What this is:** a pointer list. "Bronze" = the raw, original data files as their owners maintain them.
We do **NOT copy** these into the project (they're big and owned by others) — we record their **exact server
address**, who owns them, and which silver/gold outputs they feed. If a path here ever breaks, that's the
first thing to check.

**Convention:** raw (bronze, pointed-to here) → cleaned (silver, `../silver/`) → combined (gold, `../gold/`).
Everything keys on the canonical `ASMA_id` (see `build/lib_ids.py`).

Last updated: 2026-07-15. Preliminary flags reflect owner notes at that date — verify against the live file.

---

## SAFETY gate

| Source file (exact address) | Owner | What it holds | Feeds |
|---|---|---|---|
| `/usr2/people/protect/Arkin_Lab/hilzinger/hemolysis/ASMArep_HemolysisResultsSummary_063026_ASMAid.xlsx` | Cassandra Reyes (via Jake) | α/β hemolysis at 24/48/72 h, per isolate (1,638 rows) | `silver_hemolysis` |
| `/usr2/people/protect/Arkin_Lab/hilzinger/hemolysis/cassie rep plate_well_sorted.xlsx` | Cassandra Reyes | Rep-plate w/ curated Strain Group / Representative / Genus / Species (306 rows) | interim taxonomy (now superseded by Alex's gtdbtk/mash below) |
| `/usr2/people/protect/Arkin_Lab/hilzinger/hemolysis/HemolysisScreenPlateManifests.xlsx` | Cassandra Reyes | Plate→well layout maps | provenance only |
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260714.xlsx` → sheet `Antibiotic_resistance_v2` | Sun-Young Kim (he/him) | Measured abx growth-under-drug for 6 antibiotics + ΔOD600 QC (~2,350 rows) | `silver_amr_measured` |
| `/usr2/people/alex.styer/protect/ASMA/amrfinder.tsv` | Alex Styer | Predicted AMR genes, one row per gene per isolate (~34k rows) | `silver_amr_genomic` |
| `/usr2/people/alex.styer/protect/ASMA/metaVF.tsv` | Alex Styer | Predicted virulence factors (sibling of AMR; optional safety input) | `silver_amr_genomic` (virulence add-on) |

## VIABILITY gate

| Source | Owner | Holds | Feeds |
|---|---|---|---|
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260714.xlsx` → sheet `Growth_endpoint` | SYK | SCFM_72 / SCFM_mucin_0.5_72 grow-no-grow + BHIS/No_Carbon controls (~2,361 rows) | `silver_growth_endpoint` |
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260714.xlsx` → sheet `Growth_Curve_single_96` | SYK | 96-well single-carbon growth curves, cyc=10 min (~1,537 rows) | `silver_growth_curves` |

## COMPETITION gate

| Source | Owner | Holds | Feeds |
|---|---|---|---|
| `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260714.xlsx` → sheet `Competition` (**Standard conditions only**) | SYK | Inhibition of PA reporter by 1–5-member SynComs (~27,667 rows) | `silver_competition` + `formulations` |

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

## RELEVANCE  *(derived, later)*

Use Emma's **`final_dataset_clean/`** only (canonical; other `analysis_cluster*` variants are outdated). Full
scoping + join recipe: `docs/emma_metagenomics_integration_plan.md`.

| Source (exact path) | Owner | Holds | Feeds |
|---|---|---|---|
| `Zengler_Lab/Emma/final_dataset_clean/ogu_species.tsv` (species x samples; this one is metaRS, metaG species table TBD) | Emma | per-species airway abundance | `silver_airway_abundance` -> `airway_ubiquity` |
| `Zengler_Lab/Emma/final_dataset_clean/sparcc_PApos/out_metaG/median_correlation.tsv` + `pvalues.tsv` | Emma | SparCC co-occurrence with PA (**PA = cluster 737**) | `silver_pa_cooccurrence` -> new `pa_cooccurrence` |
| `Zengler_Lab/Emma/custom_database/genome_to_cluster_95.map` + `genome_to_species_full.map` | Emma | cluster_95 id -> ASMA / species (keyed by our ASMA ids) | joins Emma's metaG data to our strains |
| `Zengler_Lab/Emma/final_dataset_clean/MIND/data/MIND_PA_competitors_per_sample.tsv` | Emma | metabolic competitors of PA (optional) | future `pa_metabolic_competitor` |
| `patient_sample_isolate_linkage` v4 (`Arkin_Lab/protect_data/patient_sample_isolate_linkage_data/`) | Arkin data | ASMA_id -> patient (patient prevalence) | `silver_airway_abundance` |

## NOT YET ON SERVER (can't be bronze until delivered)
- **Tissue damage + tissue competition** — Gwyn (local). | **Mouse** — Fatemeh (local). | **BSL-1 list** — Gwyn.

---

### Reference
- Alex's own manifest (authoritative for the genomics files above): `/usr2/people/alex.styer/protect/MANIFEST.md`
- Our data catalog (discovery layer): `/usr2/people/protect/protect-data-manifest/`
