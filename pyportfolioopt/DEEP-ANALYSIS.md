# PyPortfolioOpt 深度分析

> 原始仓库: <https://github.com/PyPortfolio/PyPortfolioOpt>
> 分析基线：`PyPortfolio/PyPortfolioOpt` commit `a6638d2e06dae6f444fd022cfd4b3c528902a85b`，版本 1.6.0。本文为静态源码和测试核对，不构成任何优化结果、投资建议或真实市场验证。

## 1. 设计边界

PyPortfolioOpt 采用清晰的四层结构：

```text
price or return panel
  -> expected return estimator + covariance/risk estimator
  -> optimizer with explicit objectives and constraints
  -> continuous weights -> discrete allocation
```

`EfficientFrontier` 不获取数据，也不下单；它接收预期收益和协方差。`BaseConvexOptimizer` 负责 CVXPY 变量、权重边界、目标、约束和 solver 调用。每个优化器实例在第一次求解后冻结其目标与约束集合，变更时要求重新实例化，避免在已经编译的 CVXPY problem 上产生隐性状态。

这正好适合作为本项目的 `PortfolioOptimizationRun`：输入、参数、求解器、输出和失败原因应是一份不可变运行记录，而非覆盖上一轮权重。

## 2. 均值方差与可解释约束

`EfficientFrontier` 提供 min volatility、max Sharpe、最大二次效用、目标风险、目标收益和 generic convex objective。权重边界先转成 CVXPY 约束，默认 long-only `(0, 1)`；可额外限制单标的、行业暴露、换手和正则化。

值得迁移的是输入和约束都显式化：

| 优化输入 | 当前项目应记录的审计字段 |
|----------|--------------------------|
| `expected_returns` | alpha/预测来源、时间戳、样本窗口、置信度、版本 |
| `cov_matrix` | 风险模型、频率、窗口、缺失值规则、PSD 修复方式 |
| `weight_bounds` | 单标的上/下限、空头许可、账户与市场限制来源 |
| sector constraint | 分类版本、行业映射日期、每个行业上/下限 |
| transaction cost objective | 当前权重、成本模型、调仓假设、货币与单位 |
| solver/options | solver 名称、版本、容差、优化状态、异常文本 |

`max_sharpe()` 会对问题做变量替换，上游明确警告额外目标在该变换下可能不符合直觉。因此首版应把 min volatility、HRP、受约束 quadratic utility 作为稳定对照，不应把 max Sharpe 当默认“最佳组合”。

## 3. 风险模型与 Black-Litterman

`risk_models.py` 提供样本协方差、半协方差、指数加权协方差、Ledoit-Wolf/Oracle shrinkage，并检查协方差是否 PSD；若不是，可用 spectral 或 diagonal 方法修复。

这不是数据质量处理的替代品。PSD 修复只能让优化问题可解，不能证明输入行情正确、复权一致、无前视、股票池无幸存者偏差或年化频率一致。

Black-Litterman 将市场先验 `pi`、观点矩阵 `P`、观点收益 `Q`、不确定性 `omega`、风险厌恶和 `tau` 分离；`idzorek` 可将百分比观点置信度转成不确定性。对 Agent 场景，正确映射是：

```text
Agent research claim
  -> structured view (asset/relative view, horizon, evidence, confidence)
  -> review/validation
  -> BL Q/P/omega
  -> posterior returns
  -> constrained optimizer
```

Agent 的自然语言结论不能直接成为 `absolute_views`。必须先有来源、时间范围、方向、数值含义和置信度转换规则。

## 4. HRP 与离散分配

`HRPOpt` 通过相关性距离做层级聚类，再递归按 cluster variance 分配权重。它避免了显式逆协方差矩阵，适合与均值方差结果并列比较，而不是取代所有优化方法。

`DiscreteAllocation` 处理连续权重到整数股数：

- `greedy_portfolio()` 先按目标权重向下取整，再用剩余资金减小权重偏差；
- `lp_portfolio()` 用整数规划最小化权重偏差加剩余资金；
- 返回 allocation 与剩余资金，并可计算离散化 RMSE。

它的整数单位默认为单股。A 股应另建 `LotSizingAdapter`，至少处理 100 股整手、卖出碎股、停牌、涨跌停、可用资金、T+1、佣金印花税、最小费用和下单价格保护。离散分配输出只能作为 `RebalancePlan` 的候选，不是可执行委托。

## 5. 测试证据与限制

上游测试覆盖有效前沿的权重和收益约束、不同 CVXPY solver、交易成本目标、L2 正则、短仓、风险模型、Black-Litterman、HRP 和离散分配。离散分配测试验证 allocation 加 leftover 的资金守恒，也验证短仓比例。

本轮未运行 pytest，原因是资料库环境未安装 CVXPY、solver 及其上游依赖。静态核对不能证明任一 solver 在目标部署环境可用，也不能证明金融输入在本项目的时间语义正确。

## 6. 推荐集成契约

```text
PortfolioInputSnapshot
  assets, eligible universe, prices/returns data version,
  current positions, market rules, cash, constraints

PortfolioOptimizationRun
  objective, expected-return method, risk method, frequency,
  solver/options, input snapshot hash, output weights, status/error

RebalancePlan
  target weights, discrete lots, expected cash, turnover/cost,
  blocked instruments, warnings, expires_at

ActionGuard approval
  paper_only, scope, human approval, idempotency key
```

首版应只支持 long-only、单标的上限、行业上限、最小现金、换手成本和 paper rebalance。Black-Litterman、空头、非凸目标和自动执行均应后置。
