# polymarket-uma-ctf-adapter 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/uma-ctf-adapter
> 分析基线：
> - `polymarket-uma-ctf-adapter`：commit `8b76cc9e0d46c6f7450a0adb0ddc0f5b0568c9cc`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-uma-ctf-adapter`
<!-- source-sync:end -->


## 系统边界

主合约是 `src/UmaCtfAdapter.sol`，接口、认证、公告板、辅助数据、payout 和 transfer 逻辑拆分到 `interfaces/`、`mixins/`、`libraries/`；Foundry 测试位于 `src/test/`。

## 关键模块

- 初始化：保存 ancillary data、request timestamp、reward token/reward，并 prepare CTF condition。
- UMA request：向 Optimistic Oracle 发起价格/结果请求。
- dispute/reset：首次争议可重置请求，后续争议进入 UMA DVM 流程。
- `resolve`：在结果可用后写入 Conditional Tokens payout。
- `AncillaryDataLib` / `PayoutHelperLib`：解析数据和 outcome 转 payout。

## 执行流与数据流

```text
initialize -> CTF prepare + UMA request -> propose -> liveness/dispute
-> reset or DVM -> resolve -> payout denominator/numerators -> redeem
```

resolution-subgraph 和 Go watcher 可监听上述生命周期，工作台应把 question id、request id、oracle state、block 和 transaction 统一到 `ResolutionRecord`。

## 契约、状态与持久化

状态在链上合约中保存，离线系统只能建立索引和缓存；审计目录包含报告，deployments 以 releases/地址为准。时间窗口和 oracle version 必须进入回测与结算模型。

## 质量、安全、性能与运维

README 要求 Foundry `forge build`/`forge test`，且包含 OpenZeppelin audit；当前未运行 forge。部署前必须验证 submodule、solc 版本、chain address、oracle finder 和 liveness 参数。

## 可迁移模式与限制

可迁移的是显式 resolution state machine 和 oracle adapter 边界；不要在应用层复制 payout 计算或假设 resolve 是即时的。任何结算动作必须由链上事件确认。
