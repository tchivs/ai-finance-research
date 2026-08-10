# polymarket-poly-market-maker 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/poly-market-maker
> 分析基线：
> - `polymarket-poly-market-maker`：commit `55b83499ffc81bbd6b7c15c40ff9179b5e3d323c`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-poly-market-maker`
<!-- source-sync:end -->


## 系统边界

入口是 `poly_market_maker/app.py`，CLOB 接口在 `clob_api.py`，订单状态在 `orderbook.py`，策略在 `strategies/` 和 `strategy.py`，配置位于 `config/`。它是单进程 keeper，不包含持久化数据库或分布式协调。

## 关键模块

- `App.synchronize`：周期性协调市场、策略和订单簿。
- `OrderBookManager`：维护 active orders/balances、取消/下单中的状态和线程池。
- `BaseStrategy`、`BandsStrategy`、`AMMStrategy`：根据 midpoint/token prices 生成目标 orders。
- `ClobApi`：封装下单、撤单、余额和 API latency metrics。
- `lifecycle.py`、`gas.py`、`price_feed.py`：进程生命周期、gas 和价格输入。

## 执行流与数据流

```text
refresh orderbook/balances -> strategy.synchronize
-> orders_to_cancel + orders_to_place -> background cancel/place
-> wait for stable orderbook -> next sync
```

`OrderBookManager` 对取消和下单使用线程池并维护 cancelling/placing 集合；这提供了并发执行雏形，但必须在外层增加 operation id、幂等和 crash recovery。

## 契约、状态与持久化

配置通过 `CONDITION_ID`、`STRATEGY`、`CONFIG` 选择市场和策略，Bands/AMM 配置为 JSON。当前订单簿状态只在内存，SIGTERM 清理依赖进程正常退出。

## 质量、安全、性能与运维

仓库有 pytest 覆盖 AMM、Bands、order type、market、lifecycle、price feed 和 utils，并提供 Dockerfile/Compose；未安装依赖运行测试。生产必须补充强制 cancel-all、断线重启、库存上限、最大订单量、订单回报 reconciliation 和 kill switch。

## 可迁移模式与限制

可迁移的是目标订单与当前订单差异计算、策略插件和 graceful shutdown。不要直接复制线程模型到分布式系统；新工作台应把 strategy intent 发到 execution service，由单一 per-account actor 串行化副作用。
