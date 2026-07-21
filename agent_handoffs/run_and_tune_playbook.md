# Agent playbook: run and tune the Unified Sheet on Spencer's behalf

**Your job:** Spencer (relaying his team, often live in a meeting) tells you the settings, thresholds,
formulation criteria, or ranking he wants. You translate that into edits of the config files, run the pipeline,
verify it worked, and report the results plainly with a pointer to the output. He should not have to touch any
files. Be fast, be safe, and confirm anything ambiguous before running.

> **This is for experimentation / demos. Do NOT commit or push these config changes** unless Spencer explicitly
> says "make this the new default." They are throwaway scenarios. Reset with `git checkout config/` between them.

---

## The loop (every request is this)
1. **Translate** the request into edits of one or more config files (tables below).
2. **Run:** `bash build/run_all.sh` from the project dir (~15-20 sec; the `_ARRAY_API` warnings are cosmetic).
3. **Verify** it ran clean (no error, funnel printed).
4. **Report** to Spencer: what you changed, the funnel numbers, the top of the shortlist, and where the file is.

**Project dir:** `/usr2/people/protect/Arkin_Lab/sjlong/current_tasks_7_2026/formulation_unified_data_sheet_7_14_2026/`
**Outputs:** `data/gold/formulation_shortlist.xlsx` (ranked shortlist; the `_switchboard` tab prints the active
settings), `data/gold/gold_unified_sheet.xlsx` (full card), and `.csv` versions of both.
**Baseline (shipped defaults):** 739 candidates → **317 pass the gates → 87 ranked** + 230 pass-but-unscreened; 422 excluded.

## The three config files
| File | Controls | Change it for... |
|---|---|---|
| `config/thresholds.yaml` | how a column's VALUE is computed (cutoffs) | "call resistance at 30%", "what counts as growing" — **needs the full rebuild to take effect** |
| `config/formulation_criteria.yaml` | how columns GATE and RANK (the shortlist logic) | gates, bars, ranking, "focus on X" — most requests land here |
| `config/data_sources.yaml` | what data is plugged in (on/off per source) | "turn off source Y", "show it without Z" |

**Criteria vocabulary** (`formulation_criteria.yaml`): each criterion has a `mode` = `gate` (must-pass),
`rank` (orders survivors, never excludes), or `off` (ignored); gates have a `pass_when` test (`"== N"`, `"<= 2"`,
`">= 50"`); `ranking.order` lists the rank criteria to sort by (best first); `candidates_only` (true/false)
restricts to non-pathogens. Rank criteria also have `higher_is_better` (true/false) and a `missing` policy
(`rank_last`/`rank_first`). Keep the quotes on `pass_when`, and keep YAML indentation exact.

---

## Translation table (team request → exact edit)
Numbers are the result vs. the 317/87 baseline (verified). "criteria" = `formulation_criteria.yaml`, "thresholds" = `thresholds.yaml`, "sources" = `data_sources.yaml`.

| Team says... | Edit | File | Effect |
|---|---|---|---|
| "Call resistance at 30% (not 50%)" | `resistance_cutoff_pct: 50` → `30` | thresholds | more flagged resistant → 289 pass / 77 ranked |
| "Require growth in SCFM" | on `grows_in_scfm`: `mode: rank`→`gate`, add `pass_when: "== Y"` | criteria | 105 pass / 20 ranked |
| "Resist at most 1 drug" | on `amr_not_mdr`: `pass_when: "<= 2"` → `"<= 1"` | criteria | 195 pass / 49 ranked |
| "Zero antibiotic resistance" | on `amr_not_mdr`: `pass_when` → `"== 0"` | criteria | 126 pass / 20 ranked |
| "Drop the AMR gate" | on `amr_not_mdr`: `mode: gate` → `off` | criteria | AMR no longer excludes anyone |
| "Non-hemolytic only" | already the default (`non_hemolytic` is a gate) | criteria | (no change needed) |
| "Must knock down PA ≥ 50%" | add the **gate block** below (`comp_best_team_pa >= 50`) | criteria | 251 pass / 21 ranked |
| "Rank by airway commonness too" | add the **rank block** below (`prevalence_metag`), add its name to `ranking.order` | criteria | same survivors, re-sorted |
| "Prefer PA displacers" | add rank block on `pa_cooccurrence` with `higher_is_better: false` (NEGATIVE = displacer), add to `ranking.order` | criteria | re-sorted toward displacers |
| "Factor in predicted metabolic competitors" | add rank block on `pa_metabolic_competitor` (`higher_is_better: true`), add to `ranking.order` | criteria | re-sorted |
| "Rank by competition, then growth, then commonness" | `ranking.order: [beats_pa, grows_in_scfm, common_in_airways]` | criteria | changes the sort order only |
| "Include the pathogens too" | `candidates_only: true` → `false` | criteria | pool 739→780; 320 pass / 88 ranked |
| "Change what counts as growing in SCFM" | `scfm_grow_min_od: 0.1` → new value | thresholds | changes the grows_scfm calls (rebuild) |
| "Use mean, not median, for repeat wells" | `replicate_aggregation: median` → `mean` | thresholds | changes competition numbers (rebuild) |
| "Turn off genomic AMR data" | on `amr_genomic`: `enabled: true` → `false` | sources | that column blanks out |

