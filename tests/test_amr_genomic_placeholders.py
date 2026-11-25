"""
test_amr_genomic_placeholders.py -- `total_elements` must count elements, not screened isolates.

Alex's amrfinder.tsv records an isolate that ran through AMRFinderPlus and came back EMPTY as a
placeholder row whose every field except `ASMA_id` is the literal 'NA'. That row is a coverage
marker ("screened, zero hits"), not an element that was found. Counting it made `total_elements`
read 1 for an isolate that has nothing -- so the column did not mean what its name says. The
builder now skips it, while still emitting the isolate (screened-and-clean is a real answer, and
a different one from never-screened, which is absent from the table entirely).

  - GOLDEN: the placeholder detector on hand-written rows (data-free; must always pass).
  - REAL INVARIANTS: total_elements never below amr_gene_count; a screened-but-empty isolate
    reads 0, not 1; and no isolate is dropped by the skip.
  - SOURCE INTEGRITY: total_elements re-derived straight from the source file (counting the
    non-placeholder rows) matches the built column exactly.

The same 'NA' placeholder convention exists in the sibling metaVF.tsv; no builder reads that file
today, so if a virulence add-on is ever built it must reuse `is_no_hit_placeholder`.
"""
import os
import sys
import unittest
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build"))
import silver_amr_genomic as G     # noqa: E402
import data_sources as DS          # noqa: E402
import heuristic_shortlist as H    # noqa: E402  (reuse read_delimited)
from lib_ids import normalize_asma_id, read_delimited   # noqa: E402

SILVER = os.path.join(os.path.dirname(HERE), "data", "silver", "silver_amr_genomic.csv")
HAVE_SRC = DS.is_enabled("amr_genomic") and os.path.exists(G.SRC)

# A realistic (abridged) pair of source rows, keyed like the real header.
_REAL = {"ASMA_id": "ASMA-401", "Element symbol": "fosA", "Type": "AMR", "Class": "FOSFOMYCIN"}
_PLACEHOLDER = {"ASMA_id": "ASMA-125", "Element symbol": "NA", "Type": "NA", "Class": "NA"}


class TestPlaceholderDetector(unittest.TestCase):
    """Data-free: the rule is 'every field except ASMA_id is the literal NA'."""

    def test_all_na_row_is_a_placeholder(self):
        self.assertTrue(G.is_no_hit_placeholder(_PLACEHOLDER))

    def test_real_hit_is_not_a_placeholder(self):
        self.assertFalse(G.is_no_hit_placeholder(_REAL))

    def test_partially_na_row_is_not_a_placeholder(self):
        # A genuine hit may carry NA in some columns (e.g. no HMM match) -- still a real element.
        partial = dict(_REAL, Class="NA")
        self.assertFalse(G.is_no_hit_placeholder(partial))

    def test_asma_id_alone_does_not_make_a_placeholder(self):
        # Guard the vacuous all() -- a row with no other fields is malformed, not a no-hit marker.
        self.assertFalse(G.is_no_hit_placeholder({"ASMA_id": "ASMA-125"}))

    def test_an_na_asma_id_does_not_matter(self):
        # Only the non-id fields decide; the id column is never part of the test.
        self.assertFalse(G.is_no_hit_placeholder(dict(_REAL, ASMA_id="NA")))

    def test_whitespace_and_blanks(self):
        self.assertTrue(G.is_no_hit_placeholder({"ASMA_id": "ASMA-1", "Type": " NA ", "Class": "NA"}))
        self.assertFalse(G.is_no_hit_placeholder({"ASMA_id": "ASMA-1", "Type": "", "Class": "NA"}))


@unittest.skipUnless(os.path.exists(SILVER), "silver_amr_genomic not built -- run `bash build/run_all.sh`")
class TestSilverInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(H.read_delimited(SILVER, ","))

    def test_total_elements_is_never_below_amr_gene_count(self):
        # AMR genes are a subset of the elements counted, so this holds for any input.
        for r in self.rows:
            self.assertGreaterEqual(int(r["total_elements"]), int(r["amr_gene_count"]),
                                    msg=f"{r['asma_id']}: total_elements < amr_gene_count")

    def test_zero_elements_implies_zero_amr_genes(self):
        for r in self.rows:
            if int(r["total_elements"]) == 0:
                self.assertEqual(int(r["amr_gene_count"]), 0,
                                 msg=f"{r['asma_id']}: 0 elements but nonzero amr_gene_count")
                self.assertEqual(r["amr_classes"], "",
                                 msg=f"{r['asma_id']}: 0 elements but a class list")

    def test_ids_are_normalized_and_unique(self):
        ids = [r["asma_id"] for r in self.rows]
        self.assertTrue(all(a.startswith("ASMA-") for a in ids))
        self.assertEqual(len(ids), len(set(ids)), "duplicate asma_id in silver_amr_genomic")


