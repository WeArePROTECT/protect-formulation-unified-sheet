# Draft Slack announcement -> the team (unified sheet v0)

*(no em dashes; fill in the two links before sending: {GITHUB_LINK} and {DRIVE_LINK})*

---

Hey team, Alex and I have a first real version of the **unified formulation decision sheet** to share, the
one Adam asked for as the "theory of operations" for choosing formulations. Wanted to get it in front of you
early so your feedback shapes where it goes.

**What it is:** one spreadsheet, one row per strain (~780 unique strains), that pulls all our screens into a
single place so we can see per strain whether it is safe, whether it grows, and whether it beats PA, and
decide what moves forward and why. It is organized around Adam's three gates: **Safety, Viability, Competition.**

**What's in it right now:**
- **Identity:** strain, species, and a candidate flag (using Alex's genomics to collapse the collection into ~780 strains)
- **Safety:** hemolysis (Cassie), measured antibiotic resistance + genomic AMR genes (Sun-Young + Alex)
- **Viability:** grows in SCFM or not, plus a mucin (prebiotic) growth boost (Sun-Young)
- **Competition:** best knock-down of PA alone vs on a team, best partner, and whether teaming actually helps (Sun-Young)
- Tissue, mouse, and airway-abundance columns are stubbed in and will fill as that data lands

**How we built it:** raw files stay where their owners keep them (we just point to them), each screen is
cleaned into its own tidy table, then everything is joined into the final card. It is fully reproducible from
the code. The genomics gave us species and strain groups, so "how many strains, how many screened" finally
has a clean answer.

**A few decisions worth knowing (all changeable):**
- Every threshold (what counts as "resistant," "grows," "good competitor") is a **best-guess default that YOU
  own.** They live in one settings file, and we can recompute the whole sheet in minutes to whatever you want.
  The sheet's `_about` tab lists the current settings.
- The candidate/safety flag is an **interim** list right now. It correctly excludes the obvious pathogens, but
  `is_candidate = true` currently means "not a known pathogen," not "safety cleared." **Gwyn, your BSL-1 list
  is what we want to plug in to make this real.**
- It is **preliminary**: Sun-Young's latest data is still pre-QC, so treat the numbers as directional.

**What we still need from you:**
- Gwyn: the BSL-1 list (to finalize candidates) + tissue data when ready
- Fatemeh: mouse data when ready
- Sun-Young: QC pass on the phenotype data so we can move it from preliminary to final
- Everyone: the thresholds and cutoffs you actually want, and any columns you think are missing

**The big ask: give us all the feedback you can.** This is a living draft built to adapt. Tell us what to
add, change, reframe, or recompute, and we will. Nothing here is locked.

**Take a look:**
- **The sheet (no code or server needed):** {DRIVE_LINK} — open it and start on the `_about` tab
- **The full project (code, data sources, and the reasoning behind every choice):** {GITHUB_LINK}

Thanks all, excited to hear what you think.
