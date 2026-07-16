# Decision Record — Thresholds Are Team-Owned (config-as-data)

**Purpose:** the governing principle for how every cutoff/policy in this build is set and changed.
Human- and agent-readable ADR. **Status:** active · **Created:** 2026-07-15.

---

## The principle
We (the data-science team) are NOT the ones who should decide the biology. Our job is to build a substrate
that computes cleanly and a **first-pass** ranking. Every threshold ("resistant at ≥50%", "grows at ≥0.1 OD",
"top formulations clear ≥50% PA") and every policy choice ("use the median", "worst-case safety") is a
**best-guess default that the biologists own and can change**.

## The decision
- **All thresholds live in ONE file: `config/thresholds.yaml`.** Nothing is hard-coded in the scripts;
  every script reads its cutoffs from there via `build/config.py`.
- **Changing a value is a one-line edit + one command** (`bash build/run_all.sh`) and the entire card
  recomputes. No code changes, no rebuild of logic.
- **The card says so out loud:** the xlsx has an `_about` sheet that lists the current settings and states
  that the team controls them. The bronze manifest and PROJECT_PLAN repeat it.
- **Safety/candidacy classification** lives in a second team-owned file, `data/reference/species_safety.csv`
  (interim, to be replaced by Gwyn's BSL-1 list) — same principle, editable by biologists.

## Why (options considered)
- **Hard-code the numbers in each script** — rejected: scattered, invisible to scientists, scary to change,
  drifts out of sync.
- **A config file (chosen)** — one visible source of truth, plain-readable by non-programmers, trivially
  changeable, and it makes the "you are in control" message literally true instead of a promise.
- **A full settings UI** — overkill for now; a commented YAML file is enough and lower-maintenance.

## What this means in practice
When a scientist says "actually, call it resistant at 30%, not 50%" or "growth should be relative to the
positive control", the answer is: change one line, re-run, done — and we log the change. We never argue the
biology; we make it easy to encode whatever the biology team decides.

## Change log
- 2026-07-15 — established alongside `config/thresholds.yaml` + `species_safety.csv`; existing AMR and
  competition sheets refactored to read from config; viability + gold built config-first.
