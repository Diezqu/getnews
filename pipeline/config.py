"""YAML config loader — cached so repeated calls are free.

Usage:
    from pipeline.config import get_config
    cfg = get_config()
    weight = cfg["scoring"]["learning"]["agent"]
"""
from functools import lru_cache
from pathlib import Path

import yaml


_DEFAULT_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config(path: Path | str = _DEFAULT_PATH) -> dict:
    """Load YAML from the given path. Raises FileNotFoundError if missing."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Cached singleton accessor for the default config path."""
    return load_config(_DEFAULT_PATH)
