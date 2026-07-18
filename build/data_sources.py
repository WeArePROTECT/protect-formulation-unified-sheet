"""
data_sources.py — single access point for the team-owned data registry
(config/data_sources.yaml). This is the "what data is plugged in" layer.

Builders read their input path/sheet through here instead of hard-coding it, so swapping a
data version or turning a source off is a one-line edit in the YAML, never a code change:

    from data_sources import source, is_enabled
    if not is_enabled("hemolysis"):
        return
    info = source("hemolysis")
    rows = read_xlsx_sheet(info["path"], info.get("sheet"))

`validate()` enforces that a `required: true` source is never disabled (the roster backbone).
`provides_map()` / `disabled_columns()` let the shortlist engine warn when a decision criterion
depends on a column whose source is turned off, so an off switch can never silently skew a ranking.
"""
import os

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "data_sources.yaml")


def load(path=_PATH):
    import yaml
    with open(path) as fh:
        return yaml.safe_load(fh)


REGISTRY = load()
SOURCES = REGISTRY.get("sources", {})


def source(name):
    """The registry entry for a source (raises if the name is unknown -> config typo caught)."""
    if name not in SOURCES:
        raise KeyError(f"no data source '{name}' in config/data_sources.yaml "
                       f"(known: {', '.join(sorted(SOURCES))})")
    return SOURCES[name]


def is_enabled(name):
    return bool(source(name).get("enabled", True))


def enabled_sources():
    return {k: v for k, v in SOURCES.items() if v.get("enabled", True)}


def validate():
    """A required source must never be disabled. Call once at the start of a build."""
    bad = [k for k, v in SOURCES.items() if v.get("required") and not v.get("enabled", True)]
    if bad:
        raise ValueError(f"required data source(s) disabled in data_sources.yaml: {', '.join(bad)} "
                         f"(the roster/backbone cannot be turned off)")


def provides_map():
    """{gold_column: source_name} across ALL sources (enabled or not)."""
    out = {}
    for name, s in SOURCES.items():
        for col in (s.get("provides") or []):
            out[col] = name
    return out


def disabled_columns():
    """Gold columns whose (only) source is currently disabled — used to flag dangling criteria."""
    return {col: name for col, name in provides_map().items() if not is_enabled(name)}
