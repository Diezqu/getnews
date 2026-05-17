# AI 每日信息聚合系统 · 规划方案

> 目标：每天/每周自动从网上抓取 Top 论文、GitHub 热门项目、AI 新闻，整理成精美 HTML 仪表盘。
> 关注方向：**Agent / 多智能体**、**AI 产品 / 应用层**。
> 偏好：**用现成开源项目**，不从零造轮子。

---

## 1. 方案选择：三档落地路径

### 🟢 极简档（推荐先跑通）—— 半天工作量
**用 Cowork 定时任务 + 静态 HTML**，完全不部署服务器：
- 让 Cowork 每天早上 9 点跑一次脚本，把 arXiv / HF Daily Papers / GitHub Search / HN Algolia 四个 API 各拉一次，渲染成 HTML 存到 `~/AI_Projects/GetNews/daily/YYYY-MM-DD.html`
- 优点：零运维、零成本、零外网暴露。
- 缺点：电脑关机就跑不了；HTML 不会自动推到云端。

### 🟡 进阶档（建议求职作品集走这个）—— 1-2 天
**Fork 一个成熟开源项目 + 改造成 Agent 工作流**：
- 主骨架：`dw-dengwei/daily-arXiv-ai-enhanced`（2.1k⭐，已有 GitHub Actions + GitHub Pages 全自动 pipeline）
- 改造点：①类目改成 `cs.MA` / `cs.AI` + `agent/MCP/RAG` 关键词；②摘要 prompt 改成你关注的 Agent/产品视角；③在 pipeline 里加入 GitHub Trending 模块和 HF Daily Papers 模块；④用 LangGraph 把抓取→去重→评分→总结串成 Agent 图。
- 优点：GitHub Pages 全自动部署，URL 可发简历，简历亮点直接是"Agent Workflow + RAG 总结管线"。
- 缺点：要花半天读懂 dengwei 的代码并改 prompt。

### 🔴 野心档（如果想替代之前那个 RAG 项目）—— 1 周
**整套自建：Horizon 骨架 + LangGraph Agent + 自托管前端**：
- 主骨架：`Thysrael/Horizon`（1.1k⭐，全链路抓取/评分/总结/发布）
- 数据层：arXiv + HF Daily + GitHub Search + HN + Reddit（5 个源）
- Agent 层：LangGraph 多节点（Fetcher → Deduper → Scorer → Summarizer → Renderer），可参考 `nickhawn/news-agent`
- 前端：TailAdmin 模板 + Tremor 图表 + 现在你看到的这套 Demo CSS
- 部署：本地 Docker / Vercel / Railway 任选
- 简历价值：可以写成"AI 信息聚合 Agent，基于 LangGraph 多节点流水线 + 混合数据源 + LLM 摘要"——直接替换之前那个 RAG 项目。

---

## 2. 推荐的开源项目组合（已调研）

