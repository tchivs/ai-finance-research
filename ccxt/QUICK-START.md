# ccxt

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/ccxt/ccxt
> 分析基线：
> - `ccxt`：commit `94b7d0ea4c6ec6e3ccbb3ea891415529230287c3`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/ccxt`
<!-- source-sync:end -->


## 一句话定位

面向 JavaScript/TypeScript、Python、Go、Java、PHP 和 C# 的统一加密交易所与预测市场 API 适配层，覆盖 REST、WebSocket、行情和订单操作。

## 核心流程

应用实例化某个交易所类后，由 `BaseExchange.describe` 提供能力、端点、认证和市场元数据；`load_markets` 获取并缓存统一市场目录，`fetch_ohlcv`、订单簿和 ticker 进入标准数据模型，`create_order` 等统一方法再映射回交易所私有 API。各交易所差异由对应实现和 `params` 保留。

## 最值得借鉴的设计

1. 能力契约：`python/ccxt/base/exchange.py` 的 `describe`/`has` 把支持的 fetch、order、WebSocket 和认证能力显式化。
2. 市场目录缓存：`load_markets` 将 symbol、精度、费用和交易规则集中到运行时 market cache，减少上层重复探测。
3. 多语言一致接口：Python、TypeScript、Go 等实现保持相近的 unified API，适合作为 `crypto-adapter` 的兼容层参考。

## 限制

统一模型不能消除交易所的精度、限频、签名、结算和错误语义；预测市场也不能直接等同于普通 spot/futures。CCXT 适合作为低层连接器，不应替换 Polymarket 官方 CLOB/CTF 结算链路，也不应绕过 provider capability、数据质量和 paper/live 闸门。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
