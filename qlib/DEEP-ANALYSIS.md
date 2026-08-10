# Qlib 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/microsoft/qlib.git
> 分析基线：
> - `qlib`：commit `79633dd9506ea689e5400dea0197717b5b3d74b7`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/qlib`
<!-- source-sync:end -->


> 量化研究操作系统 · Task/Recorder/RecordTemp · Strategy/Executor/Decision · Nested execution
> 源码: `src/qlib/`
> 原始仓库: <https://github.com/microsoft/qlib>

## 1. 为什么 Qlib 重要

前面吸收的大多数项目都围绕 LLM、Agent、MCP、盯盘和报告。Qlib 则是另一个维度：它是量化研究从数据到模型、从信号到组合、从回测到实验记录的基础设施。

如果 HermesAlpha 想从“智能投研报告”走向“可验证的投资研究系统”，需要 Qlib 这样的实验和回测骨架。LLM 负责提出假设和解释，Qlib-style workflow 负责验证假设。

## 2. 高层组件

Qlib README 描述的高层框架：

```text
Data
    -> Learning Framework
    -> Trading Strategy
    -> Executor / Backtest
    -> Analysis Report
    -> Online Serving
```

代码中对应为：

| 领域 | 关键模块 |
|------|----------|
| 数据 | `qlib.data`, `qlib.data.dataset`, `qlib.contrib.data` |
| 模型 | `qlib.model`, `qlib.contrib.model`, `qlib.model.trainer` |
| 实验 | `qlib.workflow.recorder`, `qlib.workflow.expm`, `qlib.workflow.record_temp` |
| 回测 | `qlib.backtest.backtest`, `executor`, `decision`, `exchange`, `account`, `position` |
| 策略 | `qlib.strategy.base` |
| 报告 | `qlib.contrib.report`, `qlib.contrib.evaluate` |
| 在线 | `qlib.workflow.online`, `qlib.contrib.online` |

## 3. Task-driven training

`qlib/model/trainer.py` 是 Qlib 工作流的核心之一。它把训练拆成：

```text
task_config
    -> init model by config
    -> init dataset by config
    -> model.fit(dataset)
    -> save model params.pkl
    -> save dataset metadata
    -> run record templates
```

`_exe_task()` 的关键行为：

1. 通过 `init_instance_by_config()` 初始化 Model 和 Dataset。
2. 调用 `model.fit(dataset, reweighter=...)`。
3. `R.save_objects(params.pkl=model)` 保存模型。
4. `dataset.config(dump_all=False, recursive=True)` 后保存 dataset 配置。
5. 用 `<MODEL>`、`<DATASET>` placeholder 填充后续 record 配置。
6. 遍历 record templates，生成预测、IC、回测等 artifact。

这套设计把“训练什么、用什么数据、产出什么记录”全部配置化。对 AI Agent 来说，也可以同样设计：

```text
agent_task_config
    model/provider/prompt/tool_profile/data_window/output_schema/eval_plan
```

## 4. Recorder 与 Experiment Manager

`Recorder` 抽象类似 MLflow：

```text
save_objects
load_object
start_run / end_run
log_params
log_metrics
log_artifact
set_tags / delete_tags
list_artifacts / list_metrics / list_params / list_tags
download_artifact
```

`MLflowRecorder` 包了一层 MLflow，并说明这样做的理由：

- 未来可以替换实验记录后端。
- 可以自动记录未提交代码、环境变量等额外信息。
- 用户通过不同 Recorder 管理不同 run，而不是直接操作 MLflow 细节。

`ExpManager` 负责 get/create/start/end/search experiment，并用 file lock 处理本地 file URI 下的并发创建。

### 对当前项目的意义

LLM 金融分析也需要类似 Recorder。一个完整 run 应保存：

```text
输入问题
标的与日期
数据源版本
工具调用结果
prompt 版本
模型/provider/temperature
每个 Agent 的结构化输出
最终报告
审计结果
后验结算
```

否则系统只能复读报告，无法解释报告是怎么来的。

## 5. RecordTemp: 从预测到分析

`workflow/record_temp.py` 定义 `RecordTemp`，再派生出不同记录模板。

### 5.1 SignalRecord

`SignalRecord.generate()`：

```text
pred = model.predict(dataset)
save pred.pkl
if DatasetH: save raw label.pkl
```

这是最基本的“模型信号记录”。

### 5.2 SigAnaRecord

`SigAnaRecord.generate()` 加载 `pred.pkl` 和 `label.pkl`，计算：

```text
IC
ICIR
Rank IC
Rank ICIR
Long precision
Short precision
Long-Short Average Return
Long-Short Average Sharpe
```

并保存 `ic.pkl`、`ric.pkl`、`long_pre.pkl`、`short_pre.pkl`、`long_short_r.pkl`、`long_avg_r.pkl`。

这个模板很适合 AlphaAgent / RD-Agent / Kronos / FinCast 产生的信号统一比较。

## 6. Backtest loop

`qlib/backtest/backtest.py` 的核心是 `collect_data_loop()`：

```text
trade_executor.reset(start_time, end_time)
trade_strategy.reset(level_infra=executor.get_level_infra())

