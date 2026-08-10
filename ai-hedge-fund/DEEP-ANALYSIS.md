# ai-hedge-fund 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/virattt/ai-hedge-fund.git
> 分析基线：
> - `ai-hedge-fund`：commit `eff8a7320fcf0b473b135690fa1a5b0d9b022a83`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/ai-hedge-fund`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `ai-hedge-fund`：`9557e64273e2` → `eff8a7320fcf`

提交摘要：
- eff8a73 Bump version to 2.2.0
- 75b89a1 Rename package to aihf
- 69e5946 Clean up backtester
- 1524bb1 Untrack scripts/release.sh; release tooling is local-only
- 1d83ae0 Update the command
- e026e5f Package for PyPI as hedge-fund
- a7a99e5 Make 2.0.0 the default
- 6c41ae8 Add thinking
受影响路径：
- `D	.dockerignore`
- `M	.env.example`
- `M	.gitignore`
- `M	README.md`
- `M	ROADMAP.md`
- `M	VISION.md`
- `D	app/README.md`
- `D	app/backend/README.md`
- `D	app/backend/__init__.py`
- `D	app/backend/alembic.ini`
- `D	app/backend/alembic/README`
- `D	app/backend/alembic/env.py`
- 其余 341 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> 投资流派 Agent · LangGraph 并行 analyst · 组合约束 · 波动/相关性风控 · 历史回放
> 源码: `src/ai-hedge-fund/`
> 原始仓库: <https://github.com/virattt/ai-hedge-fund>

## 1. 系统定位

`ai-hedge-fund` 是一个 AI 对冲基金概念验证。它不强调实盘执行，而是探索如何把多个投资风格、通用分析器、风控和组合经理组织成一个可回测的 AI 决策系统。

项目正在向“persistent always-on fund”演进：基金作为一等实体，可以 backtest、paper-trade，并把 investor agents 重构为 pluggable alpha models。这个方向与当前 HermesAlpha / ashare-audit 的长期路线一致：不要只做单次报告，要把报告变成可结算、可复盘的策略/组合事件。

## 2. LangGraph 流程

`src/main.py` 中的 `create_workflow()` 很短，但边界清楚：

```text
StateGraph(AgentState)
    add start_node
    add selected analyst nodes
    add risk_management_agent
    add portfolio_manager

start_node -> each analyst
each analyst -> risk_management_agent
risk_management_agent -> portfolio_manager
portfolio_manager -> END
```

这是一种 fan-out/fan-in 模式：多个 analyst 并行生成观点，risk manager 聚合所有 ticker 的价格/波动/相关性/组合信息，portfolio manager 做最终交易选择。

`AgentState` 极简：

```text
messages: BaseMessage sequence
data: dict merge
metadata: dict merge
```

业务数据集中放在 `data`：tickers、portfolio、start_date、end_date、analyst_signals。相比 TradingAgents 的 typed state，这里更灵活但审计性较弱。当前项目如果迁移，应保留它的 fan-out/fan-in 思路，但用更强 schema。

## 3. Analyst 信号协议

每个 analyst 最终把自己的输出写入：

```python
state["data"]["analyst_signals"][agent_id] = signals
```

Portfolio Manager 读取时只压缩每个 ticker 的核心字段：

```text
agent -> {sig, conf}
```

这是一种很实用的 token 控制：完整 reasoning 可以存档，但最终组合决策只需要信号方向和置信度。对当前项目来说，可以把上游证据存为 evidence_id，而不是把全文塞进组合经理 prompt。

## 4. Risk Manager 的确定性约束

`risk_management_agent()` 是这个项目最值得复用的模块。它不让 LLM 直接拍脑袋决定仓位，而是确定性计算：

1. 获取所有目标 ticker 和已有持仓 ticker 的价格。
2. 计算 daily volatility、annualized volatility、volatility percentile。
3. 构建 returns DataFrame，计算 ticker 间相关性矩阵。
4. 计算组合总价值：cash + long market value - short market value。
5. 对每个 ticker 计算 volatility-adjusted limit。
6. 根据与现有持仓的相关性计算 correlation multiplier。
7. 得到 combined position limit 和 remaining_position_limit。

### 4.1 波动率限额

`calculate_volatility_adjusted_limit()` 使用 20% baseline：

| 年化波动 | 限额逻辑 |
|----------|----------|
| < 15% | 最高 25% allocation |
| 15%-30% | 中等分配，随波动递减 |
| 30%-50% | 显著降低 |
| > 50% | 最多约 10% |

### 4.2 相关性修正

`calculate_correlation_multiplier()`：

| 平均相关性 | multiplier |
|------------|------------|
| >= 0.80 | 0.70 |
| 0.60-0.80 | 0.85 |
| 0.40-0.60 | 1.00 |
| 0.20-0.40 | 1.05 |
| < 0.20 | 1.10 |

这个设计适合当前组合层，因为 A 股热点行业抱团时，多个标的同向暴露不能简单按单票仓位相加。

## 5. Portfolio Manager 的受约束输出

`PortfolioDecision` schema：

```text
action: buy / sell / short / cover / hold
quantity: int
confidence: 0-100
reasoning: str
```

`compute_allowed_actions()` 先用现金、价格、已有多空仓位、保证金、risk max_shares 算出每个 ticker 的合法动作和最大数量。Portfolio Manager prompt 明确要求：

```text
Pick one allowed action per ticker and a quantity <= max.
No cash or margin math. Return JSON only.
```

这是一条非常重要的工程原则：LLM 负责选择，不负责底层约束计算。即使 LLM 失败，`create_default_portfolio_output()` 会填充 hold，避免产生非法订单。

## 6. BacktestEngine 的回放闭环

`BacktestEngine.run_backtest()` 的循环：

```text
prefetch one-year data
for each business day:
    lookback_start = current_date - 1 month
    fetch current prices
    run agent on lookback window
    execute decisions
    update portfolio value and exposures
    print/report daily rows
    compute metrics after enough points
