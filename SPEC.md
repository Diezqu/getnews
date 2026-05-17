# GetNews v2 · 需求与交付规格

> 这份文档是 v1 → v2 的完整重写，把 SPEC 从「AI Agent 工程师的英文日报」升级为「**中国 AI 算法/应用岗求职 + 学习的双栏中文 dashboard**」。
> 你看完后告诉我哪里要改，确认无误我再继续。

---

## 1. 定位（为什么做这个）

**一句话**：每天早上打开 Chrome 书签 → 看到一个**双栏中文 dashboard**，左侧是 AI 前沿学习，右侧是中国 AI 求职情报，顶部是 LLM 综合判断 → 5 分钟了解今天该知道的一切。

**两个使命同时承担**：
1. **防止落伍**（长期能力建设）：4 个英文源持续追踪 Agent / MCP / RAG / LLM 前沿
2. **求职准备**（短期战术）：3 个中文源专门提供面试趋势、国内行业动态、AI 工具采用信号
3. **简历资产**（对外展示）：URL 挂简历，公开运行，可被招聘官点开

**不是什么**：
- ❌ 不是新闻爬虫 / 通用 RSS 阅读器
- ❌ 不是 SaaS 产品（只服务你一个人）
- ❌ 不需要登录、订阅系统、后端数据库
- ❌ 不需要你每天敲命令（已升级为全自动）

---

## 2. 用户故事

**日常使用**（零操作）：
```
你的电脑还睡着 → 凌晨 7:00 GitHub Actions 自动跑完
                ↓
            HTML 自动推送到 GitHub Pages
                ↓
你 8:00 起床 → 打开 Chrome → 点开「AI 每日早报」书签 → ✨ 今日已就绪
```

**对外展示**：
- 简历上挂一行 "AI Daily Brief · https://你的名字.github.io/getnews"
- 招聘官点开看到一个**真实运行**、**每天更新**的**中英双源**、**带 LLM 综合判断**的工程作品

---

## 3. 整体架构

```
            ┌─────────────────────────────────────┐
            │  GitHub Actions cron (UTC 23:00)     │
            │  = 北京时间 7:00 早上                 │
            └──────────────────┬──────────────────┘
                               ▼
            ┌─────────────────────────────────────┐
            │  fetchers/ (并行抓取，互不阻塞)        │
            │  ─────────────────────────────       │
            │  📚 AI 学习线（4 源 · 英文 → 中文摘要）│
            │     arxiv · hf · github · hn        │
            │  ─────────────────────────────       │
            │  💼 求职情报线（3 源 · 全中文）        │
            │     nowcoder · china_ai · coding_tool│
            └──────────────────┬──────────────────┘
                               ▼
            ┌─────────────────────────────────────┐
            │  pipeline/                          │
            │   scorer   ─ 按 category 分别打分    │
            │   llm      ─ DeepSeek 摘要 + 翻译    │
            │   summarizer [新] ─ 顶部综合 summary │
            │   renderer ─ 渲染双栏 HTML           │
            └──────────────────┬──────────────────┘
                               ▼
            ┌─────────────────────────────────────┐
            │  git push → GitHub Pages 自动部署    │
            └─────────────────────────────────────┘
                               ▼
            ┌─────────────────────────────────────┐
            │   你打开浏览器书签，今日早报已在 ✨    │
            └─────────────────────────────────────┘
```

---

## 4. 7 个数据源详单

### 📚 AI 学习线（左栏 · 2/3 宽）

| 源 | 接入方式 | 内容 | 估计/天 |
|---|---|---|---|
| **arXiv** | 官方 API | cs.AI / cs.CL / cs.MA / cs.LG 最新论文 | 20-30 |
| **HuggingFace Daily Papers** | 官方 API | 当日热门论文（含 upvote） | 5-15 |
| **GitHub Search** | 官方 API | AI / Agent / MCP / RAG 新兴仓库 | 20-40 |
| **HackerNews** | Algolia API | AI 高分讨论 | 15-30 |

**特点**：标题保留英文（学术准确），摘要全部 LLM 翻译成中文。

### 💼 求职情报线（右栏 · 1/3 宽）

| 源 | 接入方式 | 内容 | 估计/天 |
|---|---|---|---|
| **牛客面经热榜** | RSSHub 公共实例 `/nowcoder/discuss/{tagId}` | 人工智能 / 机器学习分区热门面经 | 10-20 |
| **国内 AI 公司动态** | 各家官博 RSS + RSSHub 公众号路由 | 智谱 / 月之暗面 / DeepSeek / 通义 / Doubao / MiniMax / 阶跃 等 7-10 家 | 5-10 |
| **AI Coding 工具采用信号** | 派生源：在已抓的 HN（和 HF 摘要）数据上按关键词过滤 + LLM 翻译/精炼 | 哪些公司/团队提到了 Cursor / Claude Code / Cline / Copilot 等 | 3-5 |

**特点**：全中文，标题与摘要均为中文（牛客和国内媒体本身就是中文，无需翻译）。

### RSSHub 依赖说明

**RSSHub 是什么**：把不提供 RSS 的网站（牛客、微信公众号等）转换成 RSS 格式的开源工具。我们用公共实例 `rsshub.app`，零配置即可使用。