**Gate block template** (paste under `criteria:`, match indentation):
```yaml
  - name: beats_pa_50
    column: comp_best_team_pa
    column_fallback: comp_best_solo_pa
    mode: gate
    pass_when: ">= 50"
    missing: pass
```
**Rank block template** (paste under `criteria:`), then add its `name` to `ranking.order`:
```yaml
  - name: common_in_airways
    column: prevalence_metag
    mode: rank
    higher_is_better: true
    missing: rank_last
```
Relevance columns you can rank/gate on: `prevalence_metag`, `abundance_metag`, `prevalence_metars`,
`abundance_metars`, `pa_cooccurrence` (negative = displacer, so use `higher_is_better: false` to prefer
displacers), `pa_metabolic_competitor`. All meanings are in `docs/gold_data_dictionary.md`.

## Composing several requests
The team will often stack requests ("stricter AMR AND require SCFM AND rank by commonness"). Just make all the
edits, then run once. Report the combined result.

## "Focus on X" and specific-formulation questions (engine limits, be honest)
- The engine **ranks individual strains** by the gates + ranking you set. It does **not** auto-assemble teams.
- **"Focus on Rothia / Streptococcus / a species"**: there is no species-filter switch. Instead, run as normal,
  then **filter the shortlist output** (`formulation_shortlist.csv`) to that genus/species and report that subset.
- **"How does formulation {A+B+C} do against PA?"**: look it up in **`data/silver/formulations.csv`** (one row
  per team × reporter, with the PA knockdown). That is the place for specific-combo questions.
- **"Top N candidates"**: report the top N rows of `formulation_shortlist.csv` (already sorted best-first).
- If a request cannot be expressed with gates/ranking/thresholds, say so plainly and offer the closest thing.

## How to report results (keep it scannable for a live room)
After each run, tell Spencer:
1. **What you changed** (one line, plain English).
2. **The funnel:** "X of 739 pass the gates → Y ranked" (vs. the 87 baseline so the change is visible).
3. **Top of the shortlist:** the top ~5-10 by species with the key number(s) the team cares about (e.g. PA
   knockdown, or airway prevalence if that is what they asked to rank on).
4. **Where to open it:** `data/gold/formulation_shortlist.xlsx` (its `_switchboard` tab shows the exact settings).
5. Offer the next move: reset (`git checkout config/`) or try another scenario.

Read the `.csv` to pull the top rows for the summary; do not just point at the xlsx.

## Live-demo discipline (important)
- **Reset between scenarios:** `git checkout config/` returns all three files to the shipped defaults instantly.
- **Never commit/push these experiments** to `main`. Only if Spencer says "lock this in as the default" do you
  commit (and then also update the snapshot test baseline + run `bash tests/run_tests.sh`).
- **Confirm ambiguous asks before running.** If the team says "make it stricter" without a number, ask which
  knob and what value, or state the assumption you are making. Never invent a threshold silently.
- **Only edit config**, never `build/*.py`, for tuning. Everything the team will ask for is a config change.
- If a run errors, it is almost always a **YAML typo** (indentation, or a missing quote on `pass_when`). Fix and rerun.
- After a change, the tests' **snapshot** check will fail on purpose (it noticed the change) — that is expected;
  you do not need to run tests during a demo.
- Blank cells mean "not screened yet," not "no result." Relevance columns only affect ranking if you add them to
  `ranking.order`.

## Reference
- `docs/how_to_run_and_tune.md` — the human version of this (same recipes).
- `docs/gold_data_dictionary.md` — every column, what it means, its values, and where it came from.
- `STATUS.md` — what is in the sheet and what is still pending.
- The three config files themselves are heavily commented.

## How Spencer likes to work
- **End every turn with a short what / why / where-we-stand / next summary**, accessible level.
- **No em dashes** in your messages. Commas, colons, parentheses, periods, "and".
- **Precision matters** — the results must come from the settings, not a bug; verify each run actually reflects
  the change. He welcomes pushback if a request does not make sense.
- **The biology is the team's** — you set the switches they ask for; you do not decide the thresholds.
- Be warm, clear, and quick.