```

它与 DeepFund 的 chronological replay 类似：决策只看当前日期之前的数据，然后执行、更新组合、进入下一天。对 ashare-audit 来说，这种回放方式可以用于验证“审计结论当时是否可得”。

## 7. Portfolio 状态模型

`Portfolio` 类封装：

```text
cash
margin_used
margin_requirement
positions[ticker]: long, short, long_cost_basis, short_cost_basis, short_margin_used
realized_gains[ticker]: long, short
```

它分别实现：

| 方法 | 行为 |
|------|------|
| `apply_long_buy` | 现金足够则买入，否则按现金裁剪数量 |
| `apply_long_sell` | 不超过现有 long，计算 realized_gain |
| `apply_short_open` | 检查 margin_requirement 和 available cash |
| `apply_short_cover` | 释放保证金，计算空头 realized_gain |

A 股系统通常没有直接做空，但这个状态模型仍可简化为：cash、available_cash、positions、cost_basis、realized/unrealized PnL、max_position_pct。

## 8. 与 TradingAgents 的对比

| 维度 | TradingAgents | ai-hedge-fund |
|------|---------------|---------------|
| 组织结构 | 分析 -> 多空辩论 -> 风控辩论 -> PM | 多 analyst 并行 -> 风控 -> PM |
| 核心输出 | final_trade_decision 文本/信号 | JSON trading decisions |
| 风控 | 三方 LLM debate | 确定性波动/相关性/仓位限制 |
| 回测 | README 提及，不是主实现重点 | BacktestEngine 是核心模块 |
| 可审计性 | Graph state 很完整 | signals + portfolio/backtest 更强 |

最佳组合方式：用 TradingAgents 的结构化辩论补 ai-hedge-fund 的 fan-out/fan-in，用 ai-hedge-fund 的 deterministic constraints 补 TradingAgents 的最终动作约束。

## 9. 当前项目落地建议

### 9.1 AnalystSignal 标准化

```text
symbol
agent_id
methodology
signal: bullish / bearish / neutral
confidence: 0-100
time_horizon
evidence_ids
risk_flags
generated_at
data_asof
```

### 9.2 RiskLimits 标准化

```text
symbol
current_price
portfolio_value
current_position_value
volatility_metrics
correlation_metrics
base_position_limit_pct
combined_position_limit_pct
remaining_position_limit
allowed_actions
```

### 9.3 PortfolioDecision 标准化

```text
symbol
action
quantity_or_weight
confidence
reasoning
constraint_source
violations: []
```

## 10. 风险和限制

- 投资大师 Agent 可能产生风格化幻觉，需要把“哲学标签”转成可验证 checklist。
- Risk Manager 默认 5% daily vol fallback 偏保守但仍是硬编码，生产应按市场/行业/停牌状态做更精细 fallback。
- 回测使用 business day 日历和美股数据，A 股要替换为交易所日历、涨跌停、停牌、T+1、手续费、滑点。
- Portfolio Manager prompt 虽然受 allowed actions 限制，仍需要后验 validator 检查 action/quantity 是否真的合法。

## 11. 结论

`ai-hedge-fund` 给当前项目的关键启发是：AI 投研不是只有“报告生成”，还需要信号协议、风险限额、动作空间和回测循环。LLM 可以扮演不同投资方法论，但组合层必须由确定性约束先划出边界，再让模型在边界内做权衡。
