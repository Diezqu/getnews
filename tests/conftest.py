"""Shared pytest fixtures."""
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
