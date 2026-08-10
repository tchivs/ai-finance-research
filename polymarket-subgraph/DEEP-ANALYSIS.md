# polymarket-subgraph 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/polymarket-subgraph
> 分析基线：
> - `polymarket-subgraph`：commit `7a92ba026a9466c07381e0d245a323ba23ee8701`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-subgraph`
<!-- source-sync:end -->


## 系统边界

仓库是多个 The Graph subgraph 的 manifest、ABI、schema 和 AssemblyScript mapping 集合。README 列出 activity、fpmm、oi、orderbook、pnl、polymarket、sports-oracle 等子图，并提供 Docker 本地 graph-node 环境。

## 关键模块

- `activity-subgraph/src/ConditionalTokensMapping.ts`：Condition、Split、Merge、Redemption、Position。
- `activity-subgraph/src/NegRiskAdapterMapping.ts`：NegRiskConversion、NegRiskEvent 和相关事件。
- `oi-subgraph`：从 split/merge/redemption 计算 market/global open interest。
- `fpmm-subgraph`：FPMM 创建、funding、buy/sell 和 pool share。
- `networks.yaml`：Polygon/matic 的合约地址和 start block。
- `abis/`、`subgraph.template.yaml`：事件签名与部署模板。

## 执行流与数据流

```text
Polygon logs -> graph-node mapping -> entity store -> GraphQL query
```

部署前运行 templatify 和 codegen；本地通过 yarn create/deploy-local 写入 graph-node/Postgres/IPFS。工作台可把 subgraph 作为历史链上数据 provider，再与 CLOB order/trade 数据按 condition_id、token_id 和 transaction hash 对账。

## 契约、状态与持久化

实体 schema 是 GraphQL 数据契约；manifest 显式绑定事件 handler、ABI、network 和 start block。它记录链上派生事实，不提供用户私有订单和钱包密钥，也不应被视为实时撮合状态的唯一来源。

## 质量、安全、性能与运维

仓库有 Matchstick 配置、Docker compose、codegen 和子图测试目录；未在当前环境运行 yarn/docker 测试。必须监控 RPC 延迟、索引区块、reorg、grafting、schema 迁移和实体重复计算。

## 可迁移模式与限制

可迁移的是按领域拆分索引、ABI/地址配置化和从事件重建派生表。生产工作台不应直接复制旧 manifest；新增或变更合约地址必须经过 deployment ADR、回放窗口和与 CLOB 数据的 reconciliation。
