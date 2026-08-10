# vectorbt

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/polakowo/vectorbt
> 分析基线：
> - `vectorbt`：commit `34b6d5935e3ea3eccd549e2592bc0f455b8045f5`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/vectorbt`
<!-- source-sync:end -->


## 一句话定位

以 NumPy/pandas 广播、Numba 和可选 Rust 引擎为核心的矩阵化回测与策略实验库，擅长一次性扫描大量参数、资产和信号组合。

## 核心流程

指标由 `IndicatorFactory` 生成或组合，信号进入 `Portfolio.from_signals`，显式订单进入 `Portfolio.from_orders`；portfolio 将广播后的价格、信号、费用和滑点推进为 orders、trades、drawdowns 和统计结果，`Records` 负责结构化记录与分析。

## 最值得借鉴的设计

1. 广播式实验：同一个数组承载资产、参数和时间维度，适合因子/参数网格实验。
2. Portfolio 与 Records 解耦：`vectorbt/portfolio/base.py` 负责仿真，`records/base.py` 负责订单、交易和统计数据的统一访问。
3. 热路径可替换：Numba 与 `vectorbt-rust` 将计算加速隐藏在 Python API 后，适合作为研究 worker 的可选优化。

## 限制

矩阵化回测不是实时 OMS、事件总线或订单执行器；盘口队列、断线重连、订单回报和跨 venue 状态需要另建运行时。README 标注社区版为 Fair Code，商业集成前必须单独审查许可证和 Pro 版边界。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
