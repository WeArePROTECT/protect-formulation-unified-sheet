# PROTECT — Formulation Unified Data Sheet

A single, strain-level **decision sheet** that pulls every screen we have on the ASMA collection into one
place, so the team can see — per strain — whether it's **safe**, whether it **grows**, and whether it
**beats *Pseudomonas aeruginosa***, and decide which formulations move forward and why.

> **Status: PRELIMINARY DRAFT (2026-07-15).** A living work-in-progress. The numbers will change as
> Sun-Young's data finishes QC and as tissue/mouse/metagenome data lands. **Nothing here is a final decision.**
> Built by the data team (Spencer Long + Alex Styer); every threshold is yours to set (see below).

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
| **Reserved** (blank, fill later) | tissue, mouse, airway ubiquity |
| **Decision** | verdict + reason — *filled once the team sets the thresholds* |

> **Every column explained:** see **`docs/gold_data_dictionary.md`** for what each column means, how it was
> derived, and the values it can take. New researchers should start there.

## The three gates (Adam's "theory of operations")
Every column is a measurable proxy for one of three questions a formulation must pass:
**SAFETY** (doesn't harm the patient) · **VIABILITY** (we can grow/make it) · **COMPETITION** (excludes PA).

---

## 🎛️ You (the biologists) control every threshold
We set best-guess defaults; the biology is yours. Every cutoff and policy lives in one file,
**`config/thresholds.yaml`** — change a value, re-run, and the whole card recomputes. Safety/candidacy lives
in **`data/reference/species_safety.csv`** (an interim list, meant to be replaced by Gwyn's BSL-1 list).
See **`docs/decisions/thresholds_are_team_owned.md`**. Tell us what you want and we adapt it — you don't adapt to it.

## How it's built (bronze → silver → gold)
```
  raw source files (bronze, pointed to in data/bronze/BRONZE_MANIFEST.md — never copied)
        │   cleaned by build/silver_*.py, one tidy table per assay (data/silver/)
        ▼
  the roster: build/identity_spine.py collapses 4,365 isolates -> 780 strains (data/reference/)
        │   build/gold_unified_sheet.py joins everything, isolate -> strain
        ▼
  the card: data/gold/gold_unified_sheet.{xlsx,csv,parquet}
```
Everything keys on the canonical `ASMA_id`. Run the whole thing with **`bash build/run_all.sh`**.

## Where the data comes from
See **`data/bronze/BRONZE_MANIFEST.md`** for every source's exact server path + owner. In short:
hemolysis (Cassandra), phenotype screens — competition / antibiotics / growth (Sun-Young),
genomics — species, strain groups, AMR genes, metabolism (Alex), with tissue (Gwyn) and mouse (Fatemeh) to come.

## Why we built each piece the way we did
Decision records (options considered, what we chose, why, what would change it) are in **`docs/decisions/`** —
competition, viability, the gold card, and the team-owned-thresholds principle.

---

## Current status
**Done:** strain roster (780 strains, 93% with species) · all three gates (Safety + Viability + Competition) ·
team-owned config · interim safety/candidate list · the card + an `_about` explainer.

**Still needed (asks to the team):**
- **Gwyn's BSL-1 list** → finalize the candidate/safety set (interim list in place now).
- **Tissue** (Gwyn) + **mouse** (Fatemeh) data on the server → fill those columns.
- Sun-Young's **QC** on the phenotype data → flip the card from preliminary to final.
- The team's **thresholds** → we ship strawman defaults; you set the real bars.

## Give us feedback
This is built to change. Tell us — anything from "call it resistant at 30%, not 50%" to "add a column for X" to
"this strain shouldn't be a candidate." Contact: **Spencer Long**.

## Repo map
- `README.md` — this file · `PROJECT_PLAN.md` — fuller plan + history
- `build/` — the pipeline (`run_all.sh` runs it) · `config/thresholds.yaml` — team-owned settings
- `data/` — `bronze/BRONZE_MANIFEST.md` (source pointers, tracked) + `reference/species_safety.csv` (tracked); the roster / `silver/` / `gold/` tables are **generated, not in the repo** (run `run_all.sh`)
- `docs/` — `gold_data_dictionary.md` (every column explained), `plain_english_guide.md`, `data_readiness_scorecard.md`, `syk_phenotype_sheet_map.md`, `decisions/`

*Generated data in `data/` is reproducible from the code via `bash build/run_all.sh`.*
