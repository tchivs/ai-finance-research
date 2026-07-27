# PyPortfolioOpt 快速概览

> 原始仓库: <https://github.com/PyPortfolio/PyPortfolioOpt>
> 分析基线：`PyPortfolio/PyPortfolioOpt` commit `a6638d2e06dae6f444fd022cfd4b3c528902a85b`（2026-07-07），版本 1.6.0，MIT，Python >= 3.10 且 < 3.15。

## 一句话定位

PyPortfolioOpt 是一个将预期收益、风险模型、目标函数和权重约束显式分层的 Python 组合优化库。它补齐当前资料库从“单标的研究/信号”到“目标组合权重与离散股数”的确定性中间层。

它是优化器，不是数据源、回测系统、订单系统或风控网关。

## 核心路径

```text
versioned price/return panel
  -> expected returns + risk/covariance model
  -> EfficientFrontier / HRP / Black-Litterman
  -> continuous target weights
  -> discrete allocation
  -> local-market rebalancing rules and ActionGuard
```

| 目标 | 入口 | 可迁移价值 |
|------|------|------------|
| 均值方差优化 | `efficient_frontier/efficient_frontier.py` | min volatility、max Sharpe、目标收益/风险、额外目标与约束 |
| 风险估计 | `risk_models.py` | sample/semicovariance/指数加权/协方差收缩、PSD 修复 |
| Black-Litterman | `black_litterman.py` | 市场先验、主观观点及其置信度/不确定性分离 |
| HRP | `hierarchical_portfolio.py` | 用层级聚类降低协方差逆矩阵敏感性 |
| 离散仓位 | `discrete_allocation.py` | 连续权重转整数股数并返回剩余现金和误差 |

## 可直接吸收的模式

1. 把 alpha/LLM 观点作为 expected-return input，不把“模型给出买入”直接变成订单。
2. 把协方差方法、年化频率、无风险利率、约束、求解器和输入版本写入 `PortfolioOptimizationRun`。
3. 连续目标权重和实际离散订单是两个产物，必须分别保存、比较与审计。
4. 优化失败、非 PSD 协方差、NaN、价格缺失和不可行约束应显示为失败状态，不能静默输出旧权重。
5. 对高估计误差场景优先比较 shrinkage、HRP、最小波动和带换手惩罚的基线，不默认最大 Sharpe。

## 不应直接照搬

- 默认年化频率多处是 252；A 股日频应在自己的 `MarketCalendar` 与数据契约中显式定义，不能靠默认值。
- `DiscreteAllocation` 按单股和给定最新价分配，不理解 A 股 100 股一手、T+1、停牌、涨跌停、佣金、税费、账户可用资金或实际盘口。
- 优化器不验证数据是否前视、预期收益是否可信，也不承担样本外验证。
- 非凸目标可走 SciPy，但上游明确提醒会陷入局部最优；用户/Agent 不应任意注入非凸目标。
- 任何权重或股数都只能进入 suggestion pool/rebalance plan，真实下单仍要经过 ActionGuard。

## 推荐阅读顺序

1. [DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
2. [策略与信号系统](../07-策略与信号系统篇.md)
3. [模式决策矩阵](../18-模式决策矩阵.md)
4. [开发实施 TODO](../20-开发实施TODO.md)