**风险与对策**：rsshub.app 平均一个月有 2-4 天间歇性挂机。挂的时候那天对应的源拿不到数据 → 右栏对应区域显示「今日暂无数据」，**不影响其他 6 个源照常更新**。

**升级路径**：如果以后觉得"挂得太频繁"，30 分钟可以一次性切到自托管 Vercel 实例（免费），不动其他代码。

---

## 5. 数据 Schema 扩展

```python
Source = Literal["arxiv", "hf_papers", "github", "hackernews",
                 "nowcoder", "china_ai", "coding_tool"]
Category = Literal["learning", "job"]

@dataclass
class Item:
    id: str
    source: Source
    category: Category       # 🆕 "learning" 或 "job"，决定渲染到左栏还是右栏
    title: str               # 原标题（英文源保留英文，中文源直接是中文）
    url: str
    summary: str = ""        # LLM 生成的中文摘要（所有源都强制中文）
    raw_content: str = ""    # 原始内容（用于 LLM 输入）
    score: float = 0.0       # 个性化打分
    tags: list[str] = []
    stars: int = 0
    authors: list[str] = []
    published_at: str = ""
```

**说明**：英文源（arXiv / HF / GitHub / HN）的 `title` 保留英文不翻译；只有 `summary` 是 LLM 翻译/精炼出的中文。这样既保证了学术准确性，又让你能扫一眼英文标题快速过滤。

---

## 6. 个性化打分（按 category 分别打分）

**为什么分开打分**：学习线和求职线的"重要"含义不同。学习线是关心 Agent/MCP/RAG 新进展；求职线是关心高频面试题、目标公司动态。

### 学习线（沿用 v1，但权重小调）
```
agent / multi-agent  +3.0
MCP                  +2.5
RAG / retrieval      +1.5
LLM / language model +1.0
tool use / planning  +1.5
memory               +1.0
benchmark            +0.5
fine-tuning          +0.5
```

### 求职线（新，针对中国 AI 招聘场景）
```
# 牛客面经题型权重
transformer / attention   +3.0
RAG / 向量数据库          +2.5
agent / 多智能体          +2.5
prompt engineering        +2.0
LLM 部署 / vLLM           +2.0
fine-tuning / LoRA        +2.0
分布式训练                 +1.5
强化学习 / RLHF            +1.5

# 国内 AI 公司目标关注
智谱 / GLM                +3.0
月之暗面 / Kimi           +3.0
DeepSeek                  +3.0
通义 / 阿里               +2.5
字节 / Doubao             +2.5
MiniMax                   +2.0

# AI Coding 工具
Cursor                    +2.0
Claude Code               +2.0
Cline / Aider             +1.5
Copilot                   +1.0
```

**作者权重**：保留 v1 的 Anthropic / DeepMind / 清华 / SJTU 等 +2.0

**Stars 加权**：log(stars+1) × 0.5

**修改方式**：直接编辑 [pipeline/scorer.py](pipeline/scorer.py)。

---

## 7. LLM 三任务（DeepSeek）

DeepSeek 在 pipeline 中承担三种不同任务，每种都有专属 prompt：

### 任务 A：英文摘要翻译（per item，约 30-40 次/天）
- 输入：英文 abstract / repo description / HN 评论
- 输出：80-120 字中文，三句话结构（核心贡献 / 关键结果 / 与 Agent/RAG/MCP 关联）

### 任务 B：中文内容精炼（per item，约 10-20 次/天）
- 输入：牛客面经原文 / 公司博客全文
- 输出：60-80 字精炼要点，提炼"被问了什么 / 公司发布了什么"

### 任务 C：顶部综合 Summary（每日 1 次）
- 输入：当日全部 Item 标题 + top 15 高分 item 的摘要
- 输出：JSON `{ "headline": "30字头条", "ai_trends": [3条], "job_signals": [3条] }`

**成本估算**：
- 任务 A+B 约 50 次 × 1500 tokens = 75K tokens
- 任务 C 约 1 次 × 4000 tokens = 4K tokens
- 共约 80K tokens/天 ≈ **¥0.04/天 ≈ ¥1.2/月** —— 充 ¥10 够用 8 个月

**API key 管理**：放在 GitHub Secrets 里（`DEEPSEEK_API_KEY`），加密存储，永远不出现在日志或代码。

---

## 8. 顶部「今日总 Summary」模块

新建 `pipeline/summarizer.py`，在所有 fetcher + scorer + 单条摘要完成之后调用一次：

**Prompt 模板**：
```
你是 AI 信息分析师。下面是今天聚合到的内容，分为「AI 学习」和「求职情报」两类。
请生成一个综合判断，输出严格 JSON：

{
  "headline": "<30 字以内一句话，今天最值得知道的事>",
  "ai_trends":   ["<30 字>", "<30 字>", "<30 字>"],
  "job_signals": ["<30 字>", "<30 字>", "<30 字>"]
}

输入数据：
[学习线 top 8 item 的标题 + 摘要]
[求职线 top 8 item 的标题 + 摘要]
```

**渲染位置**：MASTHEAD 正下方，作为整页最显眼的"今日先看这里"块（v2 删了原 STAT BAR，垂直空间全给 summary）。

---

## 9. HTML 布局（每个区块详细说明）

