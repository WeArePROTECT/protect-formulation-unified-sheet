#!/usr/bin/env python3
"""
silver_hemolysis.py — SAFETY: does the isolate break down red blood cells?

Source : Cassie's ASMArep_HemolysisResultsSummary_FollowUps_08122026.xlsx (see BRONZE_MANIFEST).
Meaning: beta-hemolysis (fully lyses blood cells) is the primary "could harm the patient"
         proxy Adam named; alpha is partial. Values in the file are Y / N / (blank = not determined).
Output : one row per ASMA_id (isolate grain). Replicates/timepoints collapsed conservatively —
         a strain counts as hemolytic if it showed hemolysis in ANY replicate at ANY timepoint.

TWO SHEETS. The base sheet is the original screen. `Follow Up Results` is a second round of clean
re-reads for isolates whose original result was unreliable (the strain did not grow, or colonies
overlapped so the halo could not be attributed). `followup_policy` in data_sources.yaml decides
what happens when the two disagree. That is a TEAM-OWNED call, see the inventory project's
docs/merge_policy_decision.md:

    union          beta if beta in EITHER sheet (conservative default, preserves prior behaviour)
    followup_wins  the re-screen supersedes the original for any isolate it covers

Follow-up rows whose reason is `SYK-Skip` were deliberately never attempted and carry no readings
at all. They are skipped on read so a blank can never be mistaken for a negative result.
"""
import os
from lib_ids import normalize_asma_id, read_xlsx_sheet, write_table
from data_sources import source, is_enabled

SOURCE = "hemolysis"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_hemolysis")
_SRC = source(SOURCE)
SRC = _SRC["path"]
SHEET = _SRC.get("sheet")
FOLLOWUP_SHEET = _SRC.get("followup_sheet")
POLICY = str(_SRC.get("followup_policy") or "union").strip().lower()
VALID_POLICIES = ("union", "followup_wins")
BETA = ["24: Beta Hemolysis?", "48: Beta Hemolysis?", "72: Beta Hemolysis?"]
ALPHA = ["24: Alpha Hemolysis?", "48: Alpha Hemolysis?", "72: Alpha Hemolysis?"]
COLS = ["asma_id", "grew", "beta_hemolytic", "alpha_hemolytic", "hemolysis_concern",
        "n_reps", "n_followup_reps", "call_source", "assay", "method", "source_file"]


def any_yes(vals):
    """Y if any value is Y; else N if any is N; else None (not determined)."""
    v = [str(x).strip().upper() for x in vals if x is not None and str(x).strip().lower() not in ("", "none")]
    return "Y" if "Y" in v else ("N" if "N" in v else None)


def combine(base, followup):
    """Collapse a base call and a follow-up call into one, per the configured policy."""
    if followup is None:
        return base
    if base is None or POLICY == "followup_wins":
        return followup
    return "Y" if "Y" in (base, followup) else "N"


def accumulate(store, sheet, skip_syk_skip=False):
    """Read one sheet into {asma_id: {grew, beta, alpha, n}}."""
    for row in read_xlsx_sheet(SRC, sheet):
        aid = normalize_asma_id(row.get("ASMA_ID") or row.get("ASMA_id"))
        if not aid:
            continue
        if skip_syk_skip and str(row.get("Follow Up Reason") or "").strip().lower() == "syk-skip":
            continue
        a = store.setdefault(aid, {"grew": [], "beta": [], "alpha": [], "n": 0})
        a["n"] += 1
        a["grew"].append(row.get("Growth?"))
        a["beta"] += [row.get(c) for c in BETA]
        a["alpha"] += [row.get(c) for c in ALPHA]


def main():
    if not is_enabled(SOURCE):
        print(f"silver_hemolysis -> source '{SOURCE}' disabled in data_sources.yaml; skipping")
        return
    if POLICY not in VALID_POLICIES:
        raise ValueError(f"hemolysis.followup_policy must be one of {VALID_POLICIES}, got {POLICY!r} "
                         f"(config/data_sources.yaml)")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    empty = {"grew": [], "beta": [], "alpha": [], "n": 0}
    base, follow = {}, {}
    accumulate(base, SHEET)
    if FOLLOWUP_SHEET:
        accumulate(follow, FOLLOWUP_SHEET, skip_syk_skip=True)

    rows = []
    for aid in set(base) | set(follow):
        b = base.get(aid, empty)
        f = follow.get(aid, empty)
        beta = combine(any_yes(b["beta"]), any_yes(f["beta"]))
        rows.append({
            "asma_id": aid,
            "grew": combine(any_yes(b["grew"]), any_yes(f["grew"])),
            "beta_hemolytic": beta,
            "alpha_hemolytic": combine(any_yes(b["alpha"]), any_yes(f["alpha"])),
            "hemolysis_concern": beta == "Y",
            "n_reps": b["n"],
            "n_followup_reps": f["n"],
            "call_source": "base+followup" if (b["n"] and f["n"]) else ("followup" if f["n"] else "base"),
            "assay": "hemolysis", "method": "blood agar (ASMArep plate)",
            "source_file": os.path.basename(SRC),
        })
    rows.sort(key=lambda r: int(r["asma_id"].split("-")[1]))
    n = write_table(rows, COLS, OUT)
    conc = sum(1 for r in rows if r["hemolysis_concern"])
    undet = sum(1 for r in rows if r["beta_hemolytic"] is None)
    resc = sum(1 for r in rows if r["n_followup_reps"])
    print(f"silver_hemolysis -> {n} isolates | beta-hemolytic (safety concern): {conc} | "
          f"clear/other: {n - conc} | undetermined: {undet}")
    print(f"                    policy '{POLICY}' | {resc} isolates carry a re-screen read")


if __name__ == "__main__":
    main()
