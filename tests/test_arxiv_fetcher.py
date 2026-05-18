"""Tests for ArxivFetcher using feedparser + arXiv RSS feed."""
import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_entry(
    title="LLM Agent Survey",
    link="https://arxiv.org/abs/2405.12345",
    entry_id="oai:arXiv.org:2405.12345",
    description="arXiv:2405.12345 Announce Type: new\nAbstract: This paper surveys LLM agents in detail.",
    author="Alice Wang, Bob Zhang",
    published_parsed=None,
    tags=None,
    arxiv_announce_type="new",
):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.id = entry_id
    entry.description = description
    entry.author = author
    entry.published_parsed = published_parsed or time.strptime("Sun, 18 May 2026 00:00:00 +0000", "%a, %d %b %Y %H:%M:%S %z")
    entry.tags = tags if tags is not None else [{"term": "cs.AI"}, {"term": "cs.LG"}]
    entry.get = MagicMock(side_effect=lambda k, default="": {
        "author": author,
        "tags": entry.tags,
        "arxiv_announce_type": arxiv_announce_type,
    }.get(k, default))
    return entry


def _make_mock_feed(entries):
    feed = MagicMock()
    feed.entries = entries
    return feed


def test_fetch_returns_items_for_each_result():
    """Each RSS entry maps to one Item."""
    mock_entry = _make_mock_entry()
    mock_feed = _make_mock_feed([mock_entry])

    with patch("fetchers.arxiv_fetcher.feedparser.parse", return_value=mock_feed):
        from fetchers.arxiv_fetcher import ArxivFetcher
        items = ArxivFetcher().fetch(date(2026, 5, 18))

    assert len(items) == 1
    assert items[0].source == "arxiv"
    assert items[0].category == "learning"


def test_fetch_maps_title_and_url():
    """Title and URL are copied from the RSS entry."""
    mock_entry = _make_mock_entry(
        title="Multi-Agent RAG Systems",
        link="https://arxiv.org/abs/2405.99999",
    )
    mock_feed = _make_mock_feed([mock_entry])

    with patch("fetchers.arxiv_fetcher.feedparser.parse", return_value=mock_feed):
        from fetchers.arxiv_fetcher import ArxivFetcher
        items = ArxivFetcher().fetch(date(2026, 5, 18))

    assert items[0].title == "Multi-Agent RAG Systems"
    assert "arxiv.org" in items[0].url


def test_fetch_returns_empty_list_on_exception():
    """Network or parse errors produce an empty list, not a crash."""
    with patch("fetchers.arxiv_fetcher.feedparser.parse", side_effect=Exception("connection refused")):
        from fetchers.arxiv_fetcher import ArxivFetcher
        items = ArxivFetcher().fetch(date(2026, 5, 18))

    assert items == []


def test_fetch_uses_correct_category_url():
    """feedparser.parse is called with the RSS URL built from config categories."""
    mock_feed = _make_mock_feed([])

    with patch("fetchers.arxiv_fetcher.feedparser.parse", return_value=mock_feed) as mock_parse:
        from fetchers.arxiv_fetcher import ArxivFetcher
        ArxivFetcher().fetch(date(2026, 5, 18))

    called_url = mock_parse.call_args[0][0]
    assert called_url.startswith("https://rss.arxiv.org/rss/")
    assert "cs.AI" in called_url or "cs.LG" in called_url
