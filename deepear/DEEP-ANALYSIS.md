# DeepEar 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/HKUSTDial/DeepEar.git
> 分析基线：
> - `DeepEar`：commit `579b7d418554f5da0a708e940b8df4d1ad035067`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/DeepEar`
<!-- source-sync:end -->


> 公共舆情到投资信号 · ISQ 质量评分 · checkpoint 化研究流程 · 信号演化追踪
> 源码: `src/DeepEar/`
> 原始仓库: <https://github.com/HKUSTDial/DeepEar>

---

## 1. 总体架构

DeepEar 的运行中心是 `src/main_flow.py` 中的 `SignalFluxWorkflow`。它在初始化时创建四类 Agent 和辅助工具：

| 组件 | 作用 |
|---|---|
| `IntentAgent` | 分析用户 query，生成关键词和搜索词 |
| `TrendAgent` | 从新闻/社媒/科技源抓热点，计算情绪 |
| `FinAgent` | 把信号转成结构化投资逻辑和 ISQ 分数 |
| `ReportAgent` | 生成 Markdown/HTML 报告 |
| `SearchTools` | 主动搜索补充特定事件的信息 |
| `DatabaseManager` | 保存新闻、信号、分析结果 |
| `CheckpointManager` | 保存 run 中间态，支持恢复 |

工作流不是一次性脚本，而是有运行 ID、状态文件、中间 JSON、最终报告的可恢复流程。

---

## 2. 主流程拆解

### 2.1 意图分析与主动搜索

当用户传入 `query` 时，系统先调用 `IntentAgent.run(query)`，得到 `search_queries`、`is_specific_event` 等结构化意图。如果是特定事件，会主动搜索前两个查询词，每个最多取 5 条结果，并标准化成 news-like signal。

这解决了单纯“从固定新闻源扫热点”的盲区：用户问的是具体事件时，系统会主动补上下文，而不是只依赖当天库里的新闻。

### 2.2 多源抓取和成功源记录

`FINANCIAL_SOURCES`, `SOCIAL_SOURCES`, `TECH_SOURCES` 被合成 `ALL_SOURCES`。每个源独立 try/catch，失败只记录 warning，不拖垮整个 run。

checkpoint 中保存：

```text
trend_sources.json
  actual_sources
  successful_sources
  wide
