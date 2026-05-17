"""Registry collects fetchers by source_id and exposes iteration."""
from datetime import date

import pytest

from fetchers.base import BaseFetcher, FetcherRegistry
from pipeline.schema import Item


class _StubFetcher(BaseFetcher):
    source_id = "stub"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        return [Item(id="x", source="arxiv", title="t", url="u")]


def test_can_subclass_and_fetch():
    f = _StubFetcher()
    items = f.fetch(date(2026, 5, 17))
    assert len(items) == 1


def test_registry_register_and_lookup():
    reg = FetcherRegistry()
    f = _StubFetcher()
    reg.register(f)
    assert reg.get("stub") is f
    assert list(reg.all()) == [f]


def test_registry_filters_by_enabled_in_config():
    reg = FetcherRegistry()
    reg.register(_StubFetcher())
    cfg = {"sources": {"stub": {"enabled": False}}}
    assert list(reg.enabled(cfg)) == []
    cfg = {"sources": {"stub": {"enabled": True}}}
    assert len(list(reg.enabled(cfg))) == 1


def test_registry_unknown_source_treated_as_disabled():
    reg = FetcherRegistry()
    reg.register(_StubFetcher())
    cfg = {"sources": {}}                    # stub absent
    assert list(reg.enabled(cfg)) == []


def test_base_fetcher_requires_source_id_and_category():
    class Bad(BaseFetcher):
        pass
    with pytest.raises((TypeError, NotImplementedError)):
        Bad().fetch(date.today())
