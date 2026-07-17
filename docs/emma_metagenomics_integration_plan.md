# Emma's Metagenomics Integration Plan (for the next agent)

**Ask (Sun-Young, 2026-07-17):** fold Emma's **metaG abundance** and her **PA co-occurrence** analysis into
the sheet. Spencer agreed. This doc is the scoped plan from an exploration of Emma's directory on 2026-07-17.
It says exactly which files to use, how to build the two columns, and the one real blocker to resolve first.

**Goal columns on the gold sheet (joined BY SPECIES NAME to our GTDB species):**
- `airway_ubiquity` (already a reserved column): how prevalent/abundant each species is in patient airway metagenomes.
- `pa_cooccurrence` (new column): how each species co-occurs with *P. aeruginosa* across patient samples.

---

## Canonical source (use this, ignore the rest)
**`/usr2/people/protect/Zengler_Lab/Emma/final_dataset_clean/`** (built 2026-06-18, has a `README.md`).
This is the corrected, cleaned set: 159 samples, 149 after depth-filter + omics pairing. It supersedes the
older exploratory variants.

**Do NOT use (outdated / superseded):** the `analysis_cluster95_prok*` variant dirs (`_prok`, `_filt_genome15/25/66`,
`_filt_readbased25`), `analysis_cluster97*`, and any `features_subset10_metaRS_manual/*.tsv` that still carry the
OLD PRO222-225 columns (Emma's README lists exactly which tables were corrected). When in doubt, prefer files
under `final_dataset_clean/` and confirm with Emma.

---

## Column 1: airway abundance / ubiquity (the EASIER one, species-named)
**Source:** `final_dataset_clean/ogu_species.tsv` — `#FeatureID` is a **plain species name** (e.g.
`Pseudomonas aeruginosa`, `Abiotrophia sp001815865`), 611 species x 159 sample columns (counts). Sample columns
look like `PRO101_metaRS_respiratory_custom_subset10_align`.
- **Caveat (decide with Sun-Young / Emma):** this `ogu_species.tsv` in `final_dataset_clean/` is **metaRS**
  (metatranscriptomics, RNA activity), not metaG (DNA abundance). Sun-Young asked for **metaG** abundance.
  The metaG species-level table lives in the original woltka output (look for
  `PRO_metaRS/.../features_subset10_metaG/ogu_species.tsv` or a `features_subset10_metaG/` sibling). Confirm the
  correct metaG species table before computing. The metaG counts were "untouched" by the PRO222-225 correction
  (per README), so the metaG species table may be usable as-is.
- **Compute per species:** prevalence = fraction of samples with count > 0; mean_relative_abundance = normalize
  each sample column to its sum, then average across samples. Emit `silver_airway_abundance` keyed by species.
- **Join:** by species name to our GTDB `species`. Most match; normalize GTDB suffixes (`Neisseria_B` etc.) and
  handle `sp######` codes. Reuse the `norm_species` idea from `build/gold_unified_sheet.py`.

## Column 2: PA co-occurrence (the HARDER one, has a blocker)
**Source:** `final_dataset_clean/sparcc_PApos/out_metaG/` — SparCC network computed on **PA-positive samples**:
- `median_correlation.tsv` — species-species SparCC correlations. **Axis labels are NUMERIC cluster_95 ids**
  (`#OTU ID` = 102, 103, ...), NOT species names.
- `pvalues.tsv` — significance for each pair. `median_covariance.tsv` — covariances.
- **PA = cluster id `737`** (confirmed: it is column 298 in the matrix header, and MIND uses 737 as the PA focal id).
- **To build the column:** pull the `737` (PA) row/column from `median_correlation.tsv` -> each cluster's SparCC
  correlation with PA, attach its p-value, then map cluster id -> species. Positive = co-occurs with PA (in
  PA-positive lungs); negative = anti-correlated (candidate displacer). Emit `silver_pa_cooccurrence` keyed by species.

### The cluster_95 id -> species / ASMA map (RESOLVED 2026-07-17)
SparCC and MIND use **numeric cluster_95 ids**. The map lives in **`Emma/custom_database/`** (it is NOT in the
Arkin bridge / linkage v4 / integration / lakehouse data, which were checked on 2026-07-17 and do not carry
metagenomic clusters):
- `genome_to_cluster_95.map` — genome accession -> cluster_95 id (e.g. `ASMA1061  520`)
- `genome_to_species_full.map` — genome accession -> species (e.g. `ASMA1068  Streptococcus salivarius`)
- `taxonomy_metadata.tsv` — `accession, genus, species`

**Big bonus:** the genome accessions ARE our ASMA isolate ids (Emma built her metagenomic reference DB from the
ASMA genome collection: `ASMA1058` = `ASMA-1058`, `ABREPORTER` = the AB reporter). So cluster_95 -> species is a
join of the two maps, AND we can map cluster_95 -> ASMA id -> our strain groups directly, which is cleaner than
fuzzy species-name matching.

**Recipe:** group `genome_to_cluster_95.map` by cluster id; each cluster's members are ASMA genomes; attach
species via `genome_to_species_full.map` (should be consistent within a cluster; if not, take the dominant
species). PA = cluster **737** (corroborated by MIND focal id 737 and `ABREPORTER` = 738); confirm by checking
that the PA ASMA genomes map to 737. **Note:** ASMA ids here have NO hyphen (`ASMA1298`), so normalize to
`ASMA-1298` via `lib_ids.normalize_asma_id` (it already handles this) before joining to our sheet.

## Optional third signal (MIND, metabolic, not metagenomic)
`final_dataset_clean/MIND/data/`:
- `MIND_PA_competitors_per_sample.tsv` (`sample, focal_species, competitor, competition_score`; numeric cluster
  ids; focal 737 = PA) = metabolic-modeling prediction of which species compete with PA per sample.
- `MIND_PA_abundance_metaG.tsv` (`sample, pa_percent`) = PA relative abundance per sample.
These are MIND (metabolic) outputs, related to but distinct from metagenomic co-occurrence. Consider a
`pa_metabolic_competitor` column later; not required for Sun-Young's two asks.

---

## Recommended build order for the next agent
1. Confirm the **metaG** species abundance table (vs the metaRS one in `final_dataset_clean/`) with Emma/SYK.
2. Build `silver_airway_abundance` (prevalence + mean rel. abundance per species) and wire `airway_ubiquity`
   into the gold card. This is unblocked and delivers value immediately.
3. Build the cluster_95 -> ASMA / species map from `Emma/custom_database/` (recipe above; already located, not
   blocked). Then build `silver_pa_cooccurrence` (PA = 737) and add a `pa_cooccurrence` column, joining via
   ASMA id -> strain group (cleaner than species names).
4. Decisions to confirm with SYK/Emma: metaG vs metaRS for abundance; SparCC on PA-positive samples
   (`sparcc_PApos`) vs all samples (`sparcc/`); whether to include the MIND metabolic-competitor signal.
5. Keep it config-driven and provisional, and log the choices in `docs/decisions/` like the other sheets.

**All of this joins to the sheet by species, so it is additive: it fills the reserved `airway_ubiquity`
column and adds `pa_cooccurrence`, with no change to the existing gates.**
