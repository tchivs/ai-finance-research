# polymarket-subgraph

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/polymarket-subgraph
> 分析基线：
> - `polymarket-subgraph`：commit `7a92ba026a9466c07381e0d245a323ba23ee8701`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-subgraph`
<!-- source-sync:end -->


## 一句话定位

官方 The Graph 子图集合，按 activity、FPMM、open interest、order book、PnL、主聚合和 sports oracle 拆分链上事件索引。

## 核心流程

以 Polygon RPC、ABI、network start block 和 subgraph manifest 为输入，AssemblyScript mappings 监听 Conditional Tokens、Exchange、NegRisk、FPMM 等合约事件，生成 GraphQL entity。

## 最值得借鉴的设计

1. 按查询域拆成多个 subgraph，而不是用一个超宽表承载所有链上事实。
2. `networks.yaml`、模板 manifest 和 ABI 让部署地址/起始区块成为显式配置。
3. activity、OI、PnL 等派生视图从链上事件重建，适合回放和审计。

## 限制

它只索引链上事件，不能替代 CLOB REST/WebSocket 的实时盘口；本地部署依赖 graph-node、Postgres、IPFS、Ganache 和 RPC，需单独评估运维成本。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
