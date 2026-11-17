"""
lib_retractions.py — drop retracted rows from one of Sun-Young Kim's workbook tabs, by asma_id.

The lakehouse pipeline's datasets/phenotype/retractions.csv lists source rows deliberately dropped, one
line each with its reason, and the phenotype export reads the SAME file, so the card and
protect.phenotype drop the same rows. silver_hemolysis.py handles Cassandra Reyes's sheet, whose lines
match on asma_id + FS plate + FS well. This module handles Sun-Young's tabs, which have no plate or well:
their lines say match_on = asma_id. Each line must match exactly its expected rows or the build stops,
because a mismatch means the source changed under the retraction (if Sun-Young drops the rows at
source, the line matches 0 and must be deleted). Added 2026-11-16 for ASMA-1448 (PROTECT-59).
"""
import csv
import os
from collections import Counter


def load(path, source_path, sheet):
    """{asma_id: line} for this workbook (matched by file NAME) and sheet. No path configured = none."""
    if not path:
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for ln in csv.DictReader(fh):
            if ln["source_file"] != os.path.basename(source_path) or ln["sheet"] != sheet:
                continue
            if ln.get("match_on") != "asma_id":
                raise ValueError(f"retraction {ln['asma_id']} on {sheet!r} has match_on {ln.get('match_on')!r}; "
                                 f"this sheet has no plate or well, so it must match on asma_id alone")
            if ln["asma_id"] in out:
                raise ValueError(f"retraction {ln['asma_id']} on {sheet!r} is listed twice")
            out[ln["asma_id"]] = ln
    return out


class Tracker:
    """Counts the rows each retraction line drops, and proves each matched exactly its expected rows."""

    def __init__(self, lines, label):
        self.lines, self.label, self.hits = lines, label, Counter()

    def drop(self, raw_asma_id):
        """True if this row is retracted. Matches the id exactly as the source writes it, as the
        lakehouse export does, never a normalised form."""
        key = str(raw_asma_id or "").strip()
        if key in self.lines:
            self.hits[key] += 1
            return True
        return False

    def verify(self):
        for aid, ln in self.lines.items():
            if self.hits[aid] != int(ln["expected_rows"]):
                raise ValueError(f"retraction {aid} on {self.label} matched {self.hits[aid]} rows, expected "
                                 f"{ln['expected_rows']}; the source changed under it, stop and look")
            print(f"{self.label} -> RETRACTED {self.hits[aid]} rows: {aid} ({ln['ticket']})")
