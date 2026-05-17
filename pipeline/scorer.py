"""Deduplication and personalized scoring.

Scoring formula:
  base_score = source_base + log(stars+1)*2
  keyword_bonus = sum(weight for matched keywords)
  author_bonus  = 2.0 if any watched author matches
  final_score   = min(base_score + keyword_bonus + author_bonus, 10.0)
"""
import hashlib
import math
from pipeline.schema import Item

# ── Personalization config (edit these to tune your feed) ──────────────────
KEYWORD_WEIGHTS: dict[str, float] = {
    "agent":            3.0,
    "multi-agent":      3.0,
    "mcp":              2.5,
    "rag":              1.5,
    "retrieval":        1.0,
    "llm":              1.0,
    "language model":   1.0,
    "tool use":         1.5,
    "planning":         1.0,
    "memory":           1.0,
    "benchmark":        0.5,
    "fine-tun":         0.5,
    "green ai":         0.5,
    "distributed":      0.3,
}

WATCHED_AUTHORS: set[str] = {
    "anthropic", "deepmind", "stanford", "mit", "tsinghua", "sjtu",
    "andrej karpathy", "yann lecun", "yoshua bengio",
}

SOURCE_BASE: dict[str, float] = {
    "arxiv":      4.0,
    "hf_papers":  4.0,
    "github":     3.5,
    "hackernews": 3.0,
}

# ── Scoring ────────────────────────────────────────────────────────────────

def score_item(item: Item) -> float:
    base = SOURCE_BASE.get(item.source, 3.0)
    base += math.log(item.stars + 1) * 0.5

    text = (item.title + " " + item.raw_abstract + " " + " ".join(item.tags)).lower()
    kw_bonus = sum(w for kw, w in KEYWORD_WEIGHTS.items() if kw in text)

    authors_lower = " ".join(item.authors).lower()
    author_bonus = 2.0 if any(a in authors_lower for a in WATCHED_AUTHORS) else 0.0

    return round(min(base + kw_bonus + author_bonus, 10.0), 2)


def score_all(items: list[Item]) -> list[Item]:
    for item in items:
        item.score = score_item(item)
    return items


# ── Deduplication ──────────────────────────────────────────────────────────

def _fingerprint(item: Item) -> str:
    """Normalize title to catch near-duplicate entries across sources."""
    title = "".join(c.lower() for c in item.title if c.isalnum())
    return title[:40]


def dedup(items: list[Item]) -> list[Item]:
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
