# Decision Record — Heuristic Shortlist / Decision Engine (`heuristic_shortlist.py`)

**Purpose of this doc:** capture *why* the formulation shortlist is built the way it is. This is the step
Adam explicitly asked for ("the pass/fail formulae that allow ranking"). Readable by humans and AI agents.

**Status:** active · **Created:** 2026-07-18 · **Owner:** Spencer (+ Alex) · **Code:** `build/heuristic_shortlist.py`
**Config:** `config/formulation_criteria.yaml` (the team-owned switchboard)
**Data state at creation:** the gold card it reads is **PRELIMINARY** (SYK phenotype data pre-QC) — the shortlist inherits that.

Format note: this is an **Architecture Decision Record (ADR)**. New decisions get appended; superseded ones
are marked, not deleted.

---

## Context (what this step is)
The gold card has one row per strain with the measurable columns (safety, viability, competition). This step
turns those columns into a **ranked shortlist**: must-pass **gates** thin the field, **rank** criteria order
the survivors. The whole point of the design is that **the biologists own where every bar sits** and can
re-dial it without touching code. So the intelligence lives in a config file (the "switchboard"), and the
Python is a small, biology-agnostic engine that just applies it.

Guiding principle (from Spencer, 2026-07-18): *"We build the switches; the scientists set where the switches
point. It is not us picking the final isolates."* Every decision below serves that.

---

## Decisions

### D1 — A separate decision layer, distinct from `thresholds.yaml`
- **Options:** extend `config/thresholds.yaml` · a new `config/formulation_criteria.yaml`.
- **Chosen:** a new file, `formulation_criteria.yaml`.
- **Why:** two different jobs. `thresholds.yaml` controls how a column's **value** is computed (e.g. the AMR
  cutoff that decides `amr_resistance_count_prov`). This file controls how those columns **combine into a
  pass/fail/rank decision**. Keeping them separate means a scientist tuning the decision logic never has to
  wade through value-computation settings, and vice versa. **Revisit if:** the team would rather have one file.

### D2 — The engine is config-driven and biology-agnostic
- **Chosen:** the code knows only how to apply `gate` / `rank` / `off` + a missing-data policy to columns. It
  contains **no hard-coded thresholds and no biology.** Every gate, cutoff, ranking key, and tie-breaker is a
  line in the YAML.
- **Why:** this is the deliverable Spencer and Alex actually own — the *mechanism* by which the biologists
  express whatever standard they land on. Adding a new gate = adding a config block (no code change); changing
  viability from a gate to a ranking signal = changing one word. **Revisit if:** a criterion type appears that
  the gate/rank/off vocabulary can't express (then extend the engine, keep it generic).

### D3 — Strawman defaults: Safety gates, Viability/Competition rank
- **Chosen defaults (all provisional, all one edit away):**
  - **Safety = the only hard gates:** `non_hemolytic` (`hemolysis_beta == N`) and `amr_not_mdr`
    (`amr_resistance_count_prov <= 2`, i.e. resists at most 2 of 6 drugs).
  - **Viability = a ranking signal, NOT a gate:** `grows_in_scfm` ranks survivors; it does not exclude.
  - **Competition = the primary ranking key:** `beats_pa` = `comp_best_team_pa`, falling back to
    `comp_best_solo_pa` when a strain has no team result.
- **Why viability is not a hard gate by default:** SCFM is a deliberately harsh lung-mimic medium and the data
  is pre-QC, so only ~53 of 739 candidates score positive. Making it a must-pass collapses the shortlist from
  **87 to 20** (measured, see funnel below) and would drop strains that are perfectly manufacturable in rich
  media. That is a biology call, not a plumbing call, so we ship it as a signal and make flipping it to a gate
  a **one-line** change (documented right above the criterion in the YAML). **Revisit:** the team sets this.
- **Why team-preferred-then-solo for competition:** only 29 candidates have multi-member (team) PA data, but
  193 have a solo result; ranking on team-only would waste most of the competition evidence. The `source_beats_pa`
  output column records which was used, so nothing is hidden.

