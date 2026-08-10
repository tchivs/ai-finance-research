# polymarket-clob-client-v2 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/clob-client-v2
> 分析基线：
> - `polymarket-clob-client-v2`：commit `f3e1a05f868a1fd0c34ef85dfc45c6ce78f5bb69`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-clob-client-v2`
<!-- source-sync:end -->


## 系统边界

源码主要是 TypeScript SDK，不包含服务端订单撮合、数据库或持久化状态。入口是 `src/client.ts`，配置、端点、错误、headers、签名、订单工具和费用分别位于 `src/` 下的独立模块。

## 关键模块

- `ClobClient.createOrDeriveApiKey`：L1 钱包签名换取/派生 API credentials。
- `ClobClient.createAndPostOrder`：调用 `createOrder`、订单工具和 `postOrder`，返回 `OrderResponse`。
- `getOrderBook` / `getOrderBooks`：读取单个或批量 token order book。
- `cancelOrder` / `cancelOrders`：构造 L2 headers 后调用 DELETE 端点。
- `order-builder`、`signing`、`order-utils`：负责订单结构、EIP-712 签名和地址/金额处理。

## 执行流与数据流

```text
user order -> order builder -> EIP-712 signer -> L2 headers -> CLOB REST
market query -> public endpoint -> typed response
cancel -> order hash/payload -> L2 DELETE request
```

`createAndPostOrder` 的调用图包含订单构造、重试版本更新、post order 和错误处理；客户端本身不记录订单生命周期，工作台必须在外部保存 request、order hash、响应和幂等键。

## 契约、状态与持久化

README 明确了 GTC、FOK、FAK、GTD、post-only 等订单语义，`tickSize` 和 `negRisk` 是下单前的市场参数。L1 凭证为 key/secret/passphrase，L2 使用 HMAC；客户端只负责传递和使用，凭证托管应由上层服务完成。

## 质量、安全、性能与运维

仓库包含 Vitest 配置、Biome、husky 和 `.env.example`；未运行依赖安装后的完整测试。批量 order book 和订单接口适合由后端 worker 调用，前端只接收脱敏结果。需要为超时、401/403、tick size 变化、订单重复提交和撤单失败增加集成测试。

## 可迁移模式与限制

可迁移的是 L1/L2 认证边界、订单构造分层、错误对象和端点目录；不要直接把该客户端当作完整 execution service。新系统应优先评估 `polymarket-ts-sdk`，v2 客户端作为兼容层和签名细节参考。
