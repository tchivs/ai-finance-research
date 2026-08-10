# PA_Agent 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/rosemarycox5334-debug/PA_Agent.git
> 分析基线：
> - `PA_Agent`：commit `b1912e905800509e8f9cd50fb8589f4ef86ce21f`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/PA_Agent`
<!-- source-sync:end -->


> 原始仓库: <https://github.com/rosemarycox5334-debug/PA_Agent>

## 1. 两阶段分析：将诊断与决策分开保存

`orchestrator/two_stage.py` 负责完整链路：构建 stage 1 prompt、调用模型、验证 JSON、路由策略文件与经验记录、构建 stage 2 prompt、再次调用和验证，最终写入完整 `AnalysisRecord`。取消检查位于每个阶段和 API 调用之后；网络、超时和校验失败被写入部分记录而不是静默吞掉。

```text
KlineFrame
    -> PreflightDataGate
    -> Stage 1 diagnosis response
    -> JSON/schema/semantic validation
    -> route strategy files + load experiences
    -> Stage 2 decision response
    -> JSON/schema/semantic validation
    -> AnalysisRecord with prompts, raw outputs, usage, errors
```

这个结构优于单一“给 K 线直接要买卖建议”的 prompt：决策可以引用可检查的诊断中间态；当 JSON 被截断、正文为空、额度耗尽或字段不符合约定时，系统有明确的错误路径和可追踪的原始证据。

但两阶段仍不等于真实可信。LLM 产生的价格行为判断只能成为研究候选，必须与数据版本、时间范围、质量状态和决定性规则一起审计。

## 2. 数据与确定性门控

`check_preflight_data()` 是 LLM 前的纯函数门：它依序检查 frame 是否存在、OHLC 是否有效、K 线数是否至少为 20、EMA20/ATR14 是否不全为 NaN；任何异常按 fail-closed 返回拒绝结果。

`decision_nodes.py` 还将部分价格行为节点由程序填充，例如方向投票、趋势 bar 比例、overlap、EMA slope、ATR 回撤和超长 signal bar。节点区分不可覆盖、可覆盖、模型主导和安全 gate，避免模型把明显无效的数据包装成强结论。

可迁移的结论是：

1. 每个 Agent run 先运行确定性 `PreflightResult`，失败则输出可解释状态，不发 LLM 请求。
2. 对可计算的事实，如数据新鲜度、交易日、指标缺失、仓位上限、价格阈值，程序为主，模型只能解释或补充。
3. LLM 允许生成结构化假设，但不可覆盖最高优先级的 data/risk safety gate。

## 3. Paper execution 不是 README 所说的纯分析

README 将产品描述为“不连接券商、不执行下单”，这对真实交易路径成立；但代码已实现本地 paper execution 工作区。

`AppContext._compose_workspace_facade()` 创建 `PaperTradingRuntime`、`SQLiteExecutionLedger`、`PaperStore`、`FreshEvidenceCollector`、`RiskEngine`、`ApprovalService`、`ProposalService` 和 `KillSwitchService`。在审批输入中，target 被构造成 `ExecutionTarget(..., Mode.PAPER, ...)`；当前 UI approval 路径仅支持 spot context。

```text
persisted analysis selection
    -> ProposalService creates candidate intent
    -> fresh evidence collection
    -> deterministic RiskAssessment
    -> durable ApprovalTicket
    -> operator approval consumes current ticket
    -> dispatch permit
    -> PaperGateway operation
    -> SQLite ledger + projection + recovery
```

`PaperTradingRuntime` 将 gateway operation 通过 `PaperProjectionBridge` 投影至 ledger，并把 submission/recovery 都接到同一个 paper gateway。它体现了正确的职责分离，但只覆盖本地模拟账户，不能替代经纪商回执、外部可用性、分布式事务或日终对账。

## 4. 审批和风险的可迁移契约

`ApprovalService.consume_ticket()` 会先检查 ticket 状态与时效，再重新收集 evidence、验证 candidate digest、重新运行 `RiskEngine`，只有全部满足才原子换取 dispatch permit。证据刷新失败、过期、候选绑定变化或风险结果变化都会使 ticket 失效。

`RiskEngine.assess()` 不依赖 UI、gateway 或 ledger，针对单个 immutable candidate、target、policy 和 evidence bundle 纯函数地产生接受/拒绝结果。已覆盖的检查包括：

- 数量/价格 precision 与 minimum quantity/notional；
- 单笔名义金额、总敞口、最大挂单数与订单频率；
- UTC 日内已实现损失和回撤；
- quote 偏离、买卖价差与费率证据新鲜度；
- 账户、标的、产品和 target 的 evidence binding；
- 产品特定保证金/永续规则。

本项目可采用同样的审批票据模型，但 A 股 `RiskPolicy` 需要替换成自己的规则：股票整手、T+1、可卖数量、涨跌停、停牌、临停、账户可用资金、费用、行业集中度和目标调仓时间。

## 5. 工程边界与落地建议

### 可借鉴

- `AnalysisRecord` 作为分析过程的不可删除证据，而不是只有报告正文。
- preflight -> model JSON -> semantic validation 的 fail-closed 顺序。
- 票据在批准时重新取证，而不是复用生成建议时的陈旧价格和账户状态。
- `RiskEngine` 纯函数化，方便表驱动测试和审计复算。
- paper runtime、ledger、projection、recovery 和 kill switch 的职责分离。

### 必须自行补齐

1. API/tool 调用级的 scope、session、原始响应摘要和输入数据 provenance。
2. Agent 结论到 `InsightRecord` 的标准化，不绑定 Price Action 特定 schema。
3. A 股产品规则与只读数据层的交易日/价格可得性契约。
4. 事件序号、idempotency key、重试策略和 paper broker 状态对账。
5. 商业可用的许可证审查；AGPL 源码不进入当前产品代码。

当前实施阶段只复用其模式。先为只读研究工作流实现数据预检、结构化分析记录和报告质量状态；之后才把 `InsightRecord -> RebalancePlan -> RiskAssessment -> ApprovalTicket -> PaperOrderIntent` 接入 paper-only 工作区。
