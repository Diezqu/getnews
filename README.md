# GetNews · AI 每日早报 v2

> **双栏中文 dashboard**：左侧 AI 学习线（arXiv / HuggingFace / GitHub / HackerNews），右侧中国 AI 求职情报线（牛客 / 国内 AI 公司动态 / AI Coding 工具采用信号），顶部 LLM 综合判断。每天凌晨 7 点 GitHub Actions 自动跑完，你打开 Chrome 书签直接看。

**Live：** https://diezqu.github.io/getnews/

---

## 功能

- 📚 **AI 学习线**（左栏）
  - **arXiv** — cs.AI / cs.CL / cs.MA / cs.LG 最新论文
  - **HuggingFace Daily Papers** — 每日热门（含 upvote）
  - **GitHub** — Agent / MCP / RAG 方向快速涨星仓库
  - **HackerNews** — AI 高分讨论
- 💼 **求职情报线**（右栏）
  - **牛客面经** — 人工智能分区热榜（RSSHub）
  - **国内 AI 公司动态** — 机器之心 + 量子位 → 按目标公司过滤
  - **AI Coding 工具采用信号** — 从 HN/HF 派生，Cursor / Claude Code / Cline 等
- 💡 **顶部综合 Summary** — 每日一句 headline + 3 条 AI 趋势 + 3 条求职信号
- 🎯 **按 category 分别打分** — 学习线 vs 求职线权重独立
- 🔁 **跨源去重** — URL hash + 标题指纹
- 🧠 **LLM 三任务** — DeepSeek 同时承担英文翻译、中文精炼、跨源综合
- 📊 **7 天关键词趋势图** + 技术雷达
- 🗄️ **三层归档**（`data/processed/` / `data/summaries/` / `data/aggregates/`）为 v3 周报月报预留
- 🤖 **GitHub Actions 全自动** — 每天 UTC 23:00（北京 07:00）跑完即推

---

## 5 分钟上手

```bash
# 1. 克隆 + 安装
git clone https://github.com/Diezqu/getnews.git && cd getnews
pip install -r requirements.txt

# 2. 配 key
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 本地预览（不调 LLM，不 push）
make mock          # 等价: python daily.py --mock --no-push
open docs/index.html

# 4. 完整跑一次（调 DeepSeek + git push）
make daily
```

---

## 部署到 GitHub Pages（一次性）

1. 在 GitHub 建空仓库 `getnews`（已建好：https://github.com/Diezqu/getnews）
2. Settings → Pages → Source = `main` 分支 / `/docs` 文件夹 → Save
3. Settings → Secrets and variables → Actions → New repository secret
   - Name: `DEEPSEEK_API_KEY`
   - Value: 你的 DeepSeek API key
4. Actions 标签 → 第一次手动触发 `Daily Brief` workflow
5. 等 2-3 分钟，访问 https://diezqu.github.io/getnews/

之后每天凌晨 7 点（北京时间）自动更新，你什么都不用做。

---

## 项目结构

```
GetNews/
├── daily.py                   # 一行命令跑全流程
├── config.yaml                # 关键词权重 / 源开关 / LLM provider 都在这里
├── .github/workflows/daily.yml # 每日 7:00 自动 cron
│
├── fetchers/
│   ├── base.py                 # BaseFetcher + REGISTRY
│   ├── arxiv_fetcher.py        ├ learning
│   ├── hf_fetcher.py           │
│   ├── github_fetcher.py       │
│   ├── hn_fetcher.py           ┘
│   ├── nowcoder_fetcher.py     ┐
│   ├── china_ai_fetcher.py     ├ job
│   └── coding_tool_fetcher.py  ┘ (派生源)
│
├── pipeline/
│   ├── schema.py               # Item 数据结构
│   ├── config.py               # YAML 加载器
│   ├── scorer.py               # 按 category 打分 + 去重
│   ├── llm.py                  # BaseLLM + DeepSeek/Mock provider
│   ├── summarizer.py           # 每日综合 summary
│   ├── aggregator.py           # 周/月报 stub (v3)
│   └── renderer.py             # Jinja2 → HTML
│
├── templates/
│   ├── base.html.j2            # 主框架
│   ├── daily.html.j2           # 日报（继承 base）
│   ├── archive.html.j2         # 历史归档索引
│   ├── weekly.html.j2          # v3 周报 (stub)
│   ├── monthly.html.j2         # v3 月报 (stub)
│   └── partials/               # 9 个卡片 partial
│
├── docs/                       # GitHub Pages 根
│   ├── index.html              # 最新一天
│   ├── YYYY-MM-DD.html         # 历史日报
│   └── archive.html            # 归档索引
│
└── data/
    ├── processed/YYYY-MM-DD.json    # 当日 Item 全量
    ├── summaries/YYYY-MM-DD.json    # 当日 LLM summary
    └── aggregates/{weekly,monthly}/ # v3 输出位置
```

---

## 怎么扩展

| 需求 | 怎么做 |
|---|---|
| **加一个新数据源** | 新建 `fetchers/xxx_fetcher.py`，继承 `BaseFetcher`，末尾 `REGISTRY.register(...)`；在 `config.yaml` 的 `sources:` 下加一段配置 |
| **调关键词权重** | 改 `config.yaml`，不动代码 |
| **暂时关掉某源** | `config.yaml` → `sources.<name>.enabled: false` |
| **换 LLM 服务商** | 实现一个 `BaseLLM` 子类，在 `pipeline/llm.py:get_provider` 加分支，改 `config.yaml` |
| **加新 card 样式** | 新建 `templates/partials/card_xxx.html.j2`，在 `daily.html.j2` 引入 `{% include %}` |
| **换皮肤** | 改 `templates/base.html.j2` 的 CSS variables (`--paper`, `--navy`, ...) |
| **加周报 / 月报** | 实现 `pipeline/aggregator.build_weekly()` + 复用 `templates/weekly.html.j2` |

---

## 技术栈

Python · Jinja2 · DeepSeek API（OpenAI SDK 兼容）· RSSHub · feedparser · Chart.js · GitHub Actions · GitHub Pages

---

## 成本

每天约 80K tokens ≈ **¥0.04**。充 ¥10 够用 8 个月。