@unittest.skipUnless(HAVE_SRC and os.path.exists(SILVER), "amrfinder source or silver table unavailable")
class TestAgainstSource(unittest.TestCase):
    """Re-derive the counts from the raw file -- independent of the builder's own bookkeeping."""

    @classmethod
    def setUpClass(cls):
        cls.built = {r["asma_id"]: r for r in H.read_delimited(SILVER, ",")}
        agg = defaultdict(lambda: {"real": 0, "placeholder": 0})
        for row in read_delimited(G.SRC):
            aid = normalize_asma_id(row.get("ASMA_id"))
            if not aid:
                continue
            agg[aid]["placeholder" if G.is_no_hit_placeholder(row) else "real"] += 1
        cls.src = dict(agg)

    def test_total_elements_equals_the_non_placeholder_row_count(self):
        for aid, counts in self.src.items():
            self.assertIn(aid, self.built, msg=f"{aid} in the source but missing from silver")
            self.assertEqual(int(self.built[aid]["total_elements"]), counts["real"],
                             msg=f"{aid}: total_elements != number of real source rows")

    def test_screened_but_empty_isolates_read_zero_not_one(self):
        # The actual regression: an isolate whose ONLY row is the 'NA' placeholder.
        empties = [a for a, c in self.src.items() if c["placeholder"] and not c["real"]]
        self.assertGreater(len(empties), 0, "no screened-but-empty isolates found -- source changed?")
        for aid in empties:
            self.assertEqual(int(self.built[aid]["total_elements"]), 0,
                             msg=f"{aid}: screened with zero hits but total_elements != 0")
            self.assertEqual(int(self.built[aid]["amr_gene_count"]), 0,
                             msg=f"{aid}: screened with zero hits but amr_gene_count != 0")

    def test_screened_but_empty_isolates_are_still_reported(self):
        # Skipping the row must not drop the isolate: screened-and-clean != never-screened.
        empties = {a for a, c in self.src.items() if c["placeholder"] and not c["real"]}
        missing = empties - set(self.built)
        self.assertEqual(missing, set(), msg=f"screened-but-empty isolates dropped: {sorted(missing)[:5]}")

    def test_every_built_row_traces_back_to_the_source(self):
        extra = set(self.built) - set(self.src)
        self.assertEqual(extra, set(), msg=f"silver rows with no source isolate: {sorted(extra)[:5]}")


# ---- since 2026-11-19 (PROTECT-61): Alex's 2026-11-10 compile -------------------------------------------
_PROV = {"assembly_type": "short-read", "assembler": "spades", "amrfinder_organism": "none",
         "run_mode": "adopted-legacy"}


class TestProvenanceColumns(unittest.TestCase):
    """Data-free: his four provenance columns are FILLED on a no-hit row and must not hide it."""

    def test_placeholder_with_filled_provenance_is_a_placeholder(self):
        self.assertTrue(G.is_no_hit_placeholder({**_PLACEHOLDER, **_PROV}))

    def test_real_hit_with_provenance_is_not_a_placeholder(self):
        self.assertFalse(G.is_no_hit_placeholder({**_REAL, **_PROV}))

    def test_provenance_alone_does_not_make_a_placeholder(self):
        self.assertFalse(G.is_no_hit_placeholder({"ASMA_id": "ASMA-1", **_PROV}))


class TestPointMutationSwitch(unittest.TestCase):
    """Data-free: config/thresholds.yaml safety.amr_genomic.count_point_mutations decides the gene count."""
    ROWS = [
        {"ASMA_id": "ASMA-7", "Type": "AMR", "Subtype": "AMR", "Class": "BETA-LACTAM", **_PROV},
        {"ASMA_id": "ASMA-7", "Type": "AMR", "Subtype": "POINT", "Class": "QUINOLONE", **_PROV},
        {"ASMA_id": "ASMA-7", "Type": "STRESS", "Subtype": "METAL", "Class": "", **_PROV},
        {"ASMA_id": "ASMA-8", "Element symbol": "NA", "Type": "NA", "Subtype": "NA", "Class": "NA", **_PROV},
    ]

    def test_genes_only(self):
        a = G.aggregate(self.ROWS, count_point_mutations=False)
        self.assertEqual((a["ASMA-7"]["amr"], a["ASMA-7"]["total"], a["ASMA-7"]["classes"]), (1, 3, {"BETA-LACTAM"}))
        self.assertEqual((a["ASMA-8"]["amr"], a["ASMA-8"]["total"]), (0, 0))   # screened, nothing found: zeros

    def test_point_mutations_counted(self):
        a = G.aggregate(self.ROWS, count_point_mutations=True)
        self.assertEqual((a["ASMA-7"]["amr"], a["ASMA-7"]["total"]), (2, 3))
        self.assertEqual(a["ASMA-7"]["classes"], {"BETA-LACTAM", "QUINOLONE"})

    def test_the_switch_is_a_boolean_and_its_documented_default(self):
        v = G.CFG["safety"]["amr_genomic"]["count_point_mutations"]
        self.assertIsInstance(v, bool)
        # False since 2026-11-19: genes only, the column's meaning before the rerun. Alex Styer, 2026-11-19: "Let's
        # leave the point mutations as a separate dataset (complementary to the original)." If you flip it on
        # purpose, update this line and say why in the commit.
        self.assertIs(v, False)


@unittest.skipUnless(HAVE_SRC and os.path.exists(SILVER), "amrfinder source or silver table unavailable")
class TestGeneCountAgainstSource(unittest.TestCase):
    """Re-derive amr_gene_count from the raw file without the builder's aggregate(), under the configured switch."""

    def test_amr_gene_count_matches_the_source(self):
        count_points = G.CFG["safety"]["amr_genomic"]["count_point_mutations"]
        built = {r["asma_id"]: r for r in H.read_delimited(SILVER, ",")}
        want = defaultdict(int)
        for row in read_delimited(G.SRC):
            aid = normalize_asma_id(row.get("ASMA_id"))
            if aid and row.get("Type", "").strip() == "AMR" and (
                    count_points or row.get("Subtype", "").strip() != "POINT"):
                want[aid] += 1
        for aid, r in built.items():
            self.assertEqual(int(r["amr_gene_count"]), want.get(aid, 0), msg=aid)


if __name__ == "__main__":
    unittest.main()
