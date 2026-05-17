"""Derived fetcher: filter already-collected HN / HF / GitHub items for AI-coding-tool
adoption signals (Cursor / Claude Code / Cline / Aider / Copilot mentions).

Unlike other fetchers, this one does NO network calls. daily.py must populate
`pool` before calling .fetch(). The output reuses the original item's title/url
but re-tags it under source='coding_tool' and category='job'.
"""
import hashlib
from datetime import date

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item


class CodingToolFetcher(BaseFetcher):
    source_id = "coding_tool"
    category = "job"

    # daily.py mutates this between the main fetcher loop and calling .fetch()
    pool: list[Item] = []

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["coding_tool"]
        keywords = [k.lower() for k in cfg.get("keywords", [])]
        max_items = cfg.get("max_items", 5)

        results: list[Item] = []
        for src_item in self.pool:
            if src_item.source not in {"hackernews", "hf_papers", "github"}:
                continue
            haystack = (src_item.title + " " + src_item.raw_content).lower()
            matched = [k for k in keywords if k in haystack]
            if not matched:
                continue
            derived_url = src_item.url + "#coding_tool"  # disambiguate from original
            new_id = hashlib.sha1(derived_url.encode()).hexdigest()[:12]
            results.append(Item(
                id=new_id,
                source="coding_tool",
                category="job",
                title=src_item.title,
                url=derived_url,
                raw_content=src_item.raw_content,
                stars=src_item.stars,
                tags=[m.title() for m in matched[:3]] + [f"来源: {src_item.source}"],
                authors=src_item.authors,
                published_at=src_item.published_at,
            ))
        results.sort(key=lambda x: -x.stars)
        return results[:max_items]


REGISTRY.register(CodingToolFetcher())
