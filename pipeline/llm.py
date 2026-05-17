"""LLM provider abstraction supporting two tasks:
  A) summarize_item    — per-item Chinese summary (EN→ZH or ZH refine)
  B) summarize_daily   — daily synthesis (headline + 3 ai_trends + 3 job_signals)

Switch provider in config.yaml → llm.provider ("deepseek" | "mock").
"""
import json
import os
from abc import ABC, abstractmethod

from pipeline.config import get_config
from pipeline.schema import Item


# ── Prompts ────────────────────────────────────────────────────────────────

_PROMPT_TRANSLATE_EN = """你是 AI 领域研究助手，专注于 Agent / 多智能体 / MCP / RAG 方向。
请将下面的英文论文摘要 / 仓库描述 / 帖子标题精炼成中文摘要：
1. 第一句：核心贡献 / 这是什么
2. 第二句：关键结果或亮点数字
3. 第三句（可选）：与 Agent/RAG/MCP 方向的关联价值
字数 80-120 字，技术准确，直接输出中文，不加引号或前缀。"""

_PROMPT_REFINE_ZH = """你是中国 AI 求职情报分析师。请把下面这段中文原文精炼成 60-80 字要点：
- 如果是面经：提炼"被问了什么题型、哪家公司、哪个岗位"
- 如果是公司动态：提炼"谁发布了什么、技术亮点、对行业影响"
直接输出精炼后中文，不加引号或前缀。"""

_PROMPT_DAILY = """你是 AI 信息分析师。下面是今天聚合到的内容，分为「AI 学习」和「求职情报」两类。
请生成今日综合判断，**严格输出 JSON 对象**（不要 markdown 代码块）：

{
  "headline": "<30 字以内一句话，今天最值得知道的事>",
  "ai_trends":   ["<30 字>", "<30 字>", "<30 字>"],
  "job_signals": ["<30 字>", "<30 字>", "<30 字>"]
}

ai_trends 提取学习线的 3 个最重要趋势；job_signals 提取求职线的 3 个最重要信号。
如果某一线数据不足，对应条目写"今日数据较少"。
"""


# ── Provider abstraction ───────────────────────────────────────────────────

class BaseLLM(ABC):
    @abstractmethod
    def summarize_item(self, item: Item) -> str: ...

    @abstractmethod
    def summarize_daily(self, items: list[Item]) -> dict: ...


class MockProvider(BaseLLM):
    """No-API-call provider. Returns raw_content[:200] and a stub daily dict."""

    def summarize_item(self, item: Item) -> str:
        if item.raw_content.strip():
            return item.raw_content[:200]
        return item.title

    def summarize_daily(self, items: list[Item]) -> dict:
        learning = [i for i in items if i.category == "learning"][:1]
        job = [i for i in items if i.category == "job"][:1]
        headline_src = learning[0].title if learning else "今日 AI 数据汇总完成"
        return {
            "headline": headline_src[:30],
            "ai_trends":   ["mock: 学习趋势 1", "mock: 学习趋势 2", "mock: 学习趋势 3"],
            "job_signals": ["mock: 求职信号 1", "mock: 求职信号 2", "mock: 求职信号 3"],
        }


class DeepSeekProvider(BaseLLM):
    """OpenAI-SDK-compatible client pointed at DeepSeek."""

    def __init__(self) -> None:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError("pip install openai") from e
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise EnvironmentError("DEEPSEEK_API_KEY not set")
        cfg = get_config()["llm"]
        self._client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
        self._model = cfg.get("model", "deepseek-chat")
        self._temperature = cfg.get("temperature", 0.3)
        self._max_summary = cfg.get("max_tokens_summary", 250)
        self._max_daily = cfg.get("max_tokens_daily", 600)

    def summarize_item(self, item: Item) -> str:
        if not item.raw_content.strip():
            return item.title
        # English source → translate; Chinese source → refine
        is_chinese = item.source in {"nowcoder", "china_ai"}
        system = _PROMPT_REFINE_ZH if is_chinese else _PROMPT_TRANSLATE_EN
        user = f"标题：{item.title}\n\n原文：{item.raw_content[:1200]}"
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system},
                      {"role": "user",   "content": user}],
            max_tokens=self._max_summary,
            temperature=self._temperature,
        )
        return (resp.choices[0].message.content or "").strip()

    def summarize_daily(self, items: list[Item]) -> dict:
        learning = sorted([i for i in items if i.category == "learning"],
                          key=lambda x: -x.score)[:8]
        job = sorted([i for i in items if i.category == "job"],
                     key=lambda x: -x.score)[:8]

        def bulletize(group: list[Item]) -> str:
            return "\n".join(
                f"- [{i.source}] {i.title} | 摘要：{(i.summary or i.raw_content)[:120]}"
                for i in group
            ) or "（无数据）"

        user = (
            "【学习线 top items】\n" + bulletize(learning) +
            "\n\n【求职线 top items】\n" + bulletize(job)
        )
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": _PROMPT_DAILY},
                      {"role": "user",   "content": user}],
            max_tokens=self._max_daily,
            temperature=self._temperature,
        )
        text = (resp.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].lstrip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"  [warn] daily summary JSON parse failed; raw: {text[:200]}")
            return {
                "headline": "今日综合判断生成失败，请查看下方分区内容",
                "ai_trends":   ["LLM 返回格式异常", "—", "—"],
                "job_signals": ["LLM 返回格式异常", "—", "—"],
            }


# ── Factory + convenience ──────────────────────────────────────────────────

def get_provider(name: str | None = None) -> BaseLLM:
    if name is None:
        name = get_config()["llm"].get("provider", "mock")
    if name == "mock":
        return MockProvider()
    if name == "deepseek":
        return DeepSeekProvider()
    raise ValueError(f"Unknown LLM provider: {name}")


def summarize_all(items: list[Item], provider: BaseLLM | str | None = None) -> list[Item]:
    p = provider if isinstance(provider, BaseLLM) else get_provider(provider)
    for item in items:
        if not item.summary:
            try:
                item.summary = p.summarize_item(item)
            except Exception as e:
                print(f"  [warn] summarize failed for {item.id}: {e}")
                item.summary = item.raw_content[:200] or item.title
    return items


def summarize_daily(items: list[Item], provider: BaseLLM | str | None = None) -> dict:
    p = provider if isinstance(provider, BaseLLM) else get_provider(provider)
    try:
        return p.summarize_daily(items)
    except Exception as e:
        print(f"  [warn] daily summary failed: {e}")
        return {
            "headline": "今日综合判断暂不可用",
            "ai_trends":   ["—", "—", "—"],
            "job_signals": ["—", "—", "—"],
        }
