# Decision Record — Viability Stat Sheet (`silver_growth_endpoint.py`)

**Purpose:** why the viability (SCFM grow/no-grow) sheet is built this way. ADR, human- and agent-readable.
**Status:** active · **Created:** 2026-07-15 · **Code:** `build/silver_growth_endpoint.py`
**Thresholds:** all in `config/thresholds.yaml` (team-owned — see `thresholds_are_team_owned.md`).
**Data state:** PRELIMINARY (SYK pre-QC).

---

## Context
The `Growth_endpoint` sheet gives endpoint OD600 (culture cloudiness) after 72 h in SCFM (lung-mimic),
SCFM+mucin, rich media (BHIS = positive control), and no-carbon (negative). We turn it into a per-strain
"can it grow in SCFM, and does mucin help" readout — the VIABILITY gate.

## Decisions

### D1 — Background-subtract using the per-date BLANK wells
The sheet has 43 `BLANK` wells (media only). Per Sun-Young's note, we subtract the BLANK from the **same
`Assay_start_date`** (averaged if several) from every reading, per condition; global-average fallback if a
date has no blank. **Why:** the raw floor is ~0.04 OD (plate/media background); subtracting it makes "did it
actually grow" meaningful.

### D2 — Grow/no-grow call = above an absolute floor AND above the negative control
`grows_scfm = "Y"` if background-subtracted `SCFM_72 >= scfm_grow_min_od` (config, default 0.1) **and** it
exceeds the no-carbon control. **Options considered:** absolute floor · fraction of the positive control
(BHIS) · simply "above no-carbon". **Chosen:** absolute floor + above-negative, because it's simple, matches
Sun-Young's own ΔOD 0.1 growth-QC logic, and the data supports it (median SCFM growth is ~0.05, barely above
blank, so real growers stand out). **Revisit if:** the team prefers a relative cutoff — it's one line in the config.

### D3 — Trust a "no-grow" only if it grew in rich media (QC)
If a strain didn't even grow in BHIS (`>= qc_rich_media_min_od`, config 0.1), its SCFM no-grow is
uninformative (it's just unculturable in this run), so we mark the call **inconclusive** (blank), not "N".
At build: 97 grow, 571 no-grow, 96 inconclusive of 764.

### D4 — Mucin lift = SCFM+mucin minus SCFM
`mucin_lift` captures the **prebiotic signal** — does adding mucin help this strain grow. Positive lift is a
candidate prebiotic responder. (177 strains show a lift >= 0.1 OD.)

### D5 — Aggregate: mean of corrected values per isolate; strain rollup best-case
Replicates for one isolate average (corrected); on the gold card a strain "grows in SCFM" if any of its
isolates does (best-case, matching the competition rollup). Raw ODs are kept so any cutoff re-derives.

**Superseded in part, 2026-11-24:** the replicate summary is now a team setting, median by default (D6). The
best-case strain rollup stands.

### D6: Replicate summary is a team setting, median by default (2026-11-24)
`viability.replicate_aggregation` in `config/thresholds.yaml` (`median` or `mean`) says how an isolate's
blank-subtracted wells collapse to one number, for every condition: SCFM, SCFM+mucin, the BHIS rich-media check
and the no-carbon control. Default **median**. The rest is unchanged: each well minus the MEAN of its date's BLANK
wells (D1), floored at 0; the 0.1 OD cutoff and the no-carbon comparison (D2); the rich-media check (D3); the
best-case strain rollup (D5). The call still compares the summary rounded to 3 decimals, as before, so a median of
0.0996 counts as 0.1.

**Why:** 754 of the 762 isolates have 3 wells, and with 3 wells the mean lets one odd well decide the call: wells
of about 0.03, 0.50 and 0.03 average 0.19, a "grows", though 2 of the 3 did not grow. The median reaches 0.1
exactly when at least 2 of the 3 wells do. The same holds for the rich-media check: a strain passes it when 2 of 3
BHIS wells grew, not when one well lifts the average. Spencer's decision L, 2026-11-24, on PROTECT-60 (the ASMA
dashboard data contract, part 2, section 7): the median "for now", so this sheet and the dashboard show one
number; the science is to be checked with Gwyn.

**Options considered:** the mean (the rule before; one high well can make a "grows"); the median (chosen); the
number of wells at or above the cutoff (the same call as the median with 3 wells, but no OD value to show).

**Effect at the switch** (SYK's 20261113 workbook, the build behind curated export `curated_export_20261124_171929`;
diff in `sjlong/current_tasks_11_2026/growth_median_20261124/`):
- `grows_scfm`: 26 of 762 isolates change. 17 go from Y to N: at most one of their 3 wells reached the cutoff,
  and that well carried the mean over it (for example 0.44, 0.01 and 0.01; a few are borderline, such as 0.099,
  0.091 and 0.111). 6 go from N to inconclusive: only 1 of their 3 BHIS wells grew. 3 go from
  inconclusive to N: 2 of 3 BHIS wells grew, and a third at 0 had held the mean under 0.1. Totals: Y 96 to 79,
  N 572 to 586, inconclusive 94 to 97.
- `grows_scfm_mucin`: 22 change (10 Y to N, 3 N to Y, and the same 9 rich-media moves); Y 244 to 237.
- Gold card: `grows_scfm` changes for 25 strain groups, 13 of them through an isolate that is not the genomic
  representative; `scfm_od` changes for 484 groups and `mucin_lift` for 594, by more than 0.05 OD for 19 and 24.
- Shortlist: no status or rank moves (98 ranked, 209 unscreened, 432 excluded). The `grows_in_scfm` value changes
  for 23 groups, one of them ranked: group 563 (rank 43) goes from Y to N through its assay isolate ASMA-3318.

**Revisit if:** the bench says a single high well is usually real patchy growth rather than contamination or a
pipetting slip (a question for Gwyn and Sun-Young), or the replicate count changes (with 2 wells the median is the
mean). Going back is one line in the config.

## Not decided here
The grow/no-grow **cutoff value** and QC floor are team-owned (config). We ship 0.1 as a sensible default.
The replicate summary is team-owned too (`viability.replicate_aggregation`, D6).

## Change log
- 2026-07-15 — initial version (D1–D5), created alongside `silver_growth_endpoint.py`.
- 2026-11-24: D6, the replicate summary becomes a team setting, median by default (Spencer's decision L on PROTECT-60; PROTECT-78, epic PROTECT-76). D5's mean is superseded.
