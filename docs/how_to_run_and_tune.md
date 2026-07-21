# How to run and tune the sheet (operator cheat sheet)

For driving the pipeline live (e.g. a lab meeting): change a setting, re-run, show the result. Keep this open.

---

## The whole loop (this is all it is)
1. **Edit** one of the three config files (below).
2. **Run:** `bash build/run_all.sh`   (rebuilds everything, ~15-20 sec; ignore the `_ARRAY_API` warnings, they are cosmetic).
3. **Look** at the result:
   - the **terminal summary** it prints (the funnel: how many pass the gates, how many are ranked) — fastest to show;
   - **`data/gold/formulation_shortlist.xlsx`** — the ranked shortlist (open the **`_switchboard`** tab: it prints the exact settings that produced it);
   - **`data/gold/gold_unified_sheet.xlsx`** — the full card, one row per strain.

**Reset button (your safety net):** `git checkout config/` puts all three config files back to the shipped defaults instantly. Use it between scenarios.

---

## The three knobs (which file does what)
| File | Controls | You'll touch it to... |
|---|---|---|
| `config/data_sources.yaml` | **what data is plugged in** (on/off + version per source) | turn a data source off, or point at a newer file |
| `config/thresholds.yaml` | **how each column's value is computed** (cutoffs) | change a cutoff, e.g. what counts as "resistant" |
| `config/formulation_criteria.yaml` | **how columns become a pass/fail + ranked shortlist** (the gates and the ranking) | set the gates, tighten a bar, change the ranking |

Mental model: **PLUGGED IN → COMPUTED → USED.** Most live tuning happens in the last two files.

### Criteria vocabulary (for `formulation_criteria.yaml`)
Each criterion has a **`mode`**: `gate` (must-pass, fail it and the strain is out), `rank` (orders survivors, never excludes), or `off` (ignored). Gates also have a **`pass_when`** test (`"== N"`, `"<= 2"`, `">= 50"`). `ranking.order` lists the rank criteria to sort by, best first.

---

## Recipe card ("if the team says X, do Y")
Numbers are the current result vs. the default (317 pass the gates, 87 make the ranked shortlist). Edit the file, run, done.

| If the team says... | Change | In file | Result |
|---|---|---|---|
| "Call resistance at **30%**, not 50%" | `resistance_cutoff_pct: 50` → `30` | `thresholds.yaml` | more strains flagged resistant → **289 pass, 77 ranked** |
| "**Require** growth in SCFM" | on `grows_in_scfm`: `mode: rank` → `mode: gate`, and add `pass_when: "== Y"` | `formulation_criteria.yaml` | **105 pass, 20 ranked** |
| "Resist at most **1** drug" | on `amr_not_mdr`: `pass_when: "<= 2"` → `"<= 1"` | `formulation_criteria.yaml` | **195 pass, 49 ranked** |
| "**Zero** antibiotic resistance" | on `amr_not_mdr`: `pass_when: "<= 2"` → `"== 0"` | `formulation_criteria.yaml` | **126 pass, 20 ranked** |
| "Must knock down PA **≥ 50%**" | add the gate block below | `formulation_criteria.yaml` | **251 pass, 21 ranked** |
| "Factor in how **common in real airways**" | add the rank block below + add its name to `ranking.order` | `formulation_criteria.yaml` | same 87 survivors, **re-sorted** to favor airway-common strains |
| "Include the **pathogens** too" | `candidates_only: true` → `false` | `formulation_criteria.yaml` | pool 739 → 780; **320 pass, 88 ranked** |
| "Show it **without genomic AMR** data" | on `amr_genomic`: `enabled: true` → `false` | `data_sources.yaml` | that column goes blank on the card |

**Block to add for "must knock down PA ≥ 50%"** (paste under `criteria:`, matching the indentation):
```yaml
  - name: beats_pa_50
    column: comp_best_team_pa
    column_fallback: comp_best_solo_pa
    mode: gate
    pass_when: ">= 50"
    missing: pass
```

**Block to add for "factor in airway commonness"** (paste under `criteria:`), then update `ranking.order`:
```yaml
  - name: common_in_airways
    column: prevalence_metag
    mode: rank
    higher_is_better: true
    missing: rank_last
```
```yaml
ranking:
  order: [beats_pa, common_in_airways, grows_in_scfm]
```

---

## Live-demo tips
- **Keep the quotes** around `pass_when` values (`"== N"`, `"<= 2"`). And keep YAML indentation as-is (it is space-sensitive).
- **Reset anytime** with `git checkout config/` — great for "let's try a different scenario."
- The build reads Sun-Young's big Excel file, so a run takes ~15-20 seconds. Say a sentence while it runs.
- The quickest "wow": change one line, re-run, and read the two funnel numbers out loud (pass-the-gates and ranked). Then open the shortlist's `_switchboard` tab to show the settings that produced it.
- After a settings change, `bash tests/run_tests.sh` will show the **snapshot test failing** on purpose (it noticed your change) — that is expected, not a problem; the other tests stay green. You do not need to run tests during the demo.
- Blank cells always mean "not screened yet," not "no result." Relevance columns are on the card but only affect ranking if you add them to `ranking.order` (recipe above).

## Before the meeting (2-minute checklist)
1. `bash build/run_all.sh` → confirm it ends with **317 pass / 87 ranked** (the known-good baseline).
2. Have `data/gold/formulation_shortlist.xlsx` and `data/gold/gold_unified_sheet.xlsx` ready to open.
3. Remember the reset: `git checkout config/`.
