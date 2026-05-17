"""BaseFetcher ABC + module-level REGISTRY singleton.

Every fetcher module should end with:
    REGISTRY.register(MyFetcher())
so that daily.py can iterate REGISTRY.enabled(cfg) and not hardcode sources.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Iterator

from pipeline.schema import Category, Item


class BaseFetcher(ABC):
    source_id: str = ""            # must match a key under config["sources"]
    category: Category = "learning"

    @abstractmethod
    def fetch(self, target_date: date) -> list[Item]:
        ...


class FetcherRegistry:
    def __init__(self) -> None:
        self._items: dict[str, BaseFetcher] = {}

    def register(self, fetcher: BaseFetcher) -> None:
        if not fetcher.source_id:
            raise ValueError(f"{fetcher.__class__.__name__}.source_id is empty")
        self._items[fetcher.source_id] = fetcher

    def get(self, source_id: str) -> BaseFetcher | None:
        return self._items.get(source_id)

    def all(self) -> Iterator[BaseFetcher]:
        return iter(self._items.values())

    def enabled(self, cfg: dict) -> Iterator[BaseFetcher]:
        sources_cfg = cfg.get("sources", {})
        for f in self._items.values():
            src = sources_cfg.get(f.source_id, {})
            if src.get("enabled", False):
                yield f


# Module-level singleton.
REGISTRY = FetcherRegistry()