页面从上到下分 6 个区块（v2 把原 v1 的 STAT BAR 删了——纯数字对你没价值，把垂直空间让给「今日总 Summary」更值）。**只做桌面端布局**（你说只在电脑看），固定最小宽度 1200px，不写 `@media` 响应式规则。

### 9.1 MASTHEAD（页头横幅）

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 AI 每日早报                  2026-05-17 · 周日             │
│ INTELLIGENCE · RESEARCH · SIGNAL  [📄 38] [🚀 32] [💼 25]    │
└─────────────────────────────────────────────────────────────┘
```

- **背景**：深海军蓝 `#1e3557`，底部 3px 砖红腰线
- **左侧（白字）**：
  - 主标题 "AI 每日早报"（Cormorant Garamond 32px 衬线）
  - 副标题 "INTELLIGENCE · RESEARCH · SIGNAL"（小号大写英文）
- **右侧（白字）**：
  - 日期 + 星期（2026-05-17 · 周日）
  - **3 个数据胶囊**：
    - 📄 N Papers = 今日 arXiv + HF 论文总数
    - 🚀 N Repos = 今日 GitHub 仓库总数
    - 💼 N Jobs = 今日求职情报总数（牛客 + 国内 AI 公司 + AI Coding 信号）

### 9.2 今日总 Summary（最显眼的"先看这里"块）

```
┌─────────────────────────────────────────────────────────────┐
│ 💡 国内 4 家大模型同日发布 v2，牛客面经 RAG 工程化题暴增  ← headline
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ 📚 AI 趋势                  │  💼 求职信号                  │
│ ▸ Claude 4.8 multi-agent    │  ▸ 字节算法岗加大 RAG 工程化   │
│   benchmark 创 SOTA         │    问题考察                  │
│ ▸ MCP 标准库 v3 首批         │  ▸ 智谱本周放出 200 个研究员 HC│
│   收纳 200 工具             │                              │
│ ▸ DeepSeek-V4 推理速度       │  ▸ 国内大厂 80% 工程团队改    │
│   提升 2.3 倍               │    用 Cursor 替代自研 IDE     │
└─────────────────────────────────────────────────────────────┘
```

- **背景**：白色卡片，左侧 3px 深海军蓝边框（类似引言块），整体一处微阴影
- **顶部 headline**：LLM 综合判断今天最值得知道的一句话（30 字以内，砖红色加粗 16px）
- **下方两栏对齐（各占 50%）**：
  - **左栏 📚 AI 趋势**：3 条要点（每条 30 字内），LLM 综合学习线 top item 生成
  - **右栏 💼 求职信号**：3 条要点（每条 30 字内），LLM 综合求职线 top item 生成

### 9.3 主体内容区（双栏：左 2/3 + 右 1/3）

#### 9.3.1 左栏：📚 AI 学习线（4 张卡片垂直堆叠）

每张卡片是白底，1px 暖灰边框 `#ddd5c4`，微阴影。卡片头部有衬线大标题 + 右侧 badge。

**🔹 arXiv 最新论文卡片**（约 6-8 条 item）

每条 item 渲染为：
```
┌─────────────────────────────────────────────────────────┐
│ AutoAgent: Fully Automatic Agent Generation from NL    │ ← 英文标题（黑字 13px 加粗，可点击跳 arxiv）
│ Alice Wang · Bob Zhang · 2026-05-17                    │ ← 作者前 3 + 日期（DM Mono 11px 灰）
│ 提出无需人工标注、完全从自然语言描述自动生成 Agent 的    │ ← LLM 翻译的中文摘要（深灰 12.5px）
│ 框架。在 SWE-bench 上超越 GPT-4 基线 12 个百分点，部署   │
│ 成本极低。对 Agent 工程化方向有直接参考价值。            │
│ [cs.AI] [cs.MA] [agent] [MCP]                  9.2  ●  │ ← tags（左，等宽小标签）+ 分数 chip（右，>=8 砖红）
└─────────────────────────────────────────────────────────┘
```

**🔹 HuggingFace Daily Papers 卡片**（约 5 条 item）

跟 arXiv 类似，但额外显示 upvote 数：
```
│ LongAgent: Scaling Language Agents to 128k Context     │
│ Chen Li et al. · 342 upvotes                           │
│ 解决了 Agent 在超长上下文中注意力分散问题，引入分层记忆 │
│ 机制，128K token 窗口下任务完成率提升 31%。              │
│ [agent] [long-context] [memory]                342 👍  │ ← upvote chip（绿色）
```

**🔹 GitHub 新兴仓库卡片**（约 5-8 条 item）

```
┌─────────────────────────────────────────────────────────┐
│ microsoft/promptflow                          ★ 10.2K  │ ← 仓库全名（左）+ stars（右，金色）
│ 微软开源的 LLM 应用开发框架，支持 prompt 版本管理、     │ ← LLM 翻译的中文描述
│ 流程可视化和批量测试。本周新增 MCP 协议支持。            │
│ [Python] [MCP] [LLM]                                   │ ← 主语言 + topics
└─────────────────────────────────────────────────────────┘
```

**🔹 HackerNews AI 热议卡片**（约 8 条 item）

