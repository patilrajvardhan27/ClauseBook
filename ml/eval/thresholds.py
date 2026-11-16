"""Loads eval/thresholds.yaml once, so the CLI and CI read identical gates."""
from __future__ import annotations

from pathlib import Path

import yaml

THRESHOLDS_PATH = Path("eval/thresholds.yaml")


def load_thresholds() -> dict:
    return yaml.safe_load(THRESHOLDS_PATH.read_text())
