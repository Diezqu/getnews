"""Fetch latest papers from arXiv API (no auth required, 1 req/3s)."""
import hashlib
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import requests

from pipeline.schema import Item

_BASE = "https://export.arxiv.org/api/query"
_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
_CATEGORIES = ["cs.AI", "cs.CL", "cs.MA", "cs.LG"]
_KEYWORDS = ["agent", "multi-agent", "MCP", "RAG", "retrieval", "LLM", "language model"]


def fetch(max_results: int = 30, days_back: int = 2) -> list[Item]:
    since = (date.today() - timedelta(days=days_back)).strftime("%Y%m%d")
    query = " OR ".join(f"cat:{c}" for c in _CATEGORIES)
    # Filter by submission date
    query = f"({query}) AND submittedDate:[{since}0000 TO *]"

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        resp = requests.get(_BASE, params=params, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [warn] arXiv fetch failed: {e}")
        return []
    time.sleep(1)

    root = ET.fromstring(resp.text)
    items: list[Item] = []
    for entry in root.findall("atom:entry", _NS):
        title_el = entry.find("atom:title", _NS)
        url_el = entry.find("atom:id", _NS)
        abstract_el = entry.find("atom:summary", _NS)
        published_el = entry.find("atom:published", _NS)

        if title_el is None or url_el is None:
            continue

        title = (title_el.text or "").strip().replace("\n", " ")
        url = (url_el.text or "").strip()
        abstract = (abstract_el.text or "").strip().replace("\n", " ") if abstract_el is not None else ""
        published = (published_el.text or "")[:10] + "T00:00:00Z" if published_el is not None else ""

        authors = [
            (a.find("atom:name", _NS).text or "") for a in entry.findall("atom:author", _NS)
            if a.find("atom:name", _NS) is not None
        ]

        # Derive tags from categories and title keywords
        cats = [c.attrib.get("term", "") for c in entry.findall("arxiv:primary_category", _NS)]
        cats += [c.attrib.get("term", "") for c in entry.findall("atom:category", _NS)]
        tags = list(dict.fromkeys(cats[:3]))  # unique, keep order
        text_lower = (title + " " + abstract).lower()
        for kw in _KEYWORDS:
            if kw.lower() in text_lower and kw not in tags:
                tags.append(kw)

        item_id = hashlib.sha1(url.encode()).hexdigest()[:12]
        items.append(Item(
            id=item_id,
            source="arxiv",
            title=title,
            url=url,
            raw_abstract=abstract[:500],
            tags=tags[:6],
            authors=authors[:4],
            published_at=published,
        ))
    return items
