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
