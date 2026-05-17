#!/usr/bin/env python3
"""One-shot daily pipeline: fetch → dedup → score → summarize → render.

Usage:
    python daily.py                   # full run with DeepSeek summaries
    python daily.py --mock            # skip LLM, use raw abstracts
    python daily.py --mock --no-push  # local preview only
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from fetchers import arxiv_fetcher, hn_fetcher, github_fetcher, hf_fetcher
from pipeline.scorer import score_all, dedup
from pipeline.llm import summarize_all
from pipeline.renderer import render
from pipeline.schema import save_items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Skip LLM, use raw abstracts")
    parser.add_argument("--no-push", action="store_true", help="Skip git push after render")
    args = parser.parse_args()

    today = date.today()
    provider = "mock" if args.mock else "deepseek"

    print(f"[1/5] Fetching data for {today}...")
    items = []
    for name, fn, kwargs in [
        ("arXiv",  arxiv_fetcher.fetch,  {"max_results": 30}),
        ("HF",     hf_fetcher.fetch,     {"target_date": today}),
        ("GitHub", github_fetcher.fetch, {"max_per_query": 8}),
        ("HN",     hn_fetcher.fetch,     {"max_per_query": 10}),
    ]:
        try:
            fetched = fn(**kwargs)
            items += fetched
            print(f"  {name}: {len(fetched)} items")
        except Exception as e:
            print(f"  {name}: FAILED ({e})")

    print(f"[2/5] Scoring {len(items)} items...")
    items = score_all(items)

    print(f"[3/5] Deduplicating...")
    items = dedup(items)
    print(f"  After dedup: {len(items)} items")

    # Save raw data for history/trend
    raw_path = ROOT / "data" / "processed" / f"{today.isoformat()}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    save_items(items, str(raw_path))

    print(f"[4/5] Summarizing with provider='{provider}'...")
    items = summarize_all(items, provider=provider)

    print(f"[5/5] Rendering HTML...")
    out = render(items)
    print(f"  Output: {out}")

    if not args.no_push:
        _git_push(today)


def _git_push(today: date):
    import subprocess
    cmds = [
        ["git", "add", "docs/"],
        ["git", "add", f"data/processed/{today.isoformat()}.json"],
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
