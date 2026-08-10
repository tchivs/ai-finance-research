# hummingbot

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/hummingbot/hummingbot
> 分析基线：
> - `hummingbot`：commit `2bfaccc48dd49e71a5b6d9b3011808e127dd00cd`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/hummingbot`
<!-- source-sync:end -->


## 一句话定位

面向加密市场的策略运行与执行框架，把交易所连接器、行情、订单生命周期、做市/套利策略、纸面回测和 Gateway 组合成可部署 bot。

## 核心流程

`HummingbotApplication` 初始化配置、`TradingCore`、CLI/headless 运行模式和连接器；Strategy V2 的 `ControllerBase` 从 market data provider 读取数据，生成 executor actions；`ExecutorBase`/`ExecutorOrchestrator` 管理 position、DCA、grid、TWAP、arbitrage 等订单生命周期，connector 负责 REST/WebSocket 与交易所交互。

## 最值得借鉴的设计

1. Controller 与 Executor 分层：控制器决定策略动作，executor 负责可恢复的订单过程，降低策略代码直接管理订单的复杂度。
2. 连接器统一：CLOB CEX、CLOB DEX 和 AMM DEX 使用不同 connector/Gateway 边界，上层策略保留统一的交易对、订单和状态接口。
3. Headless 与 UI 分离：`HummingbotApplication` 根据 `headless_mode` 选择 CLI 组件，适合拆出 worker 和管理面。

## 限制

它是交易 bot/runtime，不是完整的跨市场研究、数据湖或组合风控系统；连接器和策略状态仍需外部审计、持久化和密钥隔离。生产接入应从 paper 模式开始，不能把 bot 的本地配置、钱包或 API key 直接暴露给 Agent。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
