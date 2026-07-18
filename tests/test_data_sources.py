"""
test_data_sources.py -- the data registry (config/data_sources.yaml) and its switches.

Covers the "what data is plugged in" layer:
  - PROVENANCE / CURRENCY: every enabled source's path actually exists on the server (catches a
    moved/renamed/old file immediately -- exactly the "did we pull from the wrong spot" guard).
  - required sources cannot be disabled (the roster backbone).
  - the provides -> gold-column declarations are internally consistent.
  - the on/off switch is observable: disabling a source surfaces its columns as "disabled", and the
    shortlist engine's guard flags a criterion that would then silently do nothing.
"""
import contextlib
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "build"))
import data_sources as DS            # noqa: E402
import heuristic_shortlist as H      # noqa: E402

ON_SERVER = os.path.isdir("/usr2/people/protect")


@contextlib.contextmanager
def temporarily(name, **changes):
    """Temporarily patch a registry entry (restored afterwards) so switch behavior is testable."""
    orig = dict(DS.SOURCES[name])
    DS.SOURCES[name].update(changes)
    try:
        yield
    finally:
        DS.SOURCES[name].clear()
        DS.SOURCES[name].update(orig)


class TestProvenance(unittest.TestCase):
    @unittest.skipUnless(ON_SERVER, "off-server: source paths not mounted")
    def test_every_enabled_source_path_exists(self):
        for name, s in DS.enabled_sources().items():
            path = s.get("path")
            self.assertTrue(path and os.path.exists(path),
                            msg=f"source '{name}' path missing (moved/renamed/old?): {path}")
            for f in (s.get("files") or []):
                fp = os.path.join(path, f)
                self.assertTrue(os.path.exists(fp), msg=f"source '{name}' file missing: {fp}")


class TestRequiredSources(unittest.TestCase):
    def test_validate_passes_as_shipped(self):
        DS.validate()                # the shipped registry must be valid

    def test_disabling_a_required_source_raises(self):
        req = next(k for k, v in DS.SOURCES.items() if v.get("required"))
        with temporarily(req, enabled=False):
            with self.assertRaises(ValueError):
                DS.validate()


class TestProvidesDeclarations(unittest.TestCase):
    GOLD_CARD = H.GOLD_CARD

    @unittest.skipUnless(os.path.exists(H.GOLD_CARD), "gold card not built")
    def test_provides_columns_are_all_present_or_all_absent(self):
        # A wired source's provides columns should all be in the card; a not-yet-built source's
        # (e.g. the Emma relevance sources) should all be absent. A MIX means a typo in `provides`.
        header = next(iter(H.read_delimited(self.GOLD_CARD, ",")), {})
        cols = set(header.keys())
        for name, s in DS.SOURCES.items():
            prov = s.get("provides") or []
            if not prov:
                continue
            present = [c for c in prov if c in cols]
            self.assertIn(len(present), (0, len(prov)),
                          msg=f"source '{name}' provides {prov} but only {present} are in the card (typo?)")

    def test_provides_map_is_one_source_per_column(self):
        # No two sources should claim the same gold column.
        seen = {}
        for name, s in DS.SOURCES.items():
            for col in (s.get("provides") or []):
                self.assertNotIn(col, seen, msg=f"column '{col}' claimed by both '{seen.get(col)}' and '{name}'")
                seen[col] = name


class TestOnOffSwitch(unittest.TestCase):
    def test_disabled_columns_reflects_the_switch(self):
        # Pick any non-required source that actually provides a column.
        name = next(k for k, v in DS.SOURCES.items()
                    if not v.get("required") and (v.get("provides")))
        col = DS.SOURCES[name]["provides"][0]
        self.assertNotIn(col, DS.disabled_columns())      # enabled by default
        with temporarily(name, enabled=False):
            self.assertEqual(DS.disabled_columns().get(col), name)

    def test_engine_guard_flags_a_dangling_criterion(self):
        name = next(k for k, v in DS.SOURCES.items()
                    if not v.get("required") and (v.get("provides")))
        col = DS.SOURCES[name]["provides"][0]
        cfg = {"criteria": [{"name": "depends_on_off", "column": col, "mode": "gate", "pass_when": ">= 0"}]}
        with temporarily(name, enabled=False):
            hits = H.check_source_availability(cfg)
        self.assertTrue(any(h[2] == col and h[3] == name for h in hits),
                        msg="engine did not flag a criterion pointing at a disabled source")


if __name__ == "__main__":
    unittest.main()