```
┌─────────────────────────────────────────────────────────┐
│ 1  Show HN: I built a personal AI research assistant   │ ← 排名（衬线大字）+ 英文原标题
│    2346 pts · 2026-05-17                               │ ← 砖红 N pts + 日期
│                                                         │
│ 2  An AI agent deleted our production database         │
│    860 pts · 2026-05-15                                │
└─────────────────────────────────────────────────────────┘
```

#### 9.3.2 右栏：💼 求职情报线（3 张卡片垂直堆叠）

**🔹 牛客面经热榜卡片**（约 8-12 条 item）

```
┌──────────────────────────────────────────────┐
│ 字节跳动 算法工程师 一面凉经                  │ ← 中文原标题
│ user123 · 2026-05-17                         │
│ 主要考察 transformer attention 计算、RAG 流程│ ← LLM 精炼要点（提炼"被问什么"）
│ 优化、多模态 fine-tune 实操经验。            │
│ [字节] [算法] [Transformer]                   │ ← 公司 / 岗位 / 关键技术 tag
└──────────────────────────────────────────────┘
```

**🔹 国内 AI 公司动态卡片**（约 5-8 条 item）

```
┌──────────────────────────────────────────────┐
│ DeepSeek-V4 推理速度提升 2.3 倍               │ ← 公司发布原标题（中文）
│ DeepSeek 官博 · 2026-05-17                    │
│ 全新架构 sparse-MoE，推理 token/s 提升 230%。│ ← LLM 中文精炼
│ 已在 chat.deepseek.com 全量上线。            │
│ [DeepSeek] [推理优化] [MoE]                   │
└──────────────────────────────────────────────┘
```

**🔹 AI Coding 工具采用信号卡片**（约 3-5 条 item）

派生源：从已抓的 HN/HF 数据按关键词（Cursor / Claude Code / Cline / Copilot）过滤，每条用 LLM 翻译标题 + 精炼成中文：

```
┌──────────────────────────────────────────────┐
│ 1000 人工程团队从 Copilot 切换到 Claude Code │ ← LLM 中文翻译标题
│ 来源: HN #47733217 · 588 pts                  │
│ 帖子主要内容：迁移后 PR 通过率提升 47%，      │ ← LLM 精炼讨论内容
│ 主要原因是 Claude Code 的上下文窗口...        │
│ [Claude Code] [大厂采用]                      │
└──────────────────────────────────────────────┘
```

### 9.4 关键词热度趋势图（横跨整行）

Chart.js 折线图，位于主内容区下方：
- **横轴**：过去 7 天日期（5/11, 5/12, ..., 5/17）
- **纵轴**：每个关键词当日在所有源中出现的频次（归一化到 0-100）
- **三条线**（颜色与 v2 主题对齐）：
  - Agent（深海军蓝 `#1e3557`）
  - MCP（砖红 `#c94428`）
  - RAG（森林绿 `#2a7d4f`）
- 曲线 + 半透明面积填充 + 圆点 marker
- 数据来源：`data/processed/YYYY-MM-DD.json` 历史归档

### 9.5 技术雷达（横向 progress bar 列表）

显示 6 个关键词的当前热度，从今日所有 Item 中动态计算频次百分比：

```
Agent          ████████████████░░░░  95%  多 Agent 协作框架持续爆发
MCP            ████████████████░     92%  2026 Agent 集成标准
RAG            ███████████░░░░░░░    75%  检索增强依然是核心技术
LLM Fine-tune  ██████████░░░░░░░     68%  垂直领域微调需求上升
AI Safety      ████████░░░░░░░░░     55%  对齐与可解释性研究增加
Local-First AI ███████░░░░░░░░░░     48%  隐私计算与离线部署
```

每行 = 关键词名（粗体）+ 进度条（渐变填充）+ 百分比 + 短描述。进度条颜色按关键词族分配（学习线偏蓝绿，求职线偏砖红金）。

### 9.6 FOOTER（页脚）

居中一行小字：
```
AI Pipeline 自动生成 · 2026-05-17 07:00 · GitHub 仓库
```

---

### 设计约束（不做的事）

- **不做响应式布局**：固定桌面端宽度（min-width 1200px），不写 `@media` 规则
- **不做 dark mode 切换**：已确认 light 主题（暖米色），不提供主题切换
- **不做交互状态**：所有 hover 效果保留，但不做"展开/收起"、"收藏"、"已读标记"这类需要 JS 状态的功能
- **不做搜索/过滤**：每天的内容相对固定（约 50-80 条），不加搜索框

---

## 10. 视觉风格（已确认 v1.5 light theme）

| 元素 | 样式 |
|---|---|
| 背景 | 暖米色纸张感 `#f6f2ea` |
| 卡片 | 白色 `#ffffff` + 1px 细边框 + 微阴影 |
| 主色 | 深海军蓝 `#1e3557`（标题、链接） |
| 高亮色 | 砖红 `#c94428`（高分、热点、今日 headline） |
| 求职线色 | 古铜金 `#b8872a`（区分学习线的视觉锚点） |
| 学习线色 | 森林绿 `#2a7d4f`（区分求职线的视觉锚点） |
| 衬线字体 | Cormorant Garamond（masthead + 大标题，学术期刊感） |
| 无衬线 | Outfit（正文 UI） |
| 等宽字体 | DM Mono（meta、tag、数字） |

---

