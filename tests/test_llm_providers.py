"""LLM provider abstraction + three prompt templates."""
import pytest

from pipeline.schema import Item
from pipeline.llm import (
    get_provider,
    MockProvider,
    summarize_all,
    summarize_daily,
)


def test_mock_provider_returns_raw_content_for_summary():
    p = MockProvider()
    item = Item(id="x", source="arxiv", category="learning",
                title="t", url="u", raw_content="some abstract here")
    out = p.summarize_item(item)
    assert "some abstract" in out


def test_mock_provider_daily_returns_valid_structure():
    p = MockProvider()
    items = [Item(id="x", source="arxiv", category="learning",
                  title="agent paper", url="u")]
    daily = p.summarize_daily(items)
    assert set(daily.keys()) == {"headline", "ai_trends", "job_signals"}
    assert len(daily["ai_trends"]) == 3
    assert len(daily["job_signals"]) == 3


def test_summarize_all_fills_empty_summaries():
    items = [
        Item(id="1", source="arxiv", category="learning",
             title="t1", url="u1", raw_content="abstract one"),
        Item(id="2", source="arxiv", category="learning",
             title="t2", url="u2", raw_content="abstract two", summary="already done"),
    ]
    out = summarize_all(items, provider=MockProvider())
    assert out[0].summary != ""
    assert out[1].summary == "already done"  # unchanged


def test_summarize_daily_returns_dict():
    items = [Item(id="x", source="arxiv", category="learning",
                  title="t", url="u")]
    daily = summarize_daily(items, provider=MockProvider())
    assert isinstance(daily, dict)
    assert "headline" in daily


def test_get_provider_returns_mock_when_configured(monkeypatch, repo_root):
    monkeypatch.chdir(repo_root)
    from pipeline.config import get_config
    get_config.cache_clear()
    # We can't easily change config.yaml from a test, so test get_provider("mock") direct
    p = get_provider("mock")
    assert isinstance(p, MockProvider)
