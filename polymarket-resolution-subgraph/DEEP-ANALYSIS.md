# polymarket-resolution-subgraph 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/resolution-subgraph
> 分析基线：
> - `polymarket-resolution-subgraph`：commit `75d1818547862a5bd3477ed2e6b16f693d42dab6`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-resolution-subgraph`
<!-- source-sync:end -->


## 系统边界

源码由 `src/*.ts` mappings、`schema.graphql`、多个 ABI、`subgraph.yaml` 和 generated types 组成。它关注 UMA/Polymarket resolution 事件，不管理 CLOB 订单或交易策略。

## 关键模块

- `uma-ctf-adapter.ts`：新 Adapter 的初始化、重置、解析和结算事件。
- `uma-ctf-adapter-old.ts`、`optimistic-oracle-old.ts`：旧合约兼容。
- `optimistic-oracle-v-2.ts`、`managed-oo-v2.ts`：新 Oracle request/propose/dispute 路径。
- `mod-registry.ts`：Moderator 增删和治理信息。
- `schema.graphql`：`MarketResolution`、`AncillaryDataHashToQuestionId`、`Moderator`、`Revision`。

## 执行流与数据流

```text
contract log -> version-specific mapping -> MarketResolution/Revision
             -> GraphQL query -> settlement/research reconciliation
```

`subgraph.yaml` 通过多组 data source 绑定同一套事件语义的不同 ABI；这是处理合约升级和历史迁移的关键边界。

## 契约、状态与持久化

resolution 状态至少包括 initialized、reset、proposed/disputed、resolved、settled；事件时间和链上 block 必须保留。`docker-compose.yaml`、`networks.json` 和 generated schema 形成部署契约。

## 质量、安全、性能与运维

有 qualifier 单元测试和 Graph 生成代码；未运行 yarn test。需验证多版本 ABI、reorg、重复事件、同一 question 的多次 revision 和 resolution 与 CLOB close time 的差异。

## 可迁移模式与限制

应将其接入工作台的 `SettlementEvent`/`ResolutionProvider`，而不是把 `MarketResolution` 直接当作交易信号。任何“已结算”展示都应带 block、transaction 和 oracle source。
