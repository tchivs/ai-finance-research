# polymarket-py-sdk

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/py-sdk
> 分析基线：
> - `polymarket-py-sdk`：commit `974d2e22ca92445d8ab7ecd7715a247f1ea7d65a`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-py-sdk`
<!-- source-sync:end -->


## 一句话定位

Polymarket 官方 Python 统一 SDK，提供同步/异步 public client，并把市场、账户、交易、builder attribution、钱包、位置合并和流式能力组织成工作流 API。

## 核心流程

`PublicClient` / `AsyncPublicClient` 负责市场和公开数据；认证 client 承载账户、交易和钱包操作；batch position 操作用 handle 返回，再通过 `wait()` 取得终态。

## 最值得借鉴的设计

1. 同步和异步接口共享领域模型，适合同时支持研究脚本和后台 worker。
2. 批量链上操作返回可等待 handle，避免把长操作绑在同步 HTTP 请求上。
3. `uv.lock`、Makefile、release-please 和 SDK direction 文档形成依赖与 API 演进边界。

## 限制

仓库中 `unit` 测试量较大，但 integration tests 被索引排除；Perps API 仍是实验性能力。SDK 不替代自己的数据版本、任务和审计存储。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
