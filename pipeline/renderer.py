import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Sequence

from jinja2 import Environment, FileSystemLoader

from pipeline.schema import Item

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
DOCS_DIR = Path(__file__).parent.parent / "docs"

_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
_SOURCE_LABELS = {"arxiv": "arXiv", "hf_papers": "HF", "github": "GitHub", "hackernews": "HN"}
_RADAR_DEFAULTS = [
    {"name": "Agent",         "color": "linear-gradient(90deg,#7c6af7,#5be0c4)", "desc": "多 Agent 协作框架持续爆发"},
    {"name": "MCP",           "color": "linear-gradient(90deg,#5be0c4,#7c6af7)", "desc": "2026 Agent 集成标准"},
    {"name": "RAG",           "color": "linear-gradient(90deg,#f77c6a,#f7d26a)", "desc": "检索增强依然是核心技术"},
    {"name": "LLM Fine-tune", "color": "linear-gradient(90deg,#f7d26a,#f77c6a)", "desc": "垂直领域微调需求上升"},
    {"name": "AI Safety",     "color": "linear-gradient(90deg,#7c6af7,#f77c6a)", "desc": "对齐与可解释性研究增加"},
    {"name": "Local-First AI","color": "linear-gradient(90deg,#5be0c4,#f7d26a)", "desc": "隐私计算与离线部署"},
]


def _format_stars(n: int) -> str:
    if n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def _source_label(s: str) -> str:
    return _SOURCE_LABELS.get(s, s)


def _build_radar(all_items: list[Item]) -> list[dict]:
    keywords = {r["name"].lower(): r for r in _RADAR_DEFAULTS}
    counts: dict[str, int] = {k: 0 for k in keywords}
    for item in all_items:
        text = (item.title + " " + " ".join(item.tags)).lower()
        for kw in counts:
            if kw in text:
                counts[kw] += 1
    total = max(sum(counts.values()), 1)
    result = []
    for r in _RADAR_DEFAULTS:
        kw = r["name"].lower()
        score = min(int(counts[kw] / total * 200) + 20, 95)
        result.append({**r, "score": score})
    result.sort(key=lambda x: -x["score"])
    return result


def _build_trend(history_dir: Path, keywords: list[str]) -> tuple[list[str], dict[str, list[int]]]:
    """Load or synthesize 7-day keyword frequency from daily JSON files."""
    today = date.today()
    labels = [(today - timedelta(days=6 - i)).strftime("%-m/%-d") for i in range(7)]
    series: dict[str, list[int]] = {kw: [] for kw in keywords}
    for i in range(7):
        day = today - timedelta(days=6 - i)
        path = history_dir / f"{day.isoformat()}.json"
        if path.exists():
            with open(path) as f:
                items = json.load(f)
            texts = " ".join(d.get("title", "") + " " + " ".join(d.get("tags", [])) for d in items).lower()
            for kw in keywords:
                count = texts.count(kw.lower())
                series[kw].append(min(count * 5 + 30, 95))
        else:
            for kw in keywords:
                series[kw].append(0)
    return labels, series


def render(
    today_items: list[Item],
    output_date: date | None = None,
    daily_insight: str = "",
) -> Path:
    output_date = output_date or date.today()
    date_str = output_date.isoformat()
    weekday_str = _WEEKDAYS[output_date.weekday()]

    by_source: dict[str, list[Item]] = {"arxiv": [], "hf_papers": [], "github": [], "hackernews": []}
    for item in today_items:
        by_source.setdefault(item.source, []).append(item)

    for src in by_source:
        by_source[src].sort(key=lambda x: -x.score)

    arxiv_items = by_source["arxiv"][:8]
    hf_items = by_source["hf_papers"][:5]
    github_items = by_source["github"][:8]
    hn_items = by_source["hackernews"][:8]

    # Stats
    max_stars_item = max((i for i in github_items if i.stars), key=lambda x: x.stars, default=None)
    top_hn = max((i for i in hn_items if i.stars), key=lambda x: x.stars, default=None)
    stats = {
        "max_stars": _format_stars(max_stars_item.stars) if max_stars_item else "—",
        "max_stars_repo": max_stars_item.title.split("/")[-1] if max_stars_item else "—",
        "top_hn_score": top_hn.stars if top_hn else 0,
        "top_hn_title": (top_hn.title[:20] + "…") if top_hn else "—",
    }

    all_sorted = sorted(today_items, key=lambda x: -x.score)
    top_papers = [i for i in all_sorted if i.source in ("arxiv", "hf_papers")][:3]
    top_github = [i for i in all_sorted if i.source == "github"][:3]
    top_hn_h = [i for i in all_sorted if i.source == "hackernews"][:3]
    top_all = all_sorted[:3]

    # Trend chart
    history_dir = Path(__file__).parent.parent / "data" / "processed"
    trend_labels, trend_series = _build_trend(history_dir, ["agent", "mcp", "rag"])

    # Radar
    radar_items = _build_radar(today_items)

    # Jinja2
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    env.filters["format_stars"] = _format_stars
    env.filters["source_label"] = _source_label

    tmpl = env.get_template("daily.html.j2")
    html = tmpl.render(
        date_str=date_str,
        weekday_str=weekday_str,
        arxiv_items=arxiv_items,
        hf_items=hf_items,
        github_items=github_items,
        hn_items=hn_items,
        stats=stats,
        top_papers=top_papers,
        top_github=top_github,
        top_hn=top_hn_h,
        top_all=top_all,
        daily_insight=daily_insight,
        trend_labels=trend_labels,
        trend_agent=trend_series["agent"],
        trend_mcp=trend_series["mcp"],
        trend_rag=trend_series["rag"],
        radar_items=radar_items,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DIR / f"{date_str}.html"
    out_path.write_text(html, encoding="utf-8")

    # keep latest as index.html
    index_path = DOCS_DIR / "index.html"
    index_path.write_text(html, encoding="utf-8")

    return out_path
