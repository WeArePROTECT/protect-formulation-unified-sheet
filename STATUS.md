# PROTECT Formulation Unified Sheet — Status (2026-07-20)

*A shareable snapshot for the team: what the sheet is, what data is in it now, and what we are still waiting on.
Owner: Spencer Long (data integration, with Alex Styer). Questions or change requests: Spencer.*

> **Status: PRELIMINARY DRAFT.** The numbers move as Sun-Young's phenotype data finishes QC and as tissue,
> mouse, and the BSL list arrive. **Nothing here is a final decision.** The biologists set every threshold.

---

## What this is (30 seconds)
One **strain-level decision card**: one row per strain (**780 strains**), pulling every screen we have into one
place so the team can see, per strain, whether it is **SAFE**, whether it **GROWS**, and whether it **beats
*Pseudomonas aeruginosa* (PA)**, and decide which formulations move forward and why. Adam's three gates
(**Safety / Viability / Competition**), now with a fourth **Relevance** block (is the strain actually a common,
PA-displacing resident of real patient airways?).

- **780 strains** total: **739 candidates** (not a known pathogen) + **41** flagged pathogen/opportunistic.
- Built by a reproducible bronze -> silver -> gold pipeline. Lives on GitHub (code only, no ASMA data); the card
  itself is on the team Google Drive.
- Everything is a **team-owned switch**: thresholds, the pass/fail-and-rank logic, and which data sources are
  plugged in are all config files you can change, with 62 automated tests that confirm a change did what you
  intended and not something a bug caused.

## What we've built (the machinery, done)
- The strain roster and the bronze -> silver -> gold pipeline (`bash build/run_all.sh` rebuilds everything).
- A **config-driven shortlist / ranking engine** (Adam's "pass/fail formulae that allow ranking"): must-pass
  gates thin the field, then rank the survivors, all dialed from `config/formulation_criteria.yaml`.
- A **data-source registry** (`config/data_sources.yaml`): every source has an on/off switch, a pinned path +
  version (machine-readable provenance), so swapping in a newer data version is a one-line change.
- A **test suite** (62 tests) covering the engine logic, the data joins, and provenance.

---

## Data SOURCED INTO the sheet (done)
Coverage = how many of the 739 candidate strains have that measurement so far. Blank cells mean "not screened
yet," not "no result." Every column's meaning + source + values is in `docs/gold_data_dictionary.md`.

| Gate | Card columns | What it tells you | Source (owner) | Candidate coverage |
|---|---|---|---|---|
| **Identity** | `strain_group`, `species`, `n_isolates`, `is_candidate` | which strain, what it is, candidate vs known pathogen | ASMA stock list (SYK) + GTDB taxonomy + mash strain clusters (Alex) | 692/739 have species |
| **Safety** | `hemolysis_beta` | breaks down red blood cells (main "could harm the patient" flag) | blood-agar screen (Cassandra, via Jake) | 624/739 |
| **Safety** | `amr_resistance_count_prov` | measured resistance across 6 antibiotics | antibiotic screen (Sun-Young) | 663/739 |
| **Safety** | `amr_gene_count` | resistance genes in the genome | AMRFinderPlus (Alex) | 739/739 |
| **Viability** | `grows_scfm`, `scfm_od`, `mucin_lift` | grows in lung-mimic fluid (SCFM), and mucin (prebiotic) lift | SCFM growth endpoint (Sun-Young) | 584/739 |
| **Competition** | `comp_best_solo_pa`, `comp_best_team_pa`, `comp_synergy_pa`, `comp_best_partner` | knock-down of PA alone / on a team, and whether teaming helps | competition screen (Sun-Young) | 193/739 any PA result; 29 tested in multi-member teams |
| **Relevance** | `abundance_metag`, `prevalence_metag`, `abundance_metars`, `prevalence_metars` | how common/abundant it is in real patient airways, by DNA (present) and RNA (active) | metagenomics, `final_dataset_clean` (Emma, Zengler lab) | 673/739 |
| **Relevance** | `pa_cooccurrence` (+ `_p`) | does it co-occur with, or displace, PA in real lungs | SparCC network on PA-positive samples (Emma) | 673/739 |
| **Relevance** | `pa_metabolic_competitor` | model-**predicted** strength as a metabolic competitor of PA | MIND metabolic model (Emma) | 558/739 |

**Early signal (directional):** the candidates that are abundant airway residents, anti-correlate with PA in
real lungs, *and* beat PA in the dish are **Gemella, Streptococcus, and Neisseria** species. Several are also
strong in-vitro PA knock-downs (90%+). That agreement across independent signals is encouraging, but it is
preliminary.

## Data we are STILL WAITING ON (to source in)
| Data | Owner | Status | What it fills / unblocks |
|---|---|---|---|
| **Tissue model** (PA reduction on airway tissue) | Gwyn | off-server (local, in analysis) | the reserved `tissue` column |
| **Mouse model** | Fatemeh | off-server (local) | the reserved `mouse` column |
| **BSL-1 safety list** | Gwyn | not yet delivered | replaces our interim candidate/safety list -> makes `is_candidate` / `bsl_level` authoritative |
| **Growth-curve viability** (growth rate / lag) | Sun-Young (on server) | buildable, not built yet | adds rate/lag detail to the Viability gate (beyond grow / no-grow) |
| **QC pass on the phenotype data** | Sun-Young | in progress | flips the whole card from **PRELIMINARY** to final |
| **Metabolic / GapMind columns** (capabilities, suggested partners) | Alex | Alex's lane | in-silico metabolic columns, coordinated separately |

---

## Important caveats for the team
- **PRELIMINARY.** Sun-Young's wet-lab data is still pre-QC, so treat all numbers as directional.
- **`is_candidate = True` means "not a known pathogen," NOT "safety cleared."** It is a seed list to be
  replaced by Gwyn's BSL-1 list.
- **The Relevance columns are on the card but NOT yet in the ranking.** Whether (and how) to rank on airway
  abundance, PA co-occurrence, or the predicted competitor is the team's call, and it is a one-line change.
- **You control every threshold.** Tell us the bar (for example "call it resistant at 30%, not 50%," or "require
  growth in SCFM," or "rank on co-occurrence too") and we re-run. You do not adapt to the sheet; it adapts to you.

## How to view / give feedback
- **The card:** `gold_unified_sheet.xlsx` on the team Google Drive (open the `_about` tab first). No code needed.
- **The reasoning + provenance:** the GitHub repo `WeArePROTECT/protect-formulation-unified-sheet`
  (`docs/gold_data_dictionary.md` explains every column; `docs/decisions/` explains every modeling choice).
- **Feedback:** anything from "this strain should not be a candidate" to "add a column for X" to a different
  threshold. Contact Spencer.
