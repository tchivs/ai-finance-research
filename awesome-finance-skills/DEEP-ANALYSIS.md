# Awesome Finance Skills 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/RKiding/Awesome-finance-skills.git
> 分析基线：
> - `Awesome-finance-skills`：commit `853f09b4d0baae747759ed31e21ed5c5b2316a5f`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Awesome-finance-skills`
<!-- source-sync:end -->


> plug-and-play finance skills · AlphaEar utility layer · SQLite memory · RAG/search/predict/report toolkit
> 源码: `src/Awesome-finance-skills/`
> 原始仓库: <https://github.com/RKiding/Awesome-finance-skills>

## 1. 架构定位

Awesome Finance Skills 是一套金融 Agent 能力包，而不是完整产品。它的核心价值在于把金融研究中的常见能力拆成多个低耦合 skill：数据拉取、搜索、情绪、预测、可视化、报告、在线信号读取。

这种架构和“单一大 Agent”相反：

```text
Single big finance agent
    = one prompt + many implicit responsibilities

Awesome Finance Skills
    = many small skills
    = each skill has trigger description + scripts + references + tests
    = Agent loads the smallest useful capability
```

对 HermesAlpha 来说，这提供了一个可迁移的能力封装模型；对 ashare-audit 来说，每个 skill 都天然形成一个审计边界。

## 2. Skill 分层

### 数据层

`alphaear-stock` 提供股票列表搜索、历史价格、实时行情和基本面相关能力。

关键实现：

- 主路径用 `akshare` 获取 A 股/港股列表和历史行情。
- 美股路径用 `yfinance`。
- 降级路径用 `EastMoneyDirect` 直接请求东方财富 HTTP 接口。
- 本地 SQLite 缓存 `stock_list` 和 `stock_prices`。
- 遇到代理错误时临时清除 proxy 环境变量再重试。

这类设计适合做 Agent 数据工具：先保证“能拿到”，再逐步补齐一致性和字段审计。

### 搜索层

`alphaear-search` 包含 Web 搜索和本地 RAG。核心是 `HybridSearcher`：

```text
data records
    -> concatenate text fields
    -> jieba tokenize
    -> BM25 index
    -> optional SentenceTransformer embedding
    -> BM25 rank + vector rank
    -> Reciprocal Rank Fusion
    -> top_n results with scores
```

它的细节值得借鉴：

- 默认只构建 BM25，向量模型延迟加载。
- 中文分词使用 `jieba`，避免直接按空格分词。
- 向量检索失败时 fallback 到 BM25。
- `LocalNewsSearch` 从 SQLite 的 `daily_news` 加载近 30 天新闻。
- `InMemoryRAG` 支持报告生成阶段跨章节检索。

### 情绪层

`alphaear-sentiment` 明确把 LLM 逻辑移出脚本：

- 脚本只负责 BERT 自动情绪分析。
- 如果要 LLM 判断，由调用 Agent 按 prompt 完成。
- Agent 可调用 `update_single_news_sentiment` 把人工/LLM 分析结果落库。

这是一个清晰分工：BERT 适合批量粗筛，LLM 适合高价值信号解释。

### 预测层

`alphaear-predictor` 用 `ForecastUtils.get_base_forecast` 做基础预测：

```text
ticker
    -> StockTools.get_stock_price
    -> ensure enough lookback data
    -> collect news signal titles/summaries
    -> KronosPredictorUtility.get_base_forecast(df, news_text)
    -> return List[KLinePoint]
    -> Agent applies qualitative adjustment by prompt
```

关键点不是 Kronos 本身，而是 base forecast 与 adjusted forecast 分离。

### 报告层

`alphaear-reporter` 的 `ReportUtils` 不直接大包大揽写研报，而是提供辅助能力：

- `build_bibliography`：从 signal sources 构造稳定参考文献。
- `_make_cite_key`：URL/title/source 生成 sha1 短引用 key。
- `render_references_section`：生成 Markdown 参考文献。
- `sanitize_json_chart_blocks`：修复未闭合的 chart fenced block。
- `build_structured_report`：从 Markdown 提取 title、sections、summary bullets。

这把报告生成拆成“Agent 写作”和“工具修边/结构化/引用管理”。

### 可视化层

`alphaear-logic-visualizer` 主要使用 pyecharts：

- K 线 + 成交量 grid。
- 简单预测线。
- Kronos base forecast 和 LLM adjusted forecast 两套预测 K 线。
- ground truth 对照线。
- 情绪趋势、loss 曲线、图谱等。

它的设计暗含一个好模式：研报中的图表应来自结构化数据对象，而不是 Agent 直接自由生成图表描述。

### 外部信号层

`alphaear-deepear-lite` 是最小远端信号 client：

```text
GET https://deepear.vercel.app/latest.json
    -> generated_at
    -> signals[]
    -> title/summary/sentiment/confidence/intensity/reasoning/sources
    -> Markdown report
