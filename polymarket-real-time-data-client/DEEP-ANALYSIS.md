# polymarket-real-time-data-client 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/real-time-data-client
> 分析基线：
> - `polymarket-real-time-data-client`：commit `c937d9c11cdd2b771aa4818392a1b6dda65c25de`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-real-time-data-client`
<!-- source-sync:end -->


## 系统边界

入口是 `src/client.ts`，模型在 `src/model.ts`，依赖 `ws`/`isomorphic-ws`。项目不包含消息队列、数据库、backfill 或策略计算。

## 关键模块

- `RealTimeDataClient.connect`：建立 streaming WebSocket。
- `subscribe` / `unsubscribe`：管理 topic、type 和 JSON filters。
- `onConnect` / `onMessage`：把连接生命周期交给调用方。
- 模型覆盖 `activity`、`comments`、`crypto_prices`、`crypto_prices_chainlink`、`equity_prices`，以及可认证的 `clob_user`。

## 执行流与数据流

```text
connect -> onConnect -> subscribe -> WebSocket message -> typed Message
```

README 的消息表区分公开 activity/comments/price 与 CLOB user auth；上层应把原始 message 记录到 append-only event log，再异步生成行情快照、告警和 UI SSE。

## 契约、状态与持久化

过滤器按 event_slug、market_slug、parent entity 或 symbol 组织；Trade 包含 asset、conditionId、outcome、price、size、timestamp、transactionHash。客户端没有 offset/sequence 持久化契约，断线恢复需另建。

## 质量、安全、性能与运维

仓库有 Makefile、ESLint、Prettier 和 build 配置；未安装依赖执行完整 build/lint。生产接入需要连接状态、心跳、指数退避、重复消息去重、延迟和丢包指标。

## 可迁移模式与限制

可迁移的是统一订阅描述和类型化事件模型；不要让 UI 直接持有唯一 WebSocket。应由 market-data worker 单连接/分片消费，写入 Redpanda，再由多个查询和监控消费者读取。
