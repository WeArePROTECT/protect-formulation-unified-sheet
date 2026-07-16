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

Our specific job (me + you + Alex) is the **plumbing**: gather the scattered evidence, clean it, and stack it
into that one table. The biologists then set the pass/fail bars.

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

## What I've built so far (and why)

| Piece | In plain English | Why it exists | How it works (briefly) |
|---|---|---|---|
| **`lib_ids.py`** — the ID cleaner | A "universal translator" for strain names | So data from different people about the same strain actually lines up | Takes any messy label, strips spaces/suffixes, throws out non-strain junk (like pathogen labels), and returns one clean form: `ASMA-3913` |
| **`build_10_identity.py` → `identity_spine`** — the roster | The master list of all strains — the empty report card with just the row labels | It's the backbone everything else attaches to. Build the roster first, then fill in stats | Reads the official stock list (3,972 strains), then tries to add each one's species (what kind of bacteria). Writes it out as a clean table |
| **`build/README.md`** — the build map | A checklist of every step, in order, with status | So we (and Alex) can see what's done, what's next, and what's blocked | A table listing each script, what it produces, and whether it's ready to build |
| **`docs/*` (scorecard, proposal, sheet-map, guides)** | The planning + team-facing docs | So the team agrees on the plan before we pour in effort, and so decisions are written down | Markdown docs you can read and share |

**The most useful thing the roster already told us:** of 3,972 strains, only **5%** had their species filled
in from the file we had. That's not a failure — it's a *finding*. It tells us precisely what to ask Alex for
(the species + a name-matching map for the other 95%). We turned a vague "we need Alex's help" into a
specific, answerable request.

---

## What I propose to build next (and why)

The roster is the empty report card. Next we fill in columns — one "stat sheet" (we call these **silver
tables**) per type of measurement. Each is independent, so we can build them as data arrives:

| Next piece | What it fills in | Why it's next |
|---|---|---|
| **hemolysis + antibiotic + AMR-gene silver tables** | The **SAFETY** columns ("does it harm the patient?") | All three files are already on the server, and together they complete a whole gate — a clean, visible win |
| **growth-endpoint silver table** | The **VIABILITY** column ("can we actually grow it?") | Also on the server; it's a simple yes/no-grows table |
| **competition silver table** | The **COMPETITION** column ("does it beat the pathogen?") | This is the scientific heart of the project, and I can reuse code we already wrote for the Q7 report |
| **first "gold" join** | Stacks the above onto the roster → a real draft report card | Lets us show Adam something concrete on Thursday, even with columns still missing |

**Why this order:** safety and viability are simple, self-contained, and already on the server — quick wins
that prove the pipeline. Competition is the highest-value column. The gold join then turns separate stat
sheets into the actual unified sheet. Missing pieces (tissue, mouse, etc.) leave blank columns that fill in
later — the report card is designed to be filled in gradually, not all at once.

---

## How it all fits together (the flow)

```
  messy source files  →  [ID cleaner]  →  one clean "stat sheet" per measurement (silver)
        (raw)                                          │
                                                       ▼
                              the roster (identity spine)  +  all stat sheets
                                                       │
                                                       ▼
                        one row per strain, all columns = the UNIFIED SHEET (gold)
                                                       │
                                                       ▼
                       biologists set pass/fail bars → ranked shortlist of strains
```

That's the whole project in one picture. Everything I build is one labeled box in this flow.
