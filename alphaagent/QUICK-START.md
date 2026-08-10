# AlphaAgent 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/RndmVariableQ/AlphaAgent.git
> 分析基线：
> - `AlphaAgent`：commit `b42cb397025510da44355db9dcf278304321f589`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/AlphaAgent`
<!-- source-sync:end -->


> A 股多因子研究框架 · Tushare/panel · DSL · FactorZoo · LLM factor mining
> 源码: `src/AlphaAgent/`
> 原始仓库: <https://github.com/RndmVariableQ/AlphaAgent>

## 1. 一句话定位

AlphaAgent 是一个面向中国 A 股的多因子研究框架。它从 Tushare 或本地 parquet cache 构建日频 panel，用 DSL 表达因子，在 FactorZoo 中保存/评估，并可通过 AgentScope / OpenAI tool calls 让 LLM 多轮挖掘新因子。

它的价值在于把“LLM 想一个因子”变成“可解析、可执行、可评估、可入库、可复现”的闭环。

## 2. 核心链路

```text
Tushare / open data package
    -> raw parquet caches
    -> build_panel.py
    -> panel_1d.parquet
    -> DSL expression
    -> eval_factor()
    -> IC / RankIC / MLS / decile reports
    -> FactorZoo memmap + catalog
    -> optional LLM mining loop
```

参考数据集：CSI 1000 成分股并集，2015-01 到 2026-06，约 2,757 只股票，约 6.2M panel rows。

## 3. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| 两阶段数据 | 先 fetch raw cache，再 offline build panel | 网络采集和研究面板构建解耦 |
| DSL parser | pyparsing 把 `$close`、函数、中缀表达式转成可执行 Python | 因子表达可版本化，不散落在 Python 函数里 |
| Factor eval | `evaluate_factor_on_split()` 输出 IC/RankIC/MLS/monthly robustness | 因子提交必须过标准评估 |
| FactorZoo | 全量 factor values 用 memmap，catalog 用 parquet | 大规模因子库不必全部进内存 |
| Sample summary | 每个因子保存抽样摘要，用于快速相似度/质量检查 | 适合因子去重和检索 |
| LLM mining loop | OpenAI tool calls + 并行工具执行 + JSONL 轨迹 | LLM 挖因子必须记录轨迹和工具结果 |

## 4. DSL 关键能力

AlphaAgent 的 DSL 支持：

```text
$close / $volume / $field@60m
函数调用: TS_MEAN($close, 20)
算术: + - * /
比较: > < >= <= == !=
逻辑: && ||
条件表达式: condition ? a : b
字符串字面量
多行表达式
```

解析器会把列间运算重写成 `ADD/SUBTRACT/MULTIPLY/DIVIDE`，把列间比较重写成 `GT/LT/GE/LE/EQ/NE`，从而统一处理 panel Series 对齐问题。

## 5. 因子评估指标

`evaluate_factor_on_split()` 会返回：

| 指标 | 含义 |
|------|------|
| IC / ICIR | 横截面 Pearson IC 与稳定性 |
| Rank IC | 横截面 rank correlation |
| coverage | 非空覆盖率 |
| skew/kurtosis | 因子分布形态 |
| cs_pearson_autocorr | 横截面 lag1 自相关 |
| decile_mean_label | 分位组合标签均值 |
| MLS / Fama-MacBeth | 多空/截面稳健性摘要 |
| monthly_ic_robustness | 月度 IC 稳定性 |

## 6. 对当前项目的借鉴

### HermesAlpha

1. 把 LLM 生成的量化想法先转成 DSL，不直接执行任意 Python。
2. 每个因子必须能在固定 panel 和 split 上评估。
3. 因子入库前要保存表达式、metrics、样本摘要、hash 和来源。
4. 研究报告中的“量化信号”应能回指到 FactorZoo 条目。

### ashare-audit

1. 审计 DSL 是否使用未来字段或 label 泄漏。
2. 审计 factor coverage、IC、monthly robustness 是否达标。
3. 审计 LLM mining 轨迹：每个 tool_call 的输入、输出、错误是否保存。
4. 审计 FactorZoo catalog 与 memmap 是否一致。

## 7. 不该照搬的部分

- AlphaAgent 依赖 Tushare 数据，数据授权和重分发要遵守 Tushare 条款。
- DSL 通过生成 Python 表达式执行，生产环境需要沙箱和 operator whitelist。
- 因子有效性不能只看单一 IC，必须和 Qlib/AlphaEvo 的回测、换手、成本、稳定性结合。
- Agent mining 容易产生相似表达式，需要强去重、相似度和复杂度惩罚。

## 8. 最小迁移方案

```text
1. 定义 ASharePanel
   index: date, instrument
   fields: OHLCV, fundamentals, industry, labels

2. 定义 FactorDSL
   parser + operator registry + sandbox evaluator

3. 定义 FactorEval
   train/val/test IC, coverage, monthly stability, decile return

4. 定义 FactorStore
   expression catalog + values storage + metrics + provenance

5. 定义 MiningLoop
   LLM proposes DSL -> tool evaluates -> result logged -> accepted factor stored
```

## 9. 结论

AlphaAgent 是把 LLM 因子挖掘落到 A 股面板研究的好样板。它告诉当前项目：LLM 的“灵感”必须先变成受限 DSL，再通过统一 panel 和指标体系验证，最后才能进入因子库。
