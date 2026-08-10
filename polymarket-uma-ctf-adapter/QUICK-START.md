# polymarket-uma-ctf-adapter

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/uma-ctf-adapter
> 分析基线：
> - `polymarket-uma-ctf-adapter`：commit `8b76cc9e0d46c6f7450a0adb0ddc0f5b0568c9cc`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-uma-ctf-adapter`
<!-- source-sync:end -->


## 一句话定位

Solidity resolution adapter，把 Polymarket CTF condition 接入 UMA Optimistic Oracle，负责初始化问题、请求解析、争议重置和最终 payout。

## 核心流程

市场初始化时保存 ancillary data 等参数、prepare CTF condition 并向 UMA 发起请求；未争议时等待 liveness，争议时 reset，最终由任何人调用 `resolve` 写入 payout。

## 最值得借鉴的设计

1. oracle 与 Conditional Tokens 之间使用明确 adapter 边界。
2. dispute/reset/DVM 路径被建模为解析状态，而不是简单的布尔结果。
3. 接口、libraries、mixins 和 Foundry tests 分层，便于审计和版本演进。

## 限制

解析依赖 UMA 的 proposer、争议和 DVM 时间窗口；不能把市场 close、oracle resolved 和用户可赎回视为同一个时间点。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
