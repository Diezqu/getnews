"""Fetch today's papers from HuggingFace Daily Papers API (no auth required)."""
import hashlib
from datetime import date

import requests

from pipeline.schema import Item

_BASE = "https://huggingface.co/api/daily_papers"


def fetch(target_date: date | None = None) -> list[Item]:
    target_date = target_date or date.today()
    params = {"date": target_date.isoformat()}

    try:
        resp = requests.get(_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return []

    # API returns list or {"papers": [...]}
    papers = data if isinstance(data, list) else data.get("papers", [])
    items: list[Item] = []

    for p in papers:
        paper = p.get("paper") or p  # nested or flat format
        title = paper.get("title") or p.get("title") or ""
        arxiv_id = paper.get("id") or p.get("id") or ""
        upvotes = int(p.get("numComments") or p.get("upvotes") or 0)
        abstract = paper.get("summary") or paper.get("abstract") or ""

        url = f"https://huggingface.co/papers/{arxiv_id}" if arxiv_id else ""
        if not title or not url:
            continue

        authors_raw = paper.get("authors") or []
        authors = [a.get("name", "") for a in authors_raw if isinstance(a, dict)]

        item_id = hashlib.sha1(url.encode()).hexdigest()[:12]
        items.append(Item(
            id=item_id,
            source="hf_papers",
            title=title,
            url=url,
            raw_abstract=abstract[:500],
            stars=upvotes,
            authors=authors[:4],
            published_at=target_date.isoformat() + "T00:00:00Z",
        ))

    items.sort(key=lambda x: -x.stars)
    return items
