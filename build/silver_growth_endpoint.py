#!/usr/bin/env python3
"""
silver_growth_endpoint.py — VIABILITY: can the strain grow in lung-like fluid (SCFM)?

Source : SYK ASMA_phenotype_20260714.xlsx -> sheet Growth_endpoint.
Meaning: endpoint OD600 (culture cloudiness) after 72 h in SCFM, SCFM+mucin, rich media (BHIS = positive
         "can it grow at all" control), and no-carbon (negative control). BLANK wells give the per-date
         media baseline, which we subtract (Sun-Young's rule).
Summary: each well has its date's blank (the MEAN of that date's BLANK wells) subtracted and is floored at 0;
         then an isolate's wells collapse to one number per condition by the team's setting
         viability.replicate_aggregation. MEDIAN since 2026-11-24 (Spencer's decision L, PROTECT-60 and
         PROTECT-76): with 3 wells, a strain grows only if at least 2 of them do. The mean (the rule before)
         let one odd well decide the call.
Thresholds are TEAM-OWNED (config/thresholds.yaml). Decisions: docs/decisions/viability_stat_sheet_decisions.md
Output : one row per ASMA_id. Raw ODs kept so any cutoff re-derives.
Retract: rows listed for this sheet in the `retractions` CSV (data_sources.yaml) are dropped before
         anything else, matched on asma_id, each line with an exact-count check (lib_retractions.py).
         2026-11-16: ASMA-1448, a wrong stock (PROTECT-59).
"""
import os
from collections import defaultdict
from statistics import mean, median
from lib_ids import normalize_asma_id, read_xlsx_sheet, write_table
from config import CFG
from data_sources import source, is_enabled
import lib_retractions

SOURCE = "growth_endpoint"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_growth_endpoint")
_SRC = source(SOURCE)
SRC = _SRC["path"]
SHEET = _SRC.get("sheet")
RETRACTIONS = _SRC.get("retractions")
SCFM_MIN = CFG["viability"]["scfm_grow_min_od"]        # team-owned
QC_MIN = CFG["viability"]["qc_rich_media_min_od"]      # team-owned
REPLICATES = CFG["viability"]["replicate_aggregation"]  # team-owned: median | mean
# How one isolate's blank-subtracted wells collapse to one number. Only the isolate's own wells: the blank
# baseline is always the mean of the date's BLANK wells, whatever this says.
AGGREGATIONS = {"median": median, "mean": mean}
CONDS = ["No_Carbon_72", "SCFM_72", "SCFM_mucin_0.5_72", "BHIS_72"]
COLS = ["asma_id", "scfm_od", "scfm_mucin_od", "bhis_od", "no_carbon_od",
        "grows_scfm", "grows_scfm_mucin", "mucin_lift", "qc_grew", "n_reps", "assay", "source_file"]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def replicate_summary(how):
    """The function named by viability.replicate_aggregation. Anything else stops the build, never a guess."""
    if how not in AGGREGATIONS:
        raise ValueError(f"config/thresholds.yaml viability.replicate_aggregation must be one of "
                         f"{sorted(AGGREGATIONS)}, not {how!r}")
    return AGGREGATIONS[how]


def summarize(rows, how, scfm_min, qc_min, source_file):
    """Growth_endpoint rows (retractions already dropped) -> one output row per ASMA isolate. No IO."""
    collapse = replicate_summary(how)

    # per-date BLANK baseline (mean of BLANK wells per condition); global fallback if a date has none
    blank_by_date, glob = defaultdict(lambda: defaultdict(list)), defaultdict(list)
    for r in rows:
        if str(r.get("ASMA_id")).strip().upper() == "BLANK":
            d = str(r.get("Assay_start_date"))
            for c in CONDS:
                v = num(r.get(c))
                if v is not None:
                    blank_by_date[d][c].append(v)
                    glob[c].append(v)

    def blank(d, c):
        if blank_by_date[d][c]:
            return mean(blank_by_date[d][c])
        return mean(glob[c]) if glob[c] else 0.0

    # background-subtracted values per ASMA isolate
    agg = defaultdict(lambda: {**{c: [] for c in CONDS}, "n": 0})
    for r in rows:
        aid = normalize_asma_id(r.get("ASMA_id"))
        if not aid:
            continue
        d = str(r.get("Assay_start_date"))
        a = agg[aid]
        a["n"] += 1
        for c in CONDS:
            v = num(r.get(c))
            if v is not None:
                a[c].append(max(0.0, v - blank(d, c)))

    out = []
    for aid, a in agg.items():
        def m(c):
            return round(collapse(a[c]), 3) if a[c] else None
        scfm, scfmm, bhis, nocarb = m("SCFM_72"), m("SCFM_mucin_0.5_72"), m("BHIS_72"), m("No_Carbon_72")
        qc_grew = bhis is not None and bhis >= qc_min

        def grow_call(od):
            if od is None or not qc_grew:      # inconclusive if it didn't even grow in rich media
                return None
            return "Y" if (od >= scfm_min and (nocarb is None or od > nocarb)) else "N"

        lift = round(scfmm - scfm, 3) if (scfm is not None and scfmm is not None) else None
        out.append({
            "asma_id": aid, "scfm_od": scfm, "scfm_mucin_od": scfmm, "bhis_od": bhis, "no_carbon_od": nocarb,
            "grows_scfm": grow_call(scfm), "grows_scfm_mucin": grow_call(scfmm), "mucin_lift": lift,
            "qc_grew": qc_grew, "n_reps": a["n"], "assay": "growth_endpoint_scfm",
            "source_file": source_file,
        })
    out.sort(key=lambda r: int(r["asma_id"].split("-")[1]))
    return out


def main():
    if not is_enabled(SOURCE):
        print(f"silver_growth_endpoint -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    retract = lib_retractions.Tracker(lib_retractions.load(RETRACTIONS, SRC, SHEET), "silver_growth_endpoint")
    rows = [r for r in read_xlsx_sheet(SRC, SHEET) if not retract.drop(r.get("ASMA_id"))]
    retract.verify()

    out = summarize(rows, REPLICATES, SCFM_MIN, QC_MIN, os.path.basename(SRC))
    n = write_table(out, COLS, OUT)

    grow = sum(1 for r in out if r["grows_scfm"] == "Y")
    incon = sum(1 for r in out if r["grows_scfm"] is None)
    mucin_help = sum(1 for r in out if (r["mucin_lift"] or 0) >= 0.1)
    print(f"silver_growth_endpoint -> {n} isolates")
    print(f"    replicate wells summarised by: {REPLICATES} (each well minus its date's mean blank, floored at 0)")
    print(f"    grow in SCFM (>= {SCFM_MIN} OD): {grow} | no-grow: {n - grow - incon} | inconclusive: {incon}")
    print(f"    mucin gives a growth lift (>=0.1 OD): {mucin_help}")


if __name__ == "__main__":
    main()
