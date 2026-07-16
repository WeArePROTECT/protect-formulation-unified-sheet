# Formulation Unified Sheet — Data Readiness Scorecard

**Purpose:** Answer Jake's two questions (from the 2026-07-13 meeting + Slack) for **every column**
Adam sketched for the unified formulation spreadsheet:

1. What is the **status / completeness** of the dataset? What strains, and how many, are screened?
2. Is the dataset **on the server / lakehouse** (i.e. can Spencer + Alex actually join it), or is it
   still on someone's local machine?

This is the backbone of the unified sheet: each of Adam's columns maps to a criterion (one of the
three acceptance gates), an owner, a data source, and a readiness status. Built 2026-07-14 by Spencer
from verified server paths. **Perishable facts (counts, newest file) are noted with an "as-of" — treat
the manifest `dataset.yaml` as the live source of truth for those.**

---

> **UPDATE 2026-07-14 (SYK):** `ASMA_phenotype_20260714.xlsx` + notes doc landed on the server — **the SYK
> freshness gap is closed.** It supersedes `_20250625` and adds `Growth_endpoint` (SCFM ± mucin endpoint
> viability), `Antibiotic_resistance_v2` (updated 6-abx panel + QC), and a richer `Competition` sheet (27,667
> rows, per-member inoculation-OD ratios). Sheets now carry an explicit **v1/v2 + 384→96 deprecation
> structure** — see **`syk_phenotype_sheet_map.md`** for which sheet is canonical + the QC/ingestion rules.
> Still RAW/pre-QC per SYK — treat as preliminary.

## The three acceptance gates (Adam's "theory of operations")

Adam reframed the meeting's whole point: we can't measure the *real* criteria directly, so every column
is a **proxy** for one of three gates. A formulation moves forward only when it clears all three.

| Gate | Real criterion | Measurable proxies (columns below) |
|---|---|---|
| **SAFETY** — "doesn't kill the patient" | no host damage / immune catastrophe | hemolysis, tissue damage, AMR (measured + genomic), BSL level |
| **VIABILITY** — "we can actually grow & make it" | robust, reproducible culture | growth in SCFM (± mucin), carbon profile, culturability |
| **COMPETITION** — "excludes PA at PA's expense" | metabolic competitive exclusion of the pathogen | planktonic competition, tissue competition, halo (secreted-NP screen), suppressive synergy, amelioration with prebiotic |

Two supporting axes feed prioritization but aren't gates: **RELEVANCE** (ubiquity / commensality in
airway metagenomes) and **METABOLIC RATIONALE** (in-silico capabilities, suggested partners).

---

## Scorecard

Legend — **On server?** ✅ on-server & joinable · ⚠️ partial / needs work · ❌ off-server (local machine only)

