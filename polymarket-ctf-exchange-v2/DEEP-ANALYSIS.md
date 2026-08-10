# polymarket-ctf-exchange-v2 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/ctf-exchange-v2
> 分析基线：
> - `polymarket-ctf-exchange-v2`：commit `ccc0596074f4dfd62c944fbca4de252893b82b4b`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-ctf-exchange-v2`
<!-- source-sync:end -->


## 系统边界

核心入口是 `src/exchange/CTFExchange.sol`，以 `Trading` 为主业务 mixin，依赖 Conditional Tokens、PMCT collateral 和 proxy/safe wallet 工厂。仓库使用 Foundry，包含大量 Solidity 测试、gas snapshot、audit 报告和部署地址。

## 关键模块

- `CTFExchange.matchOrders`：统一撮合入口；V2 移除 `fillOrder/fillOrders`。
- `Trading`：order status、签名验证、match type、complementary/mint/merge 结算。
- `Hashing` / `Signatures`：EIP-712、EOA、proxy、Gnosis Safe、EIP-1271。
- `AssetOperations` / collateral adapters：ERC20/ERC1155 transfer、CTF split/merge/redeem。
- `Fees`、`Pausable`、`UserPausable`、`Auth`：费用和紧急控制。

## 执行流与数据流

```text
signed orders -> operator matchOrders -> validate -> derive match type
-> complementary transfer | CTF mint | CTF merge -> OrderFilled/OrdersMatched/FeeCharged
```

V2 对多 maker mint/merge 汇总 CTF 操作，降低重复 split/merge；链下系统需监听事件重建成交、费用和持仓，而不能只记录提交请求。

## 契约、状态与持久化

`OrderStatus` 记录 filled 和 remaining；订单 hash 是主索引。新增 builder/metadata、max fee rate、self-pause block interval 和 PMCT wrapper 改变了工作台的订单/结算契约。

## 质量、安全、性能与运维

Foundry 配置使用 solc 0.8.34、optimizer runs 1,000,000、fuzz runs 256，并有 intensive profile；README 列出 Quantstamp/Cantina 审计。实施时必须固定部署地址、chain id、ABI、合约版本和 gas snapshot，不能把审计报告等同于当前部署安全证明。

## 可迁移模式与限制

可迁移的是订单状态、事件驱动对账、暂停和职责分层。不要在应用层重写合约撮合数学；执行服务应只生成签名订单、提交 operator API，并以链上事件确认最终状态。
