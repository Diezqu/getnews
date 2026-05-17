"""Item: the unit of content flowing through the pipeline.

Every fetcher produces Items; scorer/llm/renderer all consume Items.
The `category` field decides which column of the dashboard the item renders into.
"""
from dataclasses import dataclass, field, asdict
from typing import Literal
import json


Source = Literal[
    "arxiv", "hf_papers", "github", "hackernews",   # learning sources
    "nowcoder", "china_ai", "coding_tool",          # job sources
]

Category = Literal["learning", "job"]


@dataclass
class Item:
    id: str                            # sha1(url)[:12]
    source: Source
    title: str                         # raw title (English for EN sources, Chinese for CN sources)
    url: str
    category: Category = "learning"
    summary: str = ""                  # LLM-generated Chinese summary
    raw_content: str = ""              # original abstract / README / post body (LLM input)
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    stars: int = 0                     # github stars / hf upvotes / hn points
    authors: list[str] = field(default_factory=list)
    published_at: str = ""             # ISO 8601

    def to_dict(self) -> dict:
        return asdict(self)


def load_items(path: str) -> list[Item]:
    with open(path, encoding="utf-8") as f:
        return [Item(**d) for d in json.load(f)]


def save_items(items: list[Item], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([i.to_dict() for i in items], f, ensure_ascii=False, indent=2)
