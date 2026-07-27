# PA_Agent 快速概览

> 原始仓库: <https://github.com/rosemarycox5334-debug/PA_Agent>
> 分析基线：`rosemarycox5334-debug/PA_Agent` commit `b1912e905800509e8f9cd50fb8589f4ef86ce21f`（2026-07-16），AGPL-3.0-or-later，Python >= 3.11。分析时上游工作树已有未提交的规划/覆盖文档；本文只依据固定 HEAD 的静态源码，不修改上游文件，也未运行测试、连接 LLM、行情源或执行工作区。

## 一句话定位

PA_Agent 是一个面向主观 Price Action 分析的 PyQt 桌面应用。它从行情源采集 K 线，运行“诊断 -> 策略路由 -> 决策”的两阶段 LLM 流程，验证并留存结构化 JSON；当前源码还提供了仅 paper 模式的审批、风控、执行账本和 kill switch 工作区。

它适合借鉴“LLM 结论必须经过数据门、JSON 契约、确定性规则和审批后才进入 paper action”的链路，不适合作为商业/闭源系统的代码来源，也不应把其 Price Action 结论视作通用量化信号。

## 核心结构

```text
market data source
    -> KlineFrame + deterministic preflight
    -> Stage 1 diagnosis JSON
    -> strategy/experience routing
    -> Stage 2 decision JSON + semantic validation
    -> persisted AnalysisRecord
    -> paper-only proposal / risk / approval ticket
    -> PaperGateway + SQLite ledger + projection
```

| 目标 | 入口 | 可迁移价值 |
|---|---|---|
| 运行时装配 | `pa_agent/app_context.py` | 将 settings、数据源、AI client、validator、记录器和 trading workspace 显式组合 |
| 分析编排 | `orchestrator/two_stage.py` | 两阶段 prompt、取消检查、校验重试、失败记录和完整输入输出留存 |
| 数据预检 | `ai/decision_nodes.py` | 在 LLM 调用前校验 OHLC、K 线数量和指标可用性 |
| 模型输出 | `ai/json_validator.py` 与 record schema | JSON schema/语义校验，禁止未验证文本直接驱动动作 |
| 审批 | `trading/application/approval.py` | 票据消耗前刷新证据、校验绑定、检查过期并生成一次性 dispatch permit |
| 风控 | `trading/application/risk_engine.py` | 纯函数校验数量、敞口、频率、亏损、回撤、价格偏离和滑点 |
| 模拟执行 | `trading/application/paper_runtime.py` | PaperGateway、SQLite ledger、操作投影和恢复服务 |

## 已验证的重要边界

- 数据预检会拒绝空/无效 OHLC、少于 20 根 K 线和 EMA20/ATR14 全空的输入；失败时不应调用 LLM。
- 两阶段流程把 stage 1/2 的 prompt、原始响应、校验结果、策略文件、experience 和用量写入 `AnalysisRecord`，包括部分失败记录。
- `AppContext` 只装配 `PaperTradingRuntime`；审批 target 固定为 `Mode.PAPER`，没有在该运行路径中装配真实 broker gateway。
- 审批票据会在消费前重新采集账户、价格、费率、挂单、频率和亏损/回撤证据；绑定变化、证据刷新失败、过期或风险拒绝都会终止票据。
- README 的“不会下单”应理解为“不会连接真实券商下单”。实际源码能够在本地模拟账户中提交 paper order，并持续保存执行 ledger。

## 可直接吸收的模式

1. 先验证数据再请求模型，且显式返回 machine-readable rejection reason。
2. LLM 分两步完成：诊断可解释上下文，决策消费已验证诊断；两步都用 JSON contract 与持久化记录约束。
3. Prompt、原始响应、校验失败和 retry 都是研究证据，不能只保留最终自然语言结论。
4. 从分析记录构造不可变 intent，再创建可过期的审批票据；审批时重新获取证据和评估风险。
5. paper execution、风险评估、账本和 UI projection 需要分层，paper 成功不能被误读为实盘能力。

## 不应直接照搬

- 项目为 AGPL-3.0-or-later，不能直接复用到闭源或商业部署；只吸收公开的架构模式。
- Price Action 的阈值、策略文档和“未来走势”预测是领域假设，不可直接作为 HermesAlpha 的默认信号逻辑。
- `RiskEngine` 目前包含 BTC/USDT 现货、逐仓和永续等特定产品规则；A 股须另定义整手、T+1、涨跌停、停牌、复权和费用。
- 本地 SQLite ledger 和 paper gateway 不等同于跨进程幂等、券商事实回补或生产级灾难恢复。

## 推荐阅读顺序

1. [DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
2. [工程治理](../06-工程治理篇.md)
3. [策略与信号系统](../07-策略与信号系统篇.md)
4. [模式决策矩阵](../18-模式决策矩阵.md)
