# Draft Slack post — unified sheet kickoff (Spencer)

*Post to the formulation channel to open the buy-in conversation, ahead of Adam's Thursday check-in.*
*Edit freely — this is a starting point. Server paths assume teammates can browse the share; offer to paste tables inline if not.*

---

Following up on yesterday's meeting + this thread — Alex and I are set up to be the integration layer, so
before we start joining anything, here's a **v1 proposal for the unified formulation sheet** so we build it
once. Two docs (on the server, happy to paste inline if easier):

- **Data-readiness scorecard** — for each of Adam's columns: what's done, how many strains, and whether it's
  on the server yet. `…/current_tasks_7_2026/formulation_unified_data_sheet_7_14_2026/docs/data_readiness_scorecard.md`
- **Schema + lanes proposal** — `…/docs/unified_sheet_proposal_v1.md`

**The shape:** one row per **strain** (~700 unique, not the ~4,940 isolates), columns = safety / viability /
competition proxies, + a decision column. You give us clean assay tables (with experimental metadata —
date, plate format, media, temp, duration, priming, reader); we do the joins + derived metrics + a first-pass
ranking; the group sets the actual thresholds.

**5 quick things I'd love a 👍/👎 on:**
1. Grain = **strain** (~700), with isolate/species as attributes.
2. One canonical ID everywhere — **`ASMA_id`** (`ASMA-#####`); we normalize the trailing-space / `_priming` / caps mess on ingest.
3. Every assay table carries the **same experimental-metadata columns** (SYK's phenotype sheets already do this — that's the model).
4. **Lanes:** Spencer = IDs + unified table + empirical ingestion + derived cols + decision register; Alex = in-silico/metabolic + partners + clades; SYK/Gwyn/Cassandra = assay tables → server; Jake + experimentalists = thresholds.
5. You (SYK/Gwyn/Jake) own the gate cutoffs — I'll bring a strawman to argue with, not impose one.

**What would unblock the build the most (on the server, please):**
- **SYK** — ✅ thanks, `ASMA_phenotype_20260714.xlsx` + notes landed. Your notes doc is exactly the per-assay condition metadata we need — it's the model I'll point everyone to. (I'll use the current sheets: Competition, `Antibiotic_resistance_v2`, `Growth_endpoint`, 96-well curves; excluding the deprecated 384/`v1` ones.)
- **Gwyn** — tissue damage + tissue competition tables (+ metadata) + your BSL-1 list.
- **Cassie** (via Jake) — confirm the hemolysis format's final + the FREP duplicate-well fix.
- **Alex** — GapMind capability + suggested-partner columns, and the `genome_id ↔ ASMA_id` map.

If the shape looks right, I'll have a first-pass strain-level sheet from what's already on the server
(competition + hemolysis + AMR + SCFM growth) to show for Adam's Thursday check-in. Push back on anything.
