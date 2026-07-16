# Decision Record — Gold Unified Sheet (`gold_unified_sheet.py`)

**Purpose:** why the strain-level decision card is assembled the way it is. Companion to
`competition_stat_sheet_decisions.md`. Human- and agent-readable ADR.

**Status:** active · **Created:** 2026-07-15 · **Code:** `build/gold_unified_sheet.py`
**Data state:** PRELIMINARY — wet-lab silver inputs are pre-QC (SYK); the card inherits that.

---

## Decisions

### D1 — Grain = strain (780 rows), from `identity_strains`
One row per strain group, labeled by its representative isolate + species. This is the decision grain the
team asked for (not ~4,900 isolates). Isolates map up via `identity_isolates` (the strain-group map).

### D2 — Isolate → strain aggregation: worst-case safety, best-case competition
- **Safety (hemolysis, AMR):** **worst-case** across the group's isolates — if *any* isolate is
  beta-hemolytic or resistant, the strain is flagged. Rationale: safety should be conservative.
- **Competition:** **best-case** — we pick the single group isolate with the strongest team result and copy
  its whole competition record (solo / team / partner / synergy) so those numbers stay internally consistent
  (all from one isolate, not mixed). Rationale: we want the strain's demonstrated potential.
- In practice most assays were run on one isolate per strain (usually the representative), so this is
  usually a pass-through, not a real reduction. **Revisit if:** we want per-isolate detail surfaced.

### D3 — `is_candidate` from a team-owned safety reference (`species_safety.csv`)
- **What:** candidacy comes from `data/reference/species_safety.csv` (species- or genus-level rows, each with
  a level: pathogen / opportunistic / review). `is_candidate = False` for pathogen + opportunistic;
  `candidate_review` surfaces genus-watchlist ("review") and "unreviewed" strains for a biologist to vet. GTDB
  name suffixes are normalized before lookup (so `Citrobacter_B koseri` matches `Citrobacter koseri`;
  `Serratia_J` matches the `Serratia` watchlist).
- **INTERIM + honest meaning (⚠️):** the file is our best-guess seed (classic pathogens + the opportunists the
  team already flagged — C. koseri, E. coli, P. fulva — plus a genus watchlist). `is_candidate = True` means
  "NOT a known pathogen," NOT "safety-cleared." At build: 41 excluded (pathogen/opportunistic), 10 flagged
  review, 729 unreviewed candidates.
- **To finalize:** replace/merge with **Gwyn's BSL-1 list** as the authoritative source when it lands. The
  file is team-owned and editable — safety is the biologists' call; we built the mechanism, not the verdict.
- **Earlier limitation (resolved):** the previous hard-coded 8-species list let opportunists through and
  mis-counted unknown-species strains as non-candidates; the reference-file approach fixes both.

### D7 — Every threshold/policy is team-owned via `config/thresholds.yaml`
Safety/competition aggregation modes, and all cutoffs used upstream, are read from the config, not hard-coded
(see `thresholds_are_team_owned.md`). The card's `_about` sheet prints the current settings so scientists see
exactly what produced the numbers and know they can change them.

### D4 — Reserved blank columns for data not yet in hand
`viability_scfm`, `carbon_profile`, `tissue`, `mouse`, `airway_ubiquity`, `bsl_level`, `decision`,
`decision_reason` exist but are empty. Rationale: the schema is stable as data arrives; the card fills in
gradually rather than being restructured each time.

### D5 — Outputs: `.xlsx` (human) + `.csv`/`.parquet` (canonical); sorted candidates-first
xlsx for eyeballing/editing the decision register; csv/parquet as the machine-canonical build. Rows sorted
candidates-first, then best team knock-down of PA descending, so the strongest candidate competitors are at
the top. Tab is named "(PRELIM)" as a standing reminder.

### D6 — Coverage is partial and that's honest
Species + genomic-AMR are near-complete (~all strains); hemolysis / measured-AMR / competition cover only the
screened subset (~600 / ~600 / 33 candidates). Blank cells mean "not screened yet," not "no result." We do
NOT impute.

## Change log
- 2026-07-15 — initial version (D1–D6), created alongside `gold_unified_sheet.py`.
