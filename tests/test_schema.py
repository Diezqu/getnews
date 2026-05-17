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
