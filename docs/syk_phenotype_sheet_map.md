# SYK Phenotype Workbook — Canonical Sheet Map & Ingestion Rules

**Source:** `/usr2/people/protect/Arkin_Lab/SYK/ASMA_phenotype_20260714.xlsx` (on server 2026-07-14) +
`notes for ASMA_phenotype_20260714.docx`. Distilled by Spencer 2026-07-14 from SYK's notes, verified
against the actual sheet headers. **This is the "use this sheet, not that one" guide for the unified-sheet build.**

> ⚠️ **Whole workbook is RAW / pre-QC** (SYK): rigorous QC not yet applied; outliers exist across biological
> replicates; no exclusion criteria finalized; high-variability samples to be re-measured. **Treat as
> preliminary.** Each row = one **biological replicate** → aggregate per (`ASMA_id`, condition, `Assay_start_date`)
> before joining to strain grain.

**Shared keys on every sheet:** `ASMA_id` · `Assay_start_date` · `Assay_condition_type`.
(SYK's prose says `ASMA_ID`; the actual data column is `ASMA_id` — data is authoritative.)

---

## Canonical vs deprecated (which sheet to use)

| Assay → unified column | ✅ USE (canonical sheet) | ❌ Ignore (deprecated) | Why / key columns |
|---|---|---|---|
| **Planktonic competition** (`best_planktonic_inhib_pa`, synergy) | `Competition` (**Standard_\* conditions only**) | — | 27,667 rows. `Inhibition_percent`, `OD_ratio_ASMA/Reporter`, per-member inoculation ODs. **Exclude `Assay_condition_type = Non_standard_A`** (density not OD-normalized, 16–24 h variable → not quantitatively comparable). |
| **Antibiotic resistance** (`amr_measured`) | `Antibiotic_resistance_v2` | `Antibiotic_resistance_v1` (KAN/CHL/CB/TET/STR/SPE/GEN) | v2 = 2,350 rows, updated panel **Ampicillin/Ciprofloxacin/Chloramphenicol/Tetracycline/Gentamicin/Erythromycin** (better class coverage → the panel to compare vs genomic AMR). *All future abx data goes to v2 only.* |
| **SCFM ± mucin viability** (`scfm_grow`, `scfm_mucin_grow`) + **prebiotic amelioration** | `Growth_endpoint` | — | 2,361 rows. `SCFM_72` (grow/no-grow), `SCFM_mucin_0.5_72` (mucin lift), `BHIS_72` (pos ctrl), `No_Carbon_72` (neg ctrl), `SCFM_16`/`BHIS_24` (priming/viability QC). **New — this is the fast-track viability screen.** |
| **Single-carbon growth curves** (`scfm_growth_rate`, `scfm_lag`) | `Growth_Curve_single_96` | `Growth_Curve_single_384`, `Growth_Curve_dropoff_384` | 96-well Agilent LogPhase600, `cyc_*` = **10-min** intervals. Ignore `Tyrosine_only` (precipitation). Rows with `NA` `ASMA_id`/`condition` = drop. |
| **Carbon utilization** (`carbon_sources_used`) | derive from `Growth_Curve_single_96` | `Carbon_utilization_endpoint_v1` (384) | Criterion: **Mean(sole carbon) > Mean(no_carbon) + 2·SD(no_carbon)**. |
| SCFM community growth curve | — | `Growth_Curve_SCFM_384` | 384-well method deprecated as suboptimal. |

**Rule of thumb:** anything ending `_384` or `_v1` is deprecated. Current methods = 96-well / `_v2` / `Growth_endpoint`.

---

## Per-assay QC & ingestion rules (these become our pipeline rules)

- **Competition** — `Inhibition_percent = 100 − (co-culture Mean RFU ÷ reporter-only-control Mean RFU × 100)`.
  Reporter-only control drawn from the **same `Assay_start_date`** (and same `Sheet_id` when possible).
  `Mean`/`StDev`/`Top…Bottom` = raw Tecan RFU per well read-position. `Blank` in a member/reporter column =
  that strain intentionally omitted. `Well_OD600` = optional reporter-free community growth check.
- **Antibiotic_resistance_v2** — `Untreat_day3-day0_OD600` is the QC gate: **ΔOD600 < 0.1 ⇒ no growth ⇒ that
  strain's susceptibility profile FAILS QC** (drop). Negative ΔOD set to 0. `*_profile` = relative growth %
  vs untreated (100% ≈ grows normally / resistant; lower = more inhibited by the antibiotic).
- **Growth_endpoint** — background-subtract using the `BLANK` from the **same `Assay_start_date`** (average if
  several). U-bottom read plate → blanks differ from the flat-bottom phenotyping plates; don't cross-subtract.
- **Provenance:** each current assay cites a (private) protocols.io link in SYK's notes — capture as
  `protocol_url` metadata when we ingest.

---

## Why this matters for the unified sheet

SYK's note — *"there may not be many datasets that can be directly compared because some assays were
performed under inherently different experimental conditions"* — **is the exact case for our
experimental-metadata standard** (`docs/unified_sheet_proposal_v1.md` §3). His notes doc already supplies,
in prose, the condition metadata we asked every owner to attach: plate format (96 vs 384), reader (Tecan
Spark vs Agilent LogPhase), cycle interval (15 vs 10 min), media, normalization, duration. When we build,
we lift these into the standard metadata columns so joins only ever compare like-with-like. **Point the team
at this doc as the model for what "assay table + metadata" should look like.**