## 11. GitHub Actions 自动化

**文件**：`.github/workflows/daily.yml`

```yaml
name: Daily Brief
on:
  schedule:
    - cron: '0 23 * * *'        # UTC 23:00 = 北京 7:00
  workflow_dispatch:             # 也可手动触发

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.13' }
      - run: pip install -r requirements.txt
      - run: python daily.py --no-push
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Commit + push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/ data/processed/
          git diff --staged --quiet || git commit -m "auto: daily brief $(date -u +'%Y-%m-%d')"
          git push
```

**Secrets 配置**（在 GitHub 仓库 Settings → Secrets and variables → Actions）：
- `DEEPSEEK_API_KEY`：你的 DeepSeek key（加密存储，不在日志显示）

**失败容忍**：任何 fetcher 失败 → skip + log，不阻塞整体。即使 LLM 调用失败，也用 raw content 渲染。

**本地后备**：保留 `make daily` 命令，方便你本地调试 prompt 或验证新 fetcher。

---

## 12. 归档与聚合架构（为周报/月报做准备）

每天的产出不只是"今天的网页"，而是**结构化数据资产**——这样将来加周报、月报、年度复盘时不用回头爬一遍。

### 12.1 三层归档目录

```
data/
├── processed/                    # 每日 Item 全量（已存在）
│   ├── 2026-05-17.json          # 当天 50-80 条 Item 完整 JSON
│   └── ...
│
├── summaries/                    # 🆕 每日 LLM 综合 summary 输出
│   ├── 2026-05-17.json          # {headline, ai_trends, job_signals, generated_at}
│   └── ...
│
└── aggregates/                   # 🆕 周/月预聚合（v2 建目录，暂不写数据）
    ├── weekly/                   # 周报数据
    │   └── 2026-W20.json        # ISO 周编号
    └── monthly/                  # 月报数据
        └── 2026-05.json
```

```
docs/                             # GitHub Pages 根目录
├── index.html                    # 今日（最新）
├── YYYY-MM-DD.html               # 每日历史归档（已存在）
├── archive.html                  # 🆕 历史索引页（列出所有日报/周报/月报）
├── weekly/                       # 🆕 周报页面（v2 留目录，v3 填内容）
│   └── 2026-W20.html
└── monthly/                      # 🆕 月报页面
    └── 2026-05.html
```

### 12.2 每日 summary JSON 结构

`data/summaries/2026-05-17.json`：
```json
{
  "date": "2026-05-17",
  "generated_at": "2026-05-17T07:00:00+08:00",
  "headline": "国内 4 家大模型同日发布 v2，牛客面经 RAG 工程化题暴增",
  "ai_trends": [
    "Claude 4.8 multi-agent benchmark 创 SOTA",
    "MCP 标准库 v3 首批收纳 200 工具",
    "DeepSeek-V4 推理速度提升 2.3 倍"
  ],
  "job_signals": [
    "字节算法岗加大 RAG 工程化问题考察",
    "智谱本周放出 200 个研究员 HC",
    "国内大厂 80% 工程团队改用 Cursor 替代自研 IDE"
  ],
  "stats": {
    "total_items": 67,
    "learning_count": 42,
    "job_count": 25,
    "top_score": 9.5,
    "top_item_title": "字节跳动 算法工程师 一面凉经"
  }
}
```

每天 pipeline 末尾自动写一份，**LLM 调用结果与渲染解耦**——HTML 渲染失败不影响 summary 存档。

### 12.3 v3 周报/月报怎么用这些数据

设计预留接口（`pipeline/aggregator.py` 框架代码 v2 就建好）：

**周报生成**（v3 实现，但 v2 接口先定）：
- 输入：过去 7 天的 `processed/*.json` + `summaries/*.json`
- LLM 处理：跨 7 天 item 主题聚类 + 7 个 headline 做"本周叙事"综合
- 输出：`aggregates/weekly/2026-W20.json` + `docs/weekly/2026-W20.html`

**月报生成**：
- 输入：过去 30 天的 daily summary（不需要全部 item，节省 token）
- LLM 处理：识别月度趋势曲线 + 关键事件 + 主题转移
- 输出：`aggregates/monthly/2026-05.json` + `docs/monthly/2026-05.html`

### 12.4 v2 必须落地的归档部分

| 项 | v2 是否实现 | 说明 |
|---|---|---|
| `data/processed/` 每日全量 | ✅ 已实现 | 沿用现有 |
| `data/summaries/` 每日 LLM summary | ✅ v2 新增 | 一次 LLM 调用就生成，必须落盘 |
| `data/aggregates/` 目录骨架 | ✅ v2 建目录 | 空文件夹 + `.gitkeep` |
| 周报/月报内容 | ❌ v3 实现 | 接口 `pipeline/aggregator.py` v2 留空骨架 |
| `docs/archive.html` 历史索引页 | ✅ v2 新增 | 简单列表，每日生成后自动追加 |

---

## 13. 可扩展性设计

为了让以后**加新源、调权重、换主题、加新输出格式**都不用大改代码，v2 按下面 4 个原则设计：

### 13.1 Fetcher 注册表模式

抽象接口 `fetchers/base.py`：
```python
class BaseFetcher(ABC):
    source_id: str                   # e.g. "arxiv"
    category: Category               # "learning" | "job"

    @abstractmethod
    def fetch(self, target_date: date) -> list[Item]: ...
```

