# Decision Record — Tissue Stat Sheet (`silver_tissue.py`)

**Purpose:** capture *why* the tissue columns are built the way they are, the options weighed, what we chose, and
what would change our minds. Readable by humans and AI agents.

**Status:** active · **Created:** 2026-07-21 · **Owner:** Spencer (+ Alex) · **Code:** `build/silver_tissue.py`
**Companion:** the full audit trail (every number → Gwyneth's file/sheet/cell) is
`docs/tissue_provenance_and_method.md`; the coverage gaps are `docs/tissue_gaps_for_gwyn.md`.
**Data state:** **PRELIMINARY.** Gwyneth's tissue program is mid-analysis; this is her own computed data for the
subset of studies she has finished. Tissue is a **supplementary, non-gating** confirmation layer.

Format: an ADR. New decisions get appended; superseded ones are marked, not deleted.

---

## Context
Gwyneth tests formulations (teams of commensals, by ASMA id) on human airway epithelium (WT 16HBE / CF CFBE)
against *P. aeruginosa* and reads out PA burden (mCherry) and barrier integrity (Lucifer Yellow). We turn her
computed per-study analyses into two per-strain gold columns: `tissue` (PA suppression %, efficacy) and
`tissue_damage` (barrier change, safety).

## Decisions

### D1 — Source = Gwyneth's OWN computed analysis workbooks (hand-extracted with provenance)
- **Options:** (a) the prior agent's `spencer_tissue` assembly; (b) numbers scraped from her chat history;
  (c) recompute from raw ourselves; (d) her own computed analysis files.
- **Chosen:** (d). We extract from her finished workbooks (`GAHR_ptc613_614_statistics.xlsx`,
  `PAO1_NM_RM_mucin_competition_analysis.xlsx`, `523/524 summary_table.csv`, `M21_LY_analysis.xlsx`) into two
  curated, fully-sourced tables (`gahr/CURATED/tissue_results/tissue_efficacy_v1.csv`, `tissue_barrier_v1.csv`).
- **Why:** these are her numbers, her method, her statistics, the only trustworthy source. **(a) was rejected by
  Gwyneth herself** ("spencer_tissue is not correct", it covered ~9 of her ~84 co-culture studies). **(b)** is
  second-hand and mixed-unit. **(c)** is real analysis that should be hers.
- **Revisit if:** she finishes more studies (append rows) or signs off (flip preliminary→confirmed).

### D2 — Hand-curated tables, not an auto-parser
- **Chosen:** extract by hand into two CSVs (with per-row source cell + derivation), rather than auto-parsing.
- **Why:** her per-study files are **heterogeneous** (an xlsx with a `mCherry_Suppression` sheet here, per-condition
  CSVs there, a competition-analysis workbook elsewhere). A brittle parser over 4 formats would be more error-prone
  than a small, reviewed, traceable table. **Revisit if:** she standardizes her outputs, then auto-ingest.

### D3 — Efficacy (`tissue`) = best PA suppression as a formulation member
- **Chosen:** a strain gets the **max** % PA suppression across every formulation it belongs to. Where she printed
  the % directly (613/614) we used it verbatim; where she gave per-condition means (451/452, 523/524) we computed
  `(PA_alone − formulation)/PA_alone × 100` from *her* means, carrying *her* Welch p.
- **Why:** parallels the competition column (best-as-member = the strain's strongest demonstrated team). The derived
  %s reproduce her own Vade Mecum figures (56% for 451/452, 84% for 523/524), a built-in cross-check.
- **Aggregation is a config switch** (`tissue.pa_reduction_aggregation`, currently `max`), team-owned.

### D4 — Safety (`tissue_damage`) = worst monoculture barrier change, her control-subtracted method
- **Chosen:** control-subtracted Lucifer-Yellow % passage change, `(condition Post−Pre) − (SCFM Post−Pre)`, from
  the strain's **monoculture** (no PA), worst-case (max) across tissues. This is exactly her M21 `Control_Subtracted`
  method, applied uniformly to the %-passage studies. Positive = leakier/harm; negative = tighter/protective.
- **Why monoculture:** isolates the *strain's own* effect on the barrier; in co-culture, *P. aeruginosa* itself
  breaks the barrier and would confound it.
- **What we excluded:** ptc.451/452's barrier is in raw RFU (not % passage), so we left it out of `tissue_damage`
  to avoid mixing units (its efficacy still counts). **Revisit if:** Gwyneth prefers a different barrier metric or
  wants the co-culture "does the team protect against PA" reading (a different, positive signal).

### D5 — Ship it PRELIMINARY and NON-gating
- **Chosen:** the columns appear, flagged preliminary; they are **not** in `formulation_criteria.yaml` (no gate,
  no ranking weight).
- **Why:** it is her unconfirmed subset, and whether tissue efficacy gates or `tissue_damage` becomes a safety
  cutoff is the biologists' call, made in the switchboard, not baked in by us. The sheet's decisions already run on
  safety + viability + competition; tissue is confirmation on top.

## Things intentionally NOT decided here (owned elsewhere / later)
- Which of her readouts is the "headline" PA number, and whether control-subtracted % passage is the right damage
  metric: Gwyneth's call (see the gaps doc's closing question).
- The QC of individual studies (wild raw values, contamination flags): hers.
- Completing coverage of all ~20 competition studies: pending her computed files (gaps doc).

## Change log
- **2026-07-21 (append: +ptc.739/740)** — appended the **ptc.739/740 M21 LY barrier** workbook
  (`GAHR.ptc.739-740__2026-07-15__M21_LY_analysis.xlsx`, her `Control_Subtracted` sheet, WT arm) to
  `tissue_barrier_v1.csv`: a second, independent barrier study for BL (2260) and NM (3643). Data-source version
  bumped to `v1.1`. **No card value changed** (worst-case per strain unmoved: 613/614 CF stays worst); it raises
  BL/NM barrier evidence from 1 study to 2. Applied D4 unchanged (worst of plain/+mucin, her control-subtracted
  method). Used the **WT arm only**, matching the 701/702 precedent; the CF arm (which shows a significant
  BL+mucin disruption) is flagged for Gwyneth in the provenance doc. Build + 67 tests green.
- **2026-07-21 (this version)** — rebuilt from **Gwyneth's own computed analysis files** (D1–D5). **Supersedes** the
  earlier same-day version that sourced the prior agent's `spencer_tissue` table, which Gwyneth flagged as
  incorrect (it represented ~9 of her ~84 studies). 7 strains now carry tissue data (4 efficacy, 6 barrier).
- 2026-07-21 (superseded) — initial version sourced from `spencer_tissue` (gold_tissue_mart.db snapshot).
