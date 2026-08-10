# x2t 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/actionow-ai/x2t.git
> 分析基线：
> - `x2t`：commit `f90487430f8d93fa245f81ac7b37a2014301e3b5`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/x2t`
<!-- source-sync:end -->


> 从财经噪声到可结算信号 · 信源战绩 · 立场账本 · 统计防幻觉
> 源码: `src/x2t/`
> 原始仓库: <https://github.com/actionow-ai/x2t>

---

## 1. 项目架构

`x2t` 是 Next.js 15 + Prisma + PostgreSQL 的自托管应用。一个容器同时跑 Web 和后台 worker，核心脚本在 `scripts/`：

| 脚本 | 作用 |
|---|---|
| `poll.ts` | 抓取外部源 |
| `analyze.ts` | 分析 pending/failed 帖子 |
| `worker.ts` | 组合后台循环 |
| `digest.ts` | 每日摘要 |
| `seed.ts` | 初始信源 |
| `test-flip.ts`, `test-push.ts` | 关键功能冒烟 |

领域代码集中在 `src/lib/`，其中 `ingest.ts`, `agent.ts`, `stance.ts`, `stats.ts`, `prices.ts`, `alerts.ts`, `push.ts` 是核心。

---

## 2. 数据模型的价值

`prisma/schema.prisma` 一次性把“内容 -> 分析 -> 立场 -> 结算 -> 推送 -> 观测”完整建模。

### 2.1 内容核心

| Model | 关键字段 | 设计含义 |
|---|---|---|
| `Influencer` | `handle`, `platform`, `sourceConfig`, `belief` | 信源不仅是账号，还带抓取配置和历史校准信念 |
| `Post` | `contentText`, `contentZh`, `contentEn`, `analysisStatus` | 原文和双语版本都保存，分析状态可重试 |
| `PostAnalysis` | `overallStance`, `confidence`, `summary`, `keyPoints` | 帖子级总体分析 |
| `Security` | `symbol`, `name`, `exchange`, `sector` | 标的主数据 |
| `PostTicker` | `symbol`, `stance`, `rationale` | ticker 级立场，解决“一帖多票”问题 |

### 2.2 结算与事件

| Model | 作用 |
|---|---|
| `PriceDaily` | 观点结算所需的日线价格 |
| `Flip` | 物化立场转向，避免每次请求全量窗口扫描 |
| `AlertRule` | 用户条件组合，如多头数、空头数、是否 flip |
| `Delivery` | 推送去重，避免同一 post/sub/channel 重复发送 |
| `JobRun` | 后台任务运行记录，支持 health/admin 问“上次成功多久前” |

这个 schema 可以直接启发当前项目：不要只存“报告”，还要存“谁说了什么、对哪只票、什么方向、后来结果如何”。

---

## 3. 抓取: ingest.ts

`storePost()` 用 Prisma `upsert` 保证 `(influencerId, platformPostId)` 幂等。`ingestInfluencer()` 先批量查本批已存在 ID，避免每帖一次读，再只对新帖写入并触发推送。

关键设计：

| 设计 | 好处 |
|---|---|
| 单信源失败只写 `fetchError` 并抛出 | 不影响其他信源 |
| `optedOut` 信源不抓取 | 尊重移除请求 |
| `INGEST_CONCURRENCY` 限制小并发 | 防止 100 源串行超周期，也防止内存/连接过载 |
| 新帖才 notify | 避免重复推送 |

迁移到金融新闻/研报源时，同样应以 `source_id + external_id` 作为去重键。

---

## 4. AI 分析: agent.ts

`analyzePost()` 是 AI 信号生成的核心。流程如下：

```text
读取 Post + Influencer
    ↓
extractCashtags 生成候选 ticker
    ↓
getExternalDataCached 拉行情/新闻/事件等佐证
    ↓
LLM 输出 JSON: lang, overallStance, confidence, summary, keyPoints, tickers
    ↓
zod schema 校验，失败重试一次
    ↓
补中文/英文翻译
    ↓
事务写入 Security, PostTicker, PostAnalysis, Post
    ↓
