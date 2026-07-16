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

## Not decided here
The grow/no-grow **cutoff value** and QC floor are team-owned (config). We ship 0.1 as a sensible default.

## Change log
- 2026-07-15 — initial version (D1–D5), created alongside `silver_growth_endpoint.py`.
