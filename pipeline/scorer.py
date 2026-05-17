"""Per-category personalized scoring + deduplication.

Scoring formula:
    base   = source_base[source] + log(stars+1) * stars_log_weight
    kw_bonus = sum(weight for kw in scoring[category] if kw in lowercased title+content+tags)
    author_bonus = scoring.authors.bonus if any watched author matches
    final = min(base + kw_bonus + author_bonus, 10.0)

All weights come from config.yaml.
"""
import hashlib
import math

from pipeline.config import get_config
from pipeline.schema import Item


def score_item(item: Item) -> float:
    cfg = get_config()["scoring"]
    base = cfg["source_base"].get(item.source, 3.0)
    base += math.log(item.stars + 1) * cfg.get("stars_log_weight", 0.5)

    category_weights: dict[str, float] = cfg.get(item.category, {})
    text = (item.title + " " + item.raw_content + " " + " ".join(item.tags)).lower()
    kw_bonus = sum(w for kw, w in category_weights.items() if kw.lower() in text)

    authors_cfg = cfg.get("authors", {})
    watchlist = [a.lower() for a in authors_cfg.get("watchlist", [])]
    authors_lower = " ".join(item.authors).lower()
    author_bonus = (authors_cfg.get("bonus", 0.0)
                    if any(a in authors_lower for a in watchlist) else 0.0)

    return round(min(base + kw_bonus + author_bonus, 10.0), 2)


def score_all(items: list[Item]) -> list[Item]:
    for item in items:
        item.score = score_item(item)
    return items


# ── Deduplication ──────────────────────────────────────────────────────────

def _fingerprint(item: Item) -> str:
    title = "".join(c.lower() for c in item.title if c.isalnum())
    return title[:40]


def dedup(items: list[Item]) -> list[Item]:
    """Sort by score desc, then keep first occurrence of each url-hash and title-fingerprint."""
    seen_urls: set[str] = set()
    seen_fps: set[str] = set()
    result: list[Item] = []
    for item in sorted(items, key=lambda x: -x.score):
        url_key = hashlib.sha1(item.url.encode()).hexdigest()[:16]
        fp = _fingerprint(item)
        if url_key in seen_urls or fp in seen_fps:
            continue
        seen_urls.add(url_key)
        seen_fps.add(fp)
        result.append(item)
    return result
