"""Fetch latest papers from arXiv using the official RSS feed via feedparser.

The RSS endpoint (rss.arxiv.org) is served via CDN with no observed rate
limiting, replacing the arxiv.py API client that returns HTTP 429 on
GitHub Actions shared IPs.

Feed update cadence: daily ~04:00 UTC on weekdays; empty on weekends (normal).
"""
import hashlib
import time
from datetime import date

import feedparser

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_RSS_BASE = "https://rss.arxiv.org/rss/"

_KEYWORDS = ["agent", "multi-agent", "MCP", "RAG", "retrieval", "LLM", "language model"]

# Announce types we want to keep (skip "replace" and "replace-cross")
_KEEP_ANNOUNCE_TYPES = {"new", "cross"}


class ArxivFetcher(BaseFetcher):
    source_id = "arxiv"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["arxiv"]
        categories = cfg.get("categories", ["cs.AI", "cs.CL", "cs.MA", "cs.LG"])

        url = _RSS_BASE + "+".join(categories)

        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            print(f"  [warn] arXiv RSS fetch failed: {e}")
            return []

        entries = parsed.entries
        if not entries:
            print("  [info] arXiv RSS feed returned 0 entries (weekend or upstream issue)")
            return []

        items = []
        for entry in entries:
            announce_type = entry.get("arxiv_announce_type", "new")
            if announce_type not in _KEEP_ANNOUNCE_TYPES:
                continue
            items.append(_to_item(entry))

        return items


def _extract_abstract(description: str) -> str:
    """Strip the arXiv announce header from the description to get the abstract."""
    marker = "Abstract:"
    idx = description.find(marker)
    if idx != -1:
        return description[idx + len(marker):].strip()
    return description.strip()


def _to_item(entry) -> Item:
    title = entry.title.strip().replace("\n", " ")
    url = entry.link
    entry_id = entry.id  # oai:arXiv.org:<id>

    abstract = _extract_abstract(entry.description or "")
    abstract = abstract.replace("\n", " ")

    # Authors: comma-separated string → list (up to 4)
    authors = [a.strip() for a in entry.get("author", "").split(",") if a.strip()][:4]

    # Tags: arXiv category terms (up to 3), then keyword hits
    tags = [t["term"] for t in entry.get("tags", [])][:3]
    text_lower = (title + " " + abstract).lower()
    for kw in _KEYWORDS:
        if kw.lower() in text_lower and kw not in tags:
            tags.append(kw)

    # published_at: convert time.struct_time → ISO 8601 string
    published_parsed = entry.published_parsed
    if published_parsed:
        published_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", published_parsed)
    else:
        published_at = ""

    return Item(
        id=hashlib.sha1(entry_id.encode()).hexdigest()[:12],
        source="arxiv",
        category="learning",
        title=title,
        url=url,
        raw_content=abstract[:500],
        tags=tags[:6],
        authors=authors,
        published_at=published_at,
    )


REGISTRY.register(ArxivFetcher())
