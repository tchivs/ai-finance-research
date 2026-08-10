# vectorbt 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/polakowo/vectorbt
> 分析基线：
> - `vectorbt`：commit `34b6d5935e3ea3eccd549e2592bc0f455b8045f5`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/vectorbt`
<!-- source-sync:end -->


## 系统边界

vectorbt 的核心边界是 Python 中的批量研究、矩阵化仿真和结果分析。它把时间、资产和参数广播进数组，适合快速筛选策略，但不负责实时行情连接、订单回报、撮合队列、凭证管理或分布式任务编排。

## 关键模块

`vectorbt/portfolio/base.py` 的 `Portfolio` 提供 `from_orders`、`from_signals` 等入口；`vectorbt/indicators/factory.py` 的 `IndicatorFactory` 生成可广播指标；`vectorbt/records/base.py` 的 `Records` 及其字段类承载 orders、trades、drawdowns 等记录；utils/config 和 array wrapper 负责配置、索引、广播和 pandas 访问器。可选 `vectorbt-rust` 是热路径加速，而不是另一套交易语义。

## 执行流与数据流

价格/成交量/外部数据 -> indicator/feature -> entries/exits 或 order arrays -> Portfolio simulation -> order/trade/position/returns records -> stats/plots/selection。`fees`、`slippage`、`size`、频率、初始现金和方向等参数进入仿真；结果可以按资产、参数组合和时间层级切片。

## 契约、状态与持久化

Portfolio 接受 pandas/NumPy 对齐输入，广播维度、索引、频率、费用和滑点决定结果语义；Records 以结构化数组和 wrapper 暴露交易统计。库本身不提供实验账本、数据快照或订单事实持久化，工作台需要把输入 DataContract、策略版本和输出 hash 外置保存。

## 质量、安全、性能与运维

NumPy/pandas/Numba 和可选 Rust 适合研究 worker，但大规模广播可能产生高内存压力；JIT/可选引擎还会带来部署差异。必须防止未来函数、错误对齐、缺失值和不现实的成交假设。结果应保留样本区间、数据 available_time、成本模型和随机种子。

## 可迁移模式与限制

可迁移：数组广播、指标工厂、结构化 records、策略参数网格、walk-forward/robustness 工具和研究 notebook API。不应照搬：用向量化结果模拟真实订单排队、把同一 signal 直接送 live、忽略未来函数/数据可用时间，或把大规模参数矩阵放入 API 进程。README 将社区版标为 Fair Code，并同时介绍 VectorBT PRO，商业部署前必须审查当前许可证和 Pro 边界。

本文基于 commit `34b6d5935e3ea3eccd549e2592bc0f455b8045f5`、Portfolio/IndicatorFactory/Records 源码和 README 进行静态研究，并建立 codebase-memory 索引；未执行测试、编译或构建。
