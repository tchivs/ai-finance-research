# polymarket-ts-sdk

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/ts-sdk
> 分析基线：
> - `polymarket-ts-sdk`：commit `1a7d1e2bffe40462ec63237ec2976e083e610e14`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-ts-sdk`
<!-- source-sync:end -->


## 一句话定位

Polymarket 官方统一 TypeScript SDK，以 pnpm workspace 组织 client、共享 types 和内部生成 bindings，整合 REST、WebSocket、账户、交易、钱包和实验性 Perps 能力。

## 核心流程

应用通过 `packages/client` 的 public/authenticated workflow client 查询市场、账户和交易；API bindings 提供生成的协议层，`packages/types` 对外提供共享类型，examples 展示实际调用路径。

## 最值得借鉴的设计

1. 将多种 API 统一到 workflow-oriented client，而不是让业务直接拼 URL。
2. `types`、`bindings`、`client` 分层，generated bindings 不作为直接公共 API。
3. pnpm workspace、Changesets 和 trusted publishing 为多包 SDK 提供版本治理。

## 限制

README 标注 Node.js >=24、pnpm >=10，Perps API 仍为 experimental；集成测试目录被源码索引排除，真实网络行为需要单独验证。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
