# Tissue Data in the Formulation Sheet: What We Used, What's Missing (for Gwyn)

Hi Gwyn, this is a plain-English record of exactly which of your tissue results made it into the PROTECT
Formulation Unified Sheet, what is marked preliminary and why, and what (if anything) would round it out. Short
version: **we used your own computed analyses, it is looking good, and nothing here is blocking the project.**
Tissue is a supplementary confirmation layer on the sheet, not one of the gates, so this is a "nice to complete
when you can," not a "we're stuck."

## What we used (your computed files)

We built the tissue columns straight from the analysis workbooks you had already computed, the ones with your
standard-curves → per-insert → condition-summary → statistics layout:

- **ptc.613/614** (NM+BL vs PA14) — `GAHR_ptc613_614_statistics.xlsx` (your mCherry suppression + LY barrier)
- **ptc.451/452** (PAO1 vs NM+RM ± mucin) — `PAO1_NM_RM_mucin_competition_analysis.xlsx`
- **ptc.523/524** (NS ± NM vs PA14) — your `summary_table.csv` + `stats.csv`
- **ptc.701/702** (M21 CD/NB/NE monoculture) — `M21_LY_analysis.xlsx` (your control-subtracted barrier)
- **ptc.739/740** (M21 BL/NM monoculture) — `GAHR.ptc.739-740__M21_LY_analysis.xlsx` (your control-subtracted
  barrier; added 2026-07-21, WT arm) — a second barrier study confirming BL disrupts and NM is neutral

From these, the sheet now shows tissue results for **7 strains**: NM, BL, RM, NS (PA suppression on tissue) and
CD, NB, NE (barrier effect). For example, your NM+BL 43.5%/37.3% suppression and your NM+RM+mucin 56%/97.7% are
in there, with your p-values.

## What's missing (only if you want to complete it later)

We could not find a saved, computed analysis file for these, so they are **not** in the sheet yet. Most are the
same consortia repeated, so they would add confirmation, not change the story:

**Highest value if it exists (your M21 competition mCherry, the LEAD consortium work):**
- **ptc.796/797** (NM+NB, your "LEAD consortium"), **ptc.757/758** (BL+NM ~80-85%), and the **mCherry**
  (PA-suppression) files for **ptc.739/740** and **ptc.701/702** — their LY barrier is now in the sheet, but
  the mCherry is not (those competition-mCherry analysis files are Drive-only, not saved to the server).

**Earlier competitions (you have figures, but we couldn't find a data workbook):**
- **ptc.350/351** (NM+BL, "59%"), **ptc.377/378** (NM+RD exclusion), **ptc.379/380** (NM+BL ± mucin),
  **ptc.543/544** (NM/BL + PAO1), **ptc.297/298** (probiotic benchmark)

**We intentionally skipped these (your own notes say they aren't finished):** ptc.413/414 ("not yet analyzed"),
ptc.642/643 ("QC-excluded"), ptc.677/678 ("not analyzed"), ptc.846/847 ("contaminated").

### If you want any of these included
The cleanest way is: open the study's analysis in Google Sheets, and from **drive.google.com** do
right-click → **Download** (that converts it to a real Excel file, the desktop Drive copy does not). Send Spencer
that file and we drop it in, it is a two-minute add per study. If a study was never saved as its own analysis
file, that is fine too, just let us know and we can compute it from your raw readouts using your method.

## Why the tissue data is marked "preliminary"

1. It covers a subset of your studies (the ones you had finished computing), not all of them.
2. For a couple of studies you gave per-condition means rather than a single "% suppression," so we computed the
   % from your numbers (it matched your Vade Mecum, but it is our arithmetic on your data).
3. For the barrier/safety number we applied your M21 control-subtracted method to the other studies uniformly,
   and left out ptc.451/452's barrier because it was in raw RFU rather than % passage. **You should sanity-check
   that choice.**
4. Most importantly, you have not reviewed this specific assembly yet. Once you do, we flip it from preliminary
   to confirmed.

## The one thing worth your eyes

When you get a chance: **which of your readouts is your "headline" PA number** (the % suppression, the barrier,
or the fold-change)? And is the control-subtracted % passage the right way to express "did the strain harm the
tissue"? Those two answers let us lock this in. Thank you, your analyses made this straightforward.

*Full technical audit trail (every number → your file/sheet/cell): `docs/tissue_provenance_and_method.md`.*
