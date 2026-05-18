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

    # ── [5/7] Summarize (per-item + daily) ──
    print(f"[5/7] Summarizing per-item + daily synthesis (provider='{provider}')...")
    items = summarize_all(items, provider=provider)
    summary = build_daily_summary(items, llm_provider=provider, target_date=today)
    summary_path = write_summary(summary)
    print(f"  Summary written: {summary_path}")

    # ── [6/7] Persist processed items (with summaries) ──
    print("[6/7] Saving processed items with summaries...")
    raw_path = ROOT / "data" / "processed" / f"{today.isoformat()}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    save_items(items, str(raw_path))

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