while not executor.finished():
    decision = strategy.generate_trade_decision(execute_result)
    execute_result = yield from executor.collect_data(decision)
    strategy.post_exe_step(execute_result)
    calendar.step()

strategy.post_upper_level_exe_step()
collect portfolio metrics and indicators from all executors
```

这说明 Qlib 把 strategy 和 executor 解耦：策略只负责生成 trade decision，executor 负责按交易日历、exchange、account 执行。

## 7. Strategy / Executor / Decision 三件套

### 7.1 BaseStrategy

`BaseStrategy.generate_trade_decision()` 是唯一必须实现的方法。策略可以访问：

```text
executor
trade_calendar
trade_position
trade_exchange
outer_trade_decision
```

它还提供 nested execution 的 hooks：

```text
update_trade_decision
alter_outer_trade_decision
post_upper_level_exe_step
post_exe_step
```

### 7.2 BaseExecutor

`BaseExecutor.collect_data()` 的职责：

1. 如 `track_data` 开启，先 yield trade_decision 给 RL 数据采集。
2. 执行 `_collect_data()`。
3. 更新账户和交易指标。
4. trade_calendar 前进一步。
5. 返回 execute_result。

### 7.3 Order / BaseTradeDecision

`Order` 表示单笔订单，包含 stock_id、amount、direction、start_time、end_time、deal_amount、factor。`BaseTradeDecision` 表示策略输出的一组决策，并支持 trade range。`TradeRangeByTime` 可以限制分钟级交易时间段。

### 7.4 NestedExecutor

`NestedExecutor` 支持：日频外层策略产生目标仓位，分钟级内层策略/执行器拆单执行。这是高频和执行优化的基础。

对 A 股项目来说，nested execution 可用于：

```text
日频选股/调仓信号
    -> 分钟级 VWAP/TWAP/涨跌停/流动性执行模拟
```

## 8. 数据健康与生产注意点

Qlib README 特别强调数据健康：

```bash
python scripts/check_data_health.py check_data --qlib_dir ~/.qlib/qlib_data/cn_data
```

它还提醒官方数据源受政策影响暂时 disabled，用户应准备自己的高质量数据。当前项目吸收 Qlib 时，必须把数据健康作为一等 artifact：缺失、跳变、复权、停牌、涨跌停、行业分类和指数成分都要记录。

## 9. 当前项目集成方式

### 9.1 不直接大规模引入 Qlib 的情况

可以只复制 contracts：

```text
Experiment
Recorder
SignalRecord
AnalysisRecord
BacktestRecord
Strategy
Executor
Decision
```

这适合轻量自研系统。

### 9.2 直接集成 Qlib 的情况

可以把以下信号接入 Qlib workflow：

| 信号来源 | 接入方式 |
|----------|----------|
| AlphaAgent DSL 因子 | 生成 pred.pkl，与 label 做 IC 分析 |
| RD-Agent 因子 | 作为 Qlib task 自动训练/回测 |
| Kronos/FinCast 预测 | 转成 score，做 group return 和 TopK 回测 |
| LLM 评级 | 映射为数值 score，做 coverage/IC/turnover 分析 |
| TradingAgents 决策 | 转成离散 target weight，进入策略回放 |

## 10. 审计规则

ashare-audit 可基于 Qlib 思路检查：

| 审计项 | 问题 |
|--------|------|
| Task config | train/test 是否分离，label horizon 是否正确 |
| Recorder artifacts | pred/label/IC/backtest 是否来自同一个 run |
| Data health | 缺失、异常跳变、复权和停牌是否处理 |
| Backtest exchange | 手续费、滑点、涨跌停、成交量限制是否配置 |
| Signal analysis | IC/RankIC 是否稳定，是否只在少数月份有效 |
| Portfolio metrics | 是否只报告无成本收益，忽略成本后失效 |

## 11. 与已吸收项目的关系

| 项目 | 与 Qlib 组合方式 |
|------|------------------|
| RD-Agent | 官方 README 已把 RD-Agent 作为 Qlib 自动量化工厂方向 |
| AlphaAgent | DSL 因子可进入 Qlib-style IC/backtest record |
| Kronos/FinCast | 预测结果可作为 Qlib score 回测 |
| DeepFund | Portfolio decision 可以用 Qlib backtest/executor 验证 |
| ai-hedge-fund | 多 Agent decision 可转成 Qlib strategy |
| x2t | 财经观点可转成 score，做历史结算 |

## 12. 结论

Qlib 是当前资料库中最成熟的量化工程底座。它的核心不是某个模型，而是让数据、模型、信号、回测、指标和 artifact 以统一 workflow 存活。HermesAlpha 若要形成真正可验证的研究闭环，需要吸收 Qlib 的 Task、Recorder、RecordTemp 和 Backtest contracts。
