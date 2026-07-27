# vn.py（VeighNa）深度分析

> 原始仓库: <https://github.com/vnpy/vnpy>
> 分析基线：`vnpy/vnpy` commit `1b78494979deb4c4996f6b864f234d9839f2f239`。本文为静态源码核对；未连接任何券商、行情源、paper account 或风险管理扩展，也未运行上游测试。

## 1. 核心架构：事件归一化，而不是统一经纪商实现

`EventEngine` 是一个单队列、双线程的进程内分发器：处理线程从 `Queue` 读取事件，timer 线程按固定间隔写入 `EVENT_TIMER`。事件按 type 分发给专用 handler，再发给 general handler。

`MainEngine` 启动 EventEngine 后注册 Gateway、应用和基础引擎；`OmsEngine` 订阅 tick、order、trade、position、account、contract、quote 事件，维护当前状态的内存索引。

```text
broker/data adapter
  -> BaseGateway.on_order/on_trade/on_position/on_account
  -> EventEngine
  -> OmsEngine caches and active orders
  -> strategy, UI, notification, external audit adapter
```

这种模式值得借鉴的原因是接口方向正确：外部 API 的回调先规范为领域事件，后续系统只消费统一对象。不能从它推导出“框架已提供可靠的分布式事件总线”或“OMS 已持久化审计事实”。

## 2. Gateway 与订单生命周期

`BaseGateway` 定义了 `connect`、`close`、`subscribe`、`send_order`、`cancel_order`、`query_account`、`query_position` 等抽象接口，并要求实现线程安全、非阻塞、断线重连。

连接契约尤其重要：Gateway 应回补 contract、account、position、order 和 trade，并使用对应 `on_*` 回调或日志报告失败。下单契约要求：创建唯一的 `OrderData`、发送成功标记为 `SUBMITTING`、发送失败标记为 `REJECTED`、推送 order 事件并返回 `vt_orderid`。

领域对象明确区分：

| 对象 | 语义 | 重要字段 |
|------|------|----------|
| `OrderRequest` | 意图，尚未证明被受理 | symbol/exchange/direction/type/price/volume/reference |
| `OrderData` | 委托的状态机快照 | orderid/traded/status/datetime/gateway_name |
| `TradeData` | 一笔实际成交 | orderid/tradeid/price/volume/datetime |
| `PositionData` | 持仓状态 | volume/frozen/price/pnl |
| `AccountData` | 账户状态 | balance/frozen/available |

`ACTIVE_STATUSES` 包含 submitting、not traded、part traded。OMS 根据 order event 更新 active order 集合，并把 order/trade/position 更新交给每个 Gateway 的 offset converter。

### 对当前项目的契约映射

```text
StrategyDef / TargetWeight
  -> RebalancePlan (new)
  -> ActionGuard approval
  -> OrderIntent (new, idempotency key)
  -> vn.py OrderRequest
  -> OrderData / TradeData
  -> immutable AuditEvent + reconciliation
```

`OrderIntent`、审批、幂等、审计和对账是当前项目要补的层，不能用 `OrderRequest` 取代。

## 3. vnpy.alpha：研究数据、因子和组合回测

`AlphaLab` 为研究工作区创建 daily、minute、component、dataset、model、signal 目录。日线和分钟 Bar 按 `vt_symbol` 写为 Parquet；重复 datetime 会去重后排序。模型与 dataset 使用 pickle，信号使用 Parquet。

`BacktestingEngine` 为多标的 alpha 策略回放 Bar，维护活动限价单、成交、现金、合约手续费、合约 size、价格跳动和逐日盯市。其 `cross_order()` 以 OHLC Bar 模拟成交：

- 限价委托先转为 `NOTTRADED`；
- 合法触价后转为 `ALLTRADED`；
- 以开盘价与委托价取较优价成交；
- 以 10% 涨跌停检查排除整日一字板成交；
- 计算 turnover、双边费率、交易与持有盈亏。

这说明回测不是单纯 `signal * return`，但仍是 Bar 级模拟。它没有自动证明撮合规则等同于具体市场、券商和标的的真实执行。

`vnpy.alpha` 的测试还覆盖 Alpha101 表达式在 NaN、零成交量和极小价格下的计算，以及 DataProxy 算术与比较运算。它的因子表达式应视为受信研究 DSL，不应直接暴露给 Agent 或远端用户。

## 4. 工程资产与缺口

### 可复用资产

- 统一事件和交易对象。
- Gateway 回补和账户/订单状态同步要求。
- 活动委托与成交拆分。
- 合约 size、tick、手续费进入回测配置。
- 本地 Parquet 研究工作区和多标的日度 PnL。

### 必须自行补齐

1. 事件可靠性：核心 EventEngine 是单进程内存队列，没有事件序号、持久化、重放或跨进程确认。
2. 动作门禁：Gateway 侧未承载本项目所需的 OAuth/scope、idempotency key、人工确认、paper-only 和 kill switch。
3. 审计和对账：OMS 的内存 cache 不是不可变 ledger；必须周期性回补 broker 状态并记录差异。
4. 股票市场规则：T+1、最小交易单位、停牌、除权除息、涨跌停、融资融券和实际费率要由市场 adapter 与回测数据契约共同定义。
5. 外部扩展：paper account、risk manager 和具体券商 Gateway 是另包；采用前应固定包版本、依赖、测试和实盘权限模型。

## 5. 落地建议

当前阶段只借鉴 vn.py 的事件和订单状态模型，不接入真实 Gateway。先在 Phase 5 或 Phase 6 增加：

- `OrderIntent`、`OrderState`、`Fill`、`ReconciliationRecord` 契约；
- 只读订单查询和 paper broker adapter；
- RebalancePlan 到离散订单的显式转换；
- 服务端 ActionGuard、审批和审计 envelope；
- 每日 broker/account/position/order/trade 对账。

等这些前置完成后，再评估 `vn.py` Gateway 或 paper account 扩展的具体适配。
