# polymarket-py-clob-client-v2 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/py-clob-client-v2
> 分析基线：
> - `polymarket-py-clob-client-v2`：commit `215fc63a8fd6ec3a10c7edb73997c9772d8686d3`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-py-clob-client-v2`
<!-- source-sync:end -->


## 系统边界

源码位于 `py_clob_client_v2/`，以 `ClobClient` 为同步 API 入口；依赖 `httpx`、`eth-account`、`poly_eip712_structs` 和订单工具包。项目不包含数据库、后台队列或 WebSocket 运行时。

## 关键模块

- `ClobClient.create_or_derive_api_key`：L1 钱包凭证流程。
- `create_and_post_order`：订单参数、tick size、订单类型、签名和提交的组合入口。
- `get_order_book` / `get_order_books`：单个和批量 order book 查询。
- `clob_types.py`：`OrderArgs`、`MarketOrderArgs`、`OrderType`、`Side` 等类型契约。
- `signer.py`、`fees.py`、`utilities.py`：签名、费用、金额和响应处理。

## 执行流与数据流

```text
OrderArgs -> create_order -> EIP-712 signature -> L2 request -> REST response
token_id -> GET order book -> OrderBookSummary -> hash/price analysis
order hash -> cancel/cancel_all/cancel_market_orders
```

源码同时暴露批量 order book、RFQ 相关端点和市场订单接口；工作台应把返回结果转成统一 `ProviderResult` 与 `OrderRecord`，而不是将 SDK response 直接暴露给 UI。

## 契约、状态与持久化

L1 依赖 `key`，L2 依赖 API key/secret/passphrase。订单状态仍由 CLOB 和链上事件共同决定，客户端只负责请求；本地必须保存 client order id、订单 hash、提交时间、市场参数版本和最终 reconciliation 状态。

## 质量、安全、性能与运维

仓库有 pytest 用例，覆盖 fee cache、market params、order adjustment、post-order resolution 和 utilities；未在当前环境安装其 Python 依赖执行。需要补充 provider timeout、重复提交、部分成交、撤单竞态和 API version 变化测试。

## 可迁移模式与限制

可迁移的是类型化订单契约、市场参数显式传入、费用缓存测试和 REST 错误处理。新项目优先使用 `polymarket-py-sdk`，此仓库保留为低层 CLOB 兼容和订单签名参考。