每个具体 fetcher 继承 `BaseFetcher` + 在文件末尾自注册：
```python
# fetchers/arxiv_fetcher.py
class ArxivFetcher(BaseFetcher):
    source_id = "arxiv"
    category = "learning"
    def fetch(self, target_date): ...

REGISTRY.register(ArxivFetcher())
```

`daily.py` 不再硬编码 7 个 fetcher，而是循环 `REGISTRY.all()`：

```python
for fetcher in REGISTRY.all():
    items += fetcher.fetch(today)
```

**好处**：以后加 PaperWithCode / Twitter 等新源 → 只需新建一个 .py 文件，不动其他代码。

### 13.2 配置外置（YAML）

新建 `config.yaml`，把硬编码的关键词权重、目标公司、源列表等都搬出来：

```yaml
# Personalized scoring weights
scoring:
  learning:
    agent: 3.0
    MCP: 2.5
    RAG: 1.5
    # ...
  job:
    transformer: 3.0
    智谱: 3.0
    Cursor: 2.0
    # ...
  authors:
    bonus: 2.0
    watchlist:
      - anthropic
      - deepmind
      - 清华
      # ...

# Source enable/disable
sources:
  arxiv:       { enabled: true,  max_items: 30 }
  hf_papers:   { enabled: true,  max_items: 15 }
  nowcoder:    { enabled: true,  max_items: 20, rsshub_route: "/nowcoder/discuss/639" }
  china_ai:
    enabled: true
    feeds:
      - { name: "DeepSeek 官博",  url: "https://api.deepseek.com/blog/rss" }
      - { name: "智谱 GLM",       url: "https://..." }

# LLM provider
llm:
  provider: "deepseek"     # 或 "mock" / "claude_api"
  model: "deepseek-chat"
  temperature: 0.3

# Rendering
rendering:
  theme: "light"           # 'light' | 'dark' (未来加)
  max_per_card:
    arxiv: 8
    hf_papers: 5
    github: 8
    hn: 8
```

**好处**：调权重不用改代码、改 git。只改 YAML 提交即可。

### 13.3 LLM Provider 抽象（已实现，强化文档）

现有 `pipeline/llm.py` 已经有 provider 抽象（`mock` / `deepseek`）。v2 扩充为：

```python
# pipeline/llm.py
class BaseLLM(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, **kwargs) -> str: ...

PROVIDERS = {
    "deepseek":     DeepSeekProvider,
    "mock":         MockProvider,
    "claude_api":   ClaudeAPIProvider,   # v3 加
    "openai":       OpenAIProvider,       # v3 加
}
```

**好处**：未来想换 Claude 或 OpenAI → 加一个 Provider 类，改 YAML 一行。

### 13.4 Renderer 模板化

`templates/daily.html.j2` 拆为：
```
templates/
├── base.html.j2             # 主框架（masthead + footer + 双栏 grid）
├── daily.html.j2            # 日报特化（包含 today's summary + cards）
├── weekly.html.j2           # 🆕 周报特化（v3 用，v2 留空文件）
├── monthly.html.j2          # 🆕 月报特化（v3 用）
└── partials/
    ├── card_paper.html.j2     # 论文卡片（arxiv + hf 复用）
    ├── card_repo.html.j2      # GitHub 仓库卡片
    ├── card_hn.html.j2        # HN 帖卡片
    ├── card_job.html.j2       # 求职帖卡片（牛客复用）
    ├── card_company.html.j2   # 国内 AI 公司动态卡片
    └── summary_block.html.j2  # 顶部 summary 块
```

**好处**：以后加新 item 类型 → 新建一个 partial 文件 + 在 daily.html.j2 引一行 `{% include %}`，不动其他模板。

### 13.5 扩展性 Cheat Sheet

| 需求 | v2 之后怎么做 |
|---|---|
| 加新数据源（如 ArXiv Sanity / Twitter） | 新建 `fetchers/xxx_fetcher.py` 继承 BaseFetcher |
| 改关键词权重 | 改 `config.yaml`，不动代码 |
| 暂时屏蔽某源 | `config.yaml` 改 `enabled: false` |
| 换 LLM 服务商 | 新建 `LLMProvider` 类 + 改 `config.yaml` |
| 加新 card 样式 | 新建 `templates/partials/card_xxx.html.j2` |
| 加周报/月报 HTML | 新建 `templates/weekly.html.j2` + 实现 `aggregator.weekly()` |
| 换皮肤主题 | 改 `templates/base.html.j2` 的 CSS 变量 |

---

## 14. 现有代码改造工作量

