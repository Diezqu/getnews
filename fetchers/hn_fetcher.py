"""Fetch AI-related stories from HackerNews via Algolia API."""
import hashlib
from datetime import date, datetime, timedelta, timezone

import requests

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_BASE = "https://hn.algolia.com/api/v1/search"


class HNFetcher(BaseFetcher):
    source_id = "hackernews"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["hackernews"]
        queries = cfg.get("queries", ["AI agent"])
        max_per_query = cfg.get("max_per_query", 10)
        min_points = cfg.get("min_points", 20)
        days_back = cfg.get("days_back", 3)

        since_ts = int(
            (datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
             - timedelta(days=days_back)).timestamp()
        )
        seen: set[str] = set()
        items: list[Item] = []
        for q in queries:
            params = {
                "query": q,
                "tags": "story",
                "numericFilters": f"created_at_i>{since_ts},points>{min_points}",
                "hitsPerPage": max_per_query,
            }
            try:
                resp = requests.get(_BASE, params=params, timeout=10)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  [warn] HN fetch failed for query '{q}': {e}")
                continue
            for hit in resp.json().get("hits", []):
                hn_id = str(hit.get("objectID", ""))
                if hn_id in seen:
                    continue
                seen.add(hn_id)
                title = hit.get("title") or ""
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hn_id}"
                points = int(hit.get("points") or 0)
                created = hit.get("created_at") or ""
                item_id = hashlib.sha1(hn_id.encode()).hexdigest()[:12]
                items.append(Item(
                    id=item_id,
                    source="hackernews",
                    category="learning",
                    title=title,
                    url=url,
                    raw_content=title,                   # HN has no body; use title as LLM input
                    stars=points,
                    published_at=created,
                ))
        items.sort(key=lambda x: -x.stars)
        return items


REGISTRY.register(HNFetcher())
