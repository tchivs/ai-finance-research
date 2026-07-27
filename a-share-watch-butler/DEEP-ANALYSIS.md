# a-share-watch-butler 深度分析

> 定时 Agent 链路 · 三层输出契约 · 预测-验证-再校准闭环 · 可审计盯盘系统
> 源码: `/root/source/tmp/a-share-watch-butler/`
> 原始仓库: <https://github.com/nexaforgelab/a-share-watch-butler>

---

## 1. 项目形态

这个项目不是单纯的“股票推送脚本”，而是一个生产化盯盘 Skill。核心文件如下：

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 触发条件、边界、Agent 角色和 cron 示例 |
| `config.yaml` | 任务、监控池、候选池、阈值、权重、数据源、推送渠道 |
| `src/scheduler.py` | CLI 与常驻调度入口 |
| `src/orchestrator.py` | 工作流选择、并行调度、降级、卡片生成、run report |
| `src/models.py` | `AgentResult`, `LayeredCard`, `DataQualityIssue`, `RunContext` |
| `src/data/store.py` | SQLite 状态、预测、命中率、权重版本、归档 |
| `src/data/sources.py` | 数据源聚合、兜底、质量问题记录 |
| `src/backtest/backtest.py` | 轻量因子排序回测 |

项目最值得吸收的是“盯盘作为状态机和审计链”，而不是某个单独指标。

---

## 2. 三层输出契约

`src/models.py` 定义了系统最核心的数据结构：

```text
AgentResult
  agent
  objective
  ai_interpretation
  data_quality
  metrics.duration_ms

LayeredCard
  title/task/generated_at
  objective
  ai_interpretation
  data_quality
  sections
  disclaimer
```

这个契约迫使每个 Agent 回答三个问题：

1. 我拿到了什么客观数据？
2. 我如何解释这些数据？
3. 哪些数据失败、冲突或需要人工确认？

对金融系统来说，这比“把一段大模型总结发出去”可靠得多，因为报告消费者能看见证据层和解释层的边界。

---

## 3. Orchestrator 的链路设计

`Orchestrator.run()` 按 task 分派到五条链路：`premarket`、`intraday`、`postmarket`、`weekend`、`query`。

### 3.1 盘前链路

盘前同时运行 `MacroScout`、`CapitalFlow`、`TechAnalyst`，再将技术结果传给 `PoolScorer`。这是合理的 DAG：宏观、资金、技术互不依赖，可以并行；候选池排序依赖这些上下文，放在后面。

迁移建议：当前项目的盘前/盘后任务也应该显式声明哪些节点可并行，哪些节点必须等前置结果，避免 Agent 自己临时排序。

### 3.2 盘后链路

盘后由 `ReviewAttributor` 读取最近盘前预测，计算实际收益、命中率、因子有效性，再按样本数和学习率决定是否生成新权重版本。

关键点是它不是“复盘文字”，而是写入数据库的反馈循环：

```text
candidate_predictions
  -> hit_rate_records
  -> recent_factor_effectiveness
  -> factor_weight_versions
```

### 3.3 降级策略

`_safe_run()` 捕获子 Agent 异常，把失败写入 `DataQualityIssue`，整体链路继续。对定时任务来说这是必要设计：盘前报告可以缺一块数据，但不能因为某个网页接口超时完全不发。

---

## 4. SQLite 状态模型

`Store.init_schema()` 初始化六类表：

| 表 | 作用 |
|---|---|
| `candidate_predictions` | 盘前候选池预测、分数、因子、解释 |
| `anomaly_records` | 盘中异动触发条件和归因 |
| `hit_rate_records` | 盘后命中率、收益分布、因子有效性、偏差归因 |
| `factor_weight_versions` | 权重版本、父版本、调整原因、回测摘要、active 标志 |
| `weekly_archives` | 周末观察池、事件日历、报告路径 |
| `run_reports` | 每次运行的任务、状态、完整 JSON、产物路径 |

这套表结构适合当前项目直接参考。尤其是 `factor_weight_versions`：自动优化必须可追溯、可回滚、可解释，不应只覆盖一个 YAML 数值。

---

## 5. 数据源治理

`DataSourceClient` 的设计比 README 更重要。它把数据源失败作为正常路径处理：

| 数据 | 首选 | 兜底 | 数据质量说明 |
|---|---|---|---|
| 实时行情 | 东财 push2 | 腾讯 qt | 腾讯缺主力净流入，写 pending |
| 日 K | 腾讯 fqkline 优先 | 东财 push2his、Yahoo、AkShare | 失败时说明替代源和字段口径 |
| 交易日 | Tushare | 本地 weekday rule | 本地规则需确认节假日 |

这和 `a-stock-data` 的原则一致：不要假设某个公开源永远稳定；失败时输出“待确认”，而不是让报告看起来完整。

---

## 6. 因子打分和反馈闭环

`PoolScorer` 使用五个因子：

```text
relative_strength
capital_trend
event_catalyst
technical_pattern
valuation_safety
```

缺失因子按中性值处理，同时写入数据质量。`ReviewAttributor` 在盘后对预测进行验证，计算每个因子在命中和未命中样本中的差异，再通过学习率调整权重。

这不是严格统计学习，但工程上非常适合做早期闭环：先让系统有“预测、保存、验证、归因、调整”的骨架，再逐步替换更严谨的因子评估。

---

## 7. 对当前项目的落地方案

### 7.1 报告统一契约

所有 Agent/tool 输出统一为：

```text
objective: dict
ai_interpretation: dict
data_quality: list[{field,status,source,message,alternatives}]
metrics: duration/source_hit/fallback_count
```

### 7.2 运行归档

每次任务必须生成：

```text
run_id
task
input config snapshot
agent outputs
rendered report path
data quality summary
status: ok/degraded/failed
```

### 7.3 自动调权的护栏

如果迁移权重再校准，必须增加三条护栏：

1. 样本数不足不调。
2. 新权重只创建版本，不覆盖历史。
3. 调权后必须跑回测或 shadow 验证再扩大使用。

---

## 8. 值得直接写进规范的原则

1. LLM 不参与算数，只解释已计算结果。
2. 数据失败必须暴露给用户，不能补造。
3. 定时任务必须支持 `--once --dry-run`。
4. 预测必须落库，否则无法盘后复盘。
5. 自动优化必须版本化、可回滚、有原因。
6. 子 Agent 失败不应拖垮整个链路，但必须进入 run report。
7. 推送内容必须保留数据质量区和非投资建议边界。