| # | Column (Adam's sheet) | Gate | Proxy / meaning | Owner | Source (verified path) | On server? | Status / completeness (as of 2026-07-14) |
|---|---|---|---|---|---|---|---|
| 1 | **Strain** | IDENTITY (key) | canonical `ASMA_id` | Alex (genomic) + SYK (stock) | `alex.styer/protect/ASMA/isolates/` (~4,940) · `SYK/ASMA_list.xlsx` | ✅ | ~4,940 isolates → **~700 unique strains** after genomic dedup. **Grain (isolate vs strain vs species) not yet standardized — this is our first deliverable.** |
| 2 | **antibiotic resistance** | SAFETY | measured MIC + genomic AMR genes | SYK (in vitro) + Alex (genes) | SYK `ASMA_phenotype_20260714.xlsx [Antibiotic_resistance_v2]` (Amp/Cipro/Chlor/Tet/Gent/Eryth + ΔOD QC, ~2,350 rows) · Alex `amrfinder.tsv` (~34k rows) | ✅ | **On server (v2 landed 2026-07-14).** Updated panel is purpose-built for genomic-vs-measured AMR comparison; v1's old panel deprecated. Genomic AMR complete across collection. |
| 3 | **hemolysis** | SAFETY | alpha/beta hemolysis (blood agar) | **Cassandra Reyes** | `hilzinger/hemolysis/ASMArep_HemolysisResultsSummary_063026_ASMAid.xlsx` (1,638 rows, 24/48/72 h α+β) + rep-plate + plate-manifest files | ✅ (landed **today** Jul 14) | SYK: **~90% of unique strains done.** Cassie is **out sick** — Jake owns; direct format Qs to her. SYK wants to update FREP duplicate wells before it's final. |
| 4 | **tissue damage assay** | SAFETY | epithelial damage (LDH, barrier, morphology) | **Gwyneth** | tissue-culture system | ❌ | Off-server (local). F1–F10 M18/M21 set; results "in analysis." **Must request as a clean table + metadata.** |
| 5 | **halo assay** | COMPETITION | spot-on-lawn → secreted natural product? | SYK / Gwyn | — | ❌ / to-confirm | **Likely not a systematic collection-wide dataset.** SYK ran follow-ups showing the 19 leads are "likely not secondary metabolite." Confirm scope before promising this column. |
| 6 | **growth rate & yield in SCFM (and on tissue)** | VIABILITY | grow / no-grow endpoint + kinetics in SCFM ± mucin | SYK (SCFM) + Gwyn (tissue) | SYK `ASMA_phenotype_20260714.xlsx` → `Growth_endpoint` (SCFM_72 / SCFM_mucin_0.5_72 + controls, ~2,361 rows) + `Growth_Curve_single_96` (96-well Agilent, `cyc_*` 10-min, ~1,537 rows) | ✅ | **Grow/no-grow "fast track" now on server (`Growth_endpoint`, w/ BHIS/No_Carbon controls).** Still compute derived rate/lag/OD from raw curves (Alex has `growth/collate-scfm-growth.py`). Use 96-well sheets; 384-well deprecated. |
| 7 | **computational metabolic capabilities** | METABOLIC (in silico) | GapMind / gapseq pathway completeness | **Alex** | `alex.styer/protect/ASMA/` — `gapmind-carbon-rules.tsv`, `gapmind-aa-rules.tsv`, `gapseq/`, `mucmunch/`, `mucin/` | ✅ | Computed across collection. **Alex already has `DECISION-MATRIX.md` here (Jul 1) — coordinate, don't duplicate.** This is "Gapmind — Alex" in Jake's list. |
| 8 | **ubiquity in airway metagenomes (general + patient)** | RELEVANCE | metagenomic prevalence + patient carriage | Zengler (Emma) + linkage | Emma MIND tables (`zengler_metagenomics_mind`) + `patient_sample_isolate_linkage` | ⚠️ | Inputs on server; **per-strain ubiquity score is DERIVED** (species → metagenome rel. abundance + # patients carrying). Note Gwyn's "315 Rothia" caveat: raw collection counts ≠ patient ubiquity (dedup + patient-of-origin needed). |
| 9 | **active riboseq relative abundance** | RELEVANCE | metabolically active in vivo (metaRS) | Zengler (Emma) | Emma metaRS / `PROTECT sample metadata.xlsx [Metaribo-seq]` | ⚠️ | On server at OGU/species level; **per-strain value is DERIVED** via species join. |
| 10 | **carbon profile** | VIABILITY / metabolism | sole-carbon utilization (curves) | SYK (measured) + Alex (in silico) | SYK `ASMA_phenotype_20260714.xlsx [Growth_Curve_single_96]` (96-well, ~1,537 rows) + `ASMA_carbon_kinetics_20260623.xlsx` · Alex `c-sources.xlsx` + GapMind carbon rules | ⚠️ | Clean 96-well single-carbon curves now on server (supersede deprecated 384-well/endpoint_v1). Criterion: Mean(sole) > Mean(no_carbon)+2·SD. Still **plate-reader-limited coverage** — in-silico GapMind fills the gap. |
| 11 | **Planktonic competition assay** | COMPETITION (core) | inhibition of PA reporter, 1–5-member SynComs | **SYK** | SYK `ASMA_phenotype_20260714.xlsx [Competition]` (~27,667 rows) | ✅ | **The biggest, most complete dataset — newest now on server (2026-07-14).** 1–5-member SynComs vs **8 pathogen reporters** (PA14, PAO1, clinical PA, AB/KP/SA). Now carries per-member inoculation ODs + `OD_ratio_ASMA/Reporter`. **Exclude `Non_standard_A`** (unnormalized/variable → not quantitative). `Inhibition_percent` readout. |
| 12 | **tissue competition assay** | COMPETITION (tissue) | PA-abundance reduction on CF/WT tissue | **Gwyneth** | tissue system | ❌ | Off-server. F1–F10 (5 commensal pairs × SCFM/SCFM+mucin) vs PAO1-mCherry, CF+WT, n≥3. Results "in analysis." **Request.** |
| 13 | **competition amelioration w/ probiotic supplement** | COMPETITION | prebiotic lift (± mucin) | SYK/Gwyn (wet) + Alex (mucin in silico) | SYK `Growth_endpoint [SCFM_72 vs SCFM_mucin_0.5_72]` + mucin competition conditions · Alex `mucin/` `mucmunch/` mucin-catabolism | ⚠️ | **Mucin viability lift now systematic on server** (`SCFM_mucin_0.5_72` column). Prebiotic-in-competition still emerging (PoC 3643+1981+mucin = 56% PAO1↓). |
| 14 | **BSL-level** | SAFETY / regulatory | biosafety level of the species | Gwyn (curating) + taxonomy (Alex) | Gwyn's BSL-1 spreadsheet (hand-curated) + species from Alex `gtdbtk/` | ⚠️ / ❌ | Gwyn building a BSL-1 list (~13 species so far; ~30–40 candidate species). **We can accelerate:** build a species→BSL reference table and join on gtdbtk species. Watch the Neisseria trap (endocarditis → not BSL-1). |
| 15 | **suggested probiotic partners** | METABOLIC (derived) | model-proposed cross-feeding partners | **Alex** | Alex GapMind formulation calculator / dashboard + `DECISION-MATRIX.md` | ✅ | Computational; complements SYK's empirical pairs. Alex owns. |
| 16 | **suppressive synergy w/ probiotic partner** | COMPETITION | community inhibition − best single member | **SYK** (data) → Spencer (derive) | derived from `[Competition]` multi-member rows | ✅ | **DERIVED by us.** Key nuance from month-21 data: **communities often do NOT beat their best single member** — this column must show sign, not just magnitude. |
| 17 | **Decision register** | OUTPUT | pass/hold/fail + reason per strain | **Spencer + team** | *this project — to build* | — | The verdict column the whole sheet builds toward: safety✓ viability✓ competition✓ → move forward, with the reason recorded. Spencer maintains the substrate; experimentalists set thresholds. |

---

## What this tells us (the readiness summary)

- **On-server & joinable right now (build v1 from these):** planktonic competition (11), hemolysis (3),
  measured + genomic AMR (2), SCFM growth curves (6, raw), carbon binary + kinetics (10), GapMind /
  metabolic (7, 15), identity/taxonomy (1). That is **enough to draft the safety + viability + planktonic-competition
  gates for ~700 strains this week.**
- **Derived columns we (Spencer/Alex) must compute, not request:** growth rate/lag/yield from raw OD (6),
  suppressive synergy (16), patient/metagenome ubiquity (8), riboseq relative abundance (9), species→BSL (14).
- **Off-server — must request as clean tables + experimental metadata:** tissue damage (4) & tissue
  competition (12) from Gwyn; mouse from Fatemeh; Gwyn's BSL-1 list. *(SYK's phenotype data is now current
  on-server as of 2026-07-14 — `ASMA_phenotype_20260714.xlsx`.)*
- **Scope-check before promising:** halo/secreted-NP assay (5) — confirm whether a systematic dataset
  exists at all.
