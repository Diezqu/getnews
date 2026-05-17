"""Fetch 牛客 (Nowcoder) 面经 hot list via RSSHub public instance.

RSSHub may be down 2-4 days/month — we degrade gracefully (return []) and let
the pipeline continue. The "[warn]" log line surfaces in daily.py output.
"""
import hashlib
import re
from datetime import date

import feedparser

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_RSSHUB_BASE = "https://rsshub.app"

# Tag → company/position extraction patterns
_COMPANY_PATTERNS = [
    "字节", "字节跳动", "阿里", "腾讯", "百度", "美团", "京东", "拼多多",
    "华为", "小米", "Meta", "Google", "微软", "OpenAI", "Anthropic",
    "智谱", "DeepSeek", "月之暗面", "MiniMax", "通义",
]
_TECH_PATTERNS = [
    "transformer", "attention", "RAG", "agent", "LLM", "fine-tun", "LoRA",
    "vLLM", "RLHF", "强化学习", "多模态", "向量数据库", "prompt",
]


class NowcoderFetcher(BaseFetcher):
    source_id = "nowcoder"
    category = "job"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["nowcoder"]
        routes = cfg.get("rsshub_routes", [])
        max_items = cfg.get("max_items", 20)
        items: list[Item] = []
        for route in routes:
            url = _RSSHUB_BASE + route
            try:
                feed = feedparser.parse(url)
            except Exception as e:
                print(f"  [warn] Nowcoder RSSHub fetch failed: {e}")
                continue
            if feed.bozo and not feed.entries:
                print(f"  [warn] Nowcoder RSSHub returned no entries (route={route})")
                continue
            for entry in feed.entries[:max_items]:
                item = _entry_to_item(entry)
                if item:
                    items.append(item)
        return items


def _entry_to_item(entry) -> Item | None:
    title = (getattr(entry, "title", "") or "").strip()
    link = (getattr(entry, "link", "") or "").strip()
    if not title or not link:
        return None
    body_html = getattr(entry, "summary", "") or getattr(entry, "description", "")
    body_text = re.sub(r"<[^>]+>", " ", body_html)
    body_text = re.sub(r"\s+", " ", body_text).strip()
    author = (getattr(entry, "author", "") or "").strip()
    published = (getattr(entry, "published", "") or getattr(entry, "updated", "") or "")

    tags: list[str] = []
    haystack = (title + " " + body_text).lower()
    for company in _COMPANY_PATTERNS:
        if company.lower() in haystack and company not in tags:
            tags.append(company)
    for tech in _TECH_PATTERNS:
        if tech.lower() in haystack and tech not in tags:
            tags.append(tech)

    item_id = hashlib.sha1(link.encode()).hexdigest()[:12]
    return Item(
        id=item_id,
        source="nowcoder",
        category="job",
        title=title,
        url=link,
        raw_content=body_text[:800],
        tags=tags[:6],
        authors=[author] if author else [],
        published_at=published,
    )


REGISTRY.register(NowcoderFetcher())
