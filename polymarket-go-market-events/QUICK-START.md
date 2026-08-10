# polymarket-go-market-events

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/go-market-events
> 分析基线：
> - `polymarket-go-market-events`：commit `37c69d8672bc8ebea7508ccfbfcf11bbf64b7f45`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-go-market-events`
<!-- source-sync:end -->


## 一句话定位

Go 链上事件 watcher，连接 Polygon RPC，监听 Conditional Tokens 和 Optimistic Oracle 事件，为市场状态、条件和解析过程提供低层事件入口。

## 核心流程

`main.go` 建立 ethclient 并启动 propose price、dispute price、condition resolution 等监听；generated Go bindings 通过 filter/watch/parse API 解码合约日志。

## 最值得借鉴的设计

1. generated contract bindings 与 watcher 逻辑分离。
2. `constants` 集中 chain id、合约地址和 topic；`chainconfig` 按链配置 RPC/合约。
3. 事件监听适合作为轻量实时 ingestion worker，而不是同步查询 API。

## 限制

仓库主要是示例/底层 watcher，未看到完整持久化、断点续传、reorg 处理或消息总线；不能直接作为生产 indexer。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
