# Lean 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/QuantConnect/Lean.git
> 分析基线：
> - `Lean`：commit `c6cc3b743ed7b65d5e0b9fa2bfc18b7d3ac2aea0`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Lean`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `Lean`：`cd52034ddf55` → `c6cc3b743ed7`

提交摘要：
- c6cc3b743 Restore the LogEntry based SaveLogs signature (#9658)
- 3c53d1705 Fix the warm-up order analysis for Python algorithms and register the MarketOnClose too-late analysis (#9657)
- de8d2f8c9 Update US equity market hours through 2028 (#9646)
- ea470761a Re-capture starting portfolio value after warm-up and fire OnWarmupFinished before post-warm-up data (#9653)
- 138f257fb Run a reduced results analysis periodically during backtests (#9632)
- 42b9d7666 Fix the USD/KRW minimum price variation (#9656)
- da1bade3f Add Interactive Brokers KRX future fees (#9655)
- 35b32b401 Add margin-aware option strategy match selection (#9639)
受影响路径：
- `A	Algorithm.CSharp/OnWarmupFinishedOrderingRegressionAlgorithm.cs`
- `M	Algorithm.CSharp/OptionChainConsistencyRegressionAlgorithm.cs`
- `A	Algorithm.CSharp/OptionEquityOverlappingBullCallSpreadsRegressionAlgorithm.cs`
- `M	Algorithm.CSharp/TrainingInitializeRegressionAlgorithm.cs`
- `A	Algorithm.CSharp/WarmupStartingPortfolioValueRegressionAlgorithm.cs`
- `M	Common/Currencies.cs`
- `A	Common/Exceptions/ModuleNotFoundPythonExceptionInterpreter.cs`
- `A	Common/Exceptions/MultipleInheritancePythonExceptionInterpreter.cs`
- `M	Common/Interfaces/IRegressionAlgorithmDefinition.cs`
- `M	Common/Messages/Messages.Exceptions.cs`
- `M	Common/Orders/Fees/InteractiveBrokersFeeModel.cs`
- `M	Common/Securities/Option/StrategyMatcher/IOptionStrategyMatchObjectiveFunction.cs`
- 其余 54 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> 原始仓库: <https://github.com/QuantConnect/Lean>

## 1. 核心架构：以目标为边界的算法框架

Lean 的关键价值不在某个指标或经纪商，而在于将策略结果显式分层。`QCAlgorithm.Framework.cs` 提供 universe、alpha、portfolio construction、risk management 和 execution 模型的装配入口；每个模型以接口隔离，且可通过 composite model 组合。

```text
new market data slice
    -> IAlphaModel.Update()
    -> Insight[]
    -> IPortfolioConstructionModel.CreateTargets()
    -> IPortfolioTarget[]
    -> IRiskManagementModel.ManageRisk()
    -> approved/modified IPortfolioTarget[]
    -> IExecutionModel.Execute()
    -> order events / fills / results
```

接口的责任边界很清楚：

| 接口 | 输入 | 输出 | 不应承担的职责 |
|---|---|---|---|
| `IAlphaModel` | `QCAlgorithm`、`Slice` | `IEnumerable<Insight>` | 组合规模、风控、订单提交 |
| `IPortfolioConstructionModel` | `Insight[]` | `IEnumerable<IPortfolioTarget>` | broker 请求和成交确认 |
| `IRiskManagementModel` | 当前 targets | 修正后的 targets | 生成预测或直接推送自然语言建议 |
| `IExecutionModel` | 新/更新的 targets | side effect 为订单，返回 void | 把订单受理误解为成交 |

对 HermesAlpha 而言，最小映射应是：

```text
SignalRecord / evidence-backed research view
    -> InsightRecord
    -> TargetWeight / RebalancePlan
    -> deterministic RiskAssessment
    -> ApprovalTicket
    -> PaperOrderIntent
    -> PaperOrder / Fill / ReconciliationRecord
```

`InsightRecord`、`ApprovalTicket` 和审计事件属于本项目必须补齐的服务端契约，不能以 Lean 的内存对象替代。

## 2. 引擎运行时：handler 组合而不是单一回测函数

`Engine.Run()` 为一个 job 先初始化日志、通知和 results handler，再创建算法实例、brokerage、security service、data manager、history provider 和 data feed。live mode 使用 `LiveSynchronizer`，backtest 使用 `Synchronizer`；历史请求在 live mode 下会关闭并行化。

```text
AlgorithmNodePacket
    -> SetupHandler creates algorithm + brokerage
    -> DataManager / UniverseSelection
    -> DataFeed + HistoryProvider
    -> Synchronizer drives time slices
    -> AlgorithmManager / TransactionHandler
    -> ResultHandler and notification
```

这说明一个可靠的回测/执行系统需要不同 adapter 的协作：数据、时钟、标的元数据、订单、结果、存储和异常处理不能散在策略函数里。

但 Lean 的 handler 体系与其 job packet、Docker、数据目录和支持的 brokerage 深度耦合。首版只应从中借鉴依赖方向和接口拆分，不应把它作为 HermesAlpha 的进程内执行依赖。

## 3. 风控与执行的真实边界

Lean 的风控接口接收 portfolio target 后返回另一组 target，因此模型可以削减、归零或替换目标。执行接口接收的是“新或更新的 targets”，并有独立的 `OnOrderEvent()` 来消费订单事件。

这两个细节应成为本项目的约束：

1. 风控结论必须是可计算的 target mutation 或 rejection，不是提示语。
2. 执行器只能接收已经通过风险和人工审批的 `PaperOrderIntent`。
3. `OrderSubmitted`、`OrderRejected`、`PartiallyFilled`、`Filled`、`Canceled` 是不同事实；目标、订单、成交和仓位需要分离持久化。
4. 订单侧事件应携带 provider/broker source、时间、原始状态、关联 intent 和幂等键，供对账使用。

Lean 本身不能取代这些治理层：接口未表达本项目所需的 scope、审批票据、提示注入防护、API 调用审计或跨进程幂等。

## 4. A 股适配的缺口

若未来以 Lean 作为外部回测基准，需先建独立适配层：

| 范围 | 必须定义的本地语义 |
|---|---|
| 数据 | 交易日、时区、复权口径、停牌、指数/ETF/股票标识、数据版本 |
| 下单 | 整手、最小单位、T+1、涨跌停、不可交易状态、撤单和部分成交 |
| 组合 | 现金下限、行业/单标的上限、换手成本、税费和滑点模型 |
| 回测 | 撮合时间点、价格可得性、公司行为、幸存者偏差、调仓延迟 |
| 执行 | paper-only target、人工确认、账户/订单/成交的日终对账 |

未定义这些前，任何“Lean 回测结果”都只是某个抽象市场模型的结果，不能外推为 A 股可执行预期。

## 5. 落地建议

当前不引入 Lean 引擎。按阶段采用以下最小实现：

1. Phase 2：定义 `InsightRecord` 和 `TargetWeight` schema，保存输入数据版本、模型/策略版本、时间范围与置信度。
2. Phase 3：将组合优化输出持久化为 `RebalancePlan`，明确连续权重到 A 股离散订单的转换失败原因。
3. Phase 5：实现纯函数 `RiskAssessment`，它只能 reject 或产生修正后的 plan，不能提交订单。
4. Phase 6：添加 `ApprovalTicket`、paper broker adapter、订单/成交状态机、idempotency key 和每日对账。
5. 仅在这些契约稳定后，评估 Lean 是否需要作为独立 Docker 回测 benchmark，而不是核心运行时。
