# Tissue Data: Provenance & Method (how the `tissue` and `tissue_damage` columns were formed)

**Purpose:** a complete audit trail for the two tissue columns on the gold card, exactly what we formed, from
which of Gwyneth's files (down to the sheet and cell), how we derived each number, why, what it covers, and why
it is preliminary. If anyone ever asks "where did this tissue number come from?", the answer is here.

**Status:** active · **Created:** 2026-07-21 · **Last updated:** 2026-07-28 (merged to `main`) · **Owner:** Spencer (+ Alex) · **Code:** `build/silver_tissue.py`
**Data state:** **PRELIMINARY.** Gwyneth's tissue program is mid-analysis; this is her own computed data for the
subset of studies she has finished. Tissue is a **supplementary, non-gating** confirmation layer on the sheet
(the sheet's decisions run on safety + viability + competition; tissue is not a gate). Known gaps and what we
still need from Gwyneth: `docs/tissue_gaps_for_gwyn.md`.

---

## 1. TL;DR

We added two per-strain columns, built **entirely from Gwyneth's own computed analysis workbooks** (not
reconstructions, not chat-scrapes):

- **`tissue`** = the strain's best demonstrated **% suppression of *P. aeruginosa* on airway tissue** (efficacy).
- **`tissue_damage`** = the strain's **effect on the epithelial barrier**, control-subtracted Lucifer-Yellow
  % passage change from its monoculture (safety; positive = leakier/harm, negative = tighter/protective).

It covers **7 strains** from **5 of her computed studies** (3 co-culture mCherry/LY workbooks: 613/614, 451/452,
523/524; and 2 M21 LY barrier workbooks: 701/702, 739/740). Every number
traces to a specific file, sheet, and derivation (Section 5). A test (`tests/test_tissue_sources.py::TestSourceIntegrity`)
enforces that no tissue value on the card can exist unless it is in her source table.

## 2. What the two columns mean

| Column | Meaning | Units | Direction |
|---|---|---|---|
| `tissue` | Best % PA suppression achieved by any formulation the strain is a member of, on airway tissue (WT 16HBE or CF CFBE), vs the pathogen-alone control | percent | higher = better (more PA knockdown) |
| `tissue_damage` | The strain's own monoculture effect on the epithelial barrier (Lucifer-Yellow % passage, control-subtracted) | percentage-passage points | positive = leakier = harm; negative = tighter = protective |

## 3. Where the data came from (Gwyneth's computed files)

All are her **own computed analyses**, obtained via the drive.google.com folder download (which converts her
Google Sheets to real `.xlsx`, the desktop copy could not). Files live under `gahr/data_grab_7_21_26*/`.

| Study | Her file | What we took |
|---|---|---|
| 613/614 (NM+BL vs PA14) | `Experimental Data.../Co-Cultures/GAHR.ptc.613 & 614/GAHR_ptc613_614_statistics.xlsx` | sheet `mCherry_Suppression` (efficacy, her computed %); sheet `Condition_Summary` (barrier Pre/Post %) |
| 451/452 (PAO1 vs NM+RM ± mucin) | `.../Co-Cultures/GAHR.ptc.451 and 452/PAO1_NM_RM_mucin_competition_analysis.xlsx` | sheet `Summary Statistics` (per-condition mCherry means); sheet `Statistical Comparisons` (p-values) |
| 523/524 (NS ± NM vs PA14) | `.../Co-Cultures/GAHR.ptc.523 & 524/GAHR.ptc.523 and 524 - summary_table.csv` + `- stats.csv` | per-condition mCherry + LY-delta means; her Welch p-values |
| 701/702 (M21 CD/NB/NE monoculture) | `DATA AND FIGURE ORGANIZATION BLITZ/.../GAHR.ptc.701-702__2026-07-15__M21_LY_analysis.xlsx` | sheet `Control_Subtracted` (her control-subtracted barrier Δ%) |
| 739/740 (M21 BL/NM monoculture) | `DATA AND FIGURE ORGANIZATION BLITZ/.../GAHR.ptc.739-740__2026-07-15__M21_LY_analysis.xlsx` | sheet `Control_Subtracted` (her control-subtracted barrier Δ%, WT arm; added 2026-07-21) |

## 4. How we brought it together (the pipeline)

```
Gwyneth's computed workbooks  (her numbers, her method, her statistics)
        |  hand-extracted with row-level provenance (Section 5)
        v
gahr/CURATED/tissue_results/tissue_efficacy_v1.csv   (one row per study x tissue x formulation)
gahr/CURATED/tissue_results/tissue_barrier_v1.csv    (one row per study x tissue x strain monoculture)
        |  registered in config/data_sources.yaml (source key `tissue`)
        v
build/silver_tissue.py   -> rolls up to per strain (asma_id):
        efficacy = BEST PA suppression as a formulation member   (config: tissue.pa_reduction_aggregation)
        safety   = WORST monoculture barrier change per strain   (config: tissue.barrier_aggregation)
        v
build/gold_unified_sheet.py -> fills `tissue` and `tissue_damage` per strain (via the roster's group membership)
```

Two derivations were applied (documented per row in Section 5), both using **only Gwyneth's numbers**:

