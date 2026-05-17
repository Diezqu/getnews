from dataclasses import dataclass, field, asdict
from typing import Literal
import json


Source = Literal["arxiv", "hf_papers", "github", "hackernews"]

@dataclass
class Item:
    id: str                        # dedup key: sha1(url)
    source: Source
    title: str
    url: str
    summary: str = ""              # LLM 生成的中文摘要
    raw_abstract: str = ""         # 原始摘要 / README 片段
    score: float = 0.0             # 个性化打分
    tags: list[str] = field(default_factory=list)
    stars: int = 0                 # github stars / hf upvotes
    authors: list[str] = field(default_factory=list)
    published_at: str = ""         # ISO 8601

    def to_dict(self) -> dict:
        return asdict(self)


def load_items(path: str) -> list[Item]:
    with open(path, encoding="utf-8") as f:
        return [Item(**d) for d in json.load(f)]


def save_items(items: list[Item], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([i.to_dict() for i in items], f, ensure_ascii=False, indent=2)
