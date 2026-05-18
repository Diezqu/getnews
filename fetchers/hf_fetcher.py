"""Fetch today's papers from HuggingFace Daily Papers API (no auth required)."""
import hashlib
from datetime import date, timedelta

import requests

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_BASE = "https://huggingface.co/api/daily_papers"


class HFFetcher(BaseFetcher):
    source_id = "hf_papers"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        max_items = get_config()["sources"]["hf_papers"].get("max_items", 15)

        for offset in range(5):
            d = target_date - timedelta(days=offset)
            try:
                resp = requests.get(_BASE, params={"date": d.isoformat()}, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                print(f"  [warn] HF fetch failed: {e}")
                return []

            papers = data if isinstance(data, list) else data.get("papers", [])
            if not papers:
                continue

            if offset > 0:
                print(f"  hf_papers: empty for {target_date}, fell back to {d}")

            items: list[Item] = []
            for p in papers[:max_items]:
                paper = p.get("paper") or p
                title = paper.get("title") or p.get("title") or ""
                arxiv_id = paper.get("id") or p.get("id") or ""
                upvotes = int(p.get("upvotes") or p.get("numComments") or 0)
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
                    category="learning",
                    title=title,
                    url=url,
                    raw_content=abstract[:500],
                    stars=upvotes,
                    authors=authors[:4],
                    published_at=d.isoformat() + "T00:00:00Z",
                ))
            items.sort(key=lambda x: -x.stars)
            return items

        print(f"  [warn] hf_papers: 0 items after 5-day fallback")
        return []


REGISTRY.register(HFFetcher())