| 模块 | 改造内容 | 工作量 |
|---|---|---|
| **数据 & schema** | | |
| `pipeline/schema.py` | 加 `category` 字段 + Source/Category Literal 类型扩展 | 5 min |
| **Fetcher 基础设施（可扩展性）** | | |
| `fetchers/base.py` | 🆕 BaseFetcher 抽象类 + 注册表 REGISTRY | 20 min |
| 现有 4 个 fetcher | 重构继承 BaseFetcher + 加 `category="learning"` + 注册 | 20 min |
| `fetchers/nowcoder_fetcher.py` | 🆕 调 RSSHub，继承 BaseFetcher | 30 min |
| `fetchers/china_ai_fetcher.py` | 🆕 多家 RSS 并行 | 45 min |
| `fetchers/coding_tool_fetcher.py` | 🆕 派生源，关键词过滤 + LLM | 30 min |
| **配置外置（可扩展性）** | | |
| `config.yaml` | 🆕 关键词权重 / 源开关 / LLM provider / 渲染配置 | 30 min |
| `pipeline/config.py` | 🆕 配置加载器（YAML → Python dict） | 15 min |
| `pipeline/scorer.py` | 改：从 config 读权重 + 按 category 分组打分 | 20 min |
| **LLM 三任务** | | |
| `pipeline/llm.py` | 重构为 BaseLLM provider 抽象 + 多 prompt 模板 | 30 min |
| `pipeline/summarizer.py` | 🆕 顶部 summary 生成模块 | 30 min |
| **归档与聚合** | | |
| `data/summaries/` 落盘逻辑 | 🆕 在 daily.py 末尾把 summary JSON 写盘 | 10 min |
| `data/aggregates/` 目录骨架 | 🆕 建空目录 + `.gitkeep` | 2 min |
| `pipeline/aggregator.py` | 🆕 周报/月报 stub 接口（v2 留空，v3 填实现） | 15 min |
| `docs/archive.html` 生成 | 🆕 历史索引页（自动追加每日链接） | 20 min |
| **渲染（模板化）** | | |
| `templates/base.html.j2` | 🆕 主框架抽出（masthead + footer） | 20 min |
| `templates/daily.html.j2` | 改：继承 base + 引入 partials + 删 STAT BAR | 30 min |
| `templates/partials/*.html.j2` | 🆕 5-6 个 card partial 文件 | 45 min |
| **自动化** | | |
| `.github/workflows/daily.yml` | 🆕 GitHub Actions cron + secrets | 15 min |
| `daily.py` | 改：从 REGISTRY 循环 + 加 summarizer + 写 summary 落盘 | 15 min |
| `README.md` | 更新文档（v2 新结构 + 如何加新源） | 15 min |
| **总计** | | **~7 小时** |

工作量比 v1 草稿（4.5 小时）多了约 2.5 小时——多出来主要是**可扩展性基建**（base fetcher / config.yaml / 模板拆分 / 归档骨架）。这些是一次性投入，之后加新源、调权重、加新视图都会显著加速。

---

## 15. 项目结构（v2 完成态）

```
GetNews/
├── daily.py                   ← 改：从 fetcher REGISTRY 循环 + 加 summarizer
├── Makefile
├── README.md                  ← 改：v2 文档 + 如何加新源
├── SPEC.md                    ← 本文档
├── config.yaml                ← 🆕 关键词权重/源开关/LLM provider 等
├── .env.example
├── .gitignore
├── requirements.txt
│
├── .github/
│   └── workflows/
│       └── daily.yml          ← 🆕 GitHub Actions 凌晨 7:00 全自动
│
├── fetchers/
│   ├── base.py                ← 🆕 BaseFetcher 抽象类 + REGISTRY
│   ├── arxiv_fetcher.py       ← 改：继承 BaseFetcher
│   ├── hf_fetcher.py          ← 改：继承 BaseFetcher
│   ├── github_fetcher.py      ← 改：继承 BaseFetcher
│   ├── hn_fetcher.py          ← 改：继承 BaseFetcher
│   ├── nowcoder_fetcher.py    ← 🆕 牛客面经（RSSHub）
│   ├── china_ai_fetcher.py    ← 🆕 国内 AI 公司动态
│   └── coding_tool_fetcher.py ← 🆕 AI Coding 工具采用信号
│
├── pipeline/
│   ├── schema.py              ← 改：加 category 字段
│   ├── config.py              ← 🆕 YAML 配置加载器
│   ├── scorer.py              ← 改：从 config 读权重 + category 分组
│   ├── llm.py                 ← 改：重构为 BaseLLM provider 抽象
│   ├── summarizer.py          ← 🆕 顶部综合 summary 生成
│   ├── aggregator.py          ← 🆕 周/月报 stub 接口（v2 留空，v3 实现）
│   └── renderer.py            ← 改：双栏 context + 用 partials
│
├── templates/
│   ├── base.html.j2           ← 🆕 主框架（masthead + footer）
│   ├── daily.html.j2          ← 改：继承 base + 引入 partials
│   ├── weekly.html.j2         ← 🆕 空文件（v3 用）
│   ├── monthly.html.j2        ← 🆕 空文件（v3 用）
│   └── partials/              ← 🆕 卡片 partial 模板
│       ├── card_paper.html.j2     ← arXiv + HF 复用
│       ├── card_repo.html.j2      ← GitHub
│       ├── card_hn.html.j2        ← HackerNews
│       ├── card_job.html.j2       ← 牛客面经
│       ├── card_company.html.j2   ← 国内 AI 公司动态
│       └── summary_block.html.j2  ← 顶部 summary 块
│
├── docs/                      ← GitHub Pages 根目录（用户可访问）
│   ├── index.html             ← 今日最新
│   ├── YYYY-MM-DD.html        ← 每日历史归档
│   ├── archive.html           ← 🆕 历史索引页
│   ├── weekly/                ← 🆕 v3 周报输出位置（v2 空目录）
│   │   └── .gitkeep
│   └── monthly/               ← 🆕 v3 月报输出位置（v2 空目录）
│       └── .gitkeep
│
└── data/
    ├── processed/             ← 每日 Item 全量 JSON
    │   └── YYYY-MM-DD.json
    ├── summaries/             ← 🆕 每日 LLM summary JSON
    │   └── YYYY-MM-DD.json
    └── aggregates/            ← 🆕 v3 周/月聚合数据（v2 空目录）
        ├── weekly/
        │   └── .gitkeep
        └── monthly/
            └── .gitkeep
```

