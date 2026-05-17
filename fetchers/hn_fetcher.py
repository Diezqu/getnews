"""Fetch AI-related stories from HackerNews via Algolia API (no auth, 10k req/h)."""
import hashlib
from datetime import datetime, timedelta, timezone

import requests

from pipeline.schema import Item

_BASE = "https://hn.algolia.com/api/v1/search"
_QUERIES = ["AI agent", "LLM", "Claude", "GPT", "machine learning", "MCP protocol"]
_MIN_POINTS = 20


def fetch(max_per_query: int = 10, days_back: int = 3) -> list[Item]:
    since_ts = int((datetime.now(timezone.utc) - timedelta(days=days_back)).timestamp())
    seen: set[str] = set()
    items: list[Item] = []

    for q in _QUERIES:
        params = {
            "query": q,
            "tags": "story",
            "numericFilters": f"created_at_i>{since_ts},points>{_MIN_POINTS}",
            "hitsPerPage": max_per_query,
        }
        try:
            resp = requests.get(_BASE, params=params, timeout=10)
            resp.raise_for_status()
        except requests.RequestException:
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
                title=title,
                url=url,
                stars=points,
                published_at=created,
            ))

    items.sort(key=lambda x: -x.stars)
    return items
