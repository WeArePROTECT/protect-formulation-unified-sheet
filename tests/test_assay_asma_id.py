"""
test_assay_asma_id.py -- the assay_asma_id column (the arrayed isolate used in the wet-lab assays).

assay_asma_id is the isolate common to EVERY phenotype assay (growth / measured-AMR / hemolysis) that
ran for a strain group -- the arrayed, validated stock the experimentalists actually work with, which
often differs from the genomic representative_asma_id. Built in gold_unified_sheet.py; documented in
docs/assay_asma_id_lookup.md.

Guarantees:
  - STRUCTURE: every assay_asma_id isolate is a real member of its strain group.
  - NO FABRICATION: every assay_asma_id isolate actually appears in one of the assay silver tables.
  - CORRECTNESS: assay_asma_id == the set-intersection of the members present across the assays that
    ran for the group, re-derived here straight from the silver tables (not from the builder's code).
  - COVERAGE: some groups resolve an assay isolate, and some genuinely differ from the genomic rep
    (else the column would carry no information).
"""
import os
import sys
import unittest
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build"))
import data_sources as DS          # noqa: E402
import heuristic_shortlist as H     # noqa: E402  (reuse read_delimited)

ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "data", "reference")
SILVER = os.path.join(ROOT, "data", "silver")
GOLD = os.path.join(ROOT, "data", "gold", "gold_unified_sheet.csv")

# (source key, silver file) for the three phenotype assays that define the assay isolate.
ASSAY_SOURCES = [
    ("growth_endpoint", "silver_growth_endpoint.csv"),
    ("amr_measured", "silver_amr_measured.csv"),
    ("hemolysis", "silver_hemolysis.csv"),
]


def _asma_num(a):
    try:
        return int(str(a).split("-")[1])
    except (IndexError, ValueError):
        return 0


def _members():
    mem = defaultdict(set)
    for r in H.read_delimited(os.path.join(REF, "identity_isolates.csv"), ","):
        mem[r["strain_group"]].add(r["asma_id"])
    return mem


def _assay_keysets():
    """Isolate-id set for each enabled+present assay table (mirrors the builder's source selection)."""
    sets = []
    for key, fname in ASSAY_SOURCES:
        p = os.path.join(SILVER, fname)
        if DS.is_enabled(key) and os.path.exists(p):
            s = {r["asma_id"] for r in H.read_delimited(p, ",")}
            if s:
                sets.append(s)
    return sets


@unittest.skipUnless(os.path.exists(GOLD), "gold card not built -- run `bash build/run_all.sh` first")
class TestAssayAsmaId(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(H.read_delimited(GOLD, ","))
        cls.mem = _members()
        cls.keysets = _assay_keysets()
        cls.union = set().union(*cls.keysets) if cls.keysets else set()

    def _ids(self, r):
        v = (r.get("assay_asma_id") or "").strip()
        return v.split(";") if v else []

    def _gmembers(self, r):
        # mirror the builder's fallback: a group absent from identity_isolates uses its representative
        return self.mem.get(r["strain_group"]) or {r["representative_asma_id"]}

    def test_assay_isolate_is_a_group_member(self):
        for r in self.rows:
            for a in self._ids(r):
                self.assertIn(a, self._gmembers(r),
                              msg=f"{r['strain_group']}: assay isolate {a} is not a member of the group")

    def test_assay_isolate_was_actually_assayed(self):
        for r in self.rows:
            for a in self._ids(r):
                self.assertIn(a, self.union,
                              msg=f"{r['strain_group']}: assay isolate {a} is in no assay silver table")

    def test_matches_independent_intersection(self):
        # Re-derive assay_asma_id straight from the silver tables; the card must match exactly.
        for r in self.rows:
            members = self._gmembers(r)
            present = [ks & members for ks in self.keysets]
            present = [p for p in present if p]
            expected = sorted(set.intersection(*present), key=_asma_num) if present else []
            self.assertEqual(self._ids(r), expected,
                             msg=f"{r['strain_group']}: assay_asma_id != intersection of its assays")

    def test_coverage_and_divergence(self):
        resolved = [r for r in self.rows if self._ids(r)]
        differ = [r for r in resolved if r["assay_asma_id"] != r["representative_asma_id"]]
        self.assertGreater(len(resolved), 0, "no group resolved an assay isolate -- assays unbuilt?")
        self.assertGreater(len(differ), 0, "no assay isolate differs from the rep -- column adds nothing")


if __name__ == "__main__":
    unittest.main()
