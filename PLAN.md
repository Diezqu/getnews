# GetNews v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor GetNews from "English-only Agent engineer daily" (v1) to "dual-column Chinese AI job + learning dashboard" (v2), with fully-automated GitHub Actions delivery to a public GitHub Pages portfolio site.

**Architecture:**
- Plugin-style **Fetcher registry** (`fetchers/base.py`) with 7 fetchers tagged `category="learning"` or `category="job"`
- **YAML-driven config** (keyword weights, source toggles, LLM provider) so tuning never requires code edits
- **Three LLM tasks** via DeepSeek (one shared provider): per-item EN→ZH translation, per-item ZH refinement, daily synthesis (headline + 3 trends + 3 signals)
- **Three-layer data archive** (`data/processed/` items, `data/summaries/` daily LLM output, `data/aggregates/` v3 weekly/monthly stubs) to support future weekly/monthly reports
- **Template inheritance** (`base.html.j2` + Jinja partials) so adding new card types or report cadences doesn't require touching the master template
- **GitHub Actions cron @ UTC 23:00** (= Beijing 07:00) commits results back to the repo for GitHub Pages auto-deploy

**Tech Stack:** Python 3.13 · Jinja2 · DeepSeek API (OpenAI-compatible SDK) · RSSHub public instance · feedparser · PyYAML · pytest · Chart.js · GitHub Pages · GitHub Actions

**Source spec:** [SPEC.md](SPEC.md) — read sections 4 (sources), 9 (layout), 12 (archive), 13 (extensibility) before starting.

---

## File Structure (target state)

```
GetNews/
├── daily.py                    [MODIFY] registry loop + summarizer + archive writeback
├── config.yaml                 [NEW]   single source of truth for weights/sources/llm
├── requirements.txt            [MODIFY] add PyYAML, feedparser, pytest
├── README.md                   [MODIFY] v2 docs + "how to add a source"
├── .env.example                [KEEP]   already has DEEPSEEK_API_KEY
├── .github/workflows/daily.yml [NEW]   cron + commit + push
│
├── fetchers/
│   ├── base.py                 [NEW]   BaseFetcher ABC + REGISTRY singleton
│   ├── arxiv_fetcher.py        [MODIFY] inherit + register, category="learning"
│   ├── hf_fetcher.py           [MODIFY] same
│   ├── github_fetcher.py       [MODIFY] same
│   ├── hn_fetcher.py           [MODIFY] same
│   ├── nowcoder_fetcher.py     [NEW]   RSSHub /nowcoder/discuss
│   ├── china_ai_fetcher.py     [NEW]   机器之心 + 量子位 → filter by target companies
│   └── coding_tool_fetcher.py  [NEW]   derived: filter HN/HF by Cursor/Claude Code/...
│
├── pipeline/
│   ├── schema.py               [MODIFY] add `category` + extend Source literal
│   ├── config.py               [NEW]   YAML loader + cache
│   ├── scorer.py               [MODIFY] read weights from config, per-category
│   ├── llm.py                  [MODIFY] BaseLLM abstraction + 3 prompts (translate/refine/daily)
│   ├── summarizer.py           [NEW]   daily JSON summary (headline + trends + signals)
│   ├── aggregator.py           [NEW]   stub interfaces for v3 weekly/monthly
│   └── renderer.py             [MODIFY] dual column + summary block + archive index
│
├── templates/
│   ├── base.html.j2            [NEW]   masthead + footer + CSS variables
│   ├── daily.html.j2           [REWRITE] extends base, includes partials
│   ├── weekly.html.j2          [NEW]   empty stub for v3
│   ├── monthly.html.j2         [NEW]   empty stub for v3
│   ├── archive.html.j2         [NEW]   history index page
│   └── partials/
│       ├── summary_block.html.j2     [NEW]
│       ├── card_paper.html.j2        [NEW]   arXiv + HF
│       ├── card_repo.html.j2         [NEW]   GitHub
│       ├── card_hn.html.j2           [NEW]   HackerNews
│       ├── card_job.html.j2          [NEW]   牛客
│       ├── card_company.html.j2      [NEW]   国内 AI 公司动态
│       ├── card_coding_tool.html.j2  [NEW]   AI Coding 信号
│       ├── radar.html.j2             [NEW]   tech radar block
│       └── trend_chart.html.j2       [NEW]   chart.js block
│
├── docs/                       [pages root — auto-generated, do not hand-edit]
│   ├── index.html              [auto]
│   ├── YYYY-MM-DD.html         [auto]
│   ├── archive.html            [NEW auto]
│   ├── weekly/.gitkeep         [NEW]
│   └── monthly/.gitkeep        [NEW]
│
├── data/
│   ├── processed/YYYY-MM-DD.json   [auto, existing]
│   ├── summaries/YYYY-MM-DD.json   [NEW auto]
│   └── aggregates/
│       ├── weekly/.gitkeep         [NEW]
│       └── monthly/.gitkeep        [NEW]
│
└── tests/                      [NEW]
    ├── __init__.py
    ├── conftest.py
    ├── test_schema.py
    ├── test_config.py
    ├── test_registry.py
    ├── test_scorer.py
    ├── test_llm_providers.py
    └── test_summarizer.py
```

---

## Milestones

| # | Milestone | Tasks | Focus |
|---|---|---|---|
| 1 | Pre-flight | T0 | Deps, test infra, archive dirs |
| 2 | Foundation | T1-T3 | Schema, config, fetcher registry |
| 3 | Refactor existing fetchers | T4-T7 | arXiv / HF / GitHub / HN inherit BaseFetcher |
| 4 | New Chinese sources | T8-T10 | 牛客 / 国内 AI 公司 / AI Coding 信号 |
| 5 | Scorer + LLM rework | T11-T12 | Config-driven scoring, 3-prompt LLM |
| 6 | Summarizer + Archive | T13-T15 | Daily summary JSON + v3 hooks |
| 7 | Templates | T16-T20 | base + partials + daily rewrite + archive page |
| 8 | Renderer + glue | T21-T22 | Dual-column renderer + daily.py registry loop |
| 9 | Automation + Docs | T23-T24 | GitHub Actions + README v2 |

After each task: run `python daily.py --mock --no-push` end-to-end (where possible) and inspect `docs/index.html` in a browser. Commit only when both pass.

---

## Task 0: Pre-flight (deps + dirs + test scaffolding)

**Files:**
- Modify: `requirements.txt`
- Create: `tests/__init__.py`, `tests/conftest.py`
- Create: `data/summaries/.gitkeep`, `data/aggregates/weekly/.gitkeep`, `data/aggregates/monthly/.gitkeep`
- Create: `docs/weekly/.gitkeep`, `docs/monthly/.gitkeep`

- [ ] **Step 1: Add PyYAML, feedparser (verify), and pytest to requirements**

Edit `requirements.txt` so it reads exactly:

```
requests>=2.31
python-dotenv>=1.0
jinja2>=3.1
openai>=1.30          # DeepSeek 兼容 OpenAI SDK
feedparser>=6.0       # arXiv RSS fallback + RSSHub feeds
python-dateutil>=2.9
PyYAML>=6.0           # config.yaml loader
pytest>=8.0           # unit tests
```

- [ ] **Step 2: Install new deps**

Run: `pip install -r requirements.txt`
Expected: PyYAML and pytest install successfully (others already present).

- [ ] **Step 3: Create archive directory skeletons**

```bash
mkdir -p data/summaries data/aggregates/weekly data/aggregates/monthly docs/weekly docs/monthly tests
touch data/summaries/.gitkeep data/aggregates/weekly/.gitkeep data/aggregates/monthly/.gitkeep
touch docs/weekly/.gitkeep docs/monthly/.gitkeep
touch tests/__init__.py
```

- [ ] **Step 4: Create `tests/conftest.py` with shared fixtures**

```python
"""Shared pytest fixtures."""
from datetime import date
from pathlib import Path

import pytest

from pipeline.schema import Item


@pytest.fixture
def sample_learning_item() -> Item:
    return Item(
        id="abc123",
        source="arxiv",
        category="learning",
        title="AutoAgent: Fully Automatic Agent Generation from NL",
        url="https://arxiv.org/abs/2601.00001",
        raw_content="We propose AutoAgent, a framework that builds agents from natural language. On SWE-bench it outperforms GPT-4 by 12 points.",
        tags=["cs.AI", "cs.MA", "agent", "MCP"],
        authors=["Alice Wang", "Bob Zhang"],
        published_at="2026-05-17T00:00:00Z",
    )


@pytest.fixture
def sample_job_item() -> Item:
    return Item(
        id="def456",
        source="nowcoder",
        category="job",
        title="字节跳动 算法工程师 一面凉经",
        url="https://www.nowcoder.com/discuss/123",
        raw_content="一面问了 transformer attention 计算细节、RAG 流程优化思路、多模态 fine-tune 的实操经验。",
        tags=["字节", "算法", "Transformer"],
        authors=["user123"],
        published_at="2026-05-17T10:00:00+08:00",
    )


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parent.parent
```

Note: this references `category` and `raw_content` fields that Task 1 will add. Tests using these fixtures won't pass until Task 1 lands — that's expected.

- [ ] **Step 5: Verify pytest discovers the directory**

