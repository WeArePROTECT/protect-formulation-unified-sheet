"""
test_units.py -- unit tests for the pure functions the decision engine relies on.

These are CONFIG-INDEPENDENT: they must pass no matter what the switchboard says. A bug
in any of these functions would silently corrupt every result, so they are tested directly.
Run via  bash tests/run_tests.sh  (or  python -m unittest discover -s tests).
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build"))
import heuristic_shortlist as H          # noqa: E402
from lib_ids import normalize_asma_id     # noqa: E402


class TestIdNormalizer(unittest.TestCase):
    """The single most important function: same strain from different files must line up."""

    def test_canonical_forms_all_map_to_one(self):
        for raw in ["ASMA-3913", "ASMA_3913", "asma3913", "  ASMA-3913 ", "ASMA-3913_priming"]:
            self.assertEqual(normalize_asma_id(raw), "ASMA-3913", msg=raw)

    def test_zero_padding_stripped(self):
        self.assertEqual(normalize_asma_id("ASMA-0007"), "ASMA-7")

    def test_non_asma_tokens_dropped(self):
        for raw in ["PA14_KEH108_Reporter", "PAO1", "blank", "", "NA", "none", "0", None]:
            self.assertIsNone(normalize_asma_id(raw), msg=repr(raw))


class TestParseTest(unittest.TestCase):
    def test_string_operand(self):
        self.assertEqual(H.parse_test("== N"), ("==", "N"))

    def test_numeric_operands(self):
        self.assertEqual(H.parse_test("<= 2"), ("<=", 2.0))
        self.assertEqual(H.parse_test(">= 0.1"), (">=", 0.1))
        self.assertEqual(H.parse_test(">5"), (">", 5.0))

    def test_malformed_raises(self):
        with self.assertRaises(ValueError):
            H.parse_test("N")             # no operator -> config typo -> must be caught


class TestGateResult(unittest.TestCase):
    def test_string_equality(self):
        self.assertIs(H.gate_result("N", "== N"), True)
        self.assertIs(H.gate_result("Y", "== N"), False)

    def test_numeric_thresholds(self):
        self.assertIs(H.gate_result("2", "<= 2"), True)
        self.assertIs(H.gate_result("3", "<= 2"), False)
        self.assertIs(H.gate_result("0.15", ">= 0.1"), True)

    def test_incomparable_returns_none(self):
        # a numeric test against a non-numeric present value cannot be judged -> None (not a crash)
        self.assertIsNone(H.gate_result("N", "<= 2"))


class TestRankValue(unittest.TestCase):
    def test_numbers_and_categoricals(self):
        self.assertEqual(H.rank_value("91.2"), 91.2)
        self.assertEqual(H.rank_value("Y"), 1.0)
        self.assertEqual(H.rank_value("N"), 0.0)
        self.assertEqual(H.rank_value("0"), 0.0)

    def test_unrankable_is_none(self):
        for v in ["", None, "foo"]:
            self.assertIsNone(H.rank_value(v), msg=repr(v))


class TestCellWithSource(unittest.TestCase):
    CRIT = {"column": "comp_best_team_pa", "column_fallback": "comp_best_solo_pa"}

    def test_primary_used_when_present(self):
        row = {"comp_best_team_pa": "90", "comp_best_solo_pa": "70"}
        self.assertEqual(H.cell_with_source(row, self.CRIT), ("90", "comp_best_team_pa"))

    def test_fallback_used_when_primary_blank(self):
        row = {"comp_best_team_pa": "", "comp_best_solo_pa": "70"}
        self.assertEqual(H.cell_with_source(row, self.CRIT), ("70", "comp_best_solo_pa"))

    def test_both_blank(self):
        row = {"comp_best_team_pa": "", "comp_best_solo_pa": ""}
        self.assertEqual(H.cell_with_source(row, self.CRIT), (None, None))

    def test_no_fallback_defined(self):
        row = {"grows_scfm": ""}
        self.assertEqual(H.cell_with_source(row, {"column": "grows_scfm"}), (None, None))


class TestSortKey(unittest.TestCase):
    ORDER = ["k"]

    def _sorted(self, higher, missing, evs):
        rbn = {"k": {"name": "k", "higher_is_better": higher, "missing": missing}}
        return sorted(evs, key=lambda e: H.sort_key(e, self.ORDER, rbn))

    def test_higher_is_better_and_missing_last(self):
        hi = {"keys": {"k": 90.0}, "tag": "hi"}
        lo = {"keys": {"k": 50.0}, "tag": "lo"}
        mi = {"keys": {"k": None}, "tag": "mi"}
        order = [e["tag"] for e in self._sorted(True, "rank_last", [lo, mi, hi])]
        self.assertEqual(order, ["hi", "lo", "mi"])

    def test_lower_is_better(self):
        hi = {"keys": {"k": 90.0}, "tag": "hi"}
        lo = {"keys": {"k": 50.0}, "tag": "lo"}
        order = [e["tag"] for e in self._sorted(False, "rank_last", [hi, lo])]
        self.assertEqual(order, ["lo", "hi"])

    def test_missing_first_policy(self):
        hi = {"keys": {"k": 90.0}, "tag": "hi"}
        mi = {"keys": {"k": None}, "tag": "mi"}
        order = [e["tag"] for e in self._sorted(True, "rank_first", [hi, mi])]
        self.assertEqual(order, ["mi", "hi"])


class TestTinyHelpers(unittest.TestCase):
    def test_as_number(self):
        self.assertEqual(H.as_number("3"), 3.0)
        self.assertIsNone(H.as_number("x"))
        self.assertIsNone(H.as_number(None))

    def test_int_helper(self):
        self.assertEqual(H._int("3.0"), 3)
        self.assertEqual(H._int(""), 0)
        self.assertEqual(H._int(None), 0)

    def test_is_blank(self):
        self.assertTrue(H.is_blank(None))
        self.assertTrue(H.is_blank("   "))
        self.assertFalse(H.is_blank("x"))

    def test_fmt(self):
        self.assertEqual(H.fmt("91.20"), "91.2")
        self.assertEqual(H.fmt("Y"), "Y")


if __name__ == "__main__":
    unittest.main()
