#!/usr/bin/env python3
"""
silver_competition.py — COMPETITION: how well a strain knocks down the pathogen.

Source : SYK ASMA_phenotype_20260714.xlsx -> sheet Competition (STANDARD conditions only).
Meaning: each well = one formulation (team of 1-5 strains) vs one pathogen reporter, scored by
         Inhibition_percent (0 = pathogen grew freely, 100 = fully blocked).
Design decisions + rationale: docs/decisions/competition_stat_sheet_decisions.md  <-- read this.

Two outputs:
  formulations       : one row per (team x reporter)  -> team grain (what we ultimately ship)
  silver_competition : one row per STRAIN             -> best-alone / best-on-team / partner / synergy
"""
import os
from collections import defaultdict
from statistics import median, mean
from lib_ids import normalize_asma_id, read_xlsx_sheet, write_table
from config import CFG
from data_sources import source, is_enabled

SOURCE = "competition"
HERE = os.path.dirname(os.path.abspath(__file__))
SILVER = os.path.join(os.path.dirname(HERE), "data", "silver")
_SRC = source(SOURCE)
SRC = _SRC["path"]
SHEET = _SRC.get("sheet")
MEM_COLS = ["ASMA_A_id", "ASMA_B_id", "ASMA_C_id", "ASMA_D_id", "ASMA_E_id"]
# Team-owned settings — see config/thresholds.yaml
PA_PRIMARY = CFG["competition"]["headline_reporter"]   # headline PA reporter
AGG = CFG["competition"]["replicate_aggregation"]      # median | mean | max
REPORT_BAR = CFG["competition"]["report_bar_pct"]
PA_ALL = {"PA14_KEH108_Reporter", "PA14_FA_Reporter", "PAO1_Reporter",
          "ASMA-137_Reporter", "ASMA-143_Reporter"}    # all P. aeruginosa reporters (lab + clinical)


def collapse(vals):
    """Collapse replicate wells to one number per the team-chosen method (config)."""
    if AGG == "mean":
        return mean(vals)
    if AGG == "max":
        return max(vals)
    return median(vals)

FORM_COLS = ["formulation_id", "n_members", "members", "reporter",
             "inhibition_median", "inhibition_max", "n_wells"]
STRAIN_COLS = ["asma_id", "best_solo_inhib_pa", "best_team_inhib_pa", "best_partner",
               "suppressive_synergy_pa", "best_inhib_pa_any", "n_formulations_pa",
               "reporter_primary", "assay", "source_file"]


def _key(aid):
    return int(aid.split("-")[1])


def is_standard(cond):
    return str(cond or "").strip().lower().startswith("standard")   # keeps Standard_A/B/C, drops Non-standard_A


def main():
    if not is_enabled(SOURCE):
        print(f"silver_competition -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    os.makedirs(SILVER, exist_ok=True)

    # collect replicate wells: (frozenset of members, reporter) -> [inhibition values]
    vals = defaultdict(list)
    for row in read_xlsx_sheet(SRC, SHEET):
        if not is_standard(row.get("Assay_condition_type")):
            continue
        members = frozenset(m for m in (normalize_asma_id(row.get(c)) for c in MEM_COLS) if m)
        if not members:                      # reporter-only control well
            continue
        rep = str(row.get("Reporter_id") or "").strip()
        inh = row.get("Inhibition_percent")
        if not isinstance(inh, (int, float)):
            continue
        vals[(members, rep)].append(float(inh))

    # aggregate replicate wells -> headline (team-chosen: median/mean/max) + max (best-case) + n
    agg = {k: (collapse(v), max(v), len(v)) for k, v in vals.items()}

    # ---- formulations table (team x reporter) ----
    form_rows = []
    for (members, rep), (med, mx, nw) in agg.items():
        ms = "+".join(sorted(members, key=_key))
        form_rows.append({"formulation_id": ms, "n_members": len(members), "members": ms,
                          "reporter": rep, "inhibition_median": round(med, 1),
                          "inhibition_max": round(mx, 1), "n_wells": nw})
    form_rows.sort(key=lambda r: -r["inhibition_median"])
    n_form = write_table(form_rows, FORM_COLS, os.path.join(SILVER, "formulations"))

    # ---- strain rollup ----
    best_solo, best_team, best_any = defaultdict(lambda: None), defaultdict(lambda: None), defaultdict(lambda: None)
    best_partner, nform = {}, defaultdict(set)

    def better(cur, new):
        return new if (cur is None or new > cur) else cur

    for (members, rep), (med, mx, nw) in agg.items():
        for X in members:
            if rep in PA_ALL:
                best_any[X] = better(best_any[X], med)
            if rep == PA_PRIMARY:
                nform[X].add(members)
                if len(members) == 1:
                    best_solo[X] = better(best_solo[X], med)
                elif best_team[X] is None or med > best_team[X]:
                    best_team[X] = med
                    best_partner[X] = "+".join(sorted(members - {X}, key=_key))

    strain_rows = []
    for X in sorted(set(best_solo) | set(best_team) | set(best_any), key=_key):
        solo, team = best_solo.get(X), best_team.get(X)
        syn = round(team - solo, 1) if (solo is not None and team is not None) else None
        strain_rows.append({
            "asma_id": X,
            "best_solo_inhib_pa": round(solo, 1) if solo is not None else None,
            "best_team_inhib_pa": round(team, 1) if team is not None else None,
            "best_partner": best_partner.get(X),
            "suppressive_synergy_pa": syn,
            "best_inhib_pa_any": round(best_any[X], 1) if best_any.get(X) is not None else None,
            "n_formulations_pa": len(nform.get(X, ())),
            "reporter_primary": PA_PRIMARY, "assay": "competition", "source_file": os.path.basename(SRC),
        })
    n_str = write_table(strain_rows, STRAIN_COLS, os.path.join(SILVER, "silver_competition"))

    # ---- summary ----
    solo_bar = sum(1 for r in strain_rows if (r["best_solo_inhib_pa"] or 0) >= REPORT_BAR)
    team_bar = sum(1 for r in strain_rows if (r["best_team_inhib_pa"] or 0) >= REPORT_BAR)
    pos_syn = sum(1 for r in strain_rows if (r["suppressive_synergy_pa"] or 0) > 0)
    print(f"formulations       -> {n_form} (team x reporter) rows  [agg={AGG}]")
    print(f"silver_competition -> {n_str} strains screened vs PA")
    print(f"    best SOLO knock-down of PA >={REPORT_BAR}% : {solo_bar} strains")
    print(f"    best TEAM knock-down of PA >={REPORT_BAR}% : {team_bar} strains")
    print(f"    teaming helps (synergy > 0)      : {pos_syn} strains")


if __name__ == "__main__":
    main()
