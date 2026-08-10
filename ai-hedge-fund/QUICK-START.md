# ai-hedge-fund 快速概览

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


> AI-powered hedge fund proof-of-concept · 投资大师 Agent · 风险经理 · 组合经理 · backtester
> 源码: `src/ai-hedge-fund/`
> 原始仓库: <https://github.com/virattt/ai-hedge-fund>

## 1. 一句话定位

`ai-hedge-fund` 是一个教育用途的 AI 对冲基金原型。它把 19 个 Agent 串成投资决策系统：价值投资大师、成长投资大师、宏观/尾部风险/技术/情绪/估值/基本面等 analyst 生成信号，Risk Manager 计算仓位限制，Portfolio Manager 在确定性约束内生成最终交易动作。

它与 TradingAgents 的不同点在于：TradingAgents 强调“投研组织辩论流程”，ai-hedge-fund 更强调“多个投资风格 alpha model 并行投票 + 风控约束 + 组合下单”。

## 2. 核心 Agent 列表

README 中列出的 Agent 包括：

| 类型 | Agent |
|------|-------|
| 价值投资 | Warren Buffett、Charlie Munger、Ben Graham、Mohnish Pabrai、Michael Burry |
| 成长/创新 | Cathie Wood、Peter Lynch、Phil Fisher、Growth Agent |
| 宏观/特殊风格 | Stanley Druckenmiller、Bill Ackman、Nassim Taleb、Rakesh Jhunjhunwala |
| 通用分析 | Valuation、Sentiment、Fundamentals、Technicals、News Sentiment |
| 决策层 | Risk Manager、Portfolio Manager |

## 3. 工作流

```text
start_node
    -> selected analyst agents in parallel
    -> risk_management_agent
    -> portfolio_manager
    -> final JSON decisions
```

`src/main.py` 的 `create_workflow()` 使用 LangGraph：所有选中的 analyst 从 start_node 并行连到 risk manager，risk manager 再连到 portfolio manager。

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| 投资大师 Agent | 每个 Agent 表达一种投资哲学 | 适合做“方法论视角”而非唯一结论 |
| `analyst_signals` | 每个 Agent 对每个 ticker 输出 signal/confidence/reasoning | 多源观点先结构化，再交给组合层 |
| Risk Manager | 价格、波动率、相关性、组合价值计算 remaining_position_limit | LLM 不直接决定仓位，仓位上限先由规则算出 |
| Allowed actions | `compute_allowed_actions()` 给每个 ticker 计算 buy/sell/short/cover/hold 最大数量 | 组合经理只能在合法动作空间中选择 |
| Portfolio Manager schema | Pydantic `PortfolioDecision` / `PortfolioManagerOutput` | LLM 输出必须是可执行 JSON，不是自然语言建议 |
| BacktestEngine | 每个交易日滚动调用 Agent，执行交易，更新组合价值 | 把 AI 决策纳入历史回放，而不是只看单日观点 |

## 5. 对当前项目的借鉴

### HermesAlpha

可以把多个投资流派变成“解释层”，例如：

```text
Value Lens
Growth Lens
Contrarian Lens
Quality Lens
Macro Lens
Tail-Risk Lens
Technical Lens
```

每个 Lens 只输出：`signal`、`confidence`、`evidence`、`risk_flags`、`time_horizon`。最终组合建议由 deterministic constraints + Portfolio Manager 决定。

### ashare-audit

可以审计三类问题：

1. 投资大师 Agent 是否套用名人风格但没有真实数据证据。
2. Risk Manager 的 position limit 是否被 Portfolio Manager 违反。
3. Backtest 每日决策是否存在未来函数、价格不可得、现金/保证金计算错误。

## 6. 不该照搬的部分

- 投资大师人格化很容易变成表演，生产系统应保留方法论，不要依赖“名人 Agent”包装。
- README 明确说不实际交易；当前项目也不应把它作为自动下单架构。
- 数据源偏美股和 financialdatasets API，A 股需要替换为本地数据源和严格复权/交易日处理。
- 并行 analyst 到 risk manager 的结构较简单，缺少 TradingAgents 那种 bull/bear/risk debate。

## 7. 最小迁移方案

```text
1. 定义统一 AnalystSignal
   ticker, signal, confidence, reasoning, evidence_ids

2. 并行运行多个方法论 Agent
   value/growth/quality/macro/technical/tail-risk

3. 规则层计算 allowed actions
   cash, current position, max exposure, volatility, correlation

4. Portfolio Manager 只在 allowed actions 中选
   Pydantic schema + fallback hold

5. 历史回放
   每日 snapshot -> Agent signals -> risk limits -> decision -> execution -> metrics
```

## 8. 结论

`ai-hedge-fund` 最值得吸收的是“多投资风格信号 + 规则风控 + 受约束组合经理”的边界。它提醒当前项目：LLM 可以负责解释和权衡，但现金、仓位、保证金、最大可交易数量必须由确定性代码先算出来。
