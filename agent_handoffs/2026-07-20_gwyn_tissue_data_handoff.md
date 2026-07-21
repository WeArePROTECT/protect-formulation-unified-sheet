# Handoff: Explore Gwyn's data + integrate her tissue results into the Unified Sheet (2026-07-20)

You are picking up a well-established data project (the PROTECT Formulation Unified Sheet). Gwyn (Gwyneth
Hutchinson-Ramirez) has just delivered a whole database of her data, which Spencer is uploading to the server.
Your job has two parts, in order: **(A) explore and DOCUMENT her database** so the team can always find and use
what it needs, then **(B) extract the specific pieces the Unified Sheet needs (her tissue results) and integrate
them into the pipeline**, following the project's established patterns.

> **IMPORTANT — you have NOT seen her data yet, and neither had the agent who wrote this.** Do not assume her
> file formats, schema, or labels. Everything below about *her* data is a thing to **discover and confirm**, not a
> fact. Explore first, document what is actually there, and flag questions for Gwyn where it is unclear.

> **FILL IN before starting (Spencer will provide):**
> - Path to Gwyn's uploaded directory: `__________________________`  (confirm with Spencer as step 0)
> - Anything Spencer already knows about how she structured it: `__________________________`

---

## 0. Spencer's "core ask" that Gwyn was answering
Spencer asked Gwyn for, specifically:
- **PA reduction on airway tissue** (how much a formulation knocked PA down on the tissue model) = the efficacy
  readout the Unified Sheet's reserved `tissue` column is waiting for.
- **Tissue damage / cytotoxicity** (did the formulation harm the tissue) = a safety readout we want to add too.
- Keyed so we can join it: by **formulation, and the member strains as ASMA ids**.

She then delivered her fuller database on top of that. So expect more than just those two readouts, and part of
your job is to map the whole thing, not only the two columns we need first.

## 1. Get up to speed on the project (read in this order, ~15 min)
1. `STATUS.md` (what the sheet is + current state, team-facing)
2. `README.md` (repo front door)
3. `docs/how_to_run_and_tune.md` (how the pipeline runs: edit a config -> `bash build/run_all.sh` -> read result)
4. `docs/gold_data_dictionary.md` (every column, its source, and its values)
5. **`docs/decisions/competition_stat_sheet_decisions.md`** and `gold_unified_sheet_decisions.md` (HOW a
   formulation-level assay is turned into per-strain columns — tissue works the same way; this is your template)
6. `config/data_sources.yaml` (the registry you will add Gwyn to) + `PROJECT_PLAN.md` sections 8-9 (history/status)
7. This handoff.

## 2. What the project is (30 seconds)
A strain-level decision card: one row per strain (~780; 739 candidates), pulling every screen into one place so
the team can pick formulations that are SAFE, GROW, and beat *Pseudomonas aeruginosa* (PA), with a fourth
RELEVANCE block (how present/PA-displacing a strain is in real patient airways). Bronze -> silver -> gold
pipeline, everything config-driven and team-owned. Spencer + Alex Styer are the data-integration layer; the
biologists own the thresholds. On GitHub (`WeArePROTECT/protect-formulation-unified-sheet`, code only, no data).

## 3. What the SHEET specifically needs from Gwyn (the integration deliverable)
| Need | Fills | Notes |
|---|---|---|
| **PA reduction on tissue** | the reserved `tissue` column (currently blank) | the main ask; efficacy readout |
| **Tissue damage / cytotoxicity** | a NEW safety column (propose `tissue_damage`) | a safety signal; confirm naming with Spencer |
| **(separate) BSL-1 safety list** | replaces the interim `data/reference/species_safety.csv` -> makes `is_candidate`/`bsl_level` authoritative | Gwyn owns this too; it MAY or may not be in this upload — check, but it is a different artifact from the tissue data |

