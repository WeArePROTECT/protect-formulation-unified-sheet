# Unified Formulation Data Sheet — Proposal v1 (for team review)

**From:** Spencer (+ Alex) · **Date:** 2026-07-14 · **Status:** DRAFT for buy-in — please react before we build.

This is the concrete proposal for the unified sheet Adam asked for at the 2026-07-13 meeting. It exists so
we agree on **structure, IDs, and who-owns-what BEFORE anyone writes integration code** — so we build once,
not three times. Companion: `data_readiness_scorecard.md` (per-column status: what's done, what's on the server).

Please react to the **5 decisions in §5.** Nothing here sets the *scientific* thresholds — that stays with
the experimentalists.

---

## 1. What we're building

A single **strain-level decision matrix**: one row per strain, columns = the measurable proxies for the
three acceptance gates, plus a decision register. Adam: *"if you just had all our strains lined out… then
you can build a decision matrix on it as to what goes forward, and why."*

Delivered as **both**: a shareable **.xlsx** (you can read it and edit the decision column) **and** a
canonical **CSV/parquet** (so it joins/versions cleanly and can go to the lakehouse).

Under it sit standardized **source tables** (one per assay) and a **formulations** table for the
multi-member competition/tissue data. You give us clean assay tables + experimental metadata; we do the
joins, the derived metrics, and a first-pass ranking; the group sets the thresholds.

---

## 2. The three gates → columns (this is Adam's spreadsheet)

| Gate | Column | Source (owner) | Notes |
|---|---|---|---|
| — | `ASMA_id`, `species`, `genus`, `n_isolates_in_strain`, `bsl_level` | genomics (Alex) + stock list (SYK) | identity + grain |
| **SAFETY** | `hemolysis_beta`, `hemolysis_alpha` (24/48/72 h) | hemolysis (Cassandra) | β-hemolysis = primary "kills the patient" proxy |
| **SAFETY** | `amr_measured` (MIC panel), `amr_gene_risk`, `virulence_flag` | AMR/VF (SYK measured · Alex genomic) | measured MIC + genomic AMR/virulence genes |
| **VIABILITY** | `scfm_grow` (y/n), `scfm_max_od`, `scfm_growth_rate`, `scfm_lag`, `scfm_mucin_grow` | SCFM growth (SYK) | **we derive rate/lag/OD from raw curves** |
| **VIABILITY** | `carbon_sources_used`, `carbon_profile` | carbon (SYK measured · Alex GapMind) | binary + kinetics; in-silico fills the plate-reader gap |
| **COMPETITION** | `best_planktonic_inhib_pa` (%), `best_reporter`, `single_inhib_pa` | competition screen (SYK) | best inhibition of a PA reporter as a member/solo |
| **COMPETITION** | `best_partner`, `suppressive_synergy` (signed) | derived from competition (Spencer) | community − best-member; keep the **sign** |
| **COMPETITION** | `tissue_inhib_pa`, `prebiotic_amelioration` | tissue (Gwyn) | PA-abundance reduction on tissue; ± mucin lift |
| **COMPETITION** | `halo_secreted_np` | halo assay (SYK?) | *confirm this dataset exists before we promise the column* |
| RELEVANCE | `airway_ubiquity`, `patient_prevalence`, `riboseq_rel_abundance` | metagenomics/metaRS (Zengler) + linkage | **derived** via species join |
| METABOLIC | `gapmind_capabilities`, `suggested_partners` | GapMind (Alex) | Alex owns; already has `DECISION-MATRIX.md` |
| **OUTPUT** | `decision`, `decision_reason`, `decided_by`, `decision_date` | the group | the register — why it advances/holds/drops |

---

## 3. Standard experimental-metadata columns (Alex's requirement)

So we never compare a 96-well/24 h/cool run against a 384-well/8 h run and think they're the same:
**every source table you hand us should carry these columns** (or tell us the constant value so we add them):

`assay_start_date` · `assay_condition_type` · `plate_format` (96/384) · `media` (SCFM / SCFM+mucin / LSM /
BHI / LB) · `incubator_temp` · `duration_h` · `preculture_priming` · `plate_reader` · `replicate` / `n`

SYK's phenotype workbooks already carry `Assay_start_date` + `Assay_condition_type` — thank you, that's the model.

---

## 4. ID & grain standard (the thing we must lock first)

Right now IDs are inconsistent across files (`ASMA_ID` / `ASMA_id` / `ASMA-ID`; trailing spaces; `_priming`
suffixes; `ASMA_A_id…E_id` on the competition sheet; `genome_id` vs `sample_id` in genomics). Proposal:

- **Canonical key:** `ASMA_id`, value format `ASMA-#####` (we pin exact format to `SYK/ASMA_list.xlsx`).
  We normalize on ingest (strip spaces, drop annotation suffixes, uppercase prefix).
- **Grain = strain.** Vocabulary: `isolate` (physical stock, ~4,940) ⊃ `strain` (dedup unit, ~700 = the row) ⊃
  `species` (gtdbtk). "How many screened" is answered at **strain** level. This is why "we have 315 Rothia"
  ≠ "315 useful data points" — many are redundant isolates / same patient.
- One link we need from Alex: `genome_id ↔ ASMA_id` (gtdbtk/QC key on sequencing `sample_id`, not `ASMA_id`).

---

## 5. Decisions we need from the group (please react)

1. **Grain = strain** (~700), with isolate/species as attributes? 👍/👎
2. **Canonical `ASMA_id` = `ASMA-#####`** + we normalize on ingest? 👍/👎
3. **Standard experimental-metadata columns** (§3) on every assay table? 👍/👎
4. **Lanes:** Spencer = ID/grain standard, unified table, empirical ingestion, derived columns, decision
   register, xlsx/CSV/lakehouse. Alex = in-silico/metabolic columns, partners, phylogeny/clades. SYK/Gwyn/
   Cassandra = deliver assay tables + metadata to the server. Jake + experimentalists = set the thresholds. 👍/👎
5. **Thresholds:** you (SYK/Gwyn/Jake) own the gate cutoffs; we ship a strawman for you to argue with. 👍/👎

## 6. What we need on the server (to actually build)

- **SYK:** ✅ **done 2026-07-14** — `ASMA_phenotype_20260714.xlsx` + notes doc landed (Competition, `Antibiotic_resistance_v2`, `Growth_endpoint`, 96-well growth curves). His notes doc is the model for §3 metadata. Remaining: QC/outlier finalization (he flagged it's still raw).
- **Gwyn:** tissue damage + tissue competition tables + metadata; the BSL-1 list.
- **Cassandra (via Jake):** confirm hemolysis format/completeness + the FREP duplicate-well update.
- **Alex:** GapMind capability + suggested-partner columns; the `genome_id ↔ ASMA_id` map.

## 7. Strawman heuristic (so §5.5 has something to push on — NOT final)

```
SAFETY    : β-hemolysis = No  AND  not multi-drug-resistant  AND  BSL-1
VIABILITY : grows in SCFM  AND  derived max-OD ≥ cutoff
COMPETE   : best planktonic inhibition of PA ≥ 50%   (SOW deliverable bar)
→ rank survivors by competition × ubiquity; annotate suggested partners (Alex)
```
