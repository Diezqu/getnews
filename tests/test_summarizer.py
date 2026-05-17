"""Summarizer writes daily summary JSON to data/summaries/<date>.json."""
import json
from datetime import date
from pathlib import Path

import pytest

from pipeline.schema import Item
from pipeline.summarizer import build_daily_summary, write_summary


def test_build_daily_summary_includes_stats():
    items = [
        Item(id="1", source="arxiv", category="learning", title="A", url="u1", score=8.5),
        Item(id="2", source="nowcoder", category="job", title="B", url="u2", score=9.5),
        Item(id="3", source="hf_papers", category="learning", title="C", url="u3", score=6.0),
    ]
    summary = build_daily_summary(items, llm_provider="mock", target_date=date(2026, 5, 17))
    assert summary["date"] == "2026-05-17"
    assert summary["stats"]["total_items"] == 3
    assert summary["stats"]["learning_count"] == 2
    assert summary["stats"]["job_count"] == 1
    assert summary["stats"]["top_score"] == 9.5
    assert summary["stats"]["top_item_title"] == "B"
    assert summary["headline"]
    assert len(summary["ai_trends"]) == 3
    assert len(summary["job_signals"]) == 3


def test_write_summary_creates_file(tmp_path: Path):
    s = {"date": "2026-05-17", "headline": "h", "ai_trends": [], "job_signals": [], "stats": {}}
    out = write_summary(s, summaries_dir=tmp_path)
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8"))["headline"] == "h"


def test_build_summary_handles_empty_items():
    summary = build_daily_summary([], llm_provider="mock", target_date=date(2026, 5, 17))
    assert summary["stats"]["total_items"] == 0
    assert summary["stats"]["top_item_title"] == "—"
