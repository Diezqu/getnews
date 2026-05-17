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