detectFlips + Flip upsert + 推送/告警
```

Prompt 里有大量“低置信度规则”，非常值得迁移：

| 场景 | 处理 |
|---|---|
| 纯喊单/情绪宣泄 | neutral 或低 confidence |
| sarcasm/段子 | 不按字面取立场 |
| 仅转发新闻无观点 | neutral |
| penny-stock/meme 炫耀 | 不判高置信 bullish |
| 无外部数据 | 标注无佐证，不臆造 |
| Fed/AI/Q3 等普通词 | 不污染 Security 表 |

这比普通情绪分类更接近真实金融内容治理。

---

## 5. 立场与图谱: stance.ts

### 5.1 Stock Consensus

`getStockConsensus()` 对某只票按“每个博主最新一条立场”聚合，窗口外不计入当前共识。这个设计避免一个高频博主刷屏主导共识。

### 5.2 Graph Data

`getGraphData()` 对每个 `(influencer, symbol)` 取最新立场作为图谱边，并用窗口天数、最大边数、进程 memo 控制查询成本。

### 5.3 Flip Materialization

`detectFlips()` 和 `backfillFlips()` 将“博主对某票的立场转向”写入 `Flip` 表。这样首页、RSS、告警、图谱都可以索引读取，而不是每次实时窗口函数扫描。

迁移原则：只要某个派生事件会被多处读取，就应该物化并保证幂等。

---

## 6. 战绩结算: settleCalls

`settleCalls()` 是 x2t 的方法论核心。它把帖子立场结算为“是否跑赢同期 SPY”。几个细节非常关键：

| 细节 | 解决的问题 |
|---|---|
| 入场取严格晚于发帖时间戳的第一根日线 | 避免偷看当天收盘价 |
| 发帖到入场超过 `MAX_ENTRY_GAP_DAYS` 剔除 | 避免价格窗口左删失造成假样本 |
| 同标的同方向入场间隔小于 horizon 合并 | 避免重复喊单刷样本 |
| 下一个保留 call 反向时提前出场 | 观点 flip 后不能继续按旧方向结算 |
| 看多对照 SPY，多空对照做空 SPY | 评价相对市场 alpha |
| `excess > 0` 才算 beat | 不是绝对涨跌，而是跑赢市场 |

这套规则可以迁移到新闻源、研报机构、Agent 策略建议的长期评估中。

---

## 7. 统计校正

x2t 没有用裸胜率排名，而是使用三类统计工具。

| 工具 | 位置 | 目的 |
|---|---|---|
| Wilson 95% CI | `wilson95()` | 小样本比例的稳健置信区间 |
| 精确二项检验 | `binomTestGreater()` | 检查是否显著强于 50% |
| BH-FDR | `benjaminiHochberg()` | 多博主同时比较时校正假阳性 |

排行榜按 Wilson 下界排序，而不是裸 `beatRate`。这点很重要：10 次对 8 次的 80% 不应该压过 120 次对 78 次的 65%。

---

## 8. 对当前项目的迁移设计

### 8.1 SourceScore 层

建议当前项目新增信源表现表：

```text
source_id
source_type: influencer | news | report_org | agent
symbol
stance
confidence
created_at
entry_price_date
exit_price_date
aligned_return
benchmark_return
excess_return
beat
```

### 8.2 信源使用策略

Agent 生成报告时，不应平等对待所有来源。可以把 x2t 的统计结果作为 source weight：

```text
source_weight = f(wilson_ci_low, samples, recency_rate, brier_score)
```

### 8.3 观点回灌

x2t 的 `belief` 字段启发了“结算 -> 反思 -> 下次 prompt 校准”。当前项目可以为每个数据源或 Agent 维护：

```text
过去 90 天该源在半导体题材上高估，confidence 应保守
过去 30 天该源对政策事件反应快，但基本面推演弱
```

---

## 9. 风险和边界

- 信源战绩不等于未来可靠，只是校准证据。
- 价格结算依赖 `PriceDaily` 覆盖，拉不到价的样本会被排除，有幸存者偏差。
- SPY 适合美股基准，A 股需要换成沪深300/中证全指/行业指数。
- 对 A 股涨跌停、停牌、T+1 等约束，x2t 原规则需要本地化。
- 博主观点可能是交易、娱乐或品牌表达，不一定是可执行信号。
