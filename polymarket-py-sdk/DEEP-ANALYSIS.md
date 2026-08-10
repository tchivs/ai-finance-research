# polymarket-py-sdk 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/py-sdk
> 分析基线：
> - `polymarket-py-sdk`：commit `974d2e22ca92445d8ab7ecd7715a247f1ea7d65a`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-py-sdk`
<!-- source-sync:end -->


## 系统边界

源码由 `polymarket/` SDK 包和 `unit/` 测试构成，使用 `pyproject.toml`、`uv.lock` 和 Makefile 管理。SDK 负责 API/链上 workflow，不负责交易策略、数据湖或账户审计。

## 关键模块

- `PublicClient` / `AsyncPublicClient`：公开市场、搜索、价格和市场元数据。
- 认证 client：账户、订单、成交、持仓和钱包 workflow。
- 位置操作：按 condition/market 或 position id 批量 merge，返回可等待 handle。
- examples：`fetch_market.py`、`list_markets.py`、`market_prices.py`、`list_positions.py`、订单和 crypto TWAP 示例。

## 执行流与数据流

```text
client context -> HTTP/stream/chain adapter -> typed model
batch action -> handle -> wait/poll -> terminal outcome
```

同步 client 适合 research CLI，async client 适合 provider worker；统一输出仍应转换为项目自己的 DataContract，以保留 provider、fetch time、raw hash 和 schema version。

## 契约、状态与持久化

SDK API 采用 semver 目标，但 0.x minor 可能有 breaking change。Perps methods、sessions、streams 和 models 标为 experimental。handle 的终态不能只留在进程内，必须由 `JobRecord` 记录。

## 质量、安全、性能与运维

仓库有 `unit` 测试、Makefile `check`、SECURITY.md 和 release-please；未在当前环境执行 `make check`。私钥、API credentials、builder credentials 和 wallet state 应由服务端密钥系统管理。

## 可迁移模式与限制

推荐把 Python SDK 放在 research/data worker；TypeScript SDK 放在产品控制面。两侧通过自有 JSON Schema/Protobuf 对齐，不直接让前端或 Agent 依赖 SDK 内部类名。