```

这个 skill 的意义是把外部信号源包装成统一 Markdown/结构化摘要，供上层 Agent 继续分析。

## 3. SQLite 数据模型

`DatabaseManager` 初始化了一个轻量研究库：

| 表 | 用途 |
|---|---|
| `daily_news` | 新闻、来源、发布时间、情绪、分析、meta |
| `search_cache` | 原始搜索缓存，按 query_hash 存 JSON |
| `search_detail` | 展开后的搜索结果，便于引用和 RAG |
| `stock_prices` | ticker/date 级 OHLCV 缓存 |
| `stock_list` | 股票代码/名称检索 |
| `signals` | ISQ 框架下的结构化投资信号 |

这套 schema 不复杂，但足够支撑 Agent 研究中的三个需求：避免重复搜索、可追溯引用、积累信号。

## 4. ISQ 信号结构

`InvestmentSignal` 模型包含：

- `signal_id/title/summary/reasoning`
- `transmission_chain`
- `sentiment_score/confidence/intensity/expectation_gap/timeliness`
- `expected_horizon/price_in_status`
- `impact_tickers/industry_tags`
- `sources`

这比“新闻摘要 + 看多看空”更适合作为审计对象。ashare-audit 可围绕这些字段检查：是否有来源、是否有传导链、信心分是否和证据匹配、预期差是否凭空生成。

## 5. 对 HermesAlpha 的迁移方案

建议不是直接搬整个仓库，而是迁移它的拆分方式：

```text
HermesAlpha skills
    market-data
        stock search / price / fundamentals
    finance-search
        web search / local RAG / citation cache
    sentiment
        fast classifier / LLM adjudication writer
    forecast
        base model forecast / agent adjustment
    report
        cluster / section writer / bibliography / charts
    external-signals
        DeepEar / x2t / watchlist / broker signals adapters
```

每个能力都可以独立测试，也可以单独暴露给 OpenClaw/OpenCode。

## 6. 对 ashare-audit 的审计模型

可按 skill 类型建立检查项：

| Skill 类型 | 审计点 |
|---|---|
| 数据 skill | 数据源、字段映射、缓存时间、fallback 是否改变口径 |
| 搜索 skill | query、来源、TTL、去重、引用是否可回溯 |
| 情绪 skill | 模型版本、分数阈值、批处理失败、LLM 手动覆盖理由 |
| 预测 skill | base forecast、adjusted forecast、新闻输入、权重文件 |
| 报告 skill | 引用完整性、章节结构、chart JSON 合法性、证据覆盖 |
| 外部信号 skill | 拉取时间、远端 schema、信号缺字段、来源链接 |

## 7. 工程质量观察

优点：

- skill 边界清晰，便于安装和选择。
- 大量能力都有脚本而不是纯 prompt。
- 本地 SQLite 让缓存、信号、引用可落地。
- 搜索和预测都保留了 fallback 思路。

弱点：

- 各 skill 成熟度不均，有的实现完整，有的只是 prompt glue。
- 模型依赖较重，不适合默认安装全部。
- 多处外部数据源没有统一 source health 抽象。
- `SKILL.md` 与实际脚本路径存在个别命名/引用漂移，需要安装后验证。

## 8. 最关键的可复用结论

Awesome Finance Skills 的精华不是某个具体金融模型，而是金融 Agent 能力的插件化边界：

```text
Tool = deterministic work
Agent = judgment and synthesis
SQLite = memory and audit trail
SKILL.md = routing contract
Prompt references = repeatable reasoning protocol
```

如果 HermesAlpha 要长期演进，这种边界比“一个越来越大的投研 Agent”更容易维护，也更容易被 ashare-audit 审计。
