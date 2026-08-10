# polymarket-neg-risk-ctf-adapter 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/neg-risk-ctf-adapter
> 分析基线：
> - `polymarket-neg-risk-ctf-adapter`：commit `f78b35b0863b4308a431ca307d06f49b2ea65e78`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-neg-risk-ctf-adapter`
<!-- source-sync:end -->


## 系统边界

核心合约包括 `NegRiskAdapter.sol`、`NegRiskOperator.sol`、`NegRiskCtfExchange.sol`、`WrappedCollateral.sol`、`Vault.sol` 和 `NegRiskFeeModule.sol`，使用 Conditional Tokens/UMA 接口并通过 Foundry 管理。

## 关键模块

- `NegRiskOperator`：管理员准备 market/question，并绑定 oracle request。
- `NegRiskAdapter`：维护互斥二元问题、转换 NO/YES、报告 outcome 和赎回。
- `MarketDataManager`：市场、问题和 token 关系的链上数据管理。
- `WrappedCollateral` / `Vault`：把 USDC 包装为可由 adapter 管理的抵押物，并处理费用。
- `NegRiskCtfExchange`：多结果市场交易路径和接口。

## 执行流与数据流

```text
prepare questions -> one multi-outcome market -> split/convert positions
-> UMA resolution -> report outcome -> redeem/settle collateral
```

工作台必须保存 event id、market id、question id、outcome index、token id、wrapped collateral 和 resolution record，不能只保存 YES/NO 文本。

## 契约、状态与持久化

README 明确要求不能出现 tie，也不能所有 question 都为 false；`addresses.json`、foundry snapshots、ABI artifacts 和 docs 构成部署/测试证据。链上状态才是真相，缓存只作为查询加速。

## 质量、安全、性能与运维

仓库有 Integration、MarketData、Operator、Vault、WrappedCollateral 测试和 audit PDF；当前未运行 forge。需要重点验证 oracle 返回 `[1,1]`、重复 true、全 false、费用、转换精度和跨版本 adapter。

## 可迁移模式与限制

可迁移的是显式多结果约束、position conversion 和 collateral vault；不应把 NegRisk 逻辑隐藏在通用概率服务中，必须作为独立 `PredictionMarketSettlement` 模块接入。
