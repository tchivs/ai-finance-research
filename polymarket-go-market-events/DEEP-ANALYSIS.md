# polymarket-go-market-events 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/go-market-events
> 分析基线：
> - `polymarket-go-market-events`：commit `37c69d8672bc8ebea7508ccfbfcf11bbf64b7f45`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-go-market-events`
<!-- source-sync:end -->


## 系统边界

入口为 `main.go`，事件接收层在 `watcher/watcher.go`，合约 ABI 绑定在 `contracts/conditional_tokens` 和 `contracts/optimistic_oracle`，常量在 `constants/`。项目使用 Go Ethereum，不提供 API 或数据库。

## 关键模块

- `listenProposePriceEvents`、`listenDisputePriceEvents`、`listenConditionResolutionEvents`：三类核心监听。
- `watcher`：通过 filterer 建立日志 subscription，并将事件解码为 Go 类型。
- generated bindings：支持 `Watch*`、`Filter*`、`Parse*`、`GetConditionId`、`RedeemPositions` 等调用。
- `constants.CHAIN_ID` 和 TOPICS：Polygon 配置及事件标识。

## 执行流与数据流

```text
RPC websocket -> contract filterer -> decoded event -> logger/application handler
```

当前应用主要记录/打印事件；接入工作台时应在 handler 后增加 event_id、block hash、log index、reorg marker 和 durable publish。

## 契约、状态与持久化

事件对象来源于 ABI 绑定，条件 ID、question ID、oracle request 和 payout 是连接市场元数据与结算状态的关键字段。仓库没有 offset/数据库模型，断线补偿需用 block range 查询实现。

## 质量、安全、性能与运维

未执行 `go test`；应补充 RPC 断线、重复 subscription、历史补块、reorg、chain id 配错和 event decode 失败测试。RPC URL 和私有 endpoint 必须从配置注入。

## 可迁移模式与限制

适合作为 `chain-event-worker` 的最小 Go 原型；生产版本应输出 Protobuf/JSON 事件到 Redpanda，并由独立 consumer 做索引、对账和告警，而不是让 watcher 直接写业务表。
