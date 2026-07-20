# PROTECT — Formulation Unified Data Sheet

A single, strain-level **decision sheet** that pulls every screen we have on the ASMA collection into one
place, so the team can see — per strain — whether it's **safe**, whether it **grows**, and whether it
**beats *Pseudomonas aeruginosa***, and decide which formulations move forward and why.

> **Status: PRELIMINARY DRAFT (updated 2026-07-20).** A living work-in-progress. The numbers will change as
> Sun-Young's data finishes QC and as tissue/mouse data lands. **Nothing here is a final decision.**
> Built by the data team (Spencer Long + Alex Styer); every threshold is yours to set (see below).
> **For a team-facing snapshot of what is in the sheet and what we are waiting on, see [`STATUS.md`](STATUS.md).**

---

## 👉 If you open one thing, open the card
**The card** = one row per strain (~780), sorted best-competitor-first, with an `_about` tab that explains the
settings. It is shared on the team **Google Drive** (link in the announcement) so you can view it with no code
or server access. To build it yourself from source: `bash build/run_all.sh` -> `data/gold/gold_unified_sheet.xlsx`.

> **Note:** the generated data tables (`data/reference|silver|gold/`) are **not stored in this repo** — they
> rebuild from the code in seconds. This keeps the ASMA data off GitHub; the repo holds the pipeline, the
> reasoning, and *where* the data lives (`data/bronze/BRONZE_MANIFEST.md`).

## What the card tells you (per strain)
| Group | Columns |
|---|---|
| **Identity** | strain, species, # isolates, `is_candidate`, `candidate_review`, `bsl_level` |
| **Safety** | beta-hemolysis, measured antibiotic resistance, genomic AMR genes |
| **Viability** | grows in SCFM?, SCFM growth (OD), mucin lift (prebiotic signal) |
| **Competition** | best PA knock-down alone / on a team, best partner, does-teaming-help (synergy) |
| **Relevance** | airway abundance + prevalence (metaG/DNA + metaRS/RNA), PA co-occurrence, predicted PA metabolic competitor |
| **Reserved** (blank, fill later) | tissue, mouse |
| **Decision** | verdict + reason — *filled once the team sets the thresholds* |

> **Every column explained:** see **`docs/gold_data_dictionary.md`** for what each column means, how it was
> derived, and the values it can take. New researchers should start there.

