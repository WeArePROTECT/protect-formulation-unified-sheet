# Decision Record - BSL / Biosafety Level (`bsl_level` column)

**Purpose:** why and how the `bsl_level` column is populated from a curated risk-group reference
(`data/reference/species_bsl.csv`). Companion to `gold_unified_sheet_decisions.md`. Human- and agent-readable.

**Status:** active · **Created:** 2026-07-28 · **Code:** `build/gold_unified_sheet.py` (`load_bsl_ref` / `bsl_for`)
**Data state:** **INTERIM.** Sourced from authoritative published risk-group registries and cited per row, but
NOT yet signed off by a biosafety officer, and to be superseded by Gwyneth's official BSL-1 list when it lands.
Requested by Sun-Young Kim (2026-07-27, "official BSL of a given ASMA species").

---

## Background: what BSL / Risk Group means

**Biosafety Level (BSL-1..4)** is the lab containment required to safely handle an organism; it follows the
organism's **Risk Group (RG1..4)**:

- **RG1 / BSL-1** - not known to cause disease in healthy adults (most commensals).
- **RG2 / BSL-2** - can cause treatable human disease; opportunist or pathogen (e.g. *S. aureus*, *K. pneumoniae*).
- **RG3 / BSL-3** - serious/lethal disease, often airborne (e.g. *Bacillus anthracis*, *M. tuberculosis*).
- **RG4 / BSL-4** - no relevant members here.

"Official BSL of a species" = its published risk-group classification.

## Decisions

### D1 - The column is informational, NOT a gate
`bsl_level` reports a species property. It does **not** enter any gate or ranking, and it does **not** set
`is_candidate` (candidacy still comes from `data/reference/species_safety.csv`). Rationale: BSL is a
handling/containment fact for planning and safety awareness, separate from the project's candidacy decision.
The two cross-check each other (a species that is BSL-2 here and a known pathogen there both raise a flag).

### D2 - Authoritative sources, cited per row (no invention)
Every classification comes from a published risk-group registry, named in the `source` column of
`species_bsl.csv`. Sources used: **EU Directive 2000/54/EC Annex III** (and its update 2019/1833),
**ABSA International Risk Group Database**, **German TRBA 466**, **Canadian PHAC ePATHogen**. We extract and
cite; we do not assign a risk group from our own judgement.

### D3 - The regulatory default: not listed as RG2+ implies RG1
A species that is **not listed** as RG2 or higher in the authoritative registries is RG1 (BSL-1) by the
framework's own definition, not by our guess. So the real work is identifying the RG2+ species correctly (with
a citation); everything else defaults to RG1 with the source noted as "not listed as RG2+ -> RG1".

### D4 - Conservative handling of the unknown: "review", never a guessed-down number
- **GTDB genomospecies** (unnamed `sp<digits>` placeholders) have no formal risk-group entry. They inherit
  their **genus** RG only when the genus is uniform; if the genus spans RG1 and RG2, the species is left
  **`review`** (blank BSL), not guessed.
- **Contested species** (notably viridans-group streptococci and coagulase-negative staphylococci, which are
  RG1 in ABSA but RG2 in TRBA/EU because of opportunistic infections) take the **more conservative (higher)**
  RG, with the disagreement recorded in the row `note`.
- Anything genuinely unresolvable is `review`. A wrong BSL-1 on an RG2 organism is a safety error; a blank is not.

### D5 - Two-level reference; species wins, genus fills in
`species_bsl.csv` holds **species rows** (name has a space) and **genus rows** (single word). The lookup takes
the species row if present, else the genus row, else blank. This lets the ~40% of the roster that is unnamed
genomospecies inherit a genus-level call where that is safe (uniform-RG1 genera), and stay blank/`review`
otherwise. GTDB suffixes (`_B`, `_E`) are stripped before matching (shared `norm_species`).

### D6 - INTERIM, and superseded by the official list
This is a best-effort, authoritative-sourced interim so the team has a working answer now. It is explicitly
**pending biosafety sign-off** and will be replaced by Gwyneth's official BSL-1 list (the same list that will
make `is_candidate` authoritative). Until then, treat BSL-1 calls as "not a listed pathogen," not as a
containment clearance.

### D7 - Surfacing pathogens hiding in the candidate list
Sourcing BSL doubles as a safety screen: any species carrying RG2+ that is currently `is_candidate = True`
(i.e. absent from `species_safety.csv`) is flagged in the handoff for the team to decide on candidacy. This
does not itself change candidacy (that is a team call and would move the shortlist counts); it is surfaced,
not silently applied.

## How to extend / correct

Edit `data/reference/species_bsl.csv` (add/fix a species or genus row, keep the `source` citation), then
`bash build/run_all.sh && bash tests/run_tests.sh`. When Gwyneth's official BSL list arrives, replace the file
(or repoint it) and drop the "INTERIM" labels.

## Change log

- **2026-07-28 (created)** - built `species_bsl.csv` (133 rows: 43 genus + 90 species), sourced from
  TRBA 466 (read directly) cross-referenced with PHAC / Swiss / EU 2000/54/EC, cited per row and the RG2+
  calls spot-verified against the TRBA source text. Wired `bsl_level` to it in `gold_unified_sheet.py`
  (species match -> genus fallback -> safety-list fallback); added `tests/test_bsl.py` (5 tests, green).
  **Coverage on the 780-strain card:** BSL-1 = 141, BSL-2 = 444, BSL-3 = 1, review/blank = 194.
  - **Conservative-classification note.** Under TRBA (the backbone), most oral commensals in this collection
    come out **RG2/BSL-2** (viridans streptococci, `Rothia dentocariosa`, `Actinomyces`, `Gemella`,
    `Granulicatella`, commensal `Neisseria`, coagulase-negative staph) because they are opportunistic
    (endocarditis, bacteremia). ABSA / US practice treats several of these as RG1. That is why ~55% of
    candidates are BSL-2; the per-row `note` records each disagreement. The biosafety reviewer may prefer the
    ABSA reading for borderline oral commensals.
  - **RG2+ organisms currently in the CANDIDATE list (surfaced for a team candidacy call, not changed here):**
    `Bacillus anthracis` (strain_group 381, RG3/BSL-3, almost certainly a GTDB miscall or contaminant in a
    commensal set, verify), plus RG2 `Bordetella pertussis`, `Streptococcus agalactiae`, `Moraxella catarrhalis`,
    `Enterococcus faecalis`, `Klebsiella grimontii`, `Enterobacter hormaechei`, `Serratia liquefaciens`,
    `Acinetobacter ursingii/bereziniae`. `Bacillus paranthracis` is RG2 but genomically near anthracis, verify
    strain + toxin genes.