- **Efficacy where she did not print a single % (451/452, 523/524):** `% suppression = (PA_alone_mean −
  formulation_mean) / PA_alone_mean × 100`, using her per-condition background-corrected mCherry means, with her
  own Welch p-value carried along. (For 613/614 she printed the % directly, we used it verbatim.) These derived
  values reproduce the numbers in her own Vade Mecum ("56%" for 451/452, ~"84%" for 523/524), a cross-check.
- **Barrier (control-subtracted % passage):** `Δ = (condition Post% − Pre%) − (SCFM control Post% − Pre%)`,
  which is exactly her own M21 method (her `Control_Subtracted` sheet). We applied it uniformly to the
  %-passage studies (613/614, 523/524) and used her already-control-subtracted values for M21 (701/702). We
  used the **monoculture** condition (strain alone, no PA) so the number reflects the strain's *own* effect on
  the tissue, not *P. aeruginosa*'s.

## 5. Full row-level provenance

### Efficacy (`tissue_efficacy_v1.csv`)

| study | tissue | formulation | members (ASMA) | PA suppression % | p | source & derivation |
|---|---|---|---|---|---|---|
| 613/614 | WT | NM+BL | 2260+3643 | **43.5** | <0.001 | her `mCherry_Suppression` WT row (verbatim) |
| 613/614 | CF | NM+BL | 2260+3643 | **37.3** | <0.001 | her `mCherry_Suppression` CF row (verbatim) |
| 451/452 | WT | NM+RM+mucin | 1981+3643 | **56.4** | 0.01 | `Summary Statistics` comp+mucin 23.76 vs PAO1+mucin 54.47 → (54.47−23.76)/54.47 |
| 451/452 | CF | NM+RM+mucin | 1981+3643 | **97.7** | 0.04 | `Summary Statistics` comp+mucin 0.84 vs PAO1+mucin 36.82 → (36.82−0.84)/36.82 |
| 523/524 | WT | NS+NM | 3643+3913 | **84.2** | 0.012 | `summary_table` NS+PA+NM mCherry 30.36 vs PA14-only 191.67 → (191.67−30.36)/191.67 |
| 523/524 | CF | NS+NM | 3643+3913 | 29.7 | 0.54 (ns) | `summary_table` 115.84 vs 164.73 |

### Barrier / safety (`tissue_barrier_v1.csv`) — control-subtracted % passage, monoculture

| study | tissue | strain | Δ% (ctrl-sub) | source & derivation |
|---|---|---|---|---|
| 613/614 | WT | NM (3643) | −0.97 | `Condition_Summary` NM 1.35→1.19 minus SCFM 1.94→2.75 |
| 613/614 | CF | NM (3643) | +0.70 | NM 1.48→0.93 minus SCFM 2.50→1.25 |
| 613/614 | WT | BL (2260) | +8.11 | BL 1.35→10.27 minus SCFM 1.94→2.75 |
| 613/614 | CF | BL (2260) | +9.60 | BL 1.51→9.86 minus SCFM 2.50→1.25 |
| 523/524 | WT | NS (3913) | +26.93 | NS-only LY-delta 33.62 minus SCFM 6.69 |
| 523/524 | CF | NS (3913) | +1.74 | NS-only 9.52 minus SCFM 7.78 |
| 701/702 | WT | CD (2191) | −0.08 | her `Control_Subtracted` (worst of plain/+mucin) |
| 701/702 | WT | NB (4643) | −1.18 | her `Control_Subtracted` (p=0.004) |
| 701/702 | WT | NE (4509) | −1.10 | her `Control_Subtracted` (p=0.032) |
| 739/740 | WT | BL (2260) | +3.89 | her `Control_Subtracted` WT, worst of plain −0.92 / +mucin +3.89 (p=0.0003, ***) |
| 739/740 | WT | NM (3643) | −0.87 | her `Control_Subtracted` WT, worst of plain −1.24 / +mucin −0.87 (p=0.061, ns) |

## 6. The resulting card values (7 strains)

| strain group | ASMA (rep) | species | `tissue` (PA supp %) | `tissue_damage` (barrier Δ%) |
|---|---|---|---|---|
| 39 | ASMA-1981 | *R. mucilaginosa* (RM) | 97.7 | (no barrier row) |
| 392 | ASMA-3643 | *N. mucosa* (NM) | 97.7 | +0.70 (neutral) |
| 577 | ASMA-3913 | *Neisseria* sp. (NS) | 84.2 | +26.93 (disrupts) |
| 686 | ASMA-4723 (tested as 2260) | *B. licheniformis* (BL) | 43.5 | +9.60 (disrupts) |
| 482 | ASMA-2235 (tested as 2191) | *C. durum* (CD) | (no efficacy row) | −0.08 (neutral) |
| 417 | ASMA-4643 | *N. bacilliformis* (NB) | (no efficacy row) | −1.18 (protective) |
| 427 | ASMA-4509 | *N. elongata* (NE) | (no efficacy row) | −1.10 (protective) |