## The three gates (Adam's "theory of operations") + a relevance layer
Every gate column is a measurable proxy for one of three questions a formulation must pass:
**SAFETY** (doesn't harm the patient) · **VIABILITY** (we can grow/make it) · **COMPETITION** (excludes PA).
On top of the gates, a **RELEVANCE** block asks: is the strain actually a common, PA-displacing resident of real
patient airways (Emma's metagenomics)?

A config-driven **ranking engine** (`build/heuristic_shortlist.py`) turns the card into a shortlist: must-pass
gates thin the field, then survivors are ranked. Which columns gate, which rank, and every cutoff are switches
in `config/formulation_criteria.yaml` — see the config section below.

---

## 🎛️ You (the biologists) control everything (three config layers)
We set best-guess defaults; the biology is yours. Everything is a team-owned switch, across three config files
that answer three questions (PLUGGED IN → COMPUTED → USED):
- **`config/data_sources.yaml`** — *what data is plugged in.* One on/off switch + pinned path + version per
  source (also our machine-readable provenance). Swapping in a newer data version is a one-line change.
- **`config/thresholds.yaml`** — *how each column's value is computed* (cutoffs, replicate aggregation).
- **`config/formulation_criteria.yaml`** — *how columns combine into a ranked decision* (which gate, which rank).

Safety/candidacy lives in **`data/reference/species_safety.csv`** (interim, to be replaced by Gwyn's BSL-1 list).
Change a value, re-run `bash build/run_all.sh`, then `bash tests/run_tests.sh` (it confirms the change did what
you intended and not a bug). See **`docs/decisions/thresholds_are_team_owned.md`**. You don't adapt to the sheet; it adapts to you.

## How it's built (bronze → silver → gold)
```
  raw source files (bronze, pointed to in data/bronze/BRONZE_MANIFEST.md — never copied)
        │   cleaned by build/silver_*.py, one tidy table per assay (data/silver/)
        ▼
  the roster: build/identity_spine.py collapses 4,365 isolates -> 780 strains (data/reference/)
        │   build/gold_unified_sheet.py joins everything, isolate -> strain
        ▼
  the card: data/gold/gold_unified_sheet.{xlsx,csv,parquet}
        │   build/heuristic_shortlist.py applies gates + ranking (config/formulation_criteria.yaml)
        ▼
  the shortlist: data/gold/formulation_shortlist.{xlsx,csv,parquet}
```
Everything keys on the canonical `ASMA_id`, and every builder reads its input path from `config/data_sources.yaml`.
Run the whole thing with **`bash build/run_all.sh`** (then **`bash tests/run_tests.sh`** to verify).

## Where the data comes from
The machine-readable registry is **`config/data_sources.yaml`** (every source's path, version, on/off switch,
and the columns it provides); **`data/bronze/BRONZE_MANIFEST.md`** is the human-readable companion. In short:
hemolysis (Cassandra), phenotype screens — competition / antibiotics / growth (Sun-Young), genomics — species,
strain groups, AMR genes (Alex), airway metagenomics — abundance / PA co-occurrence / MIND (Emma, Zengler lab),
with tissue (Gwyn) and mouse (Fatemeh) to come.

## Why we built each piece the way we did
Decision records (options considered, what we chose, why, what would change it) are in **`docs/decisions/`** —
competition, viability, the gold card, and the team-owned-thresholds principle.

---

## Current status
**Done:** strain roster (780 strains, 739 candidates) · all three gates (Safety + Viability + Competition) · the
Relevance block (airway abundance metaG+metaRS, PA co-occurrence, MIND competitor) · a config-driven ranking
engine · a data-source registry (on/off + versioning + provenance) · three-layer team-owned config · the card +
shortlist + an `_about`/`_switchboard` explainer · a 62-test suite. Full snapshot: [`STATUS.md`](STATUS.md).

**Still needed (asks to the team):**
- **Gwyn's BSL-1 list** → finalize the candidate/safety set (interim list in place now).
- **Tissue** (Gwyn) + **mouse** (Fatemeh) data on the server → fill those columns.
- Sun-Young's **QC** on the phenotype data → flip the card from preliminary to final.
- The team's **thresholds + ranking** → we ship strawman defaults; you set the real bars (and whether relevance ranks).

## Give us feedback
This is built to change. Tell us — anything from "call it resistant at 30%, not 50%" to "add a column for X" to
"this strain shouldn't be a candidate." Contact: **Spencer Long**.

## Repo map
- `README.md` — this file · `STATUS.md` — team-facing status snapshot · `PROJECT_PLAN.md` — fuller plan + history
- `build/` — the pipeline (`run_all.sh` runs it) · `tests/` — the test suite (`bash tests/run_tests.sh`)
- `config/` — `data_sources.yaml` (what's plugged in), `thresholds.yaml` (how values compute), `formulation_criteria.yaml` (how columns rank) — all team-owned
- `data/` — `bronze/BRONZE_MANIFEST.md` (source pointers, tracked) + `reference/species_safety.csv` (tracked); the roster / `silver/` / `gold/` tables are **generated, not in the repo** (run `run_all.sh`)
- `docs/` — `gold_data_dictionary.md` (every column explained), `plain_english_guide.md`, `decisions/` (ADRs), `data_readiness_scorecard.md`, `syk_phenotype_sheet_map.md`

*Generated data in `data/` is reproducible from the code via `bash build/run_all.sh`.*
