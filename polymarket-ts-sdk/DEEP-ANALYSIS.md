# polymarket-ts-sdk 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/ts-sdk
> 分析基线：
> - `polymarket-ts-sdk`：commit `1a7d1e2bffe40462ec63237ec2976e083e610e14`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-ts-sdk`
<!-- source-sync:end -->


## 系统边界

项目是 SDK workspace，不是 Polymarket 后端。核心代码集中在 `packages/client/src`，`packages/types` 提供共享类型，`packages/bindings` 保存内部生成 API binding；examples 和 integration tests 不属于默认发布包。

## 关键模块

- `packages/client/src/clients.ts`：`BasePublicClient`、`PublicClient` 等 client 类型和公共请求边界。
- client 内的市场、账户、交易、钱包和流式 API：把 endpoint、解析和错误转换集中在 SDK。
- `packages/bindings`：协议生成代码，避免业务层重复定义 response shape。
- `packages/types`：跨包共享的 market/order/position 等类型。

## 执行流与数据流

```text
application -> public/authenticated client -> generated binding/request
             -> typed response/error -> application state
WebSocket -> client stream adapter -> typed event -> consumer callback
```

SDK 只管理请求和响应，不负责策略、持仓真相、重试队列或审计；工作台需要在 client 外包一层 provider、job、audit 和 reconciliation。

## 契约、状态与持久化

根目录使用 pnpm workspace 和 Changesets；README 明确 generated bindings 不应被直接使用。Perps APIs 标记为实验性，公共 API 版本按 semver 管理但 0.x minor 仍可能破坏兼容。

## 质量、安全、性能与运维

仓库包含 Biome、Vitest、构建配置、CI、Dependabot、SECURITY.md 和 Node 24 约束。此次未安装依赖运行完整 workspace 检查；实施时应执行 `pnpm install`、`pnpm build`，并对真实 API/WebSocket 做 integration fixture。

## 可迁移模式与限制

推荐将此 SDK 作为 HermesAlpha 的 Polymarket connector 基础，保留一层自己的 `ProviderResult`、`MarketSnapshot`、`OrderRecord` 和 `ToolCallEnvelope`。不要让业务代码依赖 generated binding，也不要把 experimental Perps API 混入稳定交易契约。
