"""v3 aggregator: weekly + monthly rollups. Stub interface defined now so that
docs/SPEC §12 commitments are visible in the codebase; bodies fill in v3.
"""
from datetime import date
from pathlib import Path


_AGGREGATES_DIR = Path(__file__).parent.parent / "data" / "aggregates"


def build_weekly(end_date: date) -> dict:
    """Aggregate the 7-day window ending on `end_date` into a weekly summary.

    v3 will:
      1. Load 7 days of data/summaries/*.json + data/processed/*.json
      2. Call LLM to cluster topics + produce a 7-day narrative
      3. Return {"week": "2026-W20", "narrative": "...", "highlights": [...], "stats": {...}}
    """
    raise NotImplementedError("weekly aggregator lands in v3")


def build_monthly(year: int, month: int) -> dict:
    """Aggregate one calendar month from daily summaries.

    v3 will read data/summaries/<year>-<month>-*.json and produce a trend report.
    """
    raise NotImplementedError("monthly aggregator lands in v3")


def aggregates_dir() -> Path:
    return _AGGREGATES_DIR
