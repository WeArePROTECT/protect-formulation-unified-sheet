# Gold Unified Sheet, Data Dictionary

Plain-language reference for every column in the decision card (`data/gold/gold_unified_sheet.xlsx` / `.csv`).
One row = one strain. Read this to orient yourself before digging into the numbers.

**A few things to keep in mind everywhere:**

- **PRELIMINARY.** Sun-Young's wet-lab data is still pre-QC, so treat values as directional.
- **Blank cell = "not screened yet," not "no result."** Species and genomic AMR cover nearly all strains;
  hemolysis, measured AMR, viability, and competition cover only the subset screened so far.
- Every threshold below is a **team-owned setting** in `config/thresholds.yaml`. Tell us and we recompute.

---

## Identity (who the strain is)
| Column | What it means | How it is derived | Values |
|---|---|---|---|
| `strain_group` | Internal ID for the strain (a cluster of near-identical isolates) | Alex's whole-genome clustering (mash, >99% identity groups) | integer key |
| `representative_asma_id` | The isolate that stands in for the strain (the one to pull / that assays used) | The group's representative from the clustering | e.g. `ASMA-3643` |
| `genus`, `species` | What kind of bacterium it is | Alex's GTDB-Tk classification of the representative genome. GTDB adds suffixes like `_B` as part of its naming | e.g. `Neisseria`, `Neisseria mucosa` (blank if unclassified) |
| `n_isolates` | How many isolates in the collection belong to this strain | Size of the genome cluster | integer (higher = more copies of this strain in the collection) |
| `is_candidate` | Is this a plausible probiotic candidate | `FALSE` if the species/genus is a known pathogen or opportunist (`species_safety.csv`), else `TRUE` | TRUE / FALSE. **TRUE means "not a known pathogen," NOT "safety cleared."** |
| `candidate_review` | Safety review status | From `species_safety.csv` | `pathogen` / `opportunistic` (excluded), `review` (genus on a watchlist, please vet), `unreviewed` (no safety flag yet) |
| `bsl_level` | Biosafety level, where known | From `species_safety.csv` | `2` for flagged pathogens; blank until assigned. **To be filled from Gwyn's BSL-1 list.** |

## Safety (does it harm the patient)
| Column | What it means | How it is derived | Values |
|---|---|---|---|
| `hemolysis_beta` | Does it break down red blood cells (beta-hemolysis) | Cassie's blood-agar screen; worst-case across the strain's isolates (Y if any isolate or timepoint was positive) | `Y` / `N` / blank (not determined). Beta-hemolysis is the main "could harm the patient" flag |
| `hemolysis_concern` | Simple safety flag | `TRUE` when `hemolysis_beta` is Y | TRUE / FALSE |
| `amr_resistance_count_prov` | How many of 6 antibiotics it resists (measured) | Sun-Young's `Antibiotic_resistance_v2`; a drug counts as resisted if growth-under-drug is at least the cutoff (default 50%). Worst-case across isolates | 0 to 6. `_prov` = provisional cutoff, team sets it |
| `amr_gene_count` | Number of resistance genes in its genome | Alex's AMRFinder (AMR-type elements); worst-case across isolates | integer. A genomic complement to the measured AMR |

## Viability (can we grow and make it)
| Column | What it means | How it is derived | Values |
|---|---|---|---|
| `grows_scfm` | Does it grow in SCFM (lung-mimic fluid) | Sun-Young's `Growth_endpoint`, background-subtracted; Y if corrected SCFM OD is at least the cutoff (default 0.1) and above the no-carbon control; blank if it did not grow even in rich media (cannot tell). Best-case across isolates | `Y` / `N` / blank (inconclusive) |
| `scfm_od` | How well it grows in SCFM | Background-subtracted OD600 at 72h | number, roughly 0 to 1.2 (higher = grows better) |
| `mucin_lift` | Growth boost from adding mucin (a prebiotic signal) | SCFM-plus-mucin OD minus SCFM OD | number; positive = mucin helps this strain grow |

## Competition (does it beat PA)
Values are percent knock-down of *P. aeruginosa* (0 = PA grew freely, 100 = fully blocked; can be negative if the strain slightly helped PA). Headline pathogen is PA14_KEH108. Repeat wells collapsed by median, best result taken across the strain's isolates.
| Column | What it means | How it is derived | Values |
|---|---|---|---|
| `comp_best_solo_pa` | Best knock-down of PA by this strain ALONE | This strain as a 1-member formulation vs PA | percent (can be negative) |
| `comp_best_team_pa` | Best knock-down of PA when this strain is ON A TEAM | Best multi-member formulation that contains this strain | percent |
| `comp_best_partner` | The partner(s) in that best team | The other members of the winning formulation | e.g. `ASMA-3643` or `ASMA-230+ASMA-2795` |
| `comp_synergy_pa` | Does teaming help | `comp_best_team_pa` minus `comp_best_solo_pa` (signed) | positive = partners boost it; 0 or negative = as good or better alone |
| `comp_n_formulations` | How many PA-tested formulations included this strain | Count of distinct formulations containing it | integer (higher = more thoroughly screened in combos) |

## Reserved (columns waiting on data)
| Column | What it will hold | Status |
|---|---|---|
| `tissue` | Tissue-model result (PA reduction on airway tissue) | Gwyn, not on the server yet |
| `mouse` | Mouse-model result | Fatemeh, not on the server yet |
| `airway_ubiquity` | How common the strain is in airway metagenomes / patients | To be derived from Zengler metagenomics + the patient linkage |

## Decision (the verdict, once the team sets the bars)
| Column | What it means | Status |
|---|---|---|
| `decision` | Move forward / hold / drop | Blank until the team sets thresholds |
| `decision_reason` | Why | Blank for now |

---

*The reasoning behind each modeling choice (why median, why worst-case safety, why the interim candidate list,
etc.) is in `docs/decisions/`. Where the raw data lives is in `data/bronze/BRONZE_MANIFEST.md`.*
