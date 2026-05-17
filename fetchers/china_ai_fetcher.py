"""Fetch Chinese AI company news from aggregator sites (机器之心 / 量子位 etc),
then filter entries that mention any of our target companies.
"""
import hashlib
import re
from datetime import date

import feedparser

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item


class ChinaAIFetcher(BaseFetcher):
    source_id = "china_ai"
    category = "job"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["china_ai"]
        feeds = cfg.get("feeds", [])
        targets = [t.lower() for t in cfg.get("target_companies", [])]
        max_items = cfg.get("max_items", 15)

        all_items: list[Item] = []
        for feed_cfg in feeds:
            name = feed_cfg.get("name", "")
            url = feed_cfg.get("url", "")
            try:
                feed = feedparser.parse(url)
            except Exception as e:
                print(f"  [warn] china_ai feed '{name}' failed: {e}")
                continue
            if feed.bozo and not feed.entries:
                print(f"  [warn] china_ai feed '{name}' empty")
                continue
            for entry in feed.entries:
                item = _entry_to_item(entry, source_name=name, targets=targets)
                if item:
                    all_items.append(item)
        # Newest first
        all_items.sort(key=lambda x: x.published_at, reverse=True)
        return all_items[:max_items]


def _entry_to_item(entry, *, source_name: str, targets: list[str]) -> Item | None:
    title = (getattr(entry, "title", "") or "").strip()
    link = (getattr(entry, "link", "") or "").strip()
    if not title or not link:
        return None
    body_html = getattr(entry, "summary", "") or getattr(entry, "description", "")
    body_text = re.sub(r"<[^>]+>", " ", body_html)
    body_text = re.sub(r"\s+", " ", body_text).strip()

    haystack = (title + " " + body_text).lower()
    matched = [t for t in targets if t in haystack]
    if not matched:
        return None  # not about any target company → drop

    tags = [source_name] + [m.capitalize() for m in matched[:3]]
    item_id = hashlib.sha1(link.encode()).hexdigest()[:12]
    return Item(
        id=item_id,
        source="china_ai",
        category="job",
        title=title,
        url=link,
        raw_content=body_text[:1000],
        tags=tags[:5],
        published_at=getattr(entry, "published", "") or getattr(entry, "updated", ""),
    )


REGISTRY.register(ChinaAIFetcher())