Note the split: the co-culture studies gave **efficacy** for NM/BL/RM/NS; the M21 monoculture workbooks gave
**barrier** for CD/NB/NE (701/702) and a second barrier study for BL/NM (739/740). That is the honest current
coverage. The 739/740 workbook (WT arm) adds a second, independent barrier study for BL and NM (BL disrupts,
NM neutral, consistent with 613/614); it does not move their worst-case card values (613/614 CF stays worst),
so it strengthens the evidence rather than changing the numbers.

## 7. Rollup logic (team-owned)

- **Efficacy** (`tissue`) = a strain's **best** PA suppression across every formulation it is a member of
  (e.g. NM = 97.7 from NM+RM on CF, its strongest team). Parallels the competition column's best-as-member.
- **Safety** (`tissue_damage`) = a strain's **worst** (most leaky) monoculture barrier change across tissues
  (conservative: surface any barrier disruption). Parallels the card's `safety = worst_case` policy.
- Both aggregations are switches in `config/thresholds.yaml → tissue:` (currently `max`), the biologists own them.
- Rationale for each choice is in the ADR: `docs/decisions/tissue_stat_sheet_decisions.md`.

## 8. Why this is PRELIMINARY

1. **Partial coverage.** 7 strains from 5 computed studies, out of her ~80 tissue/competition studies (83 in her
   catalog). She is mid-analysis (see the gaps doc).
2. **Two readouts on different strain sets.** Efficacy (NM/BL/RM/NS) and barrier (CD/NB/NE/NM/BL/NS) do not fully
   overlap, because we have her mCherry files for the co-cultures and her LY file for M21, not both for all.
3. **Some efficacy values are derived** (from her per-condition means), not printed by her as a single %,
   though they reproduce her own stated results.
4. **Barrier normalization is ours.** We applied her M21 control-subtracted method uniformly to the %-passage
   studies; 451/452's barrier (reported in raw RFU, not % passage) was excluded from `tissue_damage` to avoid
   mixing units. Gwyneth should confirm this is acceptable. For the two M21 LY workbooks (701/702, 739/740) we
   used the **WT arm only** (matching the original 701/702 precedent; the M21 CF arm is noisier). Note 739/740
   also shows a significant BL+mucin barrier disruption on CF (+4.06, p=0.005), so if Gwyneth wants the CF arm
   counted we would add it for both M21 studies.
5. **Not yet confirmed by Gwyneth.** These are faithfully extracted from her files, but she has not signed off on
   this specific assembly.

## 9. Reproduce / extend

- Source tables (with per-row provenance): `gahr/CURATED/tissue_results/tissue_efficacy_v1.csv`,
  `tissue_barrier_v1.csv`.
- Rebuild: `bash build/run_all.sh` (silver_tissue → gold). Verify: `bash tests/run_tests.sh`.
- **To add a study** when Gwyneth's file arrives: append rows to the two CSVs (same columns, fill the provenance
  cells), bump the `version` in `config/data_sources.yaml`, re-run. No code change needed.
- **To remove tissue entirely:** set `tissue: enabled: false` in `data_sources.yaml` (columns go blank), or
  revert the commit.

## 10. Open items (tracked so they are not forgotten)

Tissue is in the sheet but PRELIMINARY. These are the specific things still outstanding. None block the sheet
(tissue is non-gating); each is an append or a confirmation, not a code change.

1. **Gwyneth's sign-off (flips preliminary → confirmed).** Two questions, detailed in
   `docs/tissue_gaps_for_gwyn.md`:
   - which readout is her **headline PA-suppression** number (so `tissue` cites the metric she would), and
   - is **control-subtracted % passage** the right definition of "tissue damage" for `tissue_damage`.
2. **Her competition mCherry (the efficacy "lionshare").** The PA-suppression analyses for her M21 lead
   consortia, `796/797` (NM+NB), `757/758` (BL+NM), and the mCherry side of `739/740`, are **Drive-only**
   (native Google Sheets, not on the server), so the efficacy side for those consortia is not yet filled. She
   either web-downloads each (drive.google.com > Download, a two-minute add per study on our side) or confirms
   we may cite her Competition Vade Mecum numbers as preliminary. The inventory-grounded split of what is
   Drive-only vs not-yet-analyzed is in `gahr/docs/tissue_data_still_missing_2026-07-21.md`, grounded in the
   full server catalog `gahr/docs/full_data_catalog_2026-07-21.md`.
3. **The M21 CF arm.** We used the **WT arm only** for the two M21 barrier studies (701/702, 739/740). 739/740
   shows a significant BL+mucin barrier disruption on CF (+4.06, p=0.005); if Gwyneth wants the CF arm counted,
   we add it for both M21 studies (Section 8, item 4).
4. **Broader coverage.** 7 strains from 5 of her ~80 tissue/competition studies. Each additional computed study
   is an append when it lands.

**When any of these resolves:** append rows to the two source CSVs (Section 9), bump `version` in
`config/data_sources.yaml`, re-run `bash build/run_all.sh && bash tests/run_tests.sh`. The dated history of what
was added when is in the ADR change log (`docs/decisions/tissue_stat_sheet_decisions.md`).

*Any tissue number on the card that is not reproducible from this document is a bug, please report it.*