## 4. THE make-or-break detail: tissue is a FORMULATION-level assay
Her tissue model tests **formulations (teams of strains), not single strains** — exactly like Sun-Young's
competition screen. To put a value on our strain-grain sheet you must:
1. Map each **formulation label** she used (last we heard, an F1-F10 set — **confirm**) to its **member strains as
   ASMA ids**. If her file only carries F-numbers, you also need the F-number -> members mapping (find who
   defined those formulations: likely Sun-Young or a formulation-definition file; confirm with Spencer).
2. **Roll up to strain** the same way competition does (best result as a member). Reuse the pattern in
   `build/silver_competition.py` (order-insensitive `frozenset` of members + best-as-member aggregation) and its
   ADR. **Do not reinvent this** — copy the proven approach.

If you cannot resolve formulation -> ASMA members, STOP and get it from Spencer; nothing downstream works without it.

## 5. Your mission, in order

### Part A — Explore and DOCUMENT Gwyn's database (do this FIRST)
Goal: we can always find and use what we need from her database and her directory.
- Locate her directory (path above; confirm with Spencer). Read any README / notes / metadata she included FIRST.
- Explore without assuming a format: list every file, understand what each dataset is, what she measured, how she
  built it, how the files/tables relate (keys, IDs, formulation labels, conditions, timepoints, replicates).
- Produce a **map/guide** as the durable artifact: `docs/gwyn_data_map.md` in this repo (what is there, what each
  dataset holds, how it is keyed, how to query it, what is usable for us vs. context-only, and open questions for
  Gwyn). Consider also dropping a short `README.md` in her directory. **Verify against the actual files; do not
  guess.** This is a real deliverable on its own — Spencer explicitly wants her database understood and documented.

### Part B — Integrate the tissue data into the Unified Sheet
Once you understand her data, follow the project's standard path (this is exactly how every other source was added):
1. **Register** the tissue source(s) in `config/data_sources.yaml` (exact path, owner Gwyn, a version label, and
   the `provides:` gold columns). Update `data/bronze/BRONZE_MANIFEST.md` to match.
2. **Write `build/silver_tissue.py`**: normalize every ASMA id via `lib_ids.normalize_asma_id`; map formulations
   to members; emit per-strain tissue metrics (PA reduction; and tissue damage). Model it on `silver_competition.py`.
3. **Wire into `build/gold_unified_sheet.py`**: add the new columns to `GOLD_COLS`, load the silver table (guard
   with `is_enabled(...)`), roll up to strain. Add the builder to `build/run_all.sh`.
4. **Document**: add the columns to `docs/gold_data_dictionary.md` (meaning / how-derived / values + the section's
   Source line), then **regenerate the Word copy**: `pandoc docs/gold_data_dictionary.md -o docs/gold_data_dictionary.docx`
   (keep a blank line before every table, or pandoc merges it). Re-upload the .docx to the Drive.
5. **Write an ADR**: `docs/decisions/tissue_stat_sheet_decisions.md` (options, what you chose, why, what would change it).
6. **Add tests** in `tests/`: golden math on tiny synthetic data (known answer), real-data invariants, and a
   join-integrity check (card values trace back to the source). See `tests/test_emma_sources.py` as the template.
7. **Run + verify**: `bash build/run_all.sh` then `bash tests/run_tests.sh` (all green). Spot-check one formulation
   by hand against her raw file. Results must come from the data, not a bug.
8. **Ship**: work on a branch, keep the suite green, then merge to `main` and push. (SSH push authenticates as
   Spencer-Long; there is NO `gh` CLI — make any repo/PR via the web UI.)

Explain your plan for Part B to Spencer and get his nod before building (he likes understanding each piece).

## 6. Where things live + how to run
- **Project dir:** `/usr2/people/protect/Arkin_Lab/sjlong/current_tasks_7_2026/formulation_unified_data_sheet_7_14_2026/`
  (`/usr2/people/protect` == `/auto/sahara/namib/home/protect`, autofs). It is a SIBLING of `7_2026_monthly_report/`.
