# Plain-English Guide to the Unified Sheet Project

*A living, jargon-light explainer. I keep this current as we build. If any piece here ever feels fuzzy, ask
and I'll zoom in.*

---

## The big picture (what we're building, and why)

Our team has a big collection of bacteria (~700 useful "strains"). We want to pick a small number that,
combined into "formulations," can crowd out the lung pathogen *Pseudomonas aeruginosa* — safely.

The problem: the **evidence** for picking good strains is scattered across many people's spreadsheets, in
different formats, with the strain names written inconsistently. Nobody can see the whole picture at once.

**So we're building one master table.** Think of it like a **sports report card**: one row per strain, and
columns for every piece of evidence — Is it safe? Does it grow? Does it beat the pathogen? Once every strain
has a filled-in "report card," the team can rank them and decide which move forward. That master table is
"the unified sheet."

Our specific job (me + you + Alex) is the **plumbing**: gather the scattered evidence, clean it, stack it into
that one table, and give a first-pass way to rank the strains. The biologists then set the pass/fail bars. And
crucially, we build everything as **switches the biologists control**: which data is plugged in, how each column
is computed, and how the columns combine into a decision are all settings they can change, not code they'd edit.

---

## Three ideas that explain almost everything we do

**1. A "strain" is our row.** Every measurement is about a strain, labeled with an ID like `ASMA-3913`.
Everything connects through that ID.

**2. Names are messy, so we standardize first.** The same strain shows up as `ASMA_id`, `ASMA-ID`,
`ASMA-3913 ` (with a stray space), etc. Before we can match evidence about the same strain from different
files, we have to agree they're the same strain. (Like recognizing "NYC," "New York," and "New York City"
as one place before combining data about it.)

**3. We clean data in stages: raw → cleaned → combined.** This is a standard data-engineering pattern
(sometimes called bronze/silver/gold). Like cooking: raw ingredients → chopped-and-prepped ingredients →
finished dish. We never cook straight from the messy raw files; we prep each one first, then combine.

---

## What we've built (and why)

The report card is now filled in for all three gates, plus a fourth "relevance" block and a way to rank the
strains. In plain English:

| Piece | In plain English | Why it exists |
|---|---|---|
| **The roster** (`identity_spine`) | The list of all strains, the report card's row labels | The backbone everything attaches to: 780 strains, each with its species and how many isolates it has |
| **Safety columns** | Does it harm the patient? (hemolysis + measured antibiotic resistance + resistance genes) | The first gate; three screens from Cassandra, Sun-Young, and Alex |
| **Viability column** | Can we grow it? (does it grow in lung-mimic fluid) | The second gate; Sun-Young's growth screen |
| **Competition columns** | Does it beat the pathogen? (how much it knocks down PA, alone and on a team) | The third gate, and the scientific heart; Sun-Young's competition screen |
| **Relevance columns** | Is it actually a common, PA-displacing resident of real patient lungs? | Emma's metagenomics: how abundant/active it is in real airways, whether it displaces PA there, and a model prediction of metabolic competition |
| **The ranking engine** (`heuristic_shortlist`) | Turns the report card into a ranked shortlist | Must-pass gates thin the field, then survivors are ranked, all driven by settings the team controls |
| **The three switchboards** (config files) | The knobs the biologists turn | One file for *what data is plugged in*, one for *how each column is computed*, one for *how columns combine into a decision* |
| **The test suite** | A safety net | 62 automated checks that confirm a settings change gives the result you intended, not a bug |

**A finding worth remembering:** the strains that look best on real-world relevance (abundant in airways,
anti-correlated with PA, predicted competitors) AND beat PA in the dish are the same handful (Gemella,
Streptococcus, Neisseria). When independent signals agree, that's a good sign, though it is still preliminary.

---

## What's left (and why it's not blocking)

The report card is designed to fill in gradually, so the missing pieces just leave blank columns for now:

| Still to come | What it fills in | Who / status |
|---|---|---|
| **Tissue + mouse results** | Two reserved columns (does it work in a tissue model, then a mouse) | Gwyn + Fatemeh; not on the server yet |
| **Gwyn's BSL-1 safety list** | Makes the "is this a candidate?" call authoritative (right now it's an interim best-guess list) | Gwyn |
| **Sun-Young's QC pass** | Flips the whole card from "preliminary" to final | Sun-Young, in progress |
| **The team's real bars** | The actual pass/fail cutoffs, and whether relevance counts toward the ranking | The biologists set these; we ship best-guess defaults |

None of these block the sheet: it already works end to end, and each new piece is a plug-in (a new column or a
one-line settings change), not a rebuild.

---

## How it all fits together (the flow)

```
  messy source files  →  [ID cleaner]  →  one clean "stat sheet" per measurement (silver)
  (listed in data_sources.yaml)                        │
                                                        ▼
                              the roster (identity spine)  +  all stat sheets
                                                        │
                                                        ▼
                        one row per strain, all columns = the UNIFIED SHEET (gold)
                                                        │   gates + ranking (settings the team controls)
                                                        ▼
                              ranked shortlist of strains  →  the biologists decide
```

That's the whole project in one picture. Three switchboards sit alongside it: what data is plugged in, how each
column is computed, and how the columns combine into a ranked decision. Everything we build is one labeled box.
