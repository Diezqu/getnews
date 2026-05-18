#!/usr/bin/env python3
"""
One-shot script to re-run per-item summarization and re-render today's HTML.
Use when today's JSON was saved before summarize_all() ran (the old pipeline bug).

Usage:
    cp data/processed/2026-05-17.json data/processed/2026-05-17.json.bak
    python3 scripts/resummarize_today.py
    # Optionally pass a date: python3 scripts/resummarize_today.py 2026-05-17
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.schema import load_items, save_items
from pipeline.llm import summarize_all
from pipeline.summarizer import build_daily_summary, write_summary
from pipeline.renderer import render_daily, render_archive

target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
processed = ROOT / "data" / "processed" / f"{target.isoformat()}.json"

if not processed.exists():
    print(f"No processed file found at {processed}")
    sys.exit(1)

print(f"Loading items from {processed} ...")
items = load_items(str(processed))
before = sum(1 for i in items if i.summary)
print(f"  {before}/{len(items)} items already have summaries")

print("Running summarize_all (provider=deepseek) ...")
items = summarize_all(items, provider="deepseek")
after = sum(1 for i in items if i.summary)
print(f"  {after}/{len(items)} items now have summaries")

print("Building daily summary ...")
summary = build_daily_summary(items, llm_provider="deepseek", target_date=target)
summary_path = write_summary(summary)
print(f"  Summary written: {summary_path}")

print("Saving items (with summaries) ...")
save_items(items, str(processed))

print("Re-rendering daily HTML ...")
out = render_daily(items, summary, target_date=target)
archive = render_archive()
print(f"  Daily: {out}")
print(f"  Archive: {archive}")
print("Done. Open docs/ to verify Chinese summaries appear.")
