# polymarket-py-clob-client-v2

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/py-clob-client-v2
> 分析基线：
> - `polymarket-py-clob-client-v2`：commit `215fc63a8fd6ec3a10c7edb73997c9772d8686d3`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-py-clob-client-v2`
<!-- source-sync:end -->


## 一句话定位

官方 Python CLOB v2 客户端，提供 Python 版订单构造、L1/L2 认证、订单簿、交易、撤单和费用处理；README 同样建议新项目使用统一 `py-sdk`。

## 核心流程

`ClobClient` 使用钱包私钥创建/派生 API credentials，再调用 `create_and_post_order` 或 market order；市场参数通过 `PartialCreateOrderOptions` 注入 tick size 等约束。

## 最值得借鉴的设计

1. `client.py` 保持流程编排，`clob_types.py`、`signer.py`、`fees.py` 和 `utilities.py` 分离数据与签名逻辑。
2. 测试覆盖费用缓存、市场参数序列化、订单调整和 post-order 解析。
3. Python 版本适合作为研究 worker 的兼容适配器。

## 限制

仍是 v2 CLOB 客户端，不是账户、任务、风控或交易对账服务；私钥和 L2 credentials 必须放在服务端密钥边界。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
