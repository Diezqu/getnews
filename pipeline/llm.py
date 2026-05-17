"""LLM provider abstraction.

Usage:
    summarize(item, provider="deepseek")   # uses DEEPSEEK_API_KEY env var
    summarize(item, provider="mock")       # returns raw_abstract, no API call
"""
import os
from pipeline.schema import Item

_SYSTEM_PROMPT = """你是一个 AI 领域研究助手，专注于 Agent / 多智能体 / MCP / RAG 方向。
请将下面的论文摘要或项目描述翻译并精炼成 2-3 句中文摘要：
1. 第一句：核心贡献/这是什么
2. 第二句：关键结果或亮点数字
3. 第三句（可选）：与 Agent/RAG/MCP 方向的关联价值
字数控制在 80-120 字，技术准确，直接输出中文摘要，不加引号或前缀。"""


def summarize(item: Item, provider: str = "deepseek") -> str:
    if provider == "mock" or not item.raw_abstract.strip():
        return item.raw_abstract[:200] if item.raw_abstract else item.title

    if provider == "deepseek":
        return _summarize_deepseek(item)

    raise ValueError(f"Unknown provider: {provider}")


def summarize_all(items: list[Item], provider: str = "deepseek") -> list[Item]:
    for item in items:
        if not item.summary:
            item.summary = summarize(item, provider=provider)
    return items


def _summarize_deepseek(item: Item) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Run: pip install openai")

    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise EnvironmentError("DEEPSEEK_API_KEY not set in environment")

    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
    content = f"标题：{item.title}\n\n原文：{item.raw_abstract[:1200]}"

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        max_tokens=250,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()