### D4 — Missing data never silently drops a strain (per-criterion policy)
- **Chosen:** each criterion carries a `missing` policy. Defaults: **gates `pass`** (an untested strain is not
  punished by a gate it has no data for) and **ranking `rank_last`** (untested sinks). Strains that pass the
  gates but have no value for the **primary** ranking column go to a flagged `shortlist_unscreened` tier
  (`unscreened_tier: true`), listed separately rather than ranked as if they lost.
- **Why:** competition coverage is sparse (194 of 739 candidates). A silent "no data = out" would hide most of
  the collection and read as "we screened everything." Surfacing untested strains in their own tier is honest
  and lets the team see the screening backlog. Every part of this is a switch (`missing: fail` makes a gate
  strict; `unscreened_tier: false` folds them back into the ranking as last). **Revisit if:** the team wants
  untested strains excluded — one field.

### D5 — Ranking is lexicographic (ordered), not a weighted composite (for now)
- **Options:** ordered/lexicographic (sort by primary, break ties by the next) · weighted normalized score.
- **Chosen:** ordered, driven by `ranking.order`.
- **Why:** it is **legible and auditable** — "ranked by PA knock-down, ties broken by SCFM growth" is a
  sentence a scientist can check by eye, with no hidden normalization or weighting choices to argue about. A
  weighted composite is more flexible but opaque and introduces its own (contestable) scaling decisions.
  **Revisit if:** the team wants weighted scoring — add a `ranking.method: weighted` branch; the switchboard
  shape already anticipates it.

### D6 — Output keeps every candidate, with a status + per-gate columns + a reason
- **Chosen:** the shortlist table lists all evaluated strains with `status` ∈ {`shortlist`,
  `shortlist_unscreened`, `excluded`}, a `gate_<name>` column per gate (`pass`/`FAIL`/`untested`), a
  `value_<name>` per ranking criterion, and a plain-English `shortlist_reason`.
- **Why:** transparency. A biologist can see exactly which switch acted on each strain and, crucially, **what
  they would get back by relaxing a gate** (e.g. a strong PA competitor excluded only for AMR is right there
  with `gate_amr_not_mdr = FAIL`). The `_switchboard` tab in the xlsx prints the active settings + the funnel,
  so the sheet explains itself.

### D7 — `ranking.order` is lenient (skip-and-note), so flipping one `mode:` never breaks the build
- **Chosen:** if `ranking.order` names a criterion that isn't currently `rank`-mode (e.g. the scientist just
  flipped it to a gate), the engine skips it with a printed note instead of raising.
- **Why:** the switchboard is edited by hand by non-programmers. Flipping `grows_in_scfm` from `rank` to `gate`
  should not also require remembering to delete it from `ranking.order`. Frictionless switching is the whole
  point. **Revisit if:** we want stricter validation (then make it a `--strict` flag, not the default).

---

## Sanity check at build (default switchboard, 739 candidates)
```
gate non_hemolytic (hemolysis_beta == N)          : 336 fail
gate amr_not_mdr  (amr_resistance_count_prov <= 2): 215 fail
pass ALL gates                                    : 317
   -> ranked shortlist (has PA competition data)  :  87
   -> pass gates but competition unscreened       : 230
excluded (failed >= 1 gate)                       : 422
```
Switch-sensitivity (in-memory, to show the knobs bite): viability flipped to a hard gate -> 20 ranked;
AMR line tightened to `== 0` -> 20 ranked; an added `PA >= 50` competition gate -> 21 ranked;
`candidates_only: false` -> pool 780, 88 ranked. All from editing the YAML alone.

---

## Things intentionally NOT decided here (owned elsewhere / later)
- **Where every bar actually sits** (the hemolysis rule, the MDR line, whether viability gates, the competition
  bar): the **biologists own these**. We ship strawman defaults so there is something concrete to react to.
- **Weighted / composite scoring** (D5): available to add when the team asks.
- **Relevance / ubiquity as a ranking key:** waits on Emma's metagenomics (fills `airway_ubiquity`); once that
  column lands it is a one-line addition to `ranking.order`.
- **Tissue / mouse gates:** those columns are reserved and blank; add criteria when the data arrives.

## Change log
- 2026-07-18 — initial version (D1–D7), created alongside `heuristic_shortlist.py` + `formulation_criteria.yaml`.
