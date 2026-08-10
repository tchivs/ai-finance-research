# polymarket-poly-market-maker

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/poly-market-maker
> 分析基线：
> - `polymarket-poly-market-maker`：commit `55b83499ffc81bbd6b7c15c40ff9179b5e3d323c`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-poly-market-maker`
<!-- source-sync:end -->


## 一句话定位

实验性 Python CLOB 做市 keeper，以 midpoint 为基准，用 Bands 或 AMM 策略计算挂单，持续比较 open orders、撤单和补单。

## 核心流程

每个 `sync_interval` 获取 midpoint，策略生成期望订单，OrderBookManager 计算撤单/新单，先撤旧单再挂新单；SIGTERM 时取消全部订单并退出。

## 最值得借鉴的设计

1. `BaseStrategy`、`BandsStrategy`、`AMMStrategy` 将策略和订单管理分离。
2. OrderBookManager 维护订单状态，并将取消/下单放入后台线程。
3. Docker Compose、config file、metrics 和测试为长运行 keeper 提供最小运行框架。

## 限制

README 明确标注 experimental；仓库基线较旧，策略假设、CLOB API 和依赖需重新验证。不能直接用于实盘，必须增加 kill switch、库存风险、断线恢复和人工门禁。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
