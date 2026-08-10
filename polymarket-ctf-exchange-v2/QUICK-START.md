# polymarket-ctf-exchange-v2

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/ctf-exchange-v2
> 分析基线：
> - `polymarket-ctf-exchange-v2`：commit `ccc0596074f4dfd62c944fbca4de252893b82b4b`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-ctf-exchange-v2`
<!-- source-sync:end -->


## 一句话定位

Polymarket CTF Exchange V2 Solidity 合约，负责订单验证、匹配、签名、费用、CTF split/merge、PMCT collateral 和用户/全局暂停。

## 核心流程

用户离线签署 EIP-712 order，operator 调用 `matchOrders`；合约验证 maker/taker、价格和 token，再按 complementary、mint 或 merge 路径结算。

## 最值得借鉴的设计

1. `CTFExchange` 通过 mixin 组合 Auth、Trading、Hashing、Assets、Fees、Signatures、Pausable。
2. V2 用订单状态替代 nonce manager，并支持 order preapproval 与 user self-pause。
3. 批量 mint/merge、packed order status 和 assembly event emission 优化高负载路径。

## 限制

这是链上结算合约，不是撮合服务或订单簿；权限、operator、费用、合约地址和升级部署必须独立审计，不能仅凭 SDK response 判定成交。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
