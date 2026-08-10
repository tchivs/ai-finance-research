# nautilus-trader

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/nautechsystems/nautilus_trader
> 分析基线：
> - `nautilus-trader`：commit `67551f66236702e2f5c3ec179ac39e83d38402d3`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/nautilus-trader`
<!-- source-sync:end -->


## 一句话定位

Rust 原生的多资产、多场所事件驱动交易引擎，用同一套确定性时间模型连接研究、回测和实时执行，Python 负责策略、配置和编排。

## 核心流程

`TradingNode`/系统控制层装配消息总线、缓存、数据/执行适配器和策略；回测路径由 `BacktestEngine` 注入历史 tick、bar、盘口或自定义数据，实时路径由 venue adapter 发布同类领域事件，策略通过 `MessageBus`、portfolio 和执行 API 消费并产生订单。

## 最值得借鉴的设计

1. 研究到实盘语义一致：`crates/backtest/src/engine.rs` 与 `crates/trading/src/strategy/mod.rs` 将 actor、strategy、数据回放和交易状态放入同一事件模型。
2. Rust 核心、Python 控制面：`python/pyproject.toml` 通过 PyO3 暴露原生模块，保留 Python 生态的策略开发效率。
3. 组合状态独立：`crates/portfolio/src/portfolio.rs` 将账户、持仓、订单和缓存状态集中管理，可作为 paper/live adapter 的边界参考。

## 限制

当前上游明确聚焦单节点回测和实时交易，不负责分布式编排、通用工作台或内置 AI 平台；LGPL-3.0-or-later、Rust/Python 版本和原生扩展构建要求也必须纳入选型。对本项目应复用事件契约和 adapter 边界，不直接把其运行时嵌入浏览器或 Agent。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
