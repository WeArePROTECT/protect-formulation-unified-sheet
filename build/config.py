"""
config.py — single access point for the team-owned thresholds in config/thresholds.yaml.

Scientists change values in the YAML; every build script reads them through here, so no
threshold is ever hard-coded in more than one place. Import `CFG` and read what you need:

    from config import CFG
    cutoff = CFG["safety"]["amr_measured"]["resistance_cutoff_pct"]
"""
import os

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "thresholds.yaml")


def load(path=_PATH):
    import yaml  # PyYAML (already used by the manifest tooling on this host)
    with open(path) as fh:
        return yaml.safe_load(fh)


CFG = load()
