# GetNews · AI 每日早报

> 自动从 arXiv / HuggingFace / GitHub / HackerNews 聚合 AI 资讯，每天生成精美 HTML 仪表盘，部署到 GitHub Pages。

**Live：** [pages URL will be here after deploy]

## 功能

- 📄 **arXiv** — cs.AI / cs.CL / cs.MA 最新论文，关键词过滤
- 🤗 **HuggingFace Daily Papers** — 每日热门论文（含 upvote 数）
- 🚀 **GitHub Search** — AI 方向近期高速增长仓库
- 🟠 **HackerNews** — AI 相关高分讨论
- 🎯 **个性化打分** — 按 agent/MCP/RAG 关键词权重排序，对你最有用的排最前面
- 🔁 **去重** — 跨来源自动去除重复内容
- 🧠 **LLM 摘要** — DeepSeek API 生成中文摘要（可换 mock 模式）
- 📊 **趋势图** — 7 天关键词热度可视化

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 测试跑通（不调用 LLM）
make mock

# 4. 完整跑一次（调用 DeepSeek + 自动 git push）
make daily
```

## 项目结构

```
GetNews/
├── daily.py              # 主入口 - 一行命令跑全流程
├── fetchers/
│   ├── arxiv_fetcher.py  # arXiv API
│   ├── hf_fetcher.py     # HuggingFace Daily Papers API
│   ├── github_fetcher.py # GitHub Search API
│   └── hn_fetcher.py     # HackerNews Algolia API
├── pipeline/
│   ├── schema.py         # Item 数据结构
│   ├── scorer.py         # 去重 + 个性化打分
│   ├── llm.py            # LLM provider 抽象 (deepseek/mock)
│   └── renderer.py       # Jinja2 → HTML
├── templates/
│   └── daily.html.j2     # HTML 模板（dark theme）
├── docs/                 # GitHub Pages 根目录
│   ├── index.html        # 最新一天（自动更新）
│   └── YYYY-MM-DD.html   # 历史归档
└── data/processed/       # 每日 JSON 数据（用于趋势图）
```

## 自动化

每天在终端运行 `make daily` 即可：拉数据 → 打分去重 → LLM 摘要 → 渲染 HTML → git push → GitHub Pages 自动更新。

整个流程约 2-3 分钟（主要是 LLM API 调用时间）。

## 技术栈

Python · Jinja2 · Chart.js · DeepSeek API · GitHub Pages

---

*AI 信息聚合 Agent Pipeline — arXiv / HF / GitHub / HN 四源 · 个性化打分 · LLM 摘要*
