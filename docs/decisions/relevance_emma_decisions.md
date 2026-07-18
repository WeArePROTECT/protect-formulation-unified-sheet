# Decision Record — Relevance layer (Emma metagenomics)

**Purpose:** why the airway-relevance columns are built the way they are. These add a real-world dimension on
top of the three lab gates: is a strain actually a common, active resident of patient airways, and (later) does
it co-occur with or displace PA in real lungs. Human- and agent-readable ADR.

**Status:** active · **Created:** 2026-07-18 · **Owner:** Spencer (+ Alex) · **Data owner:** Emma (Zengler lab)
**Code:** `build/silver_emma_map.py`, `build/silver_airway_abundance.py` · **Registry:** `config/data_sources.yaml`
**Data state:** Emma `final_dataset_clean` (built 2026-06-18); treat as current, see D1.

---

## Context
The gates answer lab questions (safe? grows? beats PA in a dish?). Emma's metagenomics answers a different one:
is the strain **relevant** to real airways? We fold in her patient-sample data as additive columns, joined to our
strains, with no change to the gates. This ADR covers the shipped piece (airway abundance) and the shared
backbone; PA co-occurrence and the MIND metabolic-competitor signal follow the same pattern (see "not yet").

## Decisions

### D1 — Canonical source = `final_dataset_clean/` (verified current 2026-07-18)
- **Chosen:** use only `Zengler_Lab/Emma/final_dataset_clean/` (README: built 2026-06-18, the corrected set that
  supersedes the older `analysis_cluster*` variants).
- **Why / checked:** the sibling `PRO_metaRS_actuallast/` (an alarming name) holds only raw `.fastq.gz`
  re-sequencing inputs, not processed tables, so it does not supersede anything we use. Every source path is
  pinned in `data_sources.yaml` with a version label, and a test asserts each path exists on disk (currency).
  **Revisit if:** Emma ships a newer processed set — bump the `version`/`path` in the registry and re-run + re-test.

### D2 — The cluster_95 ↔ ASMA backbone (`silver_emma_map.py`)
- Emma's tables are keyed by **numeric cluster_95 ids**, not names. She built her reference DB from OUR ASMA
  genomes, so each cluster's member genomes ARE our ASMA isolates. We map `genome_to_cluster_95.map` +
  `genome_to_species_full.map` -> one asma_id -> cluster_95 -> species table (779 ASMA genomes mapped).
- **PA = cluster 737** (15 ASMA members: ASMA-1298, ASMA-1341, ...). The AB reporter genome maps to 738 and is
  dropped as non-ASMA by `lib_ids.normalize_asma_id`. This backbone serves abundance, co-occurrence, and MIND.

### D3 — Ship BOTH metaG and metaRS (Spencer, 2026-07-18: "use all of it")
- **Chosen:** `abundance_metag`/`prevalence_metag` (DNA = who is PRESENT) and `abundance_metars`/`prevalence_metars`
  (RNA = who is ACTIVE), as four separate columns.
- **Why:** they answer different questions and both are useful; picking one throws away signal. The team can rank
  on either (or neither) via the switchboard. Labeled clearly so RNA-activity is never confused with DNA-presence.

### D4 — Abundance math: transparent per-sample relative abundance
- **prevalence** = fraction of samples where the cluster is present (count > 0). **abundance** = mean over samples
  of the cluster's share of that sample's total counts, as a percent of the community.
- **Options:** use Emma's pre-normalized CPM table · normalize the raw paired counts ourselves.
- **Chosen:** normalize the raw `multiomics_paired_depthfiltered_raw.tsv` (149 metaG + 149 metaRS samples)
  ourselves — one obvious, inspectable definition, no dependence on an upstream normalization choice.
  **Revisit if:** the team prefers CPM or a different summary (one function, `metrics()`, changes).

### D5 — Grain: Emma is cluster_95 (coarser than our strain); each strain gets its cluster's value
- Emma's cluster_95 is a 95%-identity grouping, **coarser** than our >99% strain groups, so several of our
  strains can share one Emma cluster. On the card, a strain takes the abundance of the cluster its isolates map
  to (dominant cluster across the strain's members). **Honest limitation:** relevance is at species/cluster
  resolution, not strain resolution. Coverage: 673 of 739 candidates carry abundance.

### D6 — Additive; supersedes the reserved `airway_ubiquity` placeholder; gates untouched
- The four abundance columns replace the single blank `airway_ubiquity` reserved column with clearer,
  source-labeled values. Nothing about Safety/Viability/Competition changes. Whether abundance becomes a
  ranking key is the team's call — it is one line in `formulation_criteria.yaml` once they want it.

### D7 — On/off + provenance via the registry
- `emma_cluster_map` and `airway_abundance` are switches in `data_sources.yaml`; turning either off blanks the
  relevance columns, and the shortlist engine warns if a criterion then depends on them.

## Sanity check at build
779 ASMA genomes mapped; PA cluster 737 = 15 ASMA members; 315 clusters scored (149 metaG + 149 metaRS samples);
PA (737) metaG prevalence 1.0, mean abundance ~22% (dominant, as expected for a focal pathogen); top commensals
by prevalence = Rothia / Streptococcus salivarius (abundant airway residents, several also strong PA knockdowns).

## Things intentionally NOT decided here / not yet built
- **PA co-occurrence** (`silver_pa_cooccurrence`, SparCC PA-positive, PA=737) and **MIND metabolic competitor**
  (`silver_pa_metabolic_competitor`) — declared in the registry, builders to follow the same cluster->strain join.
- **Whether relevance gates or ranks** — team-owned (switchboard). We ship the columns, not the policy.
- **metaG vs metaRS preference** — we ship both; the team chooses which (if either) to rank on.

## Change log
- 2026-07-18 — initial version (D1–D7): backbone map + airway abundance (metaG + metaRS).
