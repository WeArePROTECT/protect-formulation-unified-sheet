# Decision Record — Competition Stat Sheet (`silver_competition.py`)

**Purpose of this doc:** capture *why* the competition stat sheet is built the way it is — the choices we
made, the options we weighed, what we picked, and what would make us change our minds later. Readable by
humans and AI agents. If anyone ever asks "why median?" or "why did you drop those wells?", the answer is here.

**Status:** active · **Created:** 2026-07-15 · **Owner:** Spencer (+ Alex) · **Code:** `build/silver_competition.py`
**Data state at creation:** SYK `ASMA_phenotype_20260714.xlsx` is **raw / pre-QC** — treat all numbers as preliminary.

Format note: this is an **Architecture Decision Record (ADR)** — a standard way to log engineering decisions.
New decisions get appended; superseded ones are marked, not deleted (so the history stays honest).

---

## Context (what this sheet is)
The `Competition` sheet has one row per lab **well**: a *formulation* (a team of 1–5 strains, in columns
`ASMA_A_id…E_id`) co-cultured with one *pathogen reporter* (`Reporter_id`), scored by `Inhibition_percent`
(0 = pathogen grew freely, 100 = fully blocked). We turn ~27,666 wells into (a) a **formulations** table
(team × pathogen) and (b) a **per-strain** summary for the decision card.

---

## Decisions

### D1 — Source = the newest workbook (`20260714`), not the Q7 file
- **Options:** reuse the Q7 dashboard's source (`20250625`) · point at the newest (`20260714`).
- **Chosen:** `20260714`.
- **Why:** it's current, and its `Competition` sheet added per-member inoculation ODs, an `OD_ratio`, and a
  documented reporter-only control the Q7 file lacked. **Revisit if:** SYK ships a newer workbook (repoint).

### D2 — Keep only "Standard" conditions; drop `Non-standard_A`
- **Options:** use all wells · keep only standardized wells.
- **Chosen:** keep wells whose `Assay_condition_type` starts with `Standard` (Standard_A/B/C); drop `Non-standard_A`.
- **Why:** SYK's notes say `Non-standard_A` wasn't OD-normalized and its incubation ran 16–24 h, so it isn't
  quantitatively comparable. (**Gotcha:** the real label is `Non-standard_A` with a hyphen, not the underscore
  the notes doc implies — we match on the `Standard` prefix to be safe.) This drops 4,075 of 27,666 wells.
  **Revisit if:** SYK re-normalizes those wells.

### D3 — A formulation is an *unordered set* of members
- **Options:** treat `{A,B}` and `{B,A}` as different · collapse to one.
- **Chosen:** collapse — represent each team as a `frozenset` of canonical `ASMA_id`s.
- **Why:** column order is arbitrary; A+B is the same community as B+A. (This idea is borrowed + validated from
  the Q7 analysis, which proved order-insensitive dedup materially changes the counts.)

### D4 — Collapse replicate wells with the **median** (keep max too)  ← the "why median" question
- **Options:** mean · **median** · max/best.
- **Chosen:** **median** is the headline; we also store `inhibition_max` and `n_wells`.
- **Why:** the data is **pre-QC with known outliers** (SYK), and the median ignores a single weird well that
  would drag a mean or inflate a max. Keeping `max` preserves the "best-case" view for anyone who wants it, and
  `n_wells` shows how much evidence backs each number. **Revisit if:** SYK finalizes QC and removes outliers —
  then mean or max may be preferable, and this is the first knob to reconsider.

### D5 — Per-strain metrics: solo, team, partner, **signed synergy**
- **Chosen columns:** `best_solo_inhib_pa` (best knock-down alone), `best_team_inhib_pa` (best knock-down on any
  team containing the strain), `best_partner` (the team that achieved it), `suppressive_synergy_pa`
  (= team − solo, **signed**), `best_inhib_pa_any` (best vs any PA reporter, for context), `n_formulations_pa`.
- **Why signed synergy:** a real finding in this project is that **bigger teams often do *not* beat their best
  single member.** A signed value (positive = partners help, ≤0 = the strain is as good or better alone) captures
  that, where a magnitude-only score would hide it. Sanity check at build: ASMA-2 = −6 solo → 87 on a team
  (+93 synergy); ASMA-230 = 78 solo → 91 team (+13). Both read correctly.
- **Two-level aggregation:** median *within* a formulation (robust), then max *across* formulations (best
  achievable) — so "best team" means the strain's strongest real community, not a noisy well.

### D6 — Headline pathogen = `PA14_KEH108`; other PA reporters pooled; VAP kept separate
- **Options:** one PA reporter · pool all PA · include VAP pathogens in the headline.
- **Chosen:** headline vs **PA14_KEH108** (the main reporter, 12k wells, and the reporter the ARPA-H "≥50% PA"
  bar is defined against); `best_inhib_pa_any` pools the 5 P. aeruginosa reporters (PA14_KEH108, PA14_FA, PAO1,
  clinical ASMA-137/143); the VAP pathogens (AB/KP/SA) are **not** in the PA headline.
- **Why:** PA is the primary target and keeps us comparable to the deliverable. **Revisit if:** we report the
  "inhibits *all* VAP pathogens ≥25%" deliverable — then add per-VAP columns from the same formulations table.

### D7 — Two output tables at two grains
- **Chosen:** `formulations` (one row per team × reporter — team grain, because teams are what we ship) and
  `silver_competition` (one row per member strain — strain grain, because the decision card is per strain).
- **Why:** the card needs per-strain rows, but we must not lose the team-level detail; keeping both lets us
  roll up or drill down.

### D8 — Wrote fresh; borrowed validated ideas from the Q7 code
- **Chosen:** re-used two proven ideas (frozenset dedup D3, best-inhibition aggregation) but wrote the sheet
  fresh — because the Q7 code was built for dashboard *counts/distributions*, pointed at the old file, didn't
  filter conditions (D2), and didn't produce the per-strain rollup (D5). **Why:** reuse the logic, not the purpose.

---

## Things intentionally NOT decided here (owned elsewhere / later)
- **Pass/fail cutoffs** (e.g. "≥50% = competitive"): the biologists set these. We store raw %s so any cutoff
  re-derives without a rebuild.
- **How competition rolls up isolate→strain on the gold card** (worst/best-case): documented with the gold card.
- **Prebiotic (± mucin) and inoculation-ratio effects:** columns exist in the source; not yet modeled.

## Change log
- 2026-07-15 — initial version (D1–D8), created alongside `silver_competition.py`.
