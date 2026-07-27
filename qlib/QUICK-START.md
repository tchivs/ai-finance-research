# Qlib 快速概览

> Microsoft Qlib · AI-oriented quantitative investment platform · 数据/模型/回测/实验记录/在线滚动
> 源码: `/root/source/tmp/qlib/`
> 原始仓库: <https://github.com/microsoft/qlib>

## 1. 一句话定位

Qlib 是一个完整的 AI 量化研究平台，覆盖数据处理、特征/标签、模型训练、预测信号、IC 分析、组合回测、交易执行、实验记录、在线滚动和任务管理。它不像前几类项目那样以 LLM 为中心，而是量化研究的工程底座。

对当前项目来说，Qlib 是“把 AI 观点变成可回测信号”的底层样板。

## 2. Qlib 覆盖的链路

```text
data provider / qlib bin
    -> Dataset / Handler / Processor
    -> Model.fit / Model.predict
    -> SignalRecord pred.pkl
    -> SigAnaRecord IC / RankIC / Long-Short return
    -> Portfolio / Strategy / Executor / Exchange backtest
    -> PortAnaRecord risk / indicator / report
    -> Recorder / Experiment / MLflow artifacts
```

## 3. 核心模块

| 模块 | 作用 | 对当前项目的价值 |
|------|------|------------------|
| `qlib.data` | 数据读取、缓存、DatasetH、Processor | 标准化数据切片和标签构建 |
| `qlib.model` | Model 接口、Trainer、任务训练 | 把模型训练从脚本变成 task config |
| `qlib.workflow` | Recorder、Experiment、RecordTemp | 每次实验保存参数、模型、预测、指标、回测结果 |
| `qlib.backtest` | Strategy、Executor、Decision、Exchange、Account | 组合回测和交易执行抽象 |
| `qlib.contrib.model` | LightGBM、Transformer、ALSTM、HIST 等模型 | 可作为模型 zoo 和 benchmark |
| `qlib.contrib.report` | IC、累计收益、风险分析图表 | 给研究报告提供标准指标图 |
| `qlib.workflow.online` | 在线模型管理与滚动更新 | 长期运行模型的版本和上线管理 |

## 4. 最值得学的设计

### 4.1 Task config 驱动训练

`TrainerR` / `task_train()` 读取 task dict，初始化 model 和 dataset，训练模型，保存 `params.pkl`、`dataset`，再按 record 配置生成预测、IC、回测和分析结果。

这适合 HermesAlpha 的量化实验层：每个信号实验都应该有 task config，而不是散落的 notebook。

### 4.2 Recorder/Experiment

`Recorder` 模仿 MLflow API：log_params、log_metrics、save_objects、load_object、list_artifacts。`MLflowRecorder` 做封装，额外支持保存对象和环境信息。

这适合 ashare-audit：审计不只看最终结果，还能追溯实验参数、模型、数据集、预测文件和回测指标。

### 4.3 RecordTemp

`SignalRecord` 生成预测 `pred.pkl`，`SigAnaRecord` 计算 IC、RankIC、Long-Short return。RecordTemp 自带依赖检查：上游 artifact 不存在就跳过或报错。

这比“一个脚本从头跑到尾”更可维护。

### 4.4 Strategy / Executor / Decision 解耦

`BaseStrategy.generate_trade_decision()` 只生成交易决策；`BaseExecutor.collect_data()` 执行决策并更新账户；`Order` 和 `BaseTradeDecision` 表示交易动作和交易范围。

这个分层能把信号、组合、执行、成交模拟分开，适合在 A 股系统中加入涨跌停、停牌、滑点、T+1、手续费。

## 5. 对 HermesAlpha 的借鉴

1. **把 AI signal 接到 Qlib-style RecordTemp**：LLM 或基础模型输出预测后，统一生成 pred、label、IC、RankIC、Long-Short、回测报告。
2. **实验统一入 Recorder**：每次因子、模型、prompt、数据版本都作为 params/tags/artifacts 保存。
3. **用 Strategy/Executor 把建议转成回测**：最终不要只问“这篇报告是否合理”，还要问“按这套规则历史表现如何”。
4. **建立 benchmark suite**：LightGBM Alpha158、Kronos/FinCast、LLM signal 应该能在同一 workflow 下比较。

## 6. 对 ashare-audit 的借鉴

1. **审计 artifact 完整性**：SignalRecord 是否有 pred.pkl/label.pkl，IC 文件和 backtest 文件是否由同一 recorder 生成。
2. **审计数据健康**：Qlib README 提到 `check_data_health.py`，当前项目也需要数据缺失、跳变、复权异常检查。
3. **审计训练/回测时间窗**：task config 中 dataset segments 必须明确 train/valid/test，防未来函数。
4. **审计回测执行假设**：Executor/Exchange/Account 的费用、可交易性、成交规则必须进入报告。

## 7. 不该照搬的部分

- Qlib 很大，不适合直接吞进一个轻量 Agent 项目；应该先学 contracts，再按需集成。
- 官方数据源在 README 中提示受数据政策影响，生产必须准备自己的高质量数据。
- Qlib 的股票代码、数据频率、回测执行默认不一定满足 A 股实盘约束，需要定制交易日历和 exchange。
- 对 LLM 项目来说，Qlib 没有天然 prompt/Agent trace，需要额外把 prompt、tool calls、LLM 输出保存成 artifacts。

## 8. 最小迁移方案

```text
1. 定义 ExperimentRun
   run_id, config, data_version, model_or_agent_version, prompt_version

2. 定义 SignalRecord
   pred table + label table + metadata

3. 定义 AnalysisRecord
   IC, RankIC, monthly IC, coverage, turnover, long-short return

4. 定义 BacktestRecord
   portfolio curve, positions, trades, costs, risk metrics

5. 定义 Artifact Store
   每个 run 保存 config、输入数据摘要、输出、指标、报告
```

## 9. 结论

Qlib 是第三批中最基础设施化的项目。它提醒当前项目：AI 金融系统不能只积累报告，还要积累可复跑的实验、可比较的信号、可审计的 artifact 和可复现的回测。
