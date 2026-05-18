"""Fetch latest papers from arXiv using the arxiv.py library (3s delay, ToS-compliant)."""
import hashlib
from datetime import date, timedelta

import arxiv

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_KEYWORDS = ["agent", "multi-agent", "MCP", "RAG", "retrieval", "LLM", "language model"]


class ArxivFetcher(BaseFetcher):
    source_id = "arxiv"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["arxiv"]
        categories = cfg.get("categories", ["cs.AI", "cs.CL", "cs.MA", "cs.LG"])
        max_results = cfg.get("max_items", 30)
        days_back = cfg.get("days_back", 2)

        since = (target_date - timedelta(days=days_back)).strftime("%Y%m%d")
        cat_q = " OR ".join(f"cat:{c}" for c in categories)
        query = f"({cat_q}) AND submittedDate:[{since}0000 TO *]"

        client = arxiv.Client(delay_seconds=3.0, num_retries=3)
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        try:
            results = list(client.results(search))
        except Exception as e:
            print(f"  [warn] arXiv fetch failed: {e}")
            return []

        return [_to_item(r) for r in results]


def _to_item(r: arxiv.Result) -> Item:
    abstract = (r.summary or "").replace("\n", " ")
    tags = list(dict.fromkeys(r.categories[:3]))
    text_lower = (r.title + " " + abstract).lower()
    for kw in _KEYWORDS:
        if kw.lower() in text_lower and kw not in tags:
            tags.append(kw)

    return Item(
        id=hashlib.sha1(r.entry_id.encode()).hexdigest()[:12],
        source="arxiv",
        category="learning",
        title=r.title.strip().replace("\n", " "),
        url=r.entry_id,
        raw_content=abstract[:500],
        tags=tags[:6],
        authors=[a.name for a in r.authors[:4]],
        published_at=r.published.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


REGISTRY.register(ArxivFetcher())