| 角色 | 推荐项目 | Star | 用途 |
|---|---|---|---|
| **全链路骨架** | [Thysrael/Horizon](https://github.com/Thysrael/Horizon) | ~1.1k | 抓取+评分+总结+发布一站式 |
| **arXiv 日报** | [dw-dengwei/daily-arXiv-ai-enhanced](https://github.com/dw-dengwei/daily-arXiv-ai-enhanced) | ~2.1k | GitHub Actions 全自动，最成熟 |
| **HF Daily Papers** | [gabrielchua/daily-ai-papers](https://github.com/gabrielchua/daily-ai-papers) | ~216 | Gemini 总结，模板极简 |
| **HF MCP 接口** | [huangxinping/huggingface-daily-paper-mcp](https://github.com/huangxinping/huggingface-daily-paper-mcp) | - | 给 Agent pipeline 用 |
| **GitHub Trending** | [dongzhang84/trend-monitor](https://github.com/dongzhang84/trend-monitor) | - | 自带 dark HTML 仪表盘生成 |
| **Agent 调度模板** | [nickhawn/news-agent](https://github.com/nickhawn/news-agent) | - | LangGraph + Tavily 日报 Agent |
| **HTML 仪表盘** | [TailAdmin](https://github.com/TailAdmin/tailadmin-free-tailwind-dashboard-template) | 高 | 现成 admin 风格外壳 |
| **UI 灵感** | [smol-ai/ainews-web-2025](https://github.com/smol-ai/ainews-web-2025) | 中 | Karpathy 点名表扬的视觉范本 |

> ⚠️ **避坑**：`karpathy/arxiv-sanity-lite` 已停维护，`MLNLP-World/AI-Paper-Collector` 偏会议历史数据不适合日报，`Papers With Code API` 2025 转交 Meta 后更新变慢——这三个不要作为主数据源。

---

## 3. 数据源清单（API 已验证可用）

| 数据源 | 是否需 Token | 推荐度 | 备注 |
|---|---|---|---|
| arXiv API | 否 | ⭐⭐⭐⭐⭐ | 1 req/3s 限速，结构化 XML |
| HuggingFace Daily Papers (`/api/daily_papers`) | 否 | ⭐⭐⭐⭐⭐ | 未文档化但稳定，含 upvote |
| GitHub Search API | 推荐 PAT | ⭐⭐⭐⭐⭐ | `created:>YYYY-MM-DD&sort=stars` 模拟 trending |
| HackerNews Algolia | 否 | ⭐⭐⭐⭐⭐ | 1 万 req/h，最爽 |
| GitHub Trending (HTML) | 否 | ⭐⭐⭐ | 无官方 API，需爬 HTML |
| Reddit r/MachineLearning | 推荐 OAuth | ⭐⭐⭐ | 必须设 User-Agent |
| Papers With Code | 否 | ⭐⭐ | 2025 后维护减弱，做补充 |

---

## 4. 你没想到的扩展功能（高 ROI）

### 🎯 个性化打分（重要！）
不是简单按"热度"排序，而是按**你的兴趣权重**评分：
- 关键词权重：`agent: 3`, `MCP: 2`, `RAG: 1`, `分布式训练: 0.5`
- 作者权重：你关注的作者（Anthropic / DeepMind / 几个个人研究者）权重 ×2
- 机构权重：清华 / SJTU / Stanford / Anthropic 等权重微调
- 这样每天看到的不是"全网最热"，而是"对你最有用的 Top 10"。

### 💡 "Why it matters" 一句话
让 LLM 在摘要里多生成一行："这跟你之前的 RAG+Agent 项目有什么关系？" ——把每篇论文/项目自动跟你的简历关键词关联，**直接成为求职话术素材**。

### 📌 收藏 + 备忘
HTML 里加一个 ⭐ 按钮，点击后把论文存到本地 JSON。每周日自动汇总成「本周精选」推到一个单独页面——一个月下来就是你的"AI 阅读笔记"。

### 🔥 "AI 产品雷达"
专门一个 tab 监控：
- Product Hunt 的 AI 类别（每日）
- 各大 AI 公司官方 changelog（Anthropic / OpenAI / Google / Mistral 等的 RSS）
- a16z / Sequoia 等 VC 博客的 AI 文章
- HuggingFace Spaces 新出的 demo
求职 AI **产品**岗，这块比论文更重要。

### 🧠 周报 / 月报 自动总结
日报数据攒一周，让 LLM 跨天总结："本周 Agent 方向出现了 3 个趋势：① 多 Agent 拓扑诊断 ② 长 horizon 系统化 ③ 评测漏洞反思"——这种二阶聚合比一阶日报有价值得多。

### 🎙️ 播客 / 视频 信息源
- Lex Fridman / Latent Space 播客的最新 episode 标题 + AI 总结的 takeaways
- Two Minute Papers / Andrej Karpathy YouTube 频道的新视频
- 适合你不想读全文的时候听通勤。

### 📡 招聘信号（顺便）
扫一遍 Anthropic / OpenAI / Mistral / Cohere 等公司的 careers 页面，找到 "AI Application Engineer / Agent Engineer" 类岗位变化——可以直接对接你的求职目标。

### 🔔 异常推送
平时只看仪表盘，但当某条信息**得分超过阈值**（比如某篇论文 24h 内 HF 上 100+ 赞，或某个 GitHub 仓库 24h 内涨 1k 星）时，弹一个桌面通知或 webhook 一下你的飞书/微信。

### 📊 趋势图（已包含）
关键词随时间的热度曲线，能让你直观看到"Agent 在涨、RAG 在跌、MCP 在爆发"。

### 🧬 论文 / 仓库去重 + 同主题聚合
同一研究方向的多篇论文 / 多个仓库，自动 cluster 成一组。每天看 10 个 cluster 而不是 50 条孤立内容——信息密度翻倍。

---

## 5. 推荐落地步骤（进阶档）

**Day 1 上午**
1. `git clone https://github.com/dw-dengwei/daily-arXiv-ai-enhanced`
2. 改 config 里的 arxiv categories → `cs.AI, cs.MA, cs.CL`
3. 改 prompt → 加入 "你关注 Agent 应用层"语境
4. 在本地跑一次 `python daily_arxiv.py`，确认能生成中文摘要

**Day 1 下午**
5. 加一个 `github_trending.py` 模块（参考 `dongzhang84/trend-monitor`）
6. 加一个 `hf_papers.py` 模块（参考 `gabrielchua/daily-ai-papers`）
7. 三个数据源的输出 merge 到一个 JSON

**Day 2 上午**
8. 把现在这套 HTML Demo（你刚看到的 `ai_daily_brief.html`）改成 Jinja2 模板，吃 JSON 出页面
9. GitHub Actions：每天 UTC 0:00 触发，生成 → 推到 GitHub Pages

**Day 2 下午**
10. 加入"个性化打分"模块（4.1 节）
11. 加入"AI 产品雷达"tab（4.4 节）
12. 写一个 README，简历可以挂这个 GitHub Pages 地址

**简历表述建议**：
> AI 信息聚合 Agent (2026.05-至今)
> - 基于 LangGraph 多节点流水线（Fetcher / Scorer / Summarizer / Renderer），日均聚合 arXiv / HF / GitHub / HN 四源约 200 条信息
> - 实现个性化兴趣打分模型 + 跨天主题聚合，将原始信息密度提升 3 倍
> - GitHub Pages 全自动部署，10+ 用户订阅日报

---

## 6. 跟你之前 RAG 项目的关系

> 你之前那个 RAG + Agent 项目是 **"做出一个 RAG 系统"**——很多人都在做。
>
> 这个新项目是 **"用 Agent 解决我自己的问题"**——主动用 AI 做事，是 AI 应用岗 HR 最想看到的信号。
>
> 而且这两个项目可以**互补**：旧项目展示你懂模型 / RAG 内部机制（infra 工程能力），新项目展示你会用 AI 解决实际问题（产品/应用思维）。简历同时挂两个比单一一个强很多。

---

## 7. 接下来你可以告诉我做什么

- "**先看 Demo，没问题再继续**" → 你打开 `ai_daily_brief.html` 看效果。
- "**直接进入极简档**" → 我把它接到 Cowork 定时任务，明天 9 点开始自动跑。
- "**走进阶档**" → 我帮你 fork dengwei 仓库，改 config 和 prompt，跑通第一次。
- "**走野心档**" → 我帮你搭一套完整的 LangGraph pipeline，能直接挂简历。
- "**Demo 这里改一下**" → 你告诉我想加/删什么板块、想换什么风格。
