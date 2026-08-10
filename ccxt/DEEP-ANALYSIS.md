# ccxt 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/ccxt/ccxt
> 分析基线：
> - `ccxt`：commit `94b7d0ea4c6ec6e3ccbb3ea891415529230287c3`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/ccxt`
<!-- source-sync:end -->


## 系统边界

CCXT 是连接器和统一 API 层，不是组合、风险、回测或订单对账系统。仓库同时维护 JavaScript/TypeScript、Python、Go、Java、PHP、C# 等语言实现，Python 主体在 `python/ccxt/base`，并通过每个 venue 的实现暴露统一和原生接口。

## 关键模块

`BaseExchange` 是公共生命周期和协议抽象；`describe` 描述 id、urls、has、fees、precision、limits、timeframes 和认证；每个交易所模块覆盖 fetch markets、ticker、order book、OHLCV、balance 和 order 方法；async_support 复制异步语义，WebSocket/Pro 扩展另外处理实时订阅。README 当前明确覆盖 CEX、DEX、Polymarket、Kalshi 等预测市场。

## 执行流与数据流

初始化 exchange -> 设置 apiKey/secret/password 等凭证 -> `describe` 合并 venue metadata -> `load_markets` 拉取、标准化并缓存市场目录 -> 调用 unified `fetch_ohlcv`/ticker/order book -> private 方法完成签名、限频和请求 -> 统一解析为 ticker、OHLCV、order、trade、balance 等模型。统一方法保留 `params` 让上层传递 venue-specific 字段，失败时由 exchange exception hierarchy 区分网络、认证、限频、参数和业务错误。

## 契约、状态与持久化

市场目录、precision/limits、symbol 映射、timeframe、side/type、订单状态和错误分类是最重要的契约。`load_markets` 的缓存既提升效率也引入 stale metadata 风险；公开 API 与私有 API 的权限、签名、nonce、时间同步和 rateLimit 不能由统一模型完全保证。执行侧必须保存 raw request/response hash、exchange order id、client order id 和对账状态。

## 质量、安全、性能与运维

多语言和大量 venue 定义带来生成/同步代码、版本兼容和依赖体量；限频、市场目录缓存、WebSocket 重连和异常映射需要逐 venue 观察。凭证必须放在执行网关，不能写入日志、Notebook 或 Agent。统一 API 的成功只代表请求被规范化，不代表成交或链上结算完成。

## 可迁移模式与限制

可迁移：provider capability registry、市场目录缓存、统一 DTO 加原生扩展、sync/async 对称接口和 per-venue error mapping。不应照搬：把所有交易所强行压成相同结算模型、把 ticker 当作可回放事实、或直接使用私有 API 做实盘。加密货币 adapter 可借鉴 CCXT；Polymarket 仍应优先走官方 `ts-sdk`/`py-sdk` 和 CLOB/CTF 研究出的链路。

本轮基于 commit `94b7d0ea4c6ec6e3ccbb3ea891415529230287c3`、`python/ccxt/base/exchange.py` 及 README 进行静态研究，并建立 codebase-memory 索引；未执行测试、编译或构建。具体交易所能力、预测市场语义和数据/商业条款仍需上线前逐项复核。
