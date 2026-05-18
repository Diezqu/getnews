"""Tests for ArxivFetcher using the arxiv.py library."""
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_result(
    entry_id="http://arxiv.org/abs/2405.12345v1",
    title="LLM Agent Survey",
    summary="This paper surveys LLM agents in detail.",
    categories=None,
    authors=None,
):
    r = MagicMock()
    r.entry_id = entry_id
    r.title = title
    r.summary = summary
    r.published = datetime(2026, 5, 17, tzinfo=timezone.utc)
    r.categories = categories or ["cs.AI", "cs.LG"]
    r.authors = [MagicMock(name=n) for n in (authors or ["Alice", "Bob"])]
    for mock_author, name in zip(r.authors, (authors or ["Alice", "Bob"])):
        mock_author.name = name
    return r


def test_fetch_returns_items_for_each_result():
    """Each arxiv.Result maps to one Item."""
    mock_result = _make_mock_result()

    with patch("fetchers.arxiv_fetcher.arxiv.Client") as MockClient:
        MockClient.return_value.results.return_value = iter([mock_result])
        from fetchers.arxiv_fetcher import ArxivFetcher
        items = ArxivFetcher().fetch(date(2026, 5, 17))

    assert len(items) == 1
    assert items[0].source == "arxiv"
    assert items[0].category == "learning"


def test_fetch_maps_title_and_url():
    """Title and URL are copied from the arxiv.Result."""
    mock_result = _make_mock_result(
        entry_id="http://arxiv.org/abs/2405.99999v2",
        title="Multi-Agent RAG Systems",
    )

    with patch("fetchers.arxiv_fetcher.arxiv.Client") as MockClient:
        MockClient.return_value.results.return_value = iter([mock_result])
        from fetchers.arxiv_fetcher import ArxivFetcher
        items = ArxivFetcher().fetch(date(2026, 5, 17))

    assert items[0].title == "Multi-Agent RAG Systems"
    assert "arxiv.org" in items[0].url


def test_fetch_returns_empty_list_on_exception():
    """Network or API errors produce an empty list, not a crash."""
    with patch("fetchers.arxiv_fetcher.arxiv.Client") as MockClient:
        MockClient.return_value.results.side_effect = Exception("connection refused")
        from fetchers.arxiv_fetcher import ArxivFetcher
        items = ArxivFetcher().fetch(date(2026, 5, 17))

    assert items == []


def test_client_uses_3s_delay():
    """Client is constructed with delay_seconds=3.0 to respect arXiv ToS."""
    with patch("fetchers.arxiv_fetcher.arxiv.Client") as MockClient:
        MockClient.return_value.results.return_value = iter([])
        from fetchers.arxiv_fetcher import ArxivFetcher
        ArxivFetcher().fetch(date(2026, 5, 17))

    call_kwargs = MockClient.call_args
    assert call_kwargs is not None
    kwargs = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
    assert kwargs.get("delay_seconds", 0) >= 3.0