Run: `pytest tests/ --collect-only -q`
Expected: "no tests ran" with exit 5 (no tests yet, but no import errors from `conftest.py` either — even if `category` field doesn't exist yet, the fixture body is only evaluated when used).

If you see ImportError on the `Item(...)` call, that's fine — the fixture isn't instantiated during collection. If you see ImportError on `from pipeline.schema import Item`, the existing schema file is fine — re-check the import path.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt tests/ data/summaries/.gitkeep data/aggregates docs/weekly docs/monthly
git commit -m "chore: scaffold v2 dirs, test infra, and new deps"
```

---

## Task 1: Extend `pipeline/schema.py` with `category` + new Source values

**Files:**
- Modify: `pipeline/schema.py` (entire file)
- Create: `tests/test_schema.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_schema.py`:

```python
"""Schema must support category + extended source literal + raw_content field."""
import json
from pathlib import Path

import pytest

from pipeline.schema import Item, load_items, save_items


def test_item_defaults_to_learning_category():
    item = Item(id="x", source="arxiv", title="t", url="u")
    assert item.category == "learning"


def test_job_item_can_be_constructed():
    item = Item(
        id="x",
        source="nowcoder",
        category="job",
        title="字节算法面经",
        url="https://nowcoder.com/discuss/1",
    )
    assert item.category == "job"
    assert item.source == "nowcoder"


def test_raw_content_replaces_raw_abstract():
    item = Item(id="x", source="github", title="repo", url="u", raw_content="README excerpt")
    assert item.raw_content == "README excerpt"
    assert not hasattr(item, "raw_abstract")


def test_roundtrip_serialization(tmp_path: Path, sample_job_item):
    p = tmp_path / "items.json"
    save_items([sample_job_item], str(p))
    [restored] = load_items(str(p))
    assert restored.category == "job"
    assert restored.source == "nowcoder"
    assert restored.tags == sample_job_item.tags


def test_all_7_sources_are_valid():
    for src in ["arxiv", "hf_papers", "github", "hackernews",
                "nowcoder", "china_ai", "coding_tool"]:
        Item(id="x", source=src, title="t", url="u")  # no exception
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_schema.py -v`
Expected: 5 failures — `Item.category` does not exist, `raw_content` does not exist, etc.

- [ ] **Step 3: Rewrite `pipeline/schema.py`**

```python
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
```

**Note:** the field is renamed `raw_abstract` → `raw_content`. Existing fetchers reference `raw_abstract`; they'll be updated in T4-T7. Until then, `python daily.py --mock` will crash. That's why this task ships together with T4-T7 in one logical migration — but commit boundaries stay per-task so review stays granular.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_schema.py -v`
Expected: all 5 pass.

- [ ] **Step 5: Commit**

```bash
git add pipeline/schema.py tests/test_schema.py
git commit -m "feat(schema): add category + raw_content + extended Source literal"
```

---

## Task 2: `config.yaml` + `pipeline/config.py` loader

**Files:**
- Create: `config.yaml`
- Create: `pipeline/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_config.py`:

```python
"""Config loader reads YAML and exposes typed dict access."""
from pathlib import Path

import pytest
import yaml

from pipeline.config import load_config, get_config


def test_load_config_returns_dict(repo_root: Path):
    cfg = load_config(repo_root / "config.yaml")
    assert isinstance(cfg, dict)
    assert "scoring" in cfg and "sources" in cfg and "llm" in cfg


def test_scoring_has_both_categories(repo_root):
    cfg = load_config(repo_root / "config.yaml")
    assert "learning" in cfg["scoring"]
    assert "job" in cfg["scoring"]


def test_sources_have_required_keys(repo_root):
    cfg = load_config(repo_root / "config.yaml")
    for src_name in ["arxiv", "hf_papers", "github", "hackernews",
                     "nowcoder", "china_ai", "coding_tool"]:
        assert src_name in cfg["sources"], f"missing source: {src_name}"
        assert "enabled" in cfg["sources"][src_name]


def test_get_config_caches(repo_root, monkeypatch):
    monkeypatch.chdir(repo_root)
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2  # same object → cached


def test_llm_section_has_provider_and_model(repo_root):
    cfg = load_config(repo_root / "config.yaml")
    assert cfg["llm"]["provider"] in {"deepseek", "mock"}
    assert cfg["llm"]["model"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: ImportError on `pipeline.config` and missing `config.yaml`.

- [ ] **Step 3: Create `config.yaml`**

```yaml
# GetNews v2 — single source of truth for weights, sources, LLM, rendering.
# Edit this file (no code changes) to tune your daily brief.

# ───────────────────────────────────────────────────────────────
# Personalized scoring weights
# ───────────────────────────────────────────────────────────────
scoring:
  source_base:                # baseline before keyword/author bonus
    arxiv:        4.0
    hf_papers:    4.0
    github:       3.5
    hackernews:   3.0
    nowcoder:     4.0
    china_ai:     3.5
    coding_tool:  3.5

  stars_log_weight: 0.5       # final += log(stars+1) * this

  learning:
    agent:            3.0
    multi-agent:      3.0
    mcp:              2.5
    rag:              1.5
    retrieval:        1.0
    llm:              1.0
    language model:   1.0
    tool use:         1.5
    planning:         1.0
    memory:           1.0
    benchmark:        0.5
    fine-tun:         0.5
    distributed:      0.3

  job:
    # 牛客面经高频题型
    transformer:      3.0
    attention:        2.5
    rag:              2.5
    向量数据库:        2.5
    agent:            2.5
    多智能体:          2.5
    prompt:           2.0
    vllm:             2.0
    部署:             2.0
    fine-tun:         2.0
    lora:             2.0
    分布式训练:        1.5
    rlhf:             1.5
    强化学习:          1.5
    # 国内 AI 公司
    智谱:             3.0
    glm:              3.0
    月之暗面:          3.0
    kimi:             3.0
    deepseek:         3.0
    通义:             2.5
    阿里:             2.5
    字节:             2.5
    doubao:           2.5
    豆包:             2.5
    minimax:          2.0
    阶跃:             2.0
    # AI Coding 工具
    cursor:           2.0
    claude code:      2.0
    cline:            1.5
    aider:            1.5
    copilot:          1.0

  authors:
    bonus: 2.0
    watchlist:
      - anthropic
      - deepmind
      - openai
      - google research
      - meta ai
      - stanford
      - mit
      - tsinghua
      - 清华
      - sjtu
      - 上交
      - andrej karpathy
      - yann lecun
      - yoshua bengio
      - geoffrey hinton

# ───────────────────────────────────────────────────────────────
# Sources: toggle on/off + per-source params
# ───────────────────────────────────────────────────────────────
sources:
  arxiv:
    enabled: true
    max_items: 30
    categories: [cs.AI, cs.CL, cs.MA, cs.LG]
    days_back: 2

  hf_papers:
    enabled: true
    max_items: 15

  github:
    enabled: true
    max_per_query: 8
    days_back: 30
    queries:
      - "agent LLM"
      - "MCP server Claude"
      - "RAG retrieval augmented"
      - "multi-agent framework"

  hackernews:
    enabled: true
    max_per_query: 10
    min_points: 20
    days_back: 3
    queries:
      - "AI agent"
      - "LLM"
      - "Claude"
      - "GPT"
      - "machine learning"
      - "MCP protocol"

  nowcoder:
    enabled: true
    max_items: 20
    # RSSHub route for 牛客 discuss; 639 = 人工智能/机器学习 分区
    rsshub_routes:
      - "/nowcoder/discuss/639"

  china_ai:
    enabled: true
    max_items: 15
    # Aggregator sites that cover all major Chinese AI companies in one feed.
    # We filter by company keywords (智谱/DeepSeek/Kimi/etc) after fetch.
    feeds:
      - name: "机器之心"
        url:  "https://www.jiqizhixin.com/rss"
      - name: "量子位"
        url:  "https://rsshub.app/qbitai"
    target_companies:
      - 智谱
      - 月之暗面
      - kimi
      - deepseek
      - 通义
      - 字节
      - doubao
      - 豆包
      - minimax
      - 阶跃

  coding_tool:
    enabled: true
    max_items: 5
    # Derived from hackernews + hf_papers — pulled at scorer/renderer stage,
    # not a network call. Filters items whose title/content mentions any of:
    keywords:
      - cursor
      - claude code
      - cline
      - aider
      - copilot
      - windsurf

# ───────────────────────────────────────────────────────────────
# LLM
# ───────────────────────────────────────────────────────────────
llm:
  provider: "deepseek"      # "deepseek" | "mock"
  model: "deepseek-chat"
  temperature: 0.3
  max_tokens_summary: 250
  max_tokens_daily: 600

# ───────────────────────────────────────────────────────────────
# Rendering
# ───────────────────────────────────────────────────────────────
rendering:
  theme: "light"
  max_per_card:
    arxiv:        8
    hf_papers:    5
    github:       8
    hackernews:   8
    nowcoder:    10
    china_ai:     8
    coding_tool:  5
  # which keywords to track on the trend chart (must overlap with scoring keys)
  trend_keywords: [agent, mcp, rag]
  # which keywords show up in the technology radar
  radar_keywords:
    - {name: "Agent",         desc: "多 Agent 协作框架持续爆发", gradient: "linear-gradient(90deg,#1e3557,#2a4a76)"}
    - {name: "MCP",           desc: "2026 Agent 集成标准",       gradient: "linear-gradient(90deg,#c94428,#e05c3a)"}
    - {name: "RAG",           desc: "检索增强依然是核心技术",     gradient: "linear-gradient(90deg,#2a7d4f,#3a9d6a)"}
    - {name: "LLM Fine-tune", desc: "垂直领域微调需求上升",       gradient: "linear-gradient(90deg,#b8872a,#d4a040)"}
    - {name: "AI Safety",     desc: "对齐与可解释性研究增加",     gradient: "linear-gradient(90deg,#1e3557,#c94428)"}
    - {name: "Local-First AI",desc: "隐私计算与离线部署",         gradient: "linear-gradient(90deg,#2a7d4f,#b8872a)"}
```

- [ ] **Step 4: Implement `pipeline/config.py`**

```python
"""YAML config loader — cached so repeated calls are free.

Usage:
    from pipeline.config import get_config
    cfg = get_config()
    weight = cfg["scoring"]["learning"]["agent"]
"""
from functools import lru_cache
from pathlib import Path

import yaml


_DEFAULT_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config(path: Path | str = _DEFAULT_PATH) -> dict:
    """Load YAML from the given path. Raises FileNotFoundError if missing."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Cached singleton accessor for the default config path."""
    return load_config(_DEFAULT_PATH)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: all 5 pass.

- [ ] **Step 6: Commit**

```bash
git add config.yaml pipeline/config.py tests/test_config.py
git commit -m "feat(config): YAML-driven configuration loader"
```

---

## Task 3: `fetchers/base.py` — BaseFetcher ABC + REGISTRY

**Files:**
- Create: `fetchers/base.py`
- Create: `tests/test_registry.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_registry.py`:

```python
"""Registry collects fetchers by source_id and exposes iteration."""
from datetime import date

import pytest

from fetchers.base import BaseFetcher, FetcherRegistry
from pipeline.schema import Item


class _StubFetcher(BaseFetcher):
    source_id = "stub"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        return [Item(id="x", source="arxiv", title="t", url="u")]


def test_can_subclass_and_fetch():
    f = _StubFetcher()
    items = f.fetch(date(2026, 5, 17))
    assert len(items) == 1


def test_registry_register_and_lookup():
    reg = FetcherRegistry()
    f = _StubFetcher()
    reg.register(f)
    assert reg.get("stub") is f
    assert list(reg.all()) == [f]


def test_registry_filters_by_enabled_in_config():
    reg = FetcherRegistry()
    reg.register(_StubFetcher())
    cfg = {"sources": {"stub": {"enabled": False}}}
    assert list(reg.enabled(cfg)) == []
    cfg = {"sources": {"stub": {"enabled": True}}}
    assert len(list(reg.enabled(cfg))) == 1


def test_registry_unknown_source_treated_as_disabled():
    reg = FetcherRegistry()
    reg.register(_StubFetcher())
    cfg = {"sources": {}}                    # stub absent
    assert list(reg.enabled(cfg)) == []


def test_base_fetcher_requires_source_id_and_category():
    class Bad(BaseFetcher):
        pass
    with pytest.raises((TypeError, NotImplementedError)):
        Bad().fetch(date.today())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_registry.py -v`
Expected: ImportError on `fetchers.base`.

- [ ] **Step 3: Implement `fetchers/base.py`**

```python
"""BaseFetcher ABC + module-level REGISTRY singleton.

Every fetcher module should end with:
    REGISTRY.register(MyFetcher())
so that daily.py can iterate REGISTRY.enabled(cfg) and not hardcode sources.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Iterator

from pipeline.schema import Category, Item


class BaseFetcher(ABC):
    source_id: str = ""            # must match a key under config["sources"]
    category: Category = "learning"

    @abstractmethod
    def fetch(self, target_date: date) -> list[Item]:
        ...


class FetcherRegistry:
    def __init__(self) -> None:
        self._items: dict[str, BaseFetcher] = {}

    def register(self, fetcher: BaseFetcher) -> None:
        if not fetcher.source_id:
            raise ValueError(f"{fetcher.__class__.__name__}.source_id is empty")
        self._items[fetcher.source_id] = fetcher

    def get(self, source_id: str) -> BaseFetcher | None:
        return self._items.get(source_id)

    def all(self) -> Iterator[BaseFetcher]:
        return iter(self._items.values())

    def enabled(self, cfg: dict) -> Iterator[BaseFetcher]:
        sources_cfg = cfg.get("sources", {})
        for f in self._items.values():
            src = sources_cfg.get(f.source_id, {})
            if src.get("enabled", False):
                yield f


# Module-level singleton.
REGISTRY = FetcherRegistry()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_registry.py -v`
Expected: all 5 pass.

- [ ] **Step 5: Commit**

```bash
git add fetchers/base.py tests/test_registry.py
git commit -m "feat(fetchers): BaseFetcher ABC and FetcherRegistry"
```

---

## Task 4: Refactor `fetchers/arxiv_fetcher.py` to BaseFetcher

**Files:**
- Modify: `fetchers/arxiv_fetcher.py`

- [ ] **Step 1: Rewrite the file**

```python
"""Fetch latest papers from arXiv API (no auth required, 1 req/3s)."""
import hashlib
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import requests

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_BASE = "https://export.arxiv.org/api/query"
_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


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

        return list(_parse(resp.text))


def _parse(xml_text: str):
    root = ET.fromstring(xml_text)
    keywords = ["agent", "multi-agent", "MCP", "RAG", "retrieval", "LLM", "language model"]
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
            (a.find("atom:name", _NS).text or "")
            for a in entry.findall("atom:author", _NS)
            if a.find("atom:name", _NS) is not None
        ]
        cats = [c.attrib.get("term", "") for c in entry.findall("arxiv:primary_category", _NS)]
        cats += [c.attrib.get("term", "") for c in entry.findall("atom:category", _NS)]
        tags = list(dict.fromkeys(cats[:3]))
        text_lower = (title + " " + abstract).lower()
        for kw in keywords:
            if kw.lower() in text_lower and kw not in tags:
                tags.append(kw)

        item_id = hashlib.sha1(url.encode()).hexdigest()[:12]
        yield Item(
            id=item_id,
            source="arxiv",
            category="learning",
            title=title,
            url=url,
            raw_content=abstract[:500],
            tags=tags[:6],
            authors=authors[:4],
            published_at=published,
        )


REGISTRY.register(ArxivFetcher())
```

- [ ] **Step 2: Verify the module imports cleanly and self-registers**

Run: `python -c "import fetchers.arxiv_fetcher; from fetchers.base import REGISTRY; print([f.source_id for f in REGISTRY.all()])"`
Expected output: `['arxiv']`

- [ ] **Step 3: Commit**

```bash
git add fetchers/arxiv_fetcher.py
git commit -m "refactor(arxiv): inherit BaseFetcher + self-register + config-driven"
```

---

## Task 5: Refactor `fetchers/hf_fetcher.py`

**Files:**
- Modify: `fetchers/hf_fetcher.py`

- [ ] **Step 1: Rewrite the file**

```python
"""Fetch today's papers from HuggingFace Daily Papers API (no auth required)."""
import hashlib
from datetime import date

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
        params = {"date": target_date.isoformat()}
        try:
            resp = requests.get(_BASE, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  [warn] HF fetch failed: {e}")
            return []

        papers = data if isinstance(data, list) else data.get("papers", [])
        items: list[Item] = []
        for p in papers[:max_items]:
            paper = p.get("paper") or p
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
                category="learning",
                title=title,
                url=url,
                raw_content=abstract[:500],
                stars=upvotes,
                authors=authors[:4],
                published_at=target_date.isoformat() + "T00:00:00Z",
            ))
        items.sort(key=lambda x: -x.stars)
        return items


REGISTRY.register(HFFetcher())
```

- [ ] **Step 2: Verify import**

Run: `python -c "import fetchers.hf_fetcher; from fetchers.base import REGISTRY; print([f.source_id for f in REGISTRY.all()])"`
Expected: `['hf_papers']` (importing only the one module).

- [ ] **Step 3: Commit**

```bash
git add fetchers/hf_fetcher.py
git commit -m "refactor(hf): inherit BaseFetcher + self-register"
```

---

## Task 6: Refactor `fetchers/github_fetcher.py`

**Files:**
- Modify: `fetchers/github_fetcher.py`

- [ ] **Step 1: Rewrite the file**

```python
"""Fetch trending AI repos from GitHub Search API (PAT optional but recommended)."""
import hashlib
import os
from datetime import date, timedelta

import requests

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_BASE = "https://api.github.com/search/repositories"
_LANG_MAP = {
    "Python": "Python", "TypeScript": "TS", "JavaScript": "JS",
    "Go": "Go", "Rust": "Rust", "Jupyter Notebook": "Jupyter",
}


class GitHubFetcher(BaseFetcher):
    source_id = "github"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["github"]
        queries = cfg.get("queries", ["agent LLM"])
        max_per_query = cfg.get("max_per_query", 8)
        days_back = cfg.get("days_back", 30)
        since = (target_date - timedelta(days=days_back)).isoformat()

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        seen: set[str] = set()
        items: list[Item] = []
        for q in queries:
            params = {
                "q": f"{q} created:>{since}",
                "sort": "stars",
                "order": "desc",
                "per_page": max_per_query,
            }
            try:
                resp = requests.get(_BASE, params=params, headers=headers, timeout=15)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  [warn] GitHub fetch failed for query '{q}': {e}")
                continue
            for repo in resp.json().get("items", []):
                full_name = repo.get("full_name", "")
                if full_name in seen:
                    continue
                seen.add(full_name)
                url = repo.get("html_url", "")
                desc = (repo.get("description") or "").strip()
                stars = int(repo.get("stargazers_count") or 0)
                lang = repo.get("language") or ""
                topics = repo.get("topics") or []
                pushed_at = repo.get("pushed_at") or ""
                tags = [_LANG_MAP.get(lang, lang)] if lang else []
                tags += [t for t in topics[:4] if t not in tags]
                item_id = hashlib.sha1(url.encode()).hexdigest()[:12]
                items.append(Item(
                    id=item_id,
                    source="github",
                    category="learning",
                    title=full_name,
                    url=url,
                    raw_content=desc,
                    stars=stars,
                    tags=tags[:5],
                    published_at=pushed_at,
                ))
        items.sort(key=lambda x: -x.stars)
        return items


REGISTRY.register(GitHubFetcher())
```

- [ ] **Step 2: Verify import**

Run: `python -c "import fetchers.github_fetcher; from fetchers.base import REGISTRY; print([f.source_id for f in REGISTRY.all()])"`
Expected: `['github']`.

- [ ] **Step 3: Commit**

```bash
git add fetchers/github_fetcher.py
git commit -m "refactor(github): inherit BaseFetcher + self-register"
```

---

## Task 7: Refactor `fetchers/hn_fetcher.py`

**Files:**
- Modify: `fetchers/hn_fetcher.py`

- [ ] **Step 1: Rewrite the file**

```python
"""Fetch AI-related stories from HackerNews via Algolia API."""
import hashlib
from datetime import date, datetime, timedelta, timezone

import requests

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item

_BASE = "https://hn.algolia.com/api/v1/search"


class HNFetcher(BaseFetcher):
    source_id = "hackernews"
    category = "learning"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["hackernews"]
        queries = cfg.get("queries", ["AI agent"])
        max_per_query = cfg.get("max_per_query", 10)
        min_points = cfg.get("min_points", 20)
        days_back = cfg.get("days_back", 3)

        since_ts = int(
            (datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
             - timedelta(days=days_back)).timestamp()
        )
        seen: set[str] = set()
        items: list[Item] = []
        for q in queries:
            params = {
                "query": q,
                "tags": "story",
                "numericFilters": f"created_at_i>{since_ts},points>{min_points}",
                "hitsPerPage": max_per_query,
            }
            try:
                resp = requests.get(_BASE, params=params, timeout=10)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  [warn] HN fetch failed for query '{q}': {e}")
                continue
            for hit in resp.json().get("hits", []):
                hn_id = str(hit.get("objectID", ""))
                if hn_id in seen:
                    continue
                seen.add(hn_id)
                title = hit.get("title") or ""
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hn_id}"
                points = int(hit.get("points") or 0)
                created = hit.get("created_at") or ""
                item_id = hashlib.sha1(hn_id.encode()).hexdigest()[:12]
                items.append(Item(
                    id=item_id,
                    source="hackernews",
                    category="learning",
                    title=title,
                    url=url,
                    raw_content=title,                   # HN has no body; use title as LLM input
                    stars=points,
                    published_at=created,
                ))
        items.sort(key=lambda x: -x.stars)
        return items


REGISTRY.register(HNFetcher())
```

- [ ] **Step 2: Verify import**

Run: `python -c "import fetchers.hn_fetcher; from fetchers.base import REGISTRY; print([f.source_id for f in REGISTRY.all()])"`
Expected: `['hackernews']`.

- [ ] **Step 3: Commit**

```bash
git add fetchers/hn_fetcher.py
git commit -m "refactor(hn): inherit BaseFetcher + self-register"
```

---

## Task 8: New `fetchers/nowcoder_fetcher.py` — 牛客面经 via RSSHub

**Files:**
- Create: `fetchers/nowcoder_fetcher.py`

- [ ] **Step 1: Implement the file**

```python
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
```

- [ ] **Step 2: Smoke-test (live call to RSSHub)**

Run:
```bash
python -c "
from datetime import date
import fetchers.nowcoder_fetcher as nf
items = nf.NowcoderFetcher().fetch(date.today())
print(f'fetched {len(items)} items')
for it in items[:3]:
    print(' -', it.title[:60])
"
```
Expected: prints "fetched N items" with N ≥ 1, plus 3 sample titles in Chinese.

If you get 0 items, RSSHub may be temporarily down — that's a known risk per SPEC §4. Re-run in 10 minutes; if still 0, log it but move on (the fetcher still imports correctly, which is what matters for the pipeline).

- [ ] **Step 3: Commit**

```bash
git add fetchers/nowcoder_fetcher.py
git commit -m "feat(fetcher): add Nowcoder 面经 fetcher via RSSHub"
```

---

## Task 9: New `fetchers/china_ai_fetcher.py` — 国内 AI 公司动态

**Strategy:** Aggregate from broad Chinese AI media (机器之心 / 量子位), then filter by the target-company keyword list from `config.yaml`. Much more reliable than chasing per-company RSS feeds.

**Files:**
- Create: `fetchers/china_ai_fetcher.py`

- [ ] **Step 1: Implement the file**

```python
"""Fetch Chinese AI company news from aggregator sites (机器之心 / 量子位 etc),
then filter entries that mention any of our target companies.
"""
import hashlib
import re
from datetime import date

import feedparser

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item


class ChinaAIFetcher(BaseFetcher):
    source_id = "china_ai"
    category = "job"

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["china_ai"]
        feeds = cfg.get("feeds", [])
        targets = [t.lower() for t in cfg.get("target_companies", [])]
        max_items = cfg.get("max_items", 15)

        all_items: list[Item] = []
        for feed_cfg in feeds:
            name = feed_cfg.get("name", "")
            url = feed_cfg.get("url", "")
            try:
                feed = feedparser.parse(url)
            except Exception as e:
                print(f"  [warn] china_ai feed '{name}' failed: {e}")
                continue
            if feed.bozo and not feed.entries:
                print(f"  [warn] china_ai feed '{name}' empty")
                continue
            for entry in feed.entries:
                item = _entry_to_item(entry, source_name=name, targets=targets)
                if item:
                    all_items.append(item)
        # Newest first
        all_items.sort(key=lambda x: x.published_at, reverse=True)
        return all_items[:max_items]


def _entry_to_item(entry, *, source_name: str, targets: list[str]) -> Item | None:
    title = (getattr(entry, "title", "") or "").strip()
    link = (getattr(entry, "link", "") or "").strip()
    if not title or not link:
        return None
    body_html = getattr(entry, "summary", "") or getattr(entry, "description", "")
    body_text = re.sub(r"<[^>]+>", " ", body_html)
    body_text = re.sub(r"\s+", " ", body_text).strip()

    haystack = (title + " " + body_text).lower()
    matched = [t for t in targets if t in haystack]
    if not matched:
        return None  # not about any target company → drop

    tags = [source_name] + [m.capitalize() for m in matched[:3]]
    item_id = hashlib.sha1(link.encode()).hexdigest()[:12]
    return Item(
        id=item_id,
        source="china_ai",
        category="job",
        title=title,
        url=link,
        raw_content=body_text[:1000],
        tags=tags[:5],
        published_at=getattr(entry, "published", "") or getattr(entry, "updated", ""),
    )


REGISTRY.register(ChinaAIFetcher())
```

- [ ] **Step 2: Smoke-test**

Run:
```bash
python -c "
from datetime import date
import fetchers.china_ai_fetcher as ca
items = ca.ChinaAIFetcher().fetch(date.today())
print(f'fetched {len(items)} items mentioning target companies')
for it in items[:5]:
    print(' -', it.tags, '|', it.title[:60])
"
```
Expected: N ≥ 1, items have company tags like ['机器之心', 'Deepseek'].

- [ ] **Step 3: Commit**

```bash
git add fetchers/china_ai_fetcher.py
git commit -m "feat(fetcher): add 国内 AI 公司动态 via 机器之心+量子位"
```

---

## Task 10: New `fetchers/coding_tool_fetcher.py` — AI Coding 工具采用信号

**Strategy:** Not a network call — this is a **derived fetcher** that filters items already collected by `hackernews` and `hf_papers`. It runs after the other fetchers but before scoring/rendering.

To stay within the BaseFetcher contract, this fetcher needs access to previously-collected items. We pass them via a constructor argument (mutated by `daily.py` between fetcher loops). This is the only fetcher that takes state, and the comment in the code makes that explicit.

**Files:**
- Create: `fetchers/coding_tool_fetcher.py`

- [ ] **Step 1: Implement the file**

```python
"""Derived fetcher: filter already-collected HN / HF / GitHub items for AI-coding-tool
adoption signals (Cursor / Claude Code / Cline / Aider / Copilot mentions).

Unlike other fetchers, this one does NO network calls. daily.py must populate
`pool` before calling .fetch(). The output reuses the original item's title/url
but re-tags it under source='coding_tool' and category='job'.
"""
import hashlib
from datetime import date

from fetchers.base import BaseFetcher, REGISTRY
from pipeline.config import get_config
from pipeline.schema import Item


class CodingToolFetcher(BaseFetcher):
    source_id = "coding_tool"
    category = "job"

    # daily.py mutates this between the main fetcher loop and calling .fetch()
    pool: list[Item] = []

    def fetch(self, target_date: date) -> list[Item]:
        cfg = get_config()["sources"]["coding_tool"]
        keywords = [k.lower() for k in cfg.get("keywords", [])]
        max_items = cfg.get("max_items", 5)

        results: list[Item] = []
        for src_item in self.pool:
            if src_item.source not in {"hackernews", "hf_papers", "github"}:
                continue
            haystack = (src_item.title + " " + src_item.raw_content).lower()
            matched = [k for k in keywords if k in haystack]
            if not matched:
                continue
            derived_url = src_item.url + "#coding_tool"  # disambiguate from original
            new_id = hashlib.sha1(derived_url.encode()).hexdigest()[:12]
            results.append(Item(
                id=new_id,
                source="coding_tool",
                category="job",
                title=src_item.title,
                url=src_item.url,
                raw_content=src_item.raw_content,
                stars=src_item.stars,
                tags=[m.title() for m in matched[:3]] + [f"来源: {src_item.source}"],
                authors=src_item.authors,
                published_at=src_item.published_at,
            ))
        results.sort(key=lambda x: -x.stars)
        return results[:max_items]


REGISTRY.register(CodingToolFetcher())
```

- [ ] **Step 2: Smoke-test with synthetic pool**

Run:
```bash
python -c "
from datetime import date
from pipeline.schema import Item
import fetchers.coding_tool_fetcher as ct
f = ct.CodingToolFetcher()
f.pool = [
    Item(id='1', source='hackernews', title='Why we switched from Copilot to Claude Code', url='https://news.ycombinator.com/item?id=1', raw_content='migration story', stars=580),
    Item(id='2', source='hackernews', title='Show HN: AI tool', url='https://x', raw_content='unrelated', stars=200),
]
items = f.fetch(date.today())
print(f'derived {len(items)} signal items')
for it in items: print(' -', it.tags, '|', it.title[:50])
"
```
Expected: `derived 1 signal items` with tags `['Copilot', 'Claude Code', '来源: hackernews']`.

- [ ] **Step 3: Commit**

```bash
git add fetchers/coding_tool_fetcher.py
git commit -m "feat(fetcher): add derived coding-tool adoption signal fetcher"
```

---

## Task 11: Refactor `pipeline/scorer.py` — config-driven, per-category

**Files:**
- Modify: `pipeline/scorer.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_scorer.py`:

```python
"""Scorer reads weights from config.yaml and applies per-category logic."""
import pytest

from pipeline.schema import Item
from pipeline.scorer import score_item, score_all, dedup


def test_learning_item_gets_learning_weights():
    item = Item(id="x", source="arxiv", category="learning",
                title="An MCP-based agent framework", url="u",
                raw_content="multi-agent + RAG")
    s = score_item(item)
    # agent (3) + mcp (2.5) + rag (1.5) + multi-agent(3) + retrieval(1) > 8 → capped at 10
    assert s >= 8.0


def test_job_item_uses_job_weights():
    item = Item(id="x", source="nowcoder", category="job",
                title="字节算法岗 transformer + RAG 面经", url="u",
                raw_content="问了 attention 和 prompt engineering")
    s = score_item(item)
    # 字节(2.5) + transformer(3) + rag(2.5) + attention(2.5) + prompt(2) → cap 10
    assert s >= 8.0


def test_learning_keyword_doesnt_apply_to_job_item():
    """A job-category item with 'agent' should use job weights only."""
    item = Item(id="x", source="nowcoder", category="job",
                title="agent 相关八股", url="u", raw_content="")
    # Under 'job' weights, agent=2.5; learning's agent=3.0 should NOT apply.
    s = score_item(item)
    # base(4.0) + agent_job(2.5) = 6.5
    assert 6.0 <= s <= 7.5


def test_author_bonus_applies(sample_learning_item):
    sample_learning_item.authors = ["Anthropic Research"]
    s = score_item(sample_learning_item)
    # author bonus 2.0 included
    base = score_item(Item(id="y", source="arxiv", category="learning",
                           title=sample_learning_item.title, url="u2",
                           raw_content=sample_learning_item.raw_content,
                           tags=sample_learning_item.tags))
    assert s - base == pytest.approx(2.0, abs=0.01)


def test_dedup_removes_duplicate_urls():
    a = Item(id="1", source="arxiv", category="learning", title="A", url="https://x/1")
    b = Item(id="2", source="hackernews", category="learning", title="A copy", url="https://x/1")
    out = dedup([a, b])
    assert len(out) == 1


def test_dedup_removes_near_title_dup():
    a = Item(id="1", source="arxiv", category="learning",
             title="MCP Protocol v3 Released", url="https://x/1", score=9.0)
    b = Item(id="2", source="hackernews", category="learning",
             title="MCP Protocol v3 Released!", url="https://x/2", score=7.0)
    out = dedup([a, b])
    assert len(out) == 1
    assert out[0].score == 9.0  # higher-scored one wins
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_scorer.py -v`
Expected: most fail (current scorer hardcodes a single weight table and references `raw_abstract`).

- [ ] **Step 3: Rewrite `pipeline/scorer.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_scorer.py -v`
Expected: all 6 pass.

- [ ] **Step 5: Commit**

```bash
git add pipeline/scorer.py tests/test_scorer.py
git commit -m "feat(scorer): config-driven weights + per-category scoring"
```

---

## Task 12: Refactor `pipeline/llm.py` — provider abstraction + 3 prompt templates

**Files:**
- Modify: `pipeline/llm.py`
- Create: `tests/test_llm_providers.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_llm_providers.py`:

```python
"""LLM provider abstraction + three prompt templates."""
import pytest

from pipeline.schema import Item
from pipeline.llm import (
    get_provider,
    MockProvider,
    summarize_all,
    summarize_daily,
)


def test_mock_provider_returns_raw_content_for_summary():
    p = MockProvider()
    item = Item(id="x", source="arxiv", category="learning",
                title="t", url="u", raw_content="some abstract here")
    out = p.summarize_item(item)
    assert "some abstract" in out


def test_mock_provider_daily_returns_valid_structure():
    p = MockProvider()
    items = [Item(id="x", source="arxiv", category="learning",
                  title="agent paper", url="u")]
    daily = p.summarize_daily(items)
    assert set(daily.keys()) == {"headline", "ai_trends", "job_signals"}
    assert len(daily["ai_trends"]) == 3
    assert len(daily["job_signals"]) == 3


def test_summarize_all_fills_empty_summaries():
    items = [
        Item(id="1", source="arxiv", category="learning",
             title="t1", url="u1", raw_content="abstract one"),
        Item(id="2", source="arxiv", category="learning",
             title="t2", url="u2", raw_content="abstract two", summary="already done"),
    ]
    out = summarize_all(items, provider=MockProvider())
    assert out[0].summary != ""
    assert out[1].summary == "already done"  # unchanged


def test_summarize_daily_returns_dict():
    items = [Item(id="x", source="arxiv", category="learning",
                  title="t", url="u")]
    daily = summarize_daily(items, provider=MockProvider())
    assert isinstance(daily, dict)
    assert "headline" in daily


def test_get_provider_returns_mock_when_configured(monkeypatch, repo_root):
    monkeypatch.chdir(repo_root)
    from pipeline.config import get_config
    get_config.cache_clear()
    # We can't easily change config.yaml from a test, so test get_provider("mock") direct
    p = get_provider("mock")
    assert isinstance(p, MockProvider)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_llm_providers.py -v`
Expected: ImportError on `MockProvider`, `summarize_daily`, etc.

- [ ] **Step 3: Rewrite `pipeline/llm.py`**

```python
"""LLM provider abstraction supporting two tasks:
  A) summarize_item    — per-item Chinese summary (EN→ZH or ZH refine)
  B) summarize_daily   — daily synthesis (headline + 3 ai_trends + 3 job_signals)

Switch provider in config.yaml → llm.provider ("deepseek" | "mock").
"""
import json
import os
from abc import ABC, abstractmethod

from pipeline.config import get_config
from pipeline.schema import Item


# ── Prompts ────────────────────────────────────────────────────────────────

_PROMPT_TRANSLATE_EN = """你是 AI 领域研究助手，专注于 Agent / 多智能体 / MCP / RAG 方向。
请将下面的英文论文摘要 / 仓库描述 / 帖子标题精炼成中文摘要：
1. 第一句：核心贡献 / 这是什么
2. 第二句：关键结果或亮点数字
3. 第三句（可选）：与 Agent/RAG/MCP 方向的关联价值
字数 80-120 字，技术准确，直接输出中文，不加引号或前缀。"""

_PROMPT_REFINE_ZH = """你是中国 AI 求职情报分析师。请把下面这段中文原文精炼成 60-80 字要点：
- 如果是面经：提炼"被问了什么题型、哪家公司、哪个岗位"
- 如果是公司动态：提炼"谁发布了什么、技术亮点、对行业影响"
直接输出精炼后中文，不加引号或前缀。"""

_PROMPT_DAILY = """你是 AI 信息分析师。下面是今天聚合到的内容，分为「AI 学习」和「求职情报」两类。
请生成今日综合判断，**严格输出 JSON 对象**（不要 markdown 代码块）：

{
  "headline": "<30 字以内一句话，今天最值得知道的事>",
  "ai_trends":   ["<30 字>", "<30 字>", "<30 字>"],
  "job_signals": ["<30 字>", "<30 字>", "<30 字>"]
}

ai_trends 提取学习线的 3 个最重要趋势；job_signals 提取求职线的 3 个最重要信号。
如果某一线数据不足，对应条目写"今日数据较少"。
"""


# ── Provider abstraction ───────────────────────────────────────────────────

class BaseLLM(ABC):
    @abstractmethod
    def summarize_item(self, item: Item) -> str: ...

    @abstractmethod
    def summarize_daily(self, items: list[Item]) -> dict: ...


class MockProvider(BaseLLM):
    """No-API-call provider. Returns raw_content[:200] and a stub daily dict."""

    def summarize_item(self, item: Item) -> str:
        if item.raw_content.strip():
            return item.raw_content[:200]
        return item.title

    def summarize_daily(self, items: list[Item]) -> dict:
        learning = [i for i in items if i.category == "learning"][:1]
        job = [i for i in items if i.category == "job"][:1]
        headline_src = learning[0].title if learning else "今日 AI 数据汇总完成"
        return {
            "headline": headline_src[:30],
            "ai_trends":   ["mock: 学习趋势 1", "mock: 学习趋势 2", "mock: 学习趋势 3"],
            "job_signals": ["mock: 求职信号 1", "mock: 求职信号 2", "mock: 求职信号 3"],
        }


class DeepSeekProvider(BaseLLM):
    """OpenAI-SDK-compatible client pointed at DeepSeek."""

    def __init__(self) -> None:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError("pip install openai") from e
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise EnvironmentError("DEEPSEEK_API_KEY not set")
        cfg = get_config()["llm"]
        self._client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
        self._model = cfg.get("model", "deepseek-chat")
        self._temperature = cfg.get("temperature", 0.3)
        self._max_summary = cfg.get("max_tokens_summary", 250)
        self._max_daily = cfg.get("max_tokens_daily", 600)

    def summarize_item(self, item: Item) -> str:
        if not item.raw_content.strip():
            return item.title
        # English source → translate; Chinese source → refine
        is_chinese = item.source in {"nowcoder", "china_ai"}
        system = _PROMPT_REFINE_ZH if is_chinese else _PROMPT_TRANSLATE_EN
        user = f"标题：{item.title}\n\n原文：{item.raw_content[:1200]}"
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system},
                      {"role": "user",   "content": user}],
            max_tokens=self._max_summary,
            temperature=self._temperature,
        )
        return (resp.choices[0].message.content or "").strip()

    def summarize_daily(self, items: list[Item]) -> dict:
        learning = sorted([i for i in items if i.category == "learning"],
                          key=lambda x: -x.score)[:8]
        job = sorted([i for i in items if i.category == "job"],
                     key=lambda x: -x.score)[:8]

        def bulletize(group: list[Item]) -> str:
            return "\n".join(
                f"- [{i.source}] {i.title} | 摘要：{(i.summary or i.raw_content)[:120]}"
                for i in group
            ) or "（无数据）"

        user = (
            "【学习线 top items】\n" + bulletize(learning) +
            "\n\n【求职线 top items】\n" + bulletize(job)
        )
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": _PROMPT_DAILY},
                      {"role": "user",   "content": user}],
            max_tokens=self._max_daily,
            temperature=self._temperature,
        )
        text = (resp.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].lstrip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"  [warn] daily summary JSON parse failed; raw: {text[:200]}")
            return {
                "headline": "今日综合判断生成失败，请查看下方分区内容",
                "ai_trends":   ["LLM 返回格式异常", "—", "—"],
                "job_signals": ["LLM 返回格式异常", "—", "—"],
            }


# ── Factory + convenience ──────────────────────────────────────────────────

def get_provider(name: str | None = None) -> BaseLLM:
    if name is None:
        name = get_config()["llm"].get("provider", "mock")
    if name == "mock":
        return MockProvider()
    if name == "deepseek":
        return DeepSeekProvider()
    raise ValueError(f"Unknown LLM provider: {name}")


def summarize_all(items: list[Item], provider: BaseLLM | str | None = None) -> list[Item]:
    p = provider if isinstance(provider, BaseLLM) else get_provider(provider)
    for item in items:
        if not item.summary:
            try:
                item.summary = p.summarize_item(item)
            except Exception as e:
                print(f"  [warn] summarize failed for {item.id}: {e}")
                item.summary = item.raw_content[:200] or item.title
    return items


def summarize_daily(items: list[Item], provider: BaseLLM | str | None = None) -> dict:
    p = provider if isinstance(provider, BaseLLM) else get_provider(provider)
    try:
        return p.summarize_daily(items)
    except Exception as e:
        print(f"  [warn] daily summary failed: {e}")
        return {
            "headline": "今日综合判断暂不可用",
            "ai_trends":   ["—", "—", "—"],
            "job_signals": ["—", "—", "—"],
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_llm_providers.py -v`
Expected: all 5 pass.

- [ ] **Step 5: Commit**

```bash
git add pipeline/llm.py tests/test_llm_providers.py
git commit -m "feat(llm): provider abstraction + 3 prompts (translate/refine/daily)"
```

---

## Task 13: New `pipeline/summarizer.py` — orchestrates daily summary + persistence

**Files:**
- Create: `pipeline/summarizer.py`
- Create: `tests/test_summarizer.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_summarizer.py`:

```python
"""Summarizer writes daily summary JSON to data/summaries/<date>.json."""
import json
from datetime import date
from pathlib import Path

import pytest

from pipeline.schema import Item
from pipeline.summarizer import build_daily_summary, write_summary


def test_build_daily_summary_includes_stats():
    items = [
        Item(id="1", source="arxiv", category="learning", title="A", url="u1", score=8.5),
        Item(id="2", source="nowcoder", category="job", title="B", url="u2", score=9.5),
        Item(id="3", source="hf_papers", category="learning", title="C", url="u3", score=6.0),
    ]
    summary = build_daily_summary(items, llm_provider="mock", target_date=date(2026, 5, 17))
    assert summary["date"] == "2026-05-17"
    assert summary["stats"]["total_items"] == 3
    assert summary["stats"]["learning_count"] == 2
    assert summary["stats"]["job_count"] == 1
    assert summary["stats"]["top_score"] == 9.5
    assert summary["stats"]["top_item_title"] == "B"
    assert summary["headline"]
    assert len(summary["ai_trends"]) == 3
    assert len(summary["job_signals"]) == 3


def test_write_summary_creates_file(tmp_path: Path):
    s = {"date": "2026-05-17", "headline": "h", "ai_trends": [], "job_signals": [], "stats": {}}
    out = write_summary(s, summaries_dir=tmp_path)
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8"))["headline"] == "h"


def test_build_summary_handles_empty_items():
    summary = build_daily_summary([], llm_provider="mock", target_date=date(2026, 5, 17))
    assert summary["stats"]["total_items"] == 0
    assert summary["stats"]["top_item_title"] == "—"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_summarizer.py -v`
Expected: ImportError on `pipeline.summarizer`.

- [ ] **Step 3: Implement `pipeline/summarizer.py`**

```python
"""Build and persist the per-day summary JSON consumed by:
  - templates/partials/summary_block.html.j2 (today's headline + trends + signals)
  - future weekly/monthly aggregator (reads from data/summaries/)
"""
import json
from datetime import date, datetime
from pathlib import Path

from pipeline.llm import summarize_daily
from pipeline.schema import Item


_SUMMARIES_DIR = Path(__file__).parent.parent / "data" / "summaries"


def build_daily_summary(
    items: list[Item],
    *,
    llm_provider: str | None = None,
    target_date: date | None = None,
) -> dict:
    target_date = target_date or date.today()
    learning = [i for i in items if i.category == "learning"]
    job = [i for i in items if i.category == "job"]

    if items:
        top = max(items, key=lambda x: x.score)
        top_score = top.score
        top_title = top.title
    else:
        top_score = 0.0
        top_title = "—"

    daily = summarize_daily(items, provider=llm_provider)

    return {
        "date": target_date.isoformat(),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "headline":     daily.get("headline", ""),
        "ai_trends":    daily.get("ai_trends",   ["—", "—", "—"])[:3],
        "job_signals":  daily.get("job_signals", ["—", "—", "—"])[:3],
        "stats": {
            "total_items":    len(items),
            "learning_count": len(learning),
            "job_count":      len(job),
            "top_score":      top_score,
            "top_item_title": top_title,
        },
    }


def write_summary(summary: dict, summaries_dir: Path = _SUMMARIES_DIR) -> Path:
    summaries_dir.mkdir(parents=True, exist_ok=True)
    out = summaries_dir / f"{summary['date']}.json"
    out.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_summarizer.py -v`
Expected: all 3 pass.

- [ ] **Step 5: Commit**

```bash
git add pipeline/summarizer.py tests/test_summarizer.py
git commit -m "feat(summarizer): build + persist daily summary JSON"
```

---

## Task 14: New `pipeline/aggregator.py` — v3 weekly/monthly stub

**Files:**
- Create: `pipeline/aggregator.py`

- [ ] **Step 1: Implement the stub**

```python
"""v3 aggregator: weekly + monthly rollups. Stub interface defined now so that
docs/SPEC §12 commitments are visible in the codebase; bodies fill in v3.
"""
from datetime import date
from pathlib import Path


_AGGREGATES_DIR = Path(__file__).parent.parent / "data" / "aggregates"


def build_weekly(end_date: date) -> dict:
    """Aggregate the 7-day window ending on `end_date` into a weekly summary.

    v3 will:
      1. Load 7 days of data/summaries/*.json + data/processed/*.json
      2. Call LLM to cluster topics + produce a 7-day narrative
      3. Return {"week": "2026-W20", "narrative": "...", "highlights": [...], "stats": {...}}
    """
    raise NotImplementedError("weekly aggregator lands in v3")


def build_monthly(year: int, month: int) -> dict:
    """Aggregate one calendar month from daily summaries.

    v3 will read data/summaries/<year>-<month>-*.json and produce a trend report.
    """
    raise NotImplementedError("monthly aggregator lands in v3")


def aggregates_dir() -> Path:
    return _AGGREGATES_DIR
```

- [ ] **Step 2: Smoke-test the import**

Run: `python -c "from pipeline.aggregator import build_weekly, build_monthly, aggregates_dir; print(aggregates_dir())"`
Expected: prints `.../data/aggregates`.

- [ ] **Step 3: Commit**

```bash
git add pipeline/aggregator.py
git commit -m "feat(aggregator): stub interface for v3 weekly/monthly"
```

---

## Task 15: Verify archive directory structure is committed

**Files:**
- Verify: `data/summaries/.gitkeep`, `data/aggregates/weekly/.gitkeep`, `data/aggregates/monthly/.gitkeep`, `docs/weekly/.gitkeep`, `docs/monthly/.gitkeep` are all tracked by git

- [ ] **Step 1: List tracked .gitkeep files**

Run: `git ls-files | grep gitkeep`
Expected: prints all 5 paths above. If T0 step 3 was committed correctly, they should be there. If any are missing, `git add <path>` and commit with `chore: ensure archive dirs are tracked`.

- [ ] **Step 2: No commit needed if all 5 are tracked.**

---

## Task 16: New `templates/base.html.j2` — masthead + footer + shared CSS

**Files:**
- Create: `templates/base.html.j2`

- [ ] **Step 1: Create the base template**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{% block title %}AI 每日早报{% endblock %}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
  {% block head_extra %}{% endblock %}
  <style>
    :root {
      --paper:    #f6f2ea;
      --paper2:   #ffffff;
      --paper3:   #f0ebe0;
      --border:   #ddd5c4;
      --border2:  #c8bfae;
      --navy:     #1e3557;
      --navy2:    #2a4a76;
      --coral:    #c94428;
      --coral2:   #e05c3a;
      --green:    #2a7d4f;
      --gold:     #b8872a;
      --text:     #1a1410;
      --text2:    #6b5e52;
      --text3:    #a0917f;
      --tag-bg:   #eee8db;
      --shadow:   0 1px 3px rgba(30,25,18,0.08), 0 4px 12px rgba(30,25,18,0.04);
      --shadow-lg:0 2px 8px rgba(30,25,18,0.10), 0 8px 24px rgba(30,25,18,0.06);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body {
      background: var(--paper);
      color: var(--text);
      font-family: 'Outfit', sans-serif;
      font-size: 14px;
      line-height: 1.65;
      min-width: 1200px;          /* desktop-only per SPEC §9 */
    }
    a { color: var(--navy); text-decoration: none; }
    a:hover { color: var(--coral); text-decoration: underline; text-underline-offset: 2px; }

    /* ─── Masthead ─── */
    .masthead {
      background: var(--navy);
      padding: 0 32px;
      display: flex;
      align-items: stretch;
      gap: 0;
      border-bottom: 3px solid var(--coral);
    }
    .masthead-brand {
      padding: 20px 28px 20px 0;
      border-right: 1px solid rgba(255,255,255,0.12);
      display: flex; flex-direction: column; justify-content: center;
    }
    .masthead-brand h1 {
      font-family: 'Cormorant Garamond', serif;
      font-size: 32px; font-weight: 700; color: #fff;
      letter-spacing: -0.5px; line-height: 1.1;
    }
    .masthead-brand .tagline {
      font-size: 11px; color: rgba(255,255,255,0.5);
      font-weight: 400; letter-spacing: 2px;
      text-transform: uppercase; margin-top: 3px;
    }
    .masthead-meta {
      padding: 20px 0 20px 28px;
      display: flex; flex-direction: column; justify-content: center; gap: 6px;
    }
    .masthead-date {
      font-size: 13px; color: rgba(255,255,255,0.75);
      font-weight: 500; letter-spacing: 0.5px;
    }
    .masthead-pills { display: flex; gap: 8px; flex-wrap: wrap; }
    .masthead-pill {
      font-size: 11px; padding: 2px 10px; border-radius: 2px;
      font-weight: 600; letter-spacing: 0.3px;
      border: 1px solid rgba(255,255,255,0.2);
      color: rgba(255,255,255,0.7);
      background: rgba(255,255,255,0.06);
    }
    .masthead-pill.papers { border-color: rgba(201,68,40,0.6);  color: #f4a58f; background: rgba(201,68,40,0.15); }
    .masthead-pill.repos  { border-color: rgba(42,125,79,0.6);  color: #7ed4a8; background: rgba(42,125,79,0.15); }
    .masthead-pill.jobs   { border-color: rgba(184,135,42,0.6); color: #f0cc7a; background: rgba(184,135,42,0.15); }

    /* ─── Section title strip ─── */
    .section-eyebrow {
      display: flex; align-items: center; gap: 10px; margin-bottom: 14px;
    }
    .section-eyebrow::before, .section-eyebrow::after {
      content: ''; flex: 1; height: 1px; background: var(--border);
    }
    .section-eyebrow span {
      font-size: 10px; font-weight: 700; letter-spacing: 2.5px;
      text-transform: uppercase; color: var(--coral); white-space: nowrap;
    }

    /* ─── Card ─── */
    .card {
      background: var(--paper2);
      border: 1px solid var(--border);
      border-radius: 4px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }
    .card-header {
      padding: 12px 18px;
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between;
      background: var(--paper2);
    }
    .card-header h2 {
      font-family: 'Cormorant Garamond', serif;
      font-size: 17px; font-weight: 600;
      color: var(--navy); letter-spacing: -0.2px;
    }
    .card-badge {
      font-size: 10px; font-weight: 600; letter-spacing: 1px;
      text-transform: uppercase; padding: 2px 8px; border-radius: 2px;
    }
    .badge-coral { background: rgba(201,68,40,0.10); color: var(--coral); border: 1px solid rgba(201,68,40,0.2); }
    .badge-navy  { background: rgba(30,53,87,0.08);  color: var(--navy);  border: 1px solid rgba(30,53,87,0.15); }
    .badge-green { background: rgba(42,125,79,0.08); color: var(--green); border: 1px solid rgba(42,125,79,0.2); }
    .badge-gold  { background: rgba(184,135,42,0.10);color: var(--gold);  border: 1px solid rgba(184,135,42,0.2); }

    /* ─── Tag chip ─── */
    .tag {
      font-size: 10px; font-weight: 500;
      padding: 2px 8px; border-radius: 2px;
      background: var(--tag-bg); color: var(--text2);
      border: 1px solid var(--border);
      font-family: 'DM Mono', monospace;
    }

    /* ─── Footer ─── */
    .footer {
      text-align: center;
      padding: 18px;
      color: var(--text3); font-size: 11px;
      border-top: 1px solid var(--border);
      background: var(--paper2);
      letter-spacing: 0.5px;
    }
    .footer a { color: var(--navy); }

    {% block extra_styles %}{% endblock %}
  </style>
</head>
<body>

<header class="masthead">
  <div class="masthead-brand">
    <h1>{% block masthead_title %}🤖 AI 每日早报{% endblock %}</h1>
    <div class="tagline">Intelligence · Research · Signal</div>
  </div>
  <div class="masthead-meta">
    <div class="masthead-date">{% block masthead_date %}{{ date_str }} &nbsp;·&nbsp; {{ weekday_str }}{% endblock %}</div>
    {% block masthead_pills %}{% endblock %}
  </div>
</header>

{% block body %}{% endblock %}

<div class="footer">
  {% block footer %}
  AI Pipeline 自动生成 &nbsp;·&nbsp; {{ generated_at }} &nbsp;·&nbsp; <a href="./archive.html">归档</a> &nbsp;·&nbsp; <a href="https://github.com/Diezqu/getnews" target="_blank">GitHub 仓库</a>
  {% endblock %}
</div>

{% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: Verify Jinja parses cleanly**

Run:
```bash
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
env.get_template('base.html.j2')
print('base.html.j2 OK')
"
```
Expected: `base.html.j2 OK`.

- [ ] **Step 3: Commit**

```bash
git add templates/base.html.j2
git commit -m "feat(template): add base.html.j2 with masthead + footer + shared CSS"
```

---

## Task 17: Create all card partials under `templates/partials/`

**Files:**
- Create: `templates/partials/summary_block.html.j2`
- Create: `templates/partials/card_paper.html.j2`
- Create: `templates/partials/card_repo.html.j2`
- Create: `templates/partials/card_hn.html.j2`
- Create: `templates/partials/card_job.html.j2`
- Create: `templates/partials/card_company.html.j2`
- Create: `templates/partials/card_coding_tool.html.j2`
- Create: `templates/partials/radar.html.j2`
- Create: `templates/partials/trend_chart.html.j2`

- [ ] **Step 1: `summary_block.html.j2`**

```html
{# Top "今日总 Summary" — drops in below the masthead. Renders the headline +
   two-column 3+3 bullet list. Inputs: summary (dict from pipeline/summarizer). #}
<style>
  .today-summary {
    background: var(--paper2);
    border-left: 3px solid var(--navy);
    border-radius: 0 4px 4px 0;
    margin: 24px 32px 0;
    padding: 20px 28px 22px;
    box-shadow: var(--shadow);
  }
  .today-summary .headline {
    font-family: 'Cormorant Garamond', serif;
    font-size: 22px; font-weight: 700;
    color: var(--coral); line-height: 1.35;
    margin-bottom: 14px;
  }
  .today-summary .divider {
    border-top: 1px solid var(--border); margin-bottom: 16px;
  }
  .today-summary .ts-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 32px;
  }
  .today-summary .ts-col h3 {
    font-size: 11px; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--text3); margin-bottom: 10px;
  }
  .today-summary .ts-col h3.learn { border-bottom: 2px solid var(--green); padding-bottom: 4px; display: inline-block; }
  .today-summary .ts-col h3.job   { border-bottom: 2px solid var(--gold);  padding-bottom: 4px; display: inline-block; }
  .today-summary .ts-col ul { list-style: none; }
  .today-summary .ts-col li {
    font-size: 13px; color: var(--text);
    padding: 6px 0 6px 16px; position: relative;
    border-bottom: 1px dashed var(--paper3);
    line-height: 1.5;
  }
  .today-summary .ts-col li:last-child { border-bottom: none; }
  .today-summary .ts-col li::before {
    content: '▸'; position: absolute; left: 0; top: 5px;
    color: var(--coral); font-size: 11px;
  }
</style>

<section class="today-summary">
  <div class="headline">💡 {{ summary.headline }}</div>
  <div class="divider"></div>
  <div class="ts-grid">
    <div class="ts-col">
      <h3 class="learn">📚 AI 趋势</h3>
      <ul>
        {% for line in summary.ai_trends %}<li>{{ line }}</li>{% endfor %}
      </ul>
    </div>
    <div class="ts-col">
      <h3 class="job">💼 求职信号</h3>
      <ul>
        {% for line in summary.job_signals %}<li>{{ line }}</li>{% endfor %}
      </ul>
    </div>
  </div>
</section>
```

- [ ] **Step 2: `card_paper.html.j2`**

```html
{# Paper card — used for both arXiv (badge=navy) and HF (badge=green).
   Inputs: card_title (str), card_badge_label (str), card_badge_class (str), items (list[Item]),
           show_upvotes (bool, default false). #}
<style>
  .paper-item {
    padding: 14px 18px;
    border-bottom: 1px solid var(--paper3);
    transition: background 0.15s;
  }
  .paper-item:hover { background: rgba(30,53,87,0.02); }
  .paper-item:last-child { border-bottom: none; }
  .paper-title { font-size: 13px; font-weight: 600; color: var(--text); line-height: 1.45; margin-bottom: 4px; }
  .paper-title a { color: inherit; }
  .paper-title a:hover { color: var(--navy); text-decoration: none; }
  .paper-meta {
    font-size: 11px; color: var(--text3);
    margin-bottom: 6px; font-family: 'DM Mono', monospace;
  }
  .paper-abstract { font-size: 12.5px; color: var(--text2); line-height: 1.6; }
  .paper-footer { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
  .score-chip {
    font-size: 10px; font-weight: 700; font-family: 'DM Mono', monospace;
    padding: 2px 7px; border-radius: 2px;
    background: rgba(30,53,87,0.08); color: var(--navy);
    border: 1px solid rgba(30,53,87,0.15);
    margin-left: auto;
  }
  .score-chip.high {
    background: rgba(201,68,40,0.10); color: var(--coral);
    border-color: rgba(201,68,40,0.2);
  }
  .upvote-chip {
    font-size: 10px; font-weight: 700;
    padding: 2px 7px; border-radius: 2px;
    background: rgba(42,125,79,0.08); color: var(--green);
    border: 1px solid rgba(42,125,79,0.2);
    margin-left: auto;
  }
</style>

<div class="card">
  <div class="card-header">
    <h2>{{ card_title }}</h2>
    <span class="card-badge {{ card_badge_class }}">{{ card_badge_label }}</span>
  </div>
  {% for item in items %}
  <div class="paper-item">
    <div class="paper-title"><a href="{{ item.url }}" target="_blank" rel="noopener">{{ item.title }}</a></div>
    {% if item.authors or item.published_at or item.stars %}
    <div class="paper-meta">
      {% if item.authors %}{{ item.authors[:3]|join(' · ') }}{% if item.authors|length > 3 %} et al.{% endif %}{% endif %}
      {% if item.published_at %} &nbsp;·&nbsp; {{ item.published_at[:10] }}{% endif %}
      {% if show_upvotes and item.stars %} &nbsp;·&nbsp; {{ item.stars }} upvotes{% endif %}
    </div>
    {% endif %}
    <div class="paper-abstract">{{ item.summary if item.summary else item.raw_content[:240] }}</div>
    <div class="paper-footer">
      {% for tag in item.tags[:4] %}<span class="tag">{{ tag }}</span>{% endfor %}
      {% if show_upvotes and item.stars %}
        <span class="upvote-chip">{{ item.stars }} 👍</span>
      {% else %}
        <span class="score-chip {% if item.score >= 8 %}high{% endif %}">{{ "%.1f"|format(item.score) }}</span>
      {% endif %}
    </div>
  </div>
  {% else %}
  <div class="paper-item" style="color:var(--text3);font-size:12px;">今日暂无数据</div>
  {% endfor %}
</div>
```

- [ ] **Step 3: `card_repo.html.j2`**

```html
{# GitHub repo card. Inputs: items (list[Item]). #}
<style>
  .repo-item { padding: 14px 18px; border-bottom: 1px solid var(--paper3); transition: background 0.15s; }
  .repo-item:hover { background: rgba(30,53,87,0.02); }
  .repo-item:last-child { border-bottom: none; }
  .repo-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 5px; }
  .repo-title { font-size: 13px; font-weight: 600; color: var(--text); }
  .repo-title a { color: inherit; }
  .repo-title a:hover { color: var(--navy); }
  .repo-stars {
    font-size: 12px; font-weight: 700; font-family: 'DM Mono', monospace;
    color: var(--gold); white-space: nowrap; flex-shrink: 0;
  }
  .repo-desc { font-size: 12px; color: var(--text2); line-height: 1.55; margin-bottom: 6px; }
  .repo-tags { display: flex; gap: 5px; flex-wrap: wrap; }
</style>

<div class="card">
  <div class="card-header">
    <h2>GitHub 新兴仓库</h2>
    <span class="card-badge badge-green">快速涨星</span>
  </div>
  {% for item in items %}
  <div class="repo-item">
    <div class="repo-header">
      <div class="repo-title"><a href="{{ item.url }}" target="_blank" rel="noopener">{{ item.title }}</a></div>
      {% if item.stars > 0 %}<div class="repo-stars">★ {{ item.stars | format_stars }}</div>{% endif %}
    </div>
    <div class="repo-desc">{{ item.summary if item.summary else item.raw_content[:160] }}</div>
    <div class="repo-tags">
      {% for tag in item.tags[:3] %}<span class="tag">{{ tag }}</span>{% endfor %}
    </div>
  </div>
  {% else %}
  <div class="repo-item" style="color:var(--text3);font-size:12px;">今日暂无 GitHub 数据</div>
  {% endfor %}
</div>
```

- [ ] **Step 4: `card_hn.html.j2`**

```html
{# Hacker News card. Inputs: items (list[Item]). #}
<style>
  .hn-item {
    padding: 10px 18px; border-bottom: 1px solid var(--paper3);
    display: flex; gap: 12px; align-items: baseline;
    transition: background 0.15s;
  }
  .hn-item:hover { background: rgba(30,53,87,0.02); }
  .hn-item:last-child { border-bottom: none; }
  .hn-rank {
    font-family: 'Cormorant Garamond', serif;
    font-size: 18px; font-weight: 700;
    color: var(--border2); min-width: 22px; line-height: 1; padding-top: 1px;
  }
  .hn-body { flex: 1; }
  .hn-title { font-size: 12.5px; font-weight: 500; color: var(--text); line-height: 1.45; margin-bottom: 3px; }
  .hn-title a { color: inherit; }
  .hn-title a:hover { color: var(--navy); }
  .hn-meta { font-size: 11px; color: var(--text3); font-family: 'DM Mono', monospace; }
  .hn-pts { color: var(--coral); font-weight: 600; }
</style>

<div class="card">
  <div class="card-header">
    <h2>HackerNews AI 热议</h2>
    <span class="card-badge badge-coral">高分讨论</span>
  </div>
  {% for item in items %}
  <div class="hn-item">
    <div class="hn-rank">{{ loop.index }}</div>
    <div class="hn-body">
      <div class="hn-title"><a href="{{ item.url }}" target="_blank" rel="noopener">{{ item.title }}</a></div>
      <div class="hn-meta">
        <span class="hn-pts">{{ item.stars }} pts</span>
        {% if item.published_at %} &nbsp;·&nbsp; {{ item.published_at[:10] }}{% endif %}
      </div>
    </div>
  </div>
  {% else %}
  <div class="hn-item" style="color:var(--text3);font-size:12px;">今日暂无 HackerNews 数据</div>
  {% endfor %}
</div>
```

- [ ] **Step 5: `card_job.html.j2`** (牛客面经)

```html
{# 牛客面经卡片. Inputs: items (list[Item]). #}
<style>
  .job-item { padding: 14px 18px; border-bottom: 1px solid var(--paper3); transition: background 0.15s; }
  .job-item:hover { background: rgba(184,135,42,0.04); }
  .job-item:last-child { border-bottom: none; }
  .job-title { font-size: 13px; font-weight: 600; color: var(--text); line-height: 1.45; margin-bottom: 4px; }
  .job-title a { color: inherit; }
  .job-title a:hover { color: var(--gold); text-decoration: none; }
  .job-meta { font-size: 11px; color: var(--text3); margin-bottom: 6px; font-family: 'DM Mono', monospace; }
  .job-body { font-size: 12.5px; color: var(--text2); line-height: 1.6; }
  .job-footer { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
</style>

<div class="card">
  <div class="card-header">
    <h2>牛客面经热榜</h2>
    <span class="card-badge badge-gold">人工智能分区</span>
  </div>
  {% for item in items %}
  <div class="job-item">
    <div class="job-title"><a href="{{ item.url }}" target="_blank" rel="noopener">{{ item.title }}</a></div>
    {% if item.authors or item.published_at %}
    <div class="job-meta">
      {% if item.authors %}{{ item.authors[0] }}{% endif %}
      {% if item.published_at %} &nbsp;·&nbsp; {{ item.published_at[:10] }}{% endif %}
    </div>
    {% endif %}
    <div class="job-body">{{ item.summary if item.summary else item.raw_content[:200] }}</div>
    <div class="job-footer">
      {% for tag in item.tags[:4] %}<span class="tag">{{ tag }}</span>{% endfor %}
      <span class="score-chip {% if item.score >= 8 %}high{% endif %}">{{ "%.1f"|format(item.score) }}</span>
    </div>
  </div>
  {% else %}
  <div class="job-item" style="color:var(--text3);font-size:12px;">RSSHub 今日无 nowcoder 数据（公共实例可能暂时不可用，明日自动重试）</div>
  {% endfor %}
</div>
```

- [ ] **Step 6: `card_company.html.j2`** (国内 AI 公司动态)

```html
{# 国内 AI 公司动态卡片. Inputs: items (list[Item]). #}
<div class="card">
  <div class="card-header">
    <h2>国内 AI 公司动态</h2>
    <span class="card-badge badge-gold">官博 / 媒体</span>
  </div>
  {% for item in items %}
  <div class="job-item">
    <div class="job-title"><a href="{{ item.url }}" target="_blank" rel="noopener">{{ item.title }}</a></div>
    {% if item.tags or item.published_at %}
    <div class="job-meta">
      {% if item.tags %}{{ item.tags[0] }}{% endif %}
      {% if item.published_at %} &nbsp;·&nbsp; {{ item.published_at[:10] }}{% endif %}
    </div>
    {% endif %}
    <div class="job-body">{{ item.summary if item.summary else item.raw_content[:200] }}</div>
    <div class="job-footer">
      {% for tag in item.tags[1:5] %}<span class="tag">{{ tag }}</span>{% endfor %}
      <span class="score-chip {% if item.score >= 8 %}high{% endif %}">{{ "%.1f"|format(item.score) }}</span>
    </div>
  </div>
  {% else %}
  <div class="job-item" style="color:var(--text3);font-size:12px;">今日聚合器未匹配到目标公司动态</div>
  {% endfor %}
</div>
```

- [ ] **Step 7: `card_coding_tool.html.j2`** (AI Coding 工具采用信号)

```html
{# AI Coding 工具采用信号卡片. Inputs: items (list[Item]). #}
<div class="card">
  <div class="card-header">
    <h2>AI Coding 工具信号</h2>
    <span class="card-badge badge-coral">采用动向</span>
  </div>
  {% for item in items %}
  <div class="job-item">
    <div class="job-title"><a href="{{ item.url }}" target="_blank" rel="noopener">{{ item.title }}</a></div>
    <div class="job-meta">
      {% if item.tags %}{{ item.tags[-1] }}{% endif %}
      {% if item.stars %} &nbsp;·&nbsp; {{ item.stars }} pts{% endif %}
    </div>
    <div class="job-body">{{ item.summary if item.summary else item.raw_content[:180] }}</div>
    <div class="job-footer">
      {% for tag in item.tags[:3] %}<span class="tag">{{ tag }}</span>{% endfor %}
    </div>
  </div>
  {% else %}
  <div class="job-item" style="color:var(--text3);font-size:12px;">今日 HN/HF 中未检出工具采用信号</div>
  {% endfor %}
</div>
```

- [ ] **Step 8: `radar.html.j2`**

```html
{# Tech radar block. Inputs: radar_items (list of dicts {name, desc, gradient, score}). #}
<style>
  .radar-list { padding: 8px 0; }
  .radar-row { padding: 8px 18px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--paper3); }
  .radar-row:last-child { border-bottom: none; }
  .radar-name { font-size: 12px; font-weight: 600; color: var(--text); min-width: 120px; }
  .radar-track { flex: 1; height: 5px; background: var(--paper3); border-radius: 3px; overflow: hidden; }
  .radar-fill { height: 100%; border-radius: 3px; transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1); }
  .radar-pct { font-size: 11px; font-family: 'DM Mono', monospace; color: var(--text3); min-width: 32px; text-align: right; }
  .radar-desc { font-size: 10.5px; color: var(--text3); min-width: 140px; text-align: right; }
</style>

<div class="card">
  <div class="card-header">
    <h2>技术雷达</h2>
    <span class="card-badge badge-navy">关键词热度</span>
  </div>
  <div class="radar-list">
    {% for r in radar_items %}
    <div class="radar-row">
      <div class="radar-name">{{ r.name }}</div>
      <div class="radar-track">
        <div class="radar-fill" style="width:{{ r.score }}%;background:{{ r.gradient }};"></div>
      </div>
      <div class="radar-pct">{{ r.score }}%</div>
      <div class="radar-desc">{{ r.desc }}</div>
    </div>
    {% endfor %}
  </div>
</div>
```

- [ ] **Step 9: `trend_chart.html.j2`**

```html
{# 7-day keyword frequency chart. Inputs: trend_labels (list[str]), trend_series (dict[str, list[int]]). #}
<style>
  .chart-wrap { padding: 16px 18px; }
  #trendChart { max-height: 220px; }
</style>

<div class="card">
  <div class="card-header">
    <h2>关键词热度趋势</h2>
    <span class="card-badge badge-gold">过去 7 天</span>
  </div>
  <div class="chart-wrap">
    <canvas id="trendChart"></canvas>
  </div>
</div>

<script>
window.__TREND__ = {
  labels: {{ trend_labels | tojson }},
  series: {{ trend_series | tojson }}
};
</script>
```

- [ ] **Step 10: Verify all partials parse**

Run:
```bash
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
import os
for f in sorted(os.listdir('templates/partials')):
    if f.endswith('.j2'):
        env.get_template(f'partials/{f}')
        print(f'  {f} OK')
"
```
Expected: prints `OK` for all 9 partial files.

- [ ] **Step 11: Commit**

```bash
git add templates/partials/
git commit -m "feat(templates): add 9 partials (summary, paper, repo, hn, job, company, coding_tool, radar, trend)"
```

---

## Task 18: Rewrite `templates/daily.html.j2` to use base + partials + dual column

**Files:**
- Rewrite: `templates/daily.html.j2`

- [ ] **Step 1: Replace the file**

```html
{% extends "base.html.j2" %}

{% block title %}AI 每日早报 · {{ date_str }}{% endblock %}

{% block head_extra %}
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
{% endblock %}

{% block extra_styles %}
  .main-wrap { padding: 0 32px 32px; }
  .main-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    align-items: start;
    margin-top: 24px;
  }
  .left-col, .right-col { display: flex; flex-direction: column; gap: 20px; }
  .full-row { margin-top: 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  .card, .today-summary { animation: fadeUp 0.4s ease both; }
{% endblock %}

{% block masthead_pills %}
  <div class="masthead-pills">
    <span class="masthead-pill papers">📄 {{ counts.papers }} Papers</span>
    <span class="masthead-pill repos">🚀 {{ counts.repos }} Repos</span>
    <span class="masthead-pill jobs">💼 {{ counts.jobs }} Jobs</span>
  </div>
{% endblock %}

{% block body %}
  {# ─── Today's Summary ─── #}
  {% include "partials/summary_block.html.j2" %}

  <div class="main-wrap">
    <div class="main-grid">

      <div class="left-col">
        {# ─── arXiv ─── #}
        {% with card_title="arXiv 最新论文",
                card_badge_label="cs.AI · cs.CL · cs.MA",
                card_badge_class="badge-navy",
                items=arxiv_items,
                show_upvotes=false %}
          {% include "partials/card_paper.html.j2" %}
        {% endwith %}

        {# ─── HF Daily Papers ─── #}
        {% with card_title="HuggingFace Daily Papers",
                card_badge_label="今日热门",
                card_badge_class="badge-green",
                items=hf_items,
                show_upvotes=true %}
          {% include "partials/card_paper.html.j2" %}
        {% endwith %}

        {# ─── GitHub ─── #}
        {% with items=github_items %}
          {% include "partials/card_repo.html.j2" %}
        {% endwith %}

        {# ─── HackerNews ─── #}
        {% with items=hn_items %}
          {% include "partials/card_hn.html.j2" %}
        {% endwith %}
      </div>

      <div class="right-col">
        {# ─── 牛客面经 ─── #}
        {% with items=nowcoder_items %}
          {% include "partials/card_job.html.j2" %}
        {% endwith %}

        {# ─── 国内 AI 公司动态 ─── #}
        {% with items=china_ai_items %}
          {% include "partials/card_company.html.j2" %}
        {% endwith %}

        {# ─── AI Coding 工具采用信号 ─── #}
        {% with items=coding_tool_items %}
          {% include "partials/card_coding_tool.html.j2" %}
        {% endwith %}

        {# ─── Radar ─── #}
        {% with radar_items=radar_items %}
          {% include "partials/radar.html.j2" %}
        {% endwith %}
      </div>

    </div>

    <div class="full-row">
      {# ─── Trend chart spans full width below dual column ─── #}
      <div style="grid-column: 1 / -1;">
        {% with trend_labels=trend_labels, trend_series=trend_series %}
          {% include "partials/trend_chart.html.j2" %}
        {% endwith %}
      </div>
    </div>
  </div>
{% endblock %}

{% block scripts %}
<script>
(function() {
  const t = window.__TREND__;
  if (!t) return;
  const ctx = document.getElementById('trendChart').getContext('2d');
  const colors = {
    agent: '#1e3557', mcp: '#c94428', rag: '#2a7d4f',
  };
  const fillColors = {
    agent: 'rgba(30,53,87,0.06)', mcp: 'rgba(201,68,40,0.05)', rag: 'rgba(42,125,79,0.05)',
  };
  const datasets = Object.keys(t.series).map(k => ({
    label: k.toUpperCase(),
    data: t.series[k],
    borderColor: colors[k] || '#888',
    backgroundColor: fillColors[k] || 'rgba(0,0,0,0.03)',
    tension: 0.4, fill: true, pointRadius: 3, borderWidth: 2,
    pointBackgroundColor: colors[k] || '#888',
  }));
  new Chart(ctx, {
    type: 'line',
    data: { labels: t.labels, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#6b5e52', font: { family: 'Outfit', size: 11 }, boxWidth: 12 } },
        tooltip: {
          backgroundColor: '#1e3557', borderColor: '#ddd5c4', borderWidth: 1,
          titleColor: '#fff', bodyColor: 'rgba(255,255,255,0.75)',
          titleFont: { family: 'Outfit' }, bodyFont: { family: 'Outfit' }
        }
      },
      scales: {
        x: { ticks: { color: '#a0917f', font: { family: 'Outfit', size: 10 } }, grid: { color: 'rgba(180,165,148,0.3)' } },
        y: { ticks: { color: '#a0917f', font: { family: 'Outfit', size: 10 } }, grid: { color: 'rgba(180,165,148,0.3)' }, min: 0, max: 100 }
      }
    }
  });
})();
</script>
{% endblock %}
```

- [ ] **Step 2: Verify the template parses**

Run:
```bash
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
env.get_template('daily.html.j2')
print('daily.html.j2 OK')
"
```
Expected: `daily.html.j2 OK`.

- [ ] **Step 3: Commit**

```bash
git add templates/daily.html.j2
git commit -m "feat(template): rewrite daily.html.j2 with base + partials + dual column"
```

---

## Task 19: New `templates/archive.html.j2` — history index page

**Files:**
- Create: `templates/archive.html.j2`

- [ ] **Step 1: Create the file**

```html
{% extends "base.html.j2" %}

{% block title %}AI 每日早报 · 历史归档{% endblock %}

{% block masthead_title %}📚 AI 每日早报 · 归档{% endblock %}
{% block masthead_date %}共 {{ entries|length }} 期日报{% endblock %}
{% block masthead_pills %}{% endblock %}

{% block extra_styles %}
  .archive-wrap { padding: 32px; max-width: 1100px; margin: 0 auto; }
  .archive-section { margin-bottom: 32px; }
  .archive-section h2 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 22px; color: var(--navy); margin-bottom: 12px;
    padding-bottom: 6px; border-bottom: 2px solid var(--coral);
    display: inline-block;
  }
  .archive-list { list-style: none; }
  .archive-list li {
    padding: 10px 0;
    border-bottom: 1px solid var(--paper3);
    display: flex; gap: 18px; align-items: baseline;
  }
  .archive-list li:last-child { border-bottom: none; }
  .archive-date { font-family: 'DM Mono', monospace; color: var(--text3); min-width: 90px; }
  .archive-headline {
    font-size: 14px; color: var(--text);
    flex: 1;
  }
  .archive-link { font-family: 'DM Mono', monospace; font-size: 11px; }
{% endblock %}

{% block body %}
<div class="archive-wrap">
  <section class="archive-section">
    <h2>每日归档</h2>
    <ul class="archive-list">
      {% for e in entries %}
      <li>
        <span class="archive-date">{{ e.date }}</span>
        <span class="archive-headline">{{ e.headline or '（无 summary）' }}</span>
        <a class="archive-link" href="{{ e.href }}">→ 查看</a>
      </li>
      {% else %}
      <li><span class="archive-headline" style="color:var(--text3);">还没有归档，请明天早 7:00 后再来。</span></li>
      {% endfor %}
    </ul>
  </section>

  <section class="archive-section">
    <h2>周报 · 月报</h2>
    <p style="color:var(--text3);font-size:13px;">v3 实装。<a href="../SPEC.md">详见 SPEC §12</a>。</p>
  </section>
</div>
{% endblock %}
```

- [ ] **Step 2: Verify it parses**

Run: `python -c "from jinja2 import Environment, FileSystemLoader; Environment(loader=FileSystemLoader('templates')).get_template('archive.html.j2'); print('OK')"`
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add templates/archive.html.j2
git commit -m "feat(template): add archive.html.j2 history index page"
```

---

## Task 20: Empty stubs for weekly + monthly templates

**Files:**
- Create: `templates/weekly.html.j2`
- Create: `templates/monthly.html.j2`

- [ ] **Step 1: Create both stubs**

`templates/weekly.html.j2`:
```html
{% extends "base.html.j2" %}
{% block title %}AI 周报 · {{ week_label }}{% endblock %}
{% block body %}
<div style="padding:48px;text-align:center;color:var(--text2);">
  <h2 style="font-family:'Cormorant Garamond',serif;font-size:24px;margin-bottom:12px;">周报功能 v3 实装</h2>
  <p>本模板已预留，v3 接入 <code>pipeline.aggregator.build_weekly()</code> 后即可渲染。</p>
</div>
{% endblock %}
```

`templates/monthly.html.j2`:
```html
{% extends "base.html.j2" %}
{% block title %}AI 月报 · {{ month_label }}{% endblock %}
{% block body %}
<div style="padding:48px;text-align:center;color:var(--text2);">
  <h2 style="font-family:'Cormorant Garamond',serif;font-size:24px;margin-bottom:12px;">月报功能 v3 实装</h2>
  <p>本模板已预留，v3 接入 <code>pipeline.aggregator.build_monthly()</code> 后即可渲染。</p>
</div>
{% endblock %}
```

- [ ] **Step 2: Verify both parse**

Run:
```bash
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
env.get_template('weekly.html.j2')
env.get_template('monthly.html.j2')
print('OK')
"
```
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add templates/weekly.html.j2 templates/monthly.html.j2
git commit -m "feat(template): add empty weekly + monthly stubs for v3"
```

---

## Task 21: Rewrite `pipeline/renderer.py` — dual column + summary block + archive generator

**Files:**
- Rewrite: `pipeline/renderer.py`

- [ ] **Step 1: Replace the file**

```python
"""Render daily HTML + archive index from Items and a daily summary dict."""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from pipeline.config import get_config
from pipeline.schema import Item


ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = ROOT / "templates"
DOCS_DIR = ROOT / "docs"
SUMMARIES_DIR = ROOT / "data" / "summaries"
PROCESSED_DIR = ROOT / "data" / "processed"

_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
_SOURCE_LABELS = {
    "arxiv": "arXiv", "hf_papers": "HF", "github": "GitHub", "hackernews": "HN",
    "nowcoder": "牛客", "china_ai": "国内AI", "coding_tool": "Coding 信号",
}


def _format_stars(n: int) -> str:
    if n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def _source_label(s: str) -> str:
    return _SOURCE_LABELS.get(s, s)


def _build_env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    env.filters["format_stars"] = _format_stars
    env.filters["source_label"] = _source_label
    return env


def _bucketize(items: list[Item]) -> dict[str, list[Item]]:
    by_source: dict[str, list[Item]] = {
        "arxiv": [], "hf_papers": [], "github": [], "hackernews": [],
        "nowcoder": [], "china_ai": [], "coding_tool": [],
    }
    for it in items:
        by_source.setdefault(it.source, []).append(it)
    for src in by_source:
        by_source[src].sort(key=lambda x: -x.score)
    return by_source


def _build_radar(items: list[Item], radar_cfg: list[dict]) -> list[dict]:
    counts = {r["name"].lower(): 0 for r in radar_cfg}
    for it in items:
        text = (it.title + " " + " ".join(it.tags) + " " + it.raw_content).lower()
        for kw in counts:
            if kw in text:
                counts[kw] += 1
    total = max(sum(counts.values()), 1)
    result = []
    for r in radar_cfg:
        kw = r["name"].lower()
        score = min(int(counts[kw] / total * 200) + 20, 95)
        result.append({**r, "score": score})
    result.sort(key=lambda x: -x["score"])
    return result


def _build_trend(target_date: date, keywords: list[str]) -> tuple[list[str], dict[str, list[int]]]:
    labels = [(target_date - timedelta(days=6 - i)).strftime("%-m/%-d") for i in range(7)]
    series: dict[str, list[int]] = {kw: [] for kw in keywords}
    for i in range(7):
        day = target_date - timedelta(days=6 - i)
        path = PROCESSED_DIR / f"{day.isoformat()}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                day_items = json.load(f)
            texts = " ".join(
                d.get("title", "") + " " + " ".join(d.get("tags", [])) + " " + d.get("raw_content", "")
                for d in day_items
            ).lower()
            for kw in keywords:
                count = texts.count(kw.lower())
                series[kw].append(min(count * 5 + 30, 95))
        else:
            for kw in keywords:
                series[kw].append(0)
    return labels, series


def render_daily(
    items: list[Item],
    summary: dict,
    *,
    target_date: date | None = None,
) -> Path:
    """Render today's HTML to docs/{date}.html and copy to docs/index.html.
    Returns the dated path.
    """
    target_date = target_date or date.today()
    date_str = target_date.isoformat()
    weekday_str = _WEEKDAYS[target_date.weekday()]
    cfg = get_config()
    max_per = cfg["rendering"]["max_per_card"]

    by_source = _bucketize(items)
    arxiv_items       = by_source["arxiv"][:max_per["arxiv"]]
    hf_items          = by_source["hf_papers"][:max_per["hf_papers"]]
    github_items      = by_source["github"][:max_per["github"]]
    hn_items          = by_source["hackernews"][:max_per["hackernews"]]
    nowcoder_items    = by_source["nowcoder"][:max_per["nowcoder"]]
    china_ai_items    = by_source["china_ai"][:max_per["china_ai"]]
    coding_tool_items = by_source["coding_tool"][:max_per["coding_tool"]]

    counts = {
        "papers": len(arxiv_items) + len(hf_items),
        "repos":  len(github_items),
        "jobs":   len(nowcoder_items) + len(china_ai_items) + len(coding_tool_items),
    }

    trend_keywords = cfg["rendering"].get("trend_keywords", ["agent", "mcp", "rag"])
    trend_labels, trend_series = _build_trend(target_date, trend_keywords)

    radar_items = _build_radar(items, cfg["rendering"].get("radar_keywords", []))

    env = _build_env()
    tmpl = env.get_template("daily.html.j2")
    html = tmpl.render(
        date_str=date_str,
        weekday_str=weekday_str,
        summary=summary,
        counts=counts,
        arxiv_items=arxiv_items,
        hf_items=hf_items,
        github_items=github_items,
        hn_items=hn_items,
        nowcoder_items=nowcoder_items,
        china_ai_items=china_ai_items,
        coding_tool_items=coding_tool_items,
        radar_items=radar_items,
        trend_labels=trend_labels,
        trend_series=trend_series,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DIR / f"{date_str}.html"
    out_path.write_text(html, encoding="utf-8")
    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
    return out_path


def render_archive() -> Path:
    """Scan data/summaries/*.json and docs/*.html → emit docs/archive.html."""
    entries: list[dict] = []
    if SUMMARIES_DIR.exists():
        for sf in sorted(SUMMARIES_DIR.glob("*.json"), reverse=True):
            try:
                s = json.loads(sf.read_text(encoding="utf-8"))
            except Exception:
                continue
            d = s.get("date", sf.stem)
            href = f"./{d}.html" if (DOCS_DIR / f"{d}.html").exists() else None
            if not href:
                continue
            entries.append({"date": d, "headline": s.get("headline", ""), "href": href})

    env = _build_env()
    tmpl = env.get_template("archive.html.j2")
    html = tmpl.render(
        entries=entries,
        date_str=date.today().isoformat(),
        weekday_str=_WEEKDAYS[date.today().weekday()],
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DIR / "archive.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path
```

- [ ] **Step 2: Smoke-test by rendering an empty-input daily**

Run:
```bash
python -c "
from datetime import date
from pipeline.renderer import render_daily, render_archive
summary = {
    'date': '2026-05-17',
    'headline': 'smoke test headline',
    'ai_trends':   ['t1', 't2', 't3'],
    'job_signals': ['s1', 's2', 's3'],
    'stats': {'total_items': 0, 'learning_count': 0, 'job_count': 0, 'top_score': 0, 'top_item_title': '—'},
}
p = render_daily([], summary, target_date=date(2026,5,17))
print('rendered', p)
p2 = render_archive()
print('archive', p2)
"
```
Expected: prints two paths under `docs/`. No exceptions.

- [ ] **Step 3: Open `docs/index.html` in browser and visually inspect**

Run: `open docs/index.html`
Expected:
- Masthead with navy bg, "🤖 AI 每日早报" title, today's date
- Today's summary block showing "smoke test headline" + 3+3 bullets
- Empty-state messages in each card ("今日暂无数据" etc.)
- Trend chart axes visible (data lines flat at 0)
- No JS console errors

- [ ] **Step 4: Commit**

```bash
git add pipeline/renderer.py
git commit -m "feat(renderer): dual-column render + summary block + archive index"
```

---

## Task 22: Rewrite `daily.py` — registry loop + summarizer + archive

**Files:**
- Rewrite: `daily.py`

- [ ] **Step 1: Replace the file**

```python
#!/usr/bin/env python3
"""GetNews v2 daily pipeline.

    python daily.py                   # full run (DeepSeek + git push)
    python daily.py --mock            # skip LLM, use raw content as summary
    python daily.py --mock --no-push  # local preview only
"""
import argparse
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Importing fetcher modules triggers REGISTRY self-registration.
from fetchers import (   # noqa: F401  (side-effect imports)
    arxiv_fetcher,
    hf_fetcher,
    github_fetcher,
    hn_fetcher,
    nowcoder_fetcher,
    china_ai_fetcher,
    coding_tool_fetcher,
)
from fetchers.base import REGISTRY
from fetchers.coding_tool_fetcher import CodingToolFetcher

from pipeline.config import get_config
from pipeline.llm import summarize_all
from pipeline.renderer import render_daily, render_archive
from pipeline.schema import save_items
from pipeline.scorer import score_all, dedup
from pipeline.summarizer import build_daily_summary, write_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Skip LLM, use raw content")
    parser.add_argument("--no-push", action="store_true", help="Skip git push after render")
    args = parser.parse_args()

    today = date.today()
    provider = "mock" if args.mock else get_config()["llm"].get("provider", "mock")
    cfg = get_config()

    # ── [1/7] Fetch from all enabled non-derived fetchers ──
    print(f"[1/7] Fetching data for {today}...")
    items: list = []
    derived_fetchers = []
    for fetcher in REGISTRY.enabled(cfg):
        if isinstance(fetcher, CodingToolFetcher):
            derived_fetchers.append(fetcher)
            continue
        try:
            got = fetcher.fetch(today)
            items += got
            print(f"  {fetcher.source_id}: {len(got)} items")
        except Exception as e:
            print(f"  {fetcher.source_id}: FAILED ({e})")

    # ── [2/7] Run derived fetchers over the pool ──
    for fetcher in derived_fetchers:
        fetcher.pool = items
        try:
            got = fetcher.fetch(today)
            items += got
            print(f"  {fetcher.source_id}: {len(got)} items (derived)")
        except Exception as e:
            print(f"  {fetcher.source_id}: FAILED ({e})")

    # ── [3/7] Score ──
    print(f"[3/7] Scoring {len(items)} items...")
    items = score_all(items)

    # ── [4/7] Dedup ──
    print("[4/7] Deduplicating...")
    items = dedup(items)
    print(f"  After dedup: {len(items)} items")

    # ── [5/7] Persist raw processed items ──
    raw_path = ROOT / "data" / "processed" / f"{today.isoformat()}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    save_items(items, str(raw_path))

    # ── [6/7] Summarize (per-item + daily) ──
    print(f"[6/7] Summarizing per-item + daily synthesis (provider='{provider}')...")
    items = summarize_all(items, provider=provider)
    summary = build_daily_summary(items, llm_provider=provider, target_date=today)
    summary_path = write_summary(summary)
    print(f"  Summary written: {summary_path}")

    # ── [7/7] Render daily HTML + archive ──
    print("[7/7] Rendering daily HTML + archive index...")
    out = render_daily(items, summary, target_date=today)
    archive = render_archive()
    print(f"  Daily: {out}")
    print(f"  Archive: {archive}")

    if not args.no_push:
        _git_push(today)


def _git_push(today: date) -> None:
    import subprocess
    cmds = [
        ["git", "add", "docs/"],
        ["git", "add", f"data/processed/{today.isoformat()}.json",
                       f"data/summaries/{today.isoformat()}.json"],
        ["git", "commit", "-m", f"daily: {today.isoformat()}"],
        ["git", "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  [warn] {' '.join(cmd)}: {result.stderr.strip()}")
        else:
            print(f"  {' '.join(cmd)}: OK")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run end-to-end in mock mode**

Run: `python daily.py --mock --no-push`
Expected output: 7 numbered steps, each printing item counts. Final two lines reference `docs/2026-05-17.html` and `docs/archive.html`. No tracebacks.

- [ ] **Step 3: Open the output and visually verify all 7 cards render**

Run: `open docs/index.html`

Visual checklist (each ✓ should be true):
- [ ] Masthead shows today's date + 3 pills with non-zero counts (papers / repos / jobs)
- [ ] Summary block shows mock headline + 3 bullets per column
- [ ] Left column: arXiv, HF, GitHub, HackerNews cards all populated or showing "暂无数据"
- [ ] Right column: 牛客, 国内 AI 公司, AI Coding 信号, 技术雷达 all present
- [ ] Trend chart shows 7-day labels on X axis
- [ ] Footer links to `./archive.html` work

Open `docs/archive.html`:
- [ ] Lists today's date with the mock headline
- [ ] "查看" link goes to `./2026-05-17.html`

- [ ] **Step 4: Commit**

```bash
git add daily.py
git commit -m "feat(daily): rewrite pipeline around fetcher registry + summarizer + archive"
```

---

## Task 23: New `.github/workflows/daily.yml` — GitHub Actions cron

**Files:**
- Create: `.github/workflows/daily.yml`

- [ ] **Step 1: Create the workflow file**

```yaml
name: Daily Brief

on:
  schedule:
    - cron: '0 23 * * *'          # UTC 23:00 = Beijing 07:00
  workflow_dispatch:               # also allow manual trigger from Actions tab

permissions:
  contents: write                  # needed for the bot to push commits back

concurrency:
  group: daily-brief
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 1

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run daily pipeline (no internal push)
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          GITHUB_TOKEN:     ${{ secrets.GITHUB_TOKEN }}
        run: python daily.py --no-push

      - name: Commit + push generated artifacts
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/ data/processed/ data/summaries/
          if git diff --staged --quiet; then
            echo "No changes to commit."
          else
            git commit -m "auto: daily brief $(date -u +'%Y-%m-%d')"
            git push
          fi
```

- [ ] **Step 2: Verify YAML parses**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/daily.yml')); print('OK')"`
Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/daily.yml
git commit -m "feat(ci): GitHub Actions daily cron at UTC 23:00 (Beijing 07:00)"
```

- [ ] **Step 4: Manual end-to-end test (do this AFTER push)**

Once pushed and the user has set up `DEEPSEEK_API_KEY` in repo secrets and configured Pages → main / `/docs`:
1. Go to Actions tab → `Daily Brief` → "Run workflow" → main branch → Run
2. Watch the job; it should finish in 2–4 minutes
3. After completion, browse to `https://diezqu.github.io/getnews/` — today's brief should be live

If anything fails, the workflow output shows which step. Common failure modes:
- `DEEPSEEK_API_KEY` not set → add via Settings → Secrets → Actions
- RSSHub down → only nowcoder/china_ai missing; other cards still render

---

## Task 24: Update `README.md` for v2

**Files:**
- Rewrite: `README.md`

- [ ] **Step 1: Replace the file**

````markdown
# GetNews · AI 每日早报 v2

> **双栏中文 dashboard**：左侧 AI 学习线（arXiv / HuggingFace / GitHub / HackerNews），右侧中国 AI 求职情报线（牛客 / 国内 AI 公司动态 / AI Coding 工具采用信号），顶部 LLM 综合判断。每天凌晨 7 点 GitHub Actions 自动跑完，你打开 Chrome 书签直接看。

**Live：** https://diezqu.github.io/getnews/

---

## 功能

- 📚 **AI 学习线**（左栏）
  - **arXiv** — cs.AI / cs.CL / cs.MA / cs.LG 最新论文
  - **HuggingFace Daily Papers** — 每日热门（含 upvote）
  - **GitHub** — Agent / MCP / RAG 方向快速涨星仓库
  - **HackerNews** — AI 高分讨论
- 💼 **求职情报线**（右栏）
  - **牛客面经** — 人工智能分区热榜（RSSHub）
  - **国内 AI 公司动态** — 机器之心 + 量子位 → 按目标公司过滤
  - **AI Coding 工具采用信号** — 从 HN/HF 派生，Cursor / Claude Code / Cline 等
- 💡 **顶部综合 Summary** — 每日一句 headline + 3 条 AI 趋势 + 3 条求职信号
- 🎯 **按 category 分别打分** — 学习线 vs 求职线权重独立
- 🔁 **跨源去重** — URL hash + 标题指纹
- 🧠 **LLM 三任务** — DeepSeek 同时承担英文翻译、中文精炼、跨源综合
- 📊 **7 天关键词趋势图** + 技术雷达
- 🗄️ **三层归档**（`data/processed/` / `data/summaries/` / `data/aggregates/`）为 v3 周报月报预留
- 🤖 **GitHub Actions 全自动** — 每天 UTC 23:00（北京 07:00）跑完即推

---

## 5 分钟上手

```bash
# 1. 克隆 + 安装
git clone https://github.com/Diezqu/getnews.git && cd getnews
pip install -r requirements.txt

# 2. 配 key
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 本地预览（不调 LLM，不 push）
make mock          # 等价: python daily.py --mock --no-push
open docs/index.html

# 4. 完整跑一次（调 DeepSeek + git push）
make daily
```

---

## 部署到 GitHub Pages（一次性）

1. 在 GitHub 建空仓库 `getnews`（已建好：https://github.com/Diezqu/getnews）
2. Settings → Pages → Source = `main` 分支 / `/docs` 文件夹 → Save
3. Settings → Secrets and variables → Actions → New repository secret
   - Name: `DEEPSEEK_API_KEY`
   - Value: 你的 DeepSeek API key
4. Actions 标签 → 第一次手动触发 `Daily Brief` workflow
5. 等 2-3 分钟，访问 https://diezqu.github.io/getnews/

之后每天凌晨 7 点（北京时间）自动更新，你什么都不用做。

---

## 项目结构

```
GetNews/
├── daily.py                   # 一行命令跑全流程
├── config.yaml                # 关键词权重 / 源开关 / LLM provider 都在这里
├── .github/workflows/daily.yml # 每日 7:00 自动 cron
│
├── fetchers/
│   ├── base.py                 # BaseFetcher + REGISTRY
│   ├── arxiv_fetcher.py        ├ learning
│   ├── hf_fetcher.py           │
│   ├── github_fetcher.py       │
│   ├── hn_fetcher.py           ┘
│   ├── nowcoder_fetcher.py     ┐
│   ├── china_ai_fetcher.py     ├ job
│   └── coding_tool_fetcher.py  ┘ (派生源)
│
├── pipeline/
│   ├── schema.py               # Item 数据结构
│   ├── config.py               # YAML 加载器
│   ├── scorer.py               # 按 category 打分 + 去重
│   ├── llm.py                  # BaseLLM + DeepSeek/Mock provider
│   ├── summarizer.py           # 每日综合 summary
│   ├── aggregator.py           # 周/月报 stub (v3)
│   └── renderer.py             # Jinja2 → HTML
│
├── templates/
│   ├── base.html.j2            # 主框架
│   ├── daily.html.j2           # 日报（继承 base）
│   ├── archive.html.j2         # 历史归档索引
│   ├── weekly.html.j2          # v3 周报 (stub)
│   ├── monthly.html.j2         # v3 月报 (stub)
│   └── partials/               # 9 个卡片 partial
│
├── docs/                       # GitHub Pages 根
│   ├── index.html              # 最新一天
│   ├── YYYY-MM-DD.html         # 历史日报
│   └── archive.html            # 归档索引
│
└── data/
    ├── processed/YYYY-MM-DD.json    # 当日 Item 全量
    ├── summaries/YYYY-MM-DD.json    # 当日 LLM summary
    └── aggregates/{weekly,monthly}/ # v3 输出位置
```

---

## 怎么扩展

| 需求 | 怎么做 |
|---|---|
| **加一个新数据源** | 新建 `fetchers/xxx_fetcher.py`，继承 `BaseFetcher`，末尾 `REGISTRY.register(...)`；在 `config.yaml` 的 `sources:` 下加一段配置 |
| **调关键词权重** | 改 `config.yaml`，不动代码 |
| **暂时关掉某源** | `config.yaml` → `sources.<name>.enabled: false` |
| **换 LLM 服务商** | 实现一个 `BaseLLM` 子类，在 `pipeline/llm.py:get_provider` 加分支，改 `config.yaml` |
| **加新 card 样式** | 新建 `templates/partials/card_xxx.html.j2`，在 `daily.html.j2` 引入 `{% include %}` |
| **换皮肤** | 改 `templates/base.html.j2` 的 CSS variables (`--paper`, `--navy`, ...) |
| **加周报 / 月报** | 实现 `pipeline/aggregator.build_weekly()` + 复用 `templates/weekly.html.j2` |

---

## 技术栈

Python · Jinja2 · DeepSeek API（OpenAI SDK 兼容）· RSSHub · feedparser · Chart.js · GitHub Actions · GitHub Pages

---

## 成本

每天约 80K tokens ≈ **¥0.04**。充 ¥10 够用 8 个月。
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for v2 (双栏 dashboard + 扩展指南)"
```

---

## Final verification

After all 24 tasks land, run this end-to-end:

- [ ] **Pre-flight checks**

```bash
pytest tests/ -v                              # all tests pass
python daily.py --mock --no-push              # end-to-end succeeds
open docs/index.html                          # dashboard renders
open docs/archive.html                        # archive index renders
```

- [ ] **Confirm git status is clean**

```bash
git status                                    # working tree clean
git log --oneline -30                         # ~25 commits since "init"
```

- [ ] **Push to remote**

```bash
git remote -v                                 # check origin is set
# if not:
git remote add origin https://github.com/Diezqu/getnews.git
git push -u origin main
```

- [ ] **GitHub side (manual user actions per SPEC §18)**

1. Repo → Settings → Secrets and variables → Actions → New repository secret → `DEEPSEEK_API_KEY` = your key
2. Repo → Settings → Pages → Source = `main` branch / `/docs` folder → Save
3. Actions tab → "Daily Brief" → "Run workflow" → main → Run
4. After 2-4 minutes, visit https://diezqu.github.io/getnews/

- [ ] **Add Chrome bookmark + add to resume**

Bookmark: https://diezqu.github.io/getnews/
Resume bullet (per SPEC §16): "AI Daily Brief · https://diezqu.github.io/getnews"

---

## Notes for the implementing engineer

- **Always work in small commits.** Each task ends with a `git commit` step — do not batch.
- **TDD where it makes sense.** Pure-logic modules (schema, config, scorer, registry, llm provider, summarizer) have tests. Fetchers and templates are verified via end-to-end smoke tests because they're tightly coupled to external APIs / browser rendering.
- **Don't run real DeepSeek calls during development.** Use `--mock` until the very last verification. The user pays per-token.
- **RSSHub flakiness is expected.** If 牛客 returns 0 items, that's documented in SPEC §4 — don't try to "fix" it by adding retry logic or switching to self-hosted; that's out of v2 scope.
- **The user's GitHub repo is `https://github.com/Diezqu/getnews`.** Use this URL in README, footer link, and any other place a repo URL is hardcoded.
- **Branch is `main`.** Do not push without confirming with the user; preserve the local-first workflow until all 24 tasks pass `make mock`.
