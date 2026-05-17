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
