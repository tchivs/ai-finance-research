# polymarket-real-time-data-client

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/real-time-data-client
> 分析基线：
> - `polymarket-real-time-data-client`：commit `c937d9c11cdd2b771aa4818392a1b6dda65c25de`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-real-time-data-client`
<!-- source-sync:end -->


## 一句话定位

TypeScript WebSocket 客户端，封装 Polymarket real-time data streaming 服务，支持活动、评论、加密价格、美股价格和 CLOB 用户消息订阅。

## 核心流程

创建 `RealTimeDataClient`，通过 `onConnect` 调用 `subscribe`，以 topic/type/filter 订阅消息；消息通过 `onMessage` 交给上层，连接可重复订阅/取消订阅并显式 disconnect。

## 最值得借鉴的设计

1. topic/type/filter 形成结构化订阅契约。
2. 一个连接支持多类消息，适合工作台统一事件流。
3. `model.ts` 对 Trade、Comment、Reaction、CryptoPrice、EquityPrice 等消息建模。

## 限制

该仓库只解决 WebSocket client 和消息模型，不是 CLOB orderbook snapshot/replay 服务；重连、去重、断点续传和落盘需要由工作台补充。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
