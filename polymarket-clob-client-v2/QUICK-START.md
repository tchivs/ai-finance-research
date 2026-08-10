# polymarket-clob-client-v2

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/clob-client-v2
> 分析基线：
> - `polymarket-clob-client-v2`：commit `f3e1a05f868a1fd0c34ef85dfc45c6ce78f5bb69`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-clob-client-v2`
<!-- source-sync:end -->


## 一句话定位

官方 TypeScript CLOB v2 客户端，封装 L1 钱包签名、L2 HMAC 请求头、订单构造、订单簿、成交和撤单；README 已提示新项目优先使用统一 `ts-sdk`。

## 核心流程

`ClobClient` 先用钱包完成 L1 API key 创建/派生，再用 API credentials 生成 L2 请求；`createAndPostOrder` 组合订单构造、签名和提交，并按 tick size、订单类型和市场选项处理参数。

## 最值得借鉴的设计

1. L1/L2 认证分层，避免把钱包签名和 API 请求签名混成一个凭证。
2. `order-builder`、`order-utils`、`signing`、`fees` 分包，便于将确定性订单逻辑独立测试。
3. 公共行情和账户写操作共用客户端，但通过端点和 headers 明确权限边界。

## 限制

这是 v2 专用客户端，README 明确推荐新项目使用统一 `ts-sdk`；不能将示例中的私钥、API secret 或 funder 地址放入前端或 Agent 上下文。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
