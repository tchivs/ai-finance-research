# vn.py（VeighNa）快速概览

> 原始仓库: <https://github.com/vnpy/vnpy>
> 分析基线：`vnpy/vnpy` commit `1b78494979deb4c4996f6b864f234d9839f2f239`（2026-05-17），MIT，Python >= 3.10。本文只核对核心仓库；具体交易 Gateway、risk manager、paper account 等多为独立扩展包，需逐项固定版本和复核。

## 一句话定位

vn.py 是中国市场生态中成熟的事件驱动量化交易框架。它定义行情、订单、成交、持仓和账户的统一对象，通过 Gateway 归一化不同券商或数据服务，再由 OMS 管理运行态；新版 `vnpy.alpha` 增加本地多因子研究、模型训练和组合回测能力。

它适合作为未来受控执行层、订单生命周期和事件模型的参考，而不是当前 Agent 直接下单的依赖。

## 核心结构

```text
Gateway adapter
  -> EventEngine queue
  -> OmsEngine cache and order conversion
  -> strategy/app/UI
  -> external broker or paper-account extension
```

| 目标 | 入口 | 可迁移价值 |
|------|------|------------|
| 事件循环 | `vnpy/event/engine.py` | 类型化事件队列、timer、专用与通用 handler |
| 运行时装配 | `vnpy/trader/engine.py` | MainEngine 注册 Gateway、App、OMS、日志和通知 |
| Gateway 契约 | `vnpy/trader/gateway.py` | connect、订阅、下单、撤单、账户/持仓回补的统一协议 |
| 核心对象 | `vnpy/trader/object.py` | Tick/Bar/Order/Trade/Position/Account 与全局唯一 ID |
| 因子研究 | `vnpy/alpha/` | Parquet 数据、因子表达式、模型、信号与组合回测 |

## 已验证的重要边界

- Gateway 在 `connect()` 后必须主动回补 contract、account、position、order、trade；不能假设重连后内存状态仍然准确。
- `OrderData` 与 `TradeData` 分离，一个 order 可产生多个 fill；`vt_orderid` 和 `vt_tradeid` 都包含 Gateway 命名空间。
- OMS 只维护内存态的缓存和 active order 集合，不等同于持久化审计、幂等服务或对账系统。
- `BaseGateway` 的 thread-safe、非阻塞、断线重连要求是接口契约；实际是否做到取决于每个具体 Gateway 实现。
- `vnpy.alpha` 回测明确模拟手续费、合约 size、价格跳动、涨跌停和暂停填充，但这不自动覆盖 A 股 T+1、股票最小交易单位、公司行为和每家券商的订单语义。

## 可直接吸收的模式

1. 统一的领域对象先于券商 adapter：所有上游最终映射为 `OrderRequest`、`OrderData`、`TradeData`、`PositionData`、`AccountData`。
2. Gateway 连接后先恢复账户、仓位、委托和成交，再允许系统推导新动作。
3. 把“订单请求”与“订单状态更新”分开；UI 和 Agent 不能把请求成功误认作成交成功。
4. 以 `(gateway, local id)` 构造全局标识，避免跨券商、模拟盘和真实盘冲突。
5. 研究信号和订单执行之间需要独立的 target-weight/rebalance/action guard 层，不能直接从 Agent 文本生成 `OrderRequest`。

## 不应直接照搬

- MainEngine、OMS 与 EventEngine 是进程内状态，没有事务、跨实例 lease、持久化 job state 或调用幂等键。
- 核心仓库不是完整 A 股现货交易产品；券商 Gateway、risk manager、paper account、策略 App 大量分布在独立包，版本兼容与真实语义必须单独验证。
- `vnpy.alpha` 的因子表达式面向本地受信研究者。上游文档明确不应把 Web 请求、远程配置或其他不可信输入直接作为表达式执行。
- 事件框架可作为执行适配器，但高风险动作仍必须经过本项目的服务端 `ActionGuard`、审批、审计、kill switch 和 fail-closed 存储。

## 推荐阅读顺序

1. [DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
2. [策略与信号系统](../07-策略与信号系统篇.md)
3. [工程治理](../06-工程治理篇.md)
4. [模式决策矩阵](../18-模式决策矩阵.md)
