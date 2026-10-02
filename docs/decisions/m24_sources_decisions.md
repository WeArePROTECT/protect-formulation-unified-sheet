# Decision Record: Sun-Young's Month 24 workbook (2026-10-01)

**Status:** active · **Created:** 2026-10-01 · **Owner:** Spencer · **Jira:** PROTECT-29 (Month 24 data),
PROTECT-34 (ASMA-4467 retraction) · **Evidence:** `/usr2/people/protect/Arkin_Lab/sjlong/current_tasks_9_2026/syk_phenotype_20260927/`

Format: Architecture Decision Record. New decisions are appended; superseded ones are marked, not deleted.

## Context
Sun-Young Kim posted his Month 24 phenotype update on 2026-09-28 and corrected it twice; he asked that
`ASMA_phenotype_20260929.xlsx` "or later" be the reference. It removes ASMA-4467, adds the full
carbon-kinetics set, a diverse-PA competition panel with a new `Media` column, and two new sheets (MIC,
96-well drop-out) that this card does not read. The same build feeds `protect.curated` on the lakehouse.

## Decisions

### D1: Repoint the three SYK sources to `20260929`
- **Chosen:** `amr_measured`, `growth_endpoint`, `competition` in `config/data_sources.yaml`.
- **Why:** his instruction (Slack, 2026-09-29). Before repointing, the unchanged sheet was rebuilt on
  2026-10-01 and reproduced all 18 of its CSV outputs byte for byte, so every change below comes from
  this workbook and these rules, not from drift in another source.

### D2: Drop ASMA-4467's hemolysis rows through a shared retraction list
- **Context:** the stock in FREP5 well B9, labelled ASMA-4467 (*Streptococcus vaginalis*), was a different
  organism (Sun-Young, 2026-09-25; the well confirmed bad 2026-09-28). He deleted its growth-endpoint and
  antibiotic rows at source. Its 2 hemolysis rows are in Cassandra Reyes's file, which cannot be reissued.
- **Chosen:** `hemolysis.retractions` points at `protect_lakehouse_pipeline/datasets/phenotype/retractions.csv`,
  the same file the lakehouse phenotype exporter reads, so the card and `protect.phenotype` drop the same
  rows. Each line must match exactly its `expected_rows` or the build stops.
- **Consequence the team must read correctly:** strain group 259 now has no hemolysis or measured-AMR
  result. The safety gates are `missing: pass`, so it moves from `excluded` to `shortlist_unscreened` with
  both gates `untested`. That means **safety unknown, not safe**, until the strain is re-isolated and
  re-tested (Sun-Young: it "may take some time").
- **Revisit if:** the re-test arrives (it will be new data, not a reversal of this line), or the team
  wants missing safety data to fail the gate (`missing: fail` in `config/formulation_criteria.yaml`).

### D3: `SCFM_10X_glucose` is not a standard condition
See `competition_stat_sheet_decisions.md` D9.

### D4: The P. aeruginosa reporter list lives in config
See `competition_stat_sheet_decisions.md` D10.

## What moved (verified by diffing the old card against the new one)
One status move: sg 259 `excluded` -> `shortlist_unscreened`. Five `value_beats_pa` moves from new team
results, none changing a status. Funnel: pass_gates 305 -> 306, ranked 96 (unchanged), unscreened
209 -> 210, excluded 434 -> 433, fail_non_hemolytic 349 -> 348. Pinned in `tests/test_default_snapshot.py`
and `tests/test_m24_sources.py`; 96 of 96 tests pass.
