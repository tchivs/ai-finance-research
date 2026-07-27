# Lean 快速概览

> 原始仓库: <https://github.com/QuantConnect/Lean>
> 分析基线：`QuantConnect/Lean` commit `cd52034ddf55c0c9aa57264d2a148e563924100f`（2026-07-23），Apache-2.0，C#/.NET 为核心，支持 Python 算法接口。本文为静态源码核对；未下载数据、启动 Docker、执行回测或连接券商。

## 一句话定位

Lean 是一个通用、事件驱动的量化研究、回测和交易引擎。它把标的范围、预测、组合构建、风控和执行拆成明确的接口，适合作为 HermesAlpha 的研究到受控行动链路的架构基准。

它不是首版应直接嵌入的底座：核心运行时是 .NET/Docker 生态，数据、交易日历、复权、经纪商适配和 A 股市场规则都需要单独实现和验证。

## 核心结构

```text
Universe selection
    -> Alpha model produces Insight
    -> Portfolio construction produces PortfolioTarget
    -> Risk model modifies/rejects targets
    -> Execution model creates orders
    -> brokerage/data/result handlers
```

| 层 | 关键接口/入口 | 可迁移价值 |
|---|---|---|
| 运行编排 | `Engine/Engine.cs` | 把算法、数据、交易、结果和实时事件作为可替换 handler 装配 |
| 标的范围 | `IUniverseSelectionModel` | 标的池变化与策略逻辑分离 |
| Alpha | `Algorithm/Alphas/IAlphaModel.cs` | 每次数据切片产生结构化 `Insight`，而不是文本建议 |
| 组合 | `Algorithm/Portfolio/IPortfolioConstructionModel.cs` | 将多个 insight 转成组合目标 |
| 风控 | `Algorithm/Risk/IRiskManagementModel.cs` | 风控消费目标并可返回修正目标 |
| 执行 | `Algorithm/Execution/IExecutionModel.cs` | 执行仅消费目标，且需处理订单状态事件 |

## 已验证的重要边界

- `IAlphaModel.Update()` 每次收到订阅证券的新数据时产生 `Insight`；预测层不是下单接口。
- `IPortfolioConstructionModel.CreateTargets()` 的输出是 `IPortfolioTarget`，而非 broker 订单。
- `IRiskManagementModel.ManageRisk()` 接收当前 target 并返回调整后的 target；风控可以作为独立、确定性阶段。
- `IExecutionModel.Execute()` 才提交订单，并通过 `OnOrderEvent()` 接收后续订单事件；目标生成不代表已成交。
- `Engine.Run()` 在 live/backtest 运行时装配 brokerage、data feed、history、transaction 和 result handler；这套流程依赖 Lean 自己的数据与运行环境，不能假设能直接覆盖 A 股现货语义。

## 可直接吸收的模式

1. **研究结果使用结构化 insight**：至少记录标的、方向、预测周期、幅度/置信度、数据截止时间、模型版本和来源证据。
2. **目标权重与订单分离**：组合层产生 `TargetWeight`/`PortfolioTarget`；本地离散化、整手、停牌、涨跌停和费用由后续 adapter 决定。
3. **风控能修正而非只提示**：策略的 target 进入确定性风险阶段后，才可以成为可审批的 action candidate。
4. **执行只消费经审批的 target**：执行层必须处理提交、拒绝、部分成交、取消和成交事件，不能把 API 请求成功视为成交。
5. **组件替换而非框架复制**：首版只实现契约和测试夹具；不要因为 Lean 功能完整而直接引入其运行时和 Docker 栈。

## 不应直接照搬

- Lean 的数据文件、市场时段、corporate action、brokerage 和 live trading 行为主要面向其支持的市场与生态；A 股 T+1、整手、涨跌停、停牌、复权和券商订单规则需由本地数据/执行契约定义。
- `Insight`、`PortfolioTarget` 和订单生命周期提供分层，不替代本项目的权限、人工审批、idempotency key、不可变审计和 broker 对账。
- 把完整 Lean 引擎嵌入 Python/TypeScript 首版会引入 .NET、Docker、数据格式和平台运维复杂度，超出当前只读数据与 paper-only 范围。
- 实盘 handler 的存在不构成真实交易安全性证明；在本项目中，真实交易仍是非目标。

## 推荐阅读顺序

1. [DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
2. [策略与信号系统](../07-策略与信号系统篇.md)
3. [工程治理](../06-工程治理篇.md)
4. [模式决策矩阵](../18-模式决策矩阵.md)
