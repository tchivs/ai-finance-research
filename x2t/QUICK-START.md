# x2t 快速概览

> 财经博主观点追踪 · AI 立场标注 · 信源战绩结算 · Flip Radar · Wilson/FDR 统计校正
> 源码: `/root/source/tmp/x2t/`
> 原始仓库: <https://github.com/actionow-ai/x2t>

---

## 一句话定位

`x2t` 把 X/Reddit/RSS/新闻里的财经博主内容转成 ticker 级 `bullish/bearish/neutral` 立场，并把这些立场按价格表现结算，给每个信源建立可审计战绩。

它最值得学习的不是抓取社媒，而是“信源可信度层”：每个观点都要落库、翻译、抽标的、判立场、检测转向、推送告警，并在 5 个交易日后和同期 SPY 对比结算。这样系统不只是相信观点，而是长期评估谁说得准。

---

## 最高价值借鉴点

| 借鉴点 | 代码位置 | 可复用价值 |
|---|---|---|
| 信源/帖子/标的 schema | `prisma/schema.prisma` | 把内容、观点、立场、价格、推送、任务观测都建模 |
| 幂等抓取 | `src/lib/ingest.ts` | `(influencerId, platformPostId)` 去重，不重复推送 |
| AI 立场标注 | `src/lib/agent.ts` | 原文语种分析、ticker 抽取、外部数据佐证、schema 校验 |
| 信念回灌 | `belief` 字段与 `beliefClauseFromStored()` | 历史校准反馈给下一次分析 prompt |
| Flip 物化表 | `Flip` model, `detectFlips()` | 立场转向作为一等事件，首页/RSS/告警直接索引读 |
| 战绩结算 | `src/lib/stance.ts` | 交易日结算、SPY 对照、flip 截断、去伪重复样本 |
| 统计校正 | `wilson95`, `binomTestGreater`, `benjaminiHochberg` | 防止小样本和多重比较制造假高手 |
| 多 Provider LLM | `src/lib/llm/` | 支持 OpenAI/Anthropic 兼容接口和 fallback |
| 生产硬化 | `ssrf.ts`, `ratelimit.ts`, `JobRun` | SSRF 防护、限流、后台任务可观测 |

---

## 核心数据流

```text
RSSHub / RSS / Manual sources
    ↓
Influencer + Post 幂等入库
    ↓
AI 分析原文: ticker, stance, rationale, confidence
    ↓
PostTicker + PostAnalysis 落库
    ↓
detectFlips 物化立场转向
    ↓
notifyFlip / evaluateAlerts 推送
    ↓
PriceDaily 补历史价格
    ↓
settleCalls 计算是否跑赢同期 SPY
    ↓
Leaderboard / Equity Curve / Calibration
```

---

## 核心表

| 表 | 作用 |
|---|---|
| `Influencer` | 信源、平台、抓取配置、历史 belief |
| `Post` | 原文、翻译、抓取时间、分析状态、重试状态 |
| `PostAnalysis` | 帖子总体立场、摘要、keyPoints、confidence、model |
| `Security` | 标的基础实体 |
| `PostTicker` | 帖子对某个 ticker 的立场和理由 |
| `PriceDaily` | 标的每日收盘价，用于结算观点 |
| `Flip` | 立场转向物化表 |
| `AlertRule` | 用户可组合告警条件 |
| `Delivery` | 推送去重和发送记录 |
| `JobRun` | 后台任务运行观测 |

---

## x2t 的统计纪律

| 纪律 | 目的 |
|---|---|
| 入场取发帖后第一根交易日收盘 | 避免偷看发帖当天已知价格 |
| 同向短间隔重复 call 合并 | 避免一个观点刷成多个样本 |
| 反向 flip 提前截断前一持仓 | 观点变了就不再按满 horizon 结算 |
| 看空对照做空 SPY | 空头评价保持市场中性 |
| Wilson 95% 区间 | 小样本胜率不虚高 |
| Benjamini-Hochberg FDR | 多个博主同时比较时减少幸运儿假阳性 |
| Brier score | 评估 AI confidence 是否校准 |

---

## 和现有项目的互补

| 项目 | 已有强项 | x2t 补的空白 |
|---|---|---|
| `DeepEar` | 事件信号评分和逻辑演化 | 信源长期战绩和观点结算 |
| `trade-skills` | 个人研究日志和图表 | 外部博主观点自动追踪 |
| `daily_stock_analysis` | 自动分析和推送 | 推送背后的信源可信度统计 |
| `Vibe-Trading` | 交易和回测 | 非交易信号的战绩审计 |

---

## 最适合迁移的设计

1. **Source Ledger**: 给每个新闻源/博主/研报机构建立观点账本。
2. **PostTicker Schema**: 每条内容可以影响多个 ticker，每个 ticker 有独立 stance/rationale。
3. **Flip Event**: 立场转向作为单独事件流，不要每次窗口函数现算。
4. **Settlement Engine**: 每条观点必须能在未来窗口结算。
5. **Calibration Panel**: 不只看胜率，还看置信度是否校准。
6. **JobRun**: 后台抓取/分析/摘要任务每轮落库，避免只靠日志。