```

这适合迁移到任何多源采集系统：下游报告不仅要知道“抓到了什么”，还要知道“哪些源失败了”。

### 2.3 LLM Filter Gate

`_llm_filter_signals()` 会把新闻列表压成 `[ID] title sentiment`，让 LLM 输出：

```text
has_valid_signals
selected_ids
reason
```

如果 `has_valid_signals=false`，系统直接返回空列表，避免对无效新闻继续做昂贵 FinAgent 分析。这个 gate 比“按情绪绝对值排序”更贴合金融场景，因为高情绪新闻未必是有效投资信号。

---

## 3. InvestmentSignal Schema

`src/schema/models.py` 的 `InvestmentSignal` 是项目的核心数据契约。

| 字段 | 含义 |
|---|---|
| `signal_id` | 唯一信号 ID |
| `title`, `summary`, `reasoning` | 标题、摘要、详细推演 |
| `transmission_chain` | 产业链传导节点列表 |
| `sentiment_score` | 看多/看空方向 |
| `confidence` | 确定性 |
| `intensity` | 影响强度 |
| `expectation_gap` | 预期差 |
| `timeliness` | 时效性 |
| `expected_horizon` | 反应时窗 |
| `price_in_status` | 市场消化程度 |
| `impact_tickers` | 受影响标的和权重 |
| `industry_tags` | 行业标签 |
| `sources` | 来源标题、URL、source_name |

这套 schema 值得迁移到当前项目，因为它把“投资逻辑”拆成了可追踪字段，不再只是报告段落。

---

## 4. ISQ Template 系统

`src/schema/isq_template.py` 把信号质量评分做成模板。默认模板包含五个维度，并提供评分指导和综合分算法。

### 4.1 维度设计

| 维度 | 权重 | 作用 |
|---|---:|---|
| `confidence` | 0.35 | 信息来源和逻辑可信度 |
| `intensity/5` | 0.30 | 影响量级 |
| `expectation_gap` | 0.20 | Alpha 来源和市场认知差 |
| `timeliness` | 0.15 | 信号窗口紧迫度 |

`sentiment` 不进入综合质量分，这一点很重要：方向和质量分开。一个看空信号也可以是高质量信号。

### 4.2 Template Manager

`ISQTemplateManager` 支持从 `config/*.json` 加载模板。迁移时可以为不同策略建立不同模板：

| 场景 | 模板差异 |
|---|---|
| 短线题材 | 提高 `timeliness` 和 `intensity` 权重 |
| 基本面研究 | 提高 `confidence` 和 `transmission` 权重 |
| 风险预警 | 看空方向与冲击强度并重 |
| 宏观事件 | 加入 `policy_uncertainty` 或 `cross_asset_impact` |

---

## 5. Checkpoint 与 Resume

DeepEar 的 checkpoint 颗粒度很实用：

| 文件 | 内容 |
|---|---|
| `state.json` | run_id、参数、状态、时间 |
| `intent.json` | query 意图分析结果 |
| `trend_sources.json` | 实际源和成功源 |
| `search_signals.json` | 主动搜索结果 |
| `raw_news_meta.json` | DB 新闻和搜索信号数量 |
| `high_value_signals.json` | 筛选后的信号概要 |
| `analyzed_signals.json` | FinAgent 输出的结构化信号 |
| `report.md` | 报告草稿/最终内容 |
| `report_structured.json` | 如果 ReportAgent 输出结构化对象则保存 |

恢复模式分两类：

| 模式 | 行为 |
|---|---|
| `resume_from=report` | 直接复用 `report.md`，重新导出报告 |
| `resume_from=analysis` | 复用 `analyzed_signals.json`，重新生成报告 |

迁移建议：所有长 Agent 流程都应该按阶段落 checkpoint，尤其是新闻抓取、信号筛选、LLM 分析、报告生成这四段。

---

## 6. update_run: 信号演化追踪

`SignalFluxWorkflow.update_run()` 是 DeepEar 最值得吸收的功能之一。它不是重新跑一遍报告，而是基于旧 run 做更新：

```text
读取旧 analyzed_signals
    ↓
刷新相关 ticker 行情
    ↓
FinAgent.track_signal(sig)
    ↓
生成 evolved_signals
    ↓
ReportAgent 生成演变对比报告
```

这可迁移为当前项目的“信号生命周期”机制：

| 状态 | 含义 |
|---|---|
| `strengthened` | 新数据强化原逻辑 |
| `weakened` | 逻辑仍在但强度下降 |
| `falsified` | 关键假设被证伪 |
| `priced_in` | 市场已经充分反映 |
| `new_branch` | 出现新的传导路径 |

当前项目如果只生成一次性报告，会缺少“当初的判断后来怎样了”。DeepEar 的 update-run 正好补这一层。

---

## 7. 并发与数据库写入边界

`main_flow.py` 支持 `--concurrency`。并发模式下，线程池只做单信号分析，结果回到主线程后再写 DB：

```text
ThreadPoolExecutor analyze_single_signal
    ↓
future.result()
    ↓
main thread self.db.save_signal()
```

源码注释明确提到 SQLite 连接线程安全问题，最终选择“分析并发，写入串行”。这是适合迁移的边界：LLM/网络可并发，状态写入要集中。

---

## 8. 对 HermesAlpha / ashare-audit 的启发

| 当前需求 | 可借鉴设计 |
|---|---|
| 热点到标的映射 | `IntentAgent + SearchTools + FinAgent` |
| 信号质量评估 | ISQ template 和 `InvestmentSignal` schema |
| 报告可恢复 | `CheckpointManager` 阶段落盘 |
| 追踪旧结论 | `update_run` 和 `track_signal` |
| 降低 LLM 成本 | reasoning/tool 双模型路由 |
| 无效新闻过滤 | `FilterResult.has_valid_signals` gate |

最优迁移顺序：

1. 先引入 `InvestmentSignal` schema。
2. 再引入 ISQ 评分模板。
3. 再给现有报告流程加 checkpoint。
4. 最后实现 update-run 演化追踪。
