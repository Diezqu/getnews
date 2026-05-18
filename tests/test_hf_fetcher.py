"""Tests for HFFetcher date-fallback logic."""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _make_response(papers: list) -> MagicMock:
    """Return a mock requests.Response whose .json() yields papers."""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = papers
    return resp


def _make_paper(title: str = "Test Paper", arxiv_id: str = "2405.00001") -> dict:
    return {
        "paper": {
            "id": arxiv_id,
            "title": title,
            "summary": "An abstract.",
            "authors": [{"name": "Alice"}],
        },
        "upvotes": 10,
    }


TARGET = date(2026, 5, 18)  # a Monday


class TestHFFetcher:
    def test_fetch_returns_items_on_weekday(self):
        """When target_date has papers, return them without fallback."""
        papers = [_make_paper("Paper A", "2405.00001"), _make_paper("Paper B", "2405.00002")]
        response = _make_response(papers)

        with patch("fetchers.hf_fetcher.requests.get", return_value=response) as mock_get:
            from fetchers.hf_fetcher import HFFetcher
            items = HFFetcher().fetch(TARGET)

        assert len(items) == 2
        assert items[0].source == "hf_papers"
        # Should only have made one request (no fallback needed)
        assert mock_get.call_count == 1
        called_params = mock_get.call_args[1]["params"]
        assert called_params["date"] == TARGET.isoformat()

    def test_fetch_falls_back_when_today_empty(self):
        """When target_date returns [], fall back to target_date - 1 day."""
        yesterday = TARGET - timedelta(days=1)
        papers_yesterday = [_make_paper("Paper C", "2405.00003")]

        def side_effect(url, params, timeout):
            if params["date"] == TARGET.isoformat():
                return _make_response([])
            if params["date"] == yesterday.isoformat():
                return _make_response(papers_yesterday)
            return _make_response([])

        with patch("fetchers.hf_fetcher.requests.get", side_effect=side_effect):
            from fetchers.hf_fetcher import HFFetcher
            items = HFFetcher().fetch(TARGET)

        assert len(items) == 1
        assert items[0].title == "Paper C"

    def test_fetch_returns_empty_after_5_day_fallback(self):
        """When all 5 candidate days return [], return [] and log warning."""
        empty_response = _make_response([])

        with patch("fetchers.hf_fetcher.requests.get", return_value=empty_response) as mock_get, \
             patch("builtins.print") as mock_print:
            from fetchers.hf_fetcher import HFFetcher
            items = HFFetcher().fetch(TARGET)

        assert items == []
        # Should have tried exactly 5 dates (offset 0–4)
        assert mock_get.call_count == 5
        # Should have printed a warning
        warning_printed = any(
            "warn" in str(call).lower() or "fallback" in str(call).lower()
            for call in mock_print.call_args_list
        )
        assert warning_printed, "Expected a warning to be printed after 5-day fallback"

    def test_fetch_logs_fallback_date(self, capsys):
        """When falling back, a message naming the fallback date is printed."""
        yesterday = TARGET - timedelta(days=1)
        papers_yesterday = [_make_paper("Paper D", "2405.00004")]

        def side_effect(url, params, timeout):
            if params["date"] == TARGET.isoformat():
                return _make_response([])
            if params["date"] == yesterday.isoformat():
                return _make_response(papers_yesterday)
            return _make_response([])

        with patch("fetchers.hf_fetcher.requests.get", side_effect=side_effect):
            from fetchers.hf_fetcher import HFFetcher
            HFFetcher().fetch(TARGET)

        captured = capsys.readouterr()
        assert yesterday.isoformat() in captured.out, (
            f"Expected fallback date {yesterday.isoformat()} to appear in stdout"
        )
