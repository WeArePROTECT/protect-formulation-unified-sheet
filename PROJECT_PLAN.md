# Formulation Unified Data Sheet — Project Plan

**Owner:** Spencer Long · **Started:** 2026-07-14 · **Source dir:** this folder
**Trigger:** 2026-07-13 formulation meeting (Adam/PI) + follow-up Slack thread (Jake, Alex, SYK, Gwyn, Cassandra)

> ### 📌 Standing reminders (for anyone — human or agent — working this project)
> - **Keep `data/bronze/BRONZE_MANIFEST.md` current.** Whenever a build step reads a new raw source (or a
>   source moves / a new dataset lands), add/update its exact server path + owner + "feeds" entry there. It's
>   our provenance record — the manifest points at data in place; we never copy big data into the project.
> - **Naming:** code files are `<layer>_<content>.py` (no numeric prefixes); run-order lives in `build/README.md`
>   + `build/run_all.sh`. Version code via **git**, not `_v2.py` copies; data outputs may be dated/versioned.
> - **Thresholds are team-owned (config-as-data):** every cutoff/policy lives in `config/thresholds.yaml`
>   (one edit + `bash build/run_all.sh` recomputes the whole card); safety/candidacy in
>   `data/reference/species_safety.csv` (interim, to be replaced by Gwyn's BSL-1 list). We make our best-guess
>   defaults and make it trivial for the biologists to change them. See `docs/decisions/thresholds_are_team_owned.md`.
> - **Test after any settings change:** run `bash tests/run_tests.sh` whenever you edit
>   `config/thresholds.yaml`, `config/formulation_criteria.yaml`, or anything under `build/`. This is a
>   science-critical pipeline: the tests prove a changed result comes from the *settings*, not a bug. The
>   unit / golden / invariant layers must stay green; the default snapshot is meant to fail on an intentional
>   default-config change (update its baseline then). See `tests/README.md`.
> - **Backlog:** do a broad server sweep for *other* formulation data we may be missing (Spencer's note
>   2026-07-15 — "we may have a lot more on the server than we think"). Future task, not blocking.

---

## 1. What the team decided (and where Spencer fits)

Adam's charge: stop "throwing shit at the wall." Build **one integrated theory of operations** for
choosing which formulations move forward, grounded in **what we can actually measure and what we already
have in hand** — not what we wish we had. Concretely he wants a spreadsheet where **each row is a strain**,
columns are the measurable proxies for the three gates (SAFETY / VIABILITY / COMPETITION), and a
**decision matrix** on top says what advances and why.

The division of labor Adam and Alex set explicitly:

> **"Alex and Spencer have to force the experimentalists to get them the data so they can organize it into
> a unified spreadsheet, and then the experimentalists build a decision matrix on those measurements."**
> — Adam
>
> **"Spencer and I can handle the reconciling of names and formats… I think this is something Spencer has
> already put work in on."** — Alex (Slack)

**So Spencer + Alex ARE the integration layer.** Not the wet-lab, not the threshold-setting — the data
engineering that makes a unified, join-able, trustworthy substrate exist, plus a **first-pass heuristic
ranking** the experimentalists then refine. Spencer's specific lanes:

1. **The canonical ID + vocabulary standard** (Alex's #1 ask: `ASMA_id` everywhere, never mixed).
2. **The grain definition** — isolate vs. strain vs. species (the denominator for "how many screened").
3. **Ingesting + joining the on-server datasets** into the unified strain-level "gold" table.
4. **Computing the derived columns** (growth rate from raw OD, suppressive synergy, ubiquity, BSL).
5. **The first-pass decision heuristic** + the decision register.
6. **Chasing the off-server data** onto the server (tissue, mouse, SYK's newest, Gwyn's BSL list).

Alex's lanes (coordinate, don't duplicate — he already has a `DECISION-MATRIX.md` going): the in-silico /
metabolic columns (GapMind capabilities, suggested partners, mucin catabolism) and the phylogeny/clade work.

**Leverage:** Spencer's `protect-data-manifest` already discovers & documents 8 of these datasets, and
Jake's original manifest use-case was *literally* "filter the ASMA collection for hemolysis + AMR + growth
phenotypes." The unified sheet is the **materialized gold view** the manifest's discovery layer was built
to feed. Use the manifest as the locator of record; register the finished sheet back into it as a curated product.

See **`docs/data_readiness_scorecard.md`** for the column-by-column status (answers Jake's two questions).

---

## 2. The deadlines (why this is urgent)

| Date | Milestone | Implication |
|---|---|---|
| **~Thu Jul 16** | Adam checks in on Slack | **Mini-deadline: a first-pass unified sheet + heuristic shortlist to show.** Adam: *"if you took a couple days just to work on that spreadsheet…"* |
| **End of Sept** | Formulation strains locked | The real down-select must be done by then. |
| **Oct 1** | Final formulations → ARPA-H | — |
| **Nov 1** | Reasoning + substrate preferences → ARPA-H | The decision register **is** this deliverable. |
| **Apr 1 2027** | 25% of formulations evaluated (ABPDU scale-up) | ABPDU contract can start ~January if only 25% needed. |

A no-cost extension (Scott/Adam) may shift these slightly — **do not rely on it.** Earlier good results =
stronger Phase-2 argument.

**Deliverable thresholds are already known** (from the SOW / ARPA-H agreement language, per prior work):
in-vitro deliverable = *"10 formulations that inhibit ALL VAP pathogens ≥25% OR PA ≥50% in vitro"*;
Go/No-Go floor = *≥30% PA reduction over 24 h*; tissue completion = *10 formulations tested + scored in
the tissue system*. We're well past the floor (lead ~98%; 882 communities ≥50%). *(Re-verify wording
against `sjlong/protect_docs/PRESIST_SOW_revised_v003.pdf` before it goes in front of ARPA-H.)*

---

## 3. Architecture of the unified sheet

Three layers, all keyed on the canonical `ASMA_id`:

```
  SOURCE / SILVER (one standardized table per assay, + experimental-condition metadata)
    hemolysis · AMR(measured) · AMR(genomic) · SCFM growth · carbon · competition · tissue · mouse …
        │  (each row carries: assay_date, plate_format 96/384, temp, media, duration, priming, plate_reader)
        ▼
  FORMULATION LAYER (multi-member assays live here — competition, tissue)
    formulations table: 1 row per SynCom composition (order-insensitive frozenset key)
    membership table:   formulation_id ⇄ ASMA_id
        │  summarize up to strain level (best inhibition as a member, best partner, synergy sign)
        ▼
  GOLD / DECISION MATRIX  (1 row per STRAIN = Adam's spreadsheet)
    ASMA_id · species · [safety cols] · [viability cols] · [competition cols] · [relevance] · decision_register
```

**Key design decisions:**

- **Grain = strain** (one row per unique strain / representative isolate). Isolate and species are
  attributes. This matches Adam's "all our strains lined out."
- **Multi-member assays don't fit strain-grain** → they get their own `formulations` + `membership`
  tables, then roll up to strain-level columns (e.g. `best_inhibition_as_member`, `best_partner`,
  `suppressive_synergy = community_inhib − best_member_inhib`, keeping the **sign** since communities
  often lose to their best member).
- **Every source table carries experimental-condition metadata** (Alex's explicit requirement) so joins
  never silently compare a 96-well/24 h/cool run against a 384-well/8 h run.
- **Derived ≠ requested.** Growth rate/lag/yield (from raw `cyc_*` OD), synergy, ubiquity, riboseq
  rel-abundance, species→BSL are **computed by us** — don't wait on anyone for these.

---

## 4. The ID / vocabulary standard (Spencer's first concrete artifact)

The IDs are a mess across sources — this is the single highest-leverage thing to lock first:

- Hemolysis: `ASMA_ID` (caps) in one file, `ASMA_id` in another, `ASMA-ID` (hyphen) in a third.
- SYK single-assay sheets: `ASMA_id`; **Competition sheet uses `ASMA_A_id`…`ASMA_E_id`** (no plain `ASMA_id`).
- Alex genomics: `ASMA_id` (amrfinder/metaVF); gtdbtk keyed on sequencing `sample_id`; assembly-manifest on `genome_id`.
- Values seen: `ASMA-3913`, `'ASMA-3913 '` (trailing space), `_priming` suffixes, a `PA14_KEH108_Reporter`
  token leaked into a member column.

**Standard to publish (`docs/id_vocabulary_standard.md`, TODO):**
- Canonical field name: **`ASMA_id`**. Canonical value format: **`ASMA-<digits>`** (pin exact padding
  against `SYK/ASMA_list.xlsx` = the stock list of record).
- Normalization rules: strip whitespace; drop annotation suffixes (`_priming`, etc.); uppercase prefix;
  reject reporter/pathogen tokens from member columns.
- **Grain vocabulary:** `isolate` (physical stock, ~4,940) ⊃ `strain` (dedup unit, ~700 — the row grain) ⊃
  `species` (gtdbtk taxonomy). The isolate→strain→species map (fastani/mash clusters + gtdbtk) is the
  denominator for every "how many screened" answer. **One unverified link to nail with Alex:**
  `genome_id ↔ ASMA_id` (gtdbtk uses sequencing sample_id, not ASMA_id).

---

## 5. First-pass decision heuristic (what we hand the experimentalists to argue over)

Not the final rubric — a **strawman** so the group refines numbers instead of starting from blank:

```
  SAFETY gate    : non-hemolytic (β-hem = No)  AND  not multi-drug-resistant  AND  BSL-1
  VIABILITY gate : grows in SCFM (grow/no-grow = yes; derived max-OD ≥ cutoff)
  COMPETITION    : best planktonic Inhibition_percent vs PA ≥ 50%  (SOW deliverable bar)
  → rank survivors by competition score × ubiquity; flag suggested partners (Alex)
```

Output: a ranked candidate shortlist + a `decision_register` reason per strain. The experimentalists
(SYK/Gwyn/Jake) then set the real thresholds and veto/bless.

---

## 6. Action plan

**Now → Thu Jul 16 (Adam check-in):**
- [ ] Lock the ID/vocabulary standard + grain map (§4).
- [ ] Ingest the 3 on-server-ready assays (competition, hemolysis, AMR) + SCFM growth → v1 strain-level table.
- [ ] Compute the cheap derived columns (max-OD from raw OD; suppressive-synergy sign).
- [ ] Apply the strawman heuristic → first-pass shortlist. Post to Slack for Adam's check-in.

**This week:**
- [ ] Request off-server data with a **clear format spec** (the experimental-metadata columns): tissue
      (Gwyn), mouse (Fatemeh), SYK's `20260713` workbook onto the server, Gwyn's BSL-1 list.
- [ ] Species→BSL reference table; join on gtdbtk species.
- [ ] Confirm halo/secreted-NP scope with SYK (does a systematic dataset exist?).
- [ ] Sync with Alex: merge his `DECISION-MATRIX.md` / GapMind columns into the schema; agree lanes.

**Ongoing / durable:**
- [ ] Ingest to lakehouse `protect_formulation` namespace (empty scaffold today).
- [ ] Register the unified sheet as a curated product in `protect-data-manifest`.

---

## 7. Decisions & open questions

**Decided (Spencer, 2026-07-14):**
- **Approach = plan-first, circulate for buy-in.** Do NOT write integration code yet. Get the team
  (Jake/Alex/SYK/Gwyn) to agree on the schema, the ID/grain standard, and the lanes first. Circulation
  artifacts: `docs/data_readiness_scorecard.md`, `docs/unified_sheet_proposal_v1.md` (team-facing),
  `docs/slack_draft_kickoff.md`.
- **Output format = both** — a shareable **.xlsx** (experimentalists edit the decision register) **and** a
  canonical **CSV/parquet** build in this project dir. Lakehouse `protect_formulation` as the durable home later.

**Still to ratify with the team (the buy-in asks):**
1. **Grain** = strain (~700), isolate/species as attributes — agree? (avoids Gwyn's "315 Rothia" trap;
   "how many screened" is reported at strain level, not isolate ~4,940.)
2. **Canonical `ASMA_id`** = `ASMA-#####` + normalization rules — agree?
3. **Standard experimental-metadata column set** on every source table (Alex's requirement) — agree?
4. **Lanes** (§1) — agree who owns which columns?
5. **Threshold ownership** — SYK/Gwyn/Jake set the final gate cutoffs; we only ship the strawman.

> **Path note (2026-07-14):** this project physically lives at
> `…/current_tasks_7_2026/formulation_unified_data_sheet_7_14_2026/` — a sibling of `7_2026_monthly_report/`,
> not inside it.

---

## 8. Build progress

**2026-07-15 — build scaffolding + roster + Safety gate (all verified):**
- **Naming convention decided:** `<layer>_<content>.py`, git for code history, order in `build/README.md` + `run_all.sh`.
- **Roster upgraded to STRAIN grain** (`build/identity_spine.py`) using Alex's files (his manifest had everything —
  see `data/bronze/BRONZE_MANIFEST.md`): `gtdbtk-summary.tsv` (species) + `mash/clusters.csv` (canonical strain
  groups). Outputs `data/reference/identity_isolates` (4,365 isolates, 95% w/ species) + `identity_strains`
  (**780 strains = the decision grain**, 93% w/ species).
- **Safety gate = 3 silver stat sheets built + run:** `silver_hemolysis` (727 isolates; 369 beta-hemolytic),
  `silver_amr_measured` (751 QC-passing; SYK `Antibiotic_resistance_v2` panel), `silver_amr_genomic` (4,923
  isolates; 3,813 with ≥1 AMR gene). All in `data/silver/`.
- **Q7 code:** borrowed the validated ideas (frozenset dedup + best-inhibition aggregation), writing competition FRESH.

**2026-07-16 — Competition gate + first gold card:** `silver_competition.py` (fresh; per-strain best-solo /
best-team PA knock-down, best partner, signed synergy; + a `formulations` table) and `gold_unified_sheet.py`
(strain-level card). Decision logs added in `docs/decisions/`.

**2026-07-17 — Viability gate, config-as-data, candidate refinement, ship:**
- **Config-as-data:** all thresholds moved to `config/thresholds.yaml` (team-owned); AMR + competition refactored to read it.
- **Viability gate:** `silver_growth_endpoint.py` (SCFM grow/no-grow + mucin lift; 97 of 764 grow in SCFM).
- **Candidate flag** now from `data/reference/species_safety.csv` (interim; 41 pathogens excluded, 10 review, 729 unreviewed).
- **Shipped:** GitHub repo `WeArePROTECT/protect-formulation-unified-sheet` (NO data on GitHub); card + Word
  data dictionary on Google Drive; team announced. Message drafts moved to gitignored `correspondence/`.
- **Emma metagenomics integration SCOPED + unblocked** (`docs/emma_metagenomics_integration_plan.md`).

---

## 9. Status at wind-down (2026-07-17) and next steps

**Where it stands:** v0 pipeline built, verified, and shipped. 780 strains, all three gates populated (Safety +
Viability + Competition), 167 candidates have all three measured. Preliminary (SYK pre-QC). Full current-state
and how-to-continue are in **`agent_handoffs/2026-07-17_handoff.md`** (the entry point for the next agent).

**Top next steps (for the Tuesday team meeting; SYK posts suggestions Monday):**
1. **Pass/fail ranking formulae** (`build/heuristic_shortlist.py`) — Adam explicitly asked; config-driven,
   provisional; must-pass Safety + Viability, rank survivors by Competition (+ Relevance).
2. **Emma metagenomics integration** (`airway_ubiquity` + new `pa_cooccurrence`) — scoped/unblocked in the Emma plan doc.

**Then / as data arrives:** Gwyn's BSL-1 list (replace interim `species_safety.csv`); tissue (Gwyn) + mouse
(Fatemeh) columns; growth-rate/lag viability; SYK QC pass (preliminary -> final); lakehouse ingestion.

**Done checklist:** roster (strain grain) · Safety gate (hemolysis, measured + genomic AMR) · Viability gate
(SCFM) · Competition gate (PA knock-down + synergy) · gold card (xlsx/csv/parquet + `_about`) · config-as-data ·
interim candidate/safety list · decision logs · data dictionary (md + docx) · GitHub repo (no data) · Drive +
team announcement · Emma integration plan.
