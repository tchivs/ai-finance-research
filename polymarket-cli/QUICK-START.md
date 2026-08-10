# polymarket-cli

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/polymarket-cli
> 分析基线：
> - `polymarket-cli`：commit `9b18b5faf5493b945c48ca22efaf9645f0c69ab8`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-cli`
<!-- source-sync:end -->


## 一句话定位

Rust 命令行工作台，提供市场浏览、JSON 输出、订单、持仓、钱包和链上 CTF 操作，既可供人使用，也可作为 Agent/脚本的结构化入口。

## 核心流程

`main.rs` 分发命令，`commands/` 组织市场和 CLOB 操作，`config/` 与 `auth/` 处理钱包和配置，输出层支持 human/JSON。公开查询不需要钱包，交易和链上操作才进入签名边界。

## 最值得借鉴的设计

1. `-o json` 将 CLI 变成可审计的 Agent 数据入口。
2. `proxy`、`eoa`、`gnosis-safe` 签名类型显式配置。
3. 公开查询与高风险钱包动作在命令层区分，适合接入 Skill Gateway。

## 限制

README 明确标注 early/experimental；默认配置包含本地私钥文件路径，不能直接复制到多租户服务或 Agent runtime。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