- **Three config layers (all team-owned):** `config/data_sources.yaml` (what's plugged in) -> `config/thresholds.yaml`
  (how values compute) -> `config/formulation_criteria.yaml` (how columns gate + rank). Loaders: `build/data_sources.py`, `build/config.py`.
- **Build/run:** `bash build/run_all.sh` (roster -> silver -> gold card -> shortlist). **Test:** `bash tests/run_tests.sh`.
- **Shared helpers:** `build/lib_ids.py` (the canonical `ASMA-<int>` normalizer + IO; use it for every id).
- **Git remote:** `git@github.com:WeArePROTECT/protect-formulation-unified-sheet.git`.

## 7. Conventions (follow exactly)
- **No pandas** (NumPy ABI noise on this host): stdlib + `openpyxl` (read xlsx) + `pyarrow` (parquet). The
  `_ARRAY_API` stderr warnings on parquet write are cosmetic.
- **Every id** through `lib_ids.normalize_asma_id` (handles `ASMA_ID`/`ASMA-3913 `/`ASMA1298`/suffixes; drops reporter/blank tokens).
- **Config-as-data:** every cutoff/policy in the YAML config, never hard-coded; every data source in `data_sources.yaml`.
- **Every modeling choice = an ADR** in `docs/decisions/`. **Every settings/code change = run the tests.**
- **When a gold-card column changes, update BOTH dictionary files** (the `.md` AND regenerate the `.docx`), and
  keep a blank line before every markdown table. (See the PROJECT_PLAN standing reminders.)
- **This host has NO LibreOffice/`soffice`/`pdftoppm`** — you cannot visually render a docx/pdf. Verify a docx via
  pandoc round-trip and `pandoc -t html file.docx | grep -c '<table'` (table count).

## 8. How Spencer likes to work (honor these)
- **Explain before building** substantial items (what + why, in a what/why/how style) and get his nod.
- **End every turn with a short what / why / where-we-stand / next summary**, accessible (undergrad) level. He
  likes seeing the full process above, but needs the digestible wrap-up.
- **No em dashes** in your messages or docs you write; use commas/colons/parentheses/periods/"and" (hyphens fine).
- **The biology belongs to the biologists.** Ship best-guess defaults, make them trivially changeable
  (config-as-data), tell the scientists they are in control, log every decision. Do NOT decide the thresholds.
- **Treat this as best-professional-data-engineer work:** verify everything, test critical logic, results must
  come from the settings/data, not bugs. **He welcomes pushback** on data-engineering gaps — speak up.
- **Precision matters**, especially anything going to the team or Adam (the PI). Verify against the real data; never make things up.
- He is warm and collaborative; match that.

## 9. Gotchas + things to verify (NOT assumptions)
- Her data format/schema is unknown until you explore — read her README/notes first.
- The **formulation-label -> ASMA-members mapping is the critical dependency** (section 4). Resolve it early.
- Confirm which **PA strain / tissue model / timepoint(s)** she used, so the `tissue` value is comparable and traceable.
- **Tissue damage** is a safety signal: ship it as a column; whether it becomes a hard gate or a ranking signal is
  the team's call (a `formulation_criteria.yaml` switch), not yours to decide.
- Her data may be **preliminary**; label it so, like the rest of the (pre-QC) card.
- Check whether the **BSL-1 list** is in this upload (separate deliverable from tissue).
- Relevance columns are already on the card but not yet in the ranking; do not touch that unless asked.

## 10. Definition of done
- `docs/gwyn_data_map.md` documents her whole database (what/where/how-keyed/usable) — Part A.
- The tissue column(s) are on the gold card, joined correctly from her data (verified against a real formulation),
  registered in `data_sources.yaml`, documented in both dictionary files, ADR'd, tested (green), and pushed to `main`.
- A short report to Spencer: what is in her data, what you integrated, what is still open or needs Gwyn.
