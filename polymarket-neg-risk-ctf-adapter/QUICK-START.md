# polymarket-neg-risk-ctf-adapter

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/neg-risk-ctf-adapter
> 分析基线：
> - `polymarket-neg-risk-ctf-adapter`：commit `f78b35b0863b4308a431ca307d06f49b2ea65e78`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-neg-risk-ctf-adapter`
<!-- source-sync:end -->


## 一句话定位

Polymarket 多结果 NegRisk 合约，把一组互斥 YES/NO 二元市场组合成一个多结果市场，并支持 NO 转 YES、抵押物和费用管理。

## 核心流程

`NegRiskOperator` 准备问题和市场，`NegRiskAdapter` 管理互斥结果与 token conversion，`WrappedCollateral`/`Vault` 管理抵押物和费用；解析通常接入 `UmaCtfAdapter`。

## 最值得借鉴的设计

1. 将互斥市场关系显式建模，而不是在上层用概率约定拼接。
2. `MarketDataManager`、operator、adapter、vault、fee module 分层。
3. 用 snapshot、integration 和 market data 测试覆盖跨合约状态。

## 限制

合约要求恰好一个结果为真；平局、全 false 或多个 true 都可能导致无法完整结算。它是高风险链上协议，不能仅按普通二元市场处理。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