---

## 16. 简历叙事（升级版）

> **GetNews · AI 每日早报**（个人项目，2026.05-至今）
> - 设计并实现**双栏 AI 资讯 + 中国求职情报聚合 pipeline**，每日聚合 7 个数据源（arXiv / HuggingFace / GitHub / HackerNews / 牛客 / 国内 AI 公司动态 / AI Coding 工具采用信号）
> - **LLM 多任务编排**：DeepSeek 同时承担英文翻译、中文摘要、跨源综合判断三种任务，每日输出 headline + 双栏要点
> - **可扩展架构**：Fetcher 注册表模式 + YAML 配置外置 + Jinja2 模板 partial 化，新增源/调权重/换主题零代码改动
> - **个性化打分模型**按学习/求职双 category 分别打分，针对中国 AI 招聘市场调优关键词权重
> - **结构化数据归档**（daily/weekly/monthly 三层）为后续周报、月报跨天分析奠定基础
> - **GitHub Actions 24/7 全自动 pipeline**，每天凌晨自动更新，零人工干预
> - 公开 Dashboard：`https://你的名字.github.io/getnews`
> - 技术栈：Python · DeepSeek API · RSSHub · Jinja2 · GitHub Actions · GitHub Pages

---

## 17. v2 不做（v3 再考虑）

- ⏰ ~~更细粒度定时（每小时 / 每 4 小时）~~ —— 一天一次足够
- 📦 ~~Product Hunt / 国际 AI 公司 changelog~~ —— 求职聚焦中国市场，国际通过 HN 间接覆盖
- 📅 ~~周报 / 月报 HTML 输出~~ —— **数据归档 v2 已建好，HTML 渲染 v3 实现**
- ⭐ ~~网页里的收藏按钮~~ —— 静态 HTML 不带后端难做，需要时改方案
- 🔔 ~~高分内容桌面通知~~ —— 增加复杂度，用 Chrome 书签足矣
- 🧬 ~~同主题论文 cluster 聚合~~ —— 单天数据量不够支撑 cluster
- 🎙️ ~~播客 / 视频信息源~~ —— 视频字幕处理复杂度高
- 🤖 ~~自托管 RSSHub~~ —— 等公共实例频繁挂再升级
- 🏢 ~~Boss直聘 / 拉勾爬取~~ —— 反爬太强，吃力不讨好

**注**：v2 已**把"关键词权重 YAML 化"和"归档目录结构"做掉**——前者支持调权重不动代码，后者为周报月报留好接口。

---

## 18. 我需要你做的事（v2 实施前提）

按时间顺序：

| 步骤 | 你做什么 | 我做什么 |
|---|---|---|
| 1 | 读完本 SPEC，确认或反馈 | 等你确认 |
| 2 | 在 GitHub 建仓库 `getnews`（公开，不初始化） | 把告诉我的 URL 写入 git remote |
| 3 | 在 GitHub 仓库 → Settings → Secrets → 添加 `DEEPSEEK_API_KEY`（点几下） | 提供操作截图指引 |
| 4 | 在 GitHub 仓库 → Settings → Pages → Source = main 分支 / `/docs` 文件夹 | 同上 |
| 5 | 等你说"可以开始" | 按改造清单实施 v2 代码（~7 小时） |
| 6 | 等待第一次 Actions 自动跑（凌晨 7 点）/ 手动触发一次 | 监控日志，看到结果给你看 |
| 7 | 在 Chrome 加 https://你的名字.github.io/getnews 到书签 | 完成 |

---

## 19. 现在请你确认

读完后，针对下面 8 条回我：

1. **定位对吗？** 双栏并重的中国 AI 求职 + 学习 dashboard
2. **数据源对吗？** 学习 4 源（arXiv / HF / GitHub / HN）+ 求职 3 源（牛客 / 国内 AI 公司 / AI Coding 信号）
3. **打分权重对吗？** 求职线权重表（第 6 节）有想加 / 改 / 删的？
4. **总 Summary 形式对吗？** 一句话 headline + 双栏 3+3 要点
5. **触发方式对吗？** GitHub Actions 凌晨 7:00 全自动，你不开机也照跑
6. **布局对吗？** 第 9 节 6 个区块（已删 STAT BAR），分块说明都清楚？
7. **归档与可扩展性架构对吗？** 第 12 节归档目录三层 + 第 13 节 Fetcher 注册 / YAML config / 模板 partial 化设计
8. **简历叙事对吗？** 第 16 节那段话是否捕捉到了项目重点？

任何一条不对都告诉我，确认无误的部分就说"OK"。
