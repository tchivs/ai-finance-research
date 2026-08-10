# DeepFund 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/HKUSTDial/DeepFund.git
> 分析基线：
> - `DeepFund`：commit `e31f1c2eae845b8627fe65621ba4febaf55c2385`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/DeepFund`
<!-- source-sync:end -->


> Live Arena 视角 · 多 Analyst 投资决策 · 组合状态数据库 · 时间顺序回放防穿越
> 源码: `src/DeepFund/`
> 原始仓库: <https://github.com/HKUSTDial/DeepFund>

---

## 1. 项目形态

DeepFund 的目标不是提供一个直接可交易的基金，而是评测 LLM 在基金投资环境中的专业能力。它强调统一环境、外部信息、多 Agent 决策、组合更新和 arena 展示。

关键文件：

| 文件 | 作用 |
|---|---|
| `src/main.py` | CLI 入口、配置加载、数据库初始化、时间顺序校验 |
| `src/graph/workflow.py` | LangGraph workflow，分析师到 Portfolio Manager |
| `src/graph/schema.py` | `FundState`, `AnalystSignal`, `Decision`, `Portfolio`, `PositionRisk` |
| `src/agents/registry.py` | Analyst 和 Portfolio Manager 注册表 |
| `src/agents/planner.py` | 根据 ticker 和候选 analysts 选择本轮分析师 |
| `src/agents/portfolio_manager.py` | 风控、决策、交易股数计算、决策落库 |
| `src/database/` | Supabase/SQLite 两套数据库实现 |
| `src/apis/router.py` | Alpha Vantage/YFinance 路由 |

---

## 2. 防止时间穿越的运行模型

`main.py` 里有一个非常重要的约束：读取当前 experiment 的最新交易日期，如果用户传入的 `trading-date` 早于数据库最新日期，就拒绝运行。

这是金融回放系统必须具备的护栏。没有这个约束，Agent 很容易在历史回测中无意读取未来组合状态或决策记忆，造成“Time Travel is Cheating”。

迁移建议：当前项目所有日频回放都应有：

```text
experiment_id
requested_trading_date
latest_recorded_trading_date
if requested < latest: hard fail
```

---

## 3. LangGraph 投资工作流

`AgentWorkflow.build()` 为每个 ticker 构建一张图：所有当前 Analyst 从 START 并行出发，全部指向 Portfolio Manager，最后到 END。

```text
START
  -> technical
  -> fundamental
  -> insider
  -> company_news
  -> macroeconomic
  -> policy
      -> portfolio manager
          -> END
```

`FundState` 用 `Annotated[List[AnalystSignal], operator.add]` 聚合多个 Analyst 输出。这是一个简洁的多 Agent 汇总模式：各角色只需要返回 `{"analyst_signals": [signal]}`，LangGraph 负责合并。

---

## 4. Planner Mode

DeepFund 支持两种模式：

| 模式 | 行为 | 适用场景 |
|---|---|---|
| `planner_mode=false` | 所有配置的 analysts 都跑 | 小 universe、需要完整证据 |
| `planner_mode=true` | Planner 根据 ticker 选择 analysts | 成本敏感、部分标的不需要全量分析 |

Planner 的输入不是任意工具，而是 `AgentRegistry` 中注册的 analyst doc。这让选择空间可控，避免 LLM 调用不存在的角色。

当前项目可以把这套机制用于审计/投研：例如重大公告审计只跑 fundamental + company_news + policy，盘中异动只跑 technical + capital_flow + event。

---

## 5. Signal 与 Decision 的结构化输出

`schema.py` 把 Analyst 输出限制为：

```text
signal: Bullish | Bearish | Neutral
justification: str
```

Portfolio Manager 输出限制为：

```text
action: Buy | Sell | Hold
shares: int
price: float
justification: str
```

这种结构化输出适合评测，因为可以统计每个 Agent 的方向偏差、理由长度、决策频率、实际收益和组合影响。

对当前项目的启发：审计和研究结论也应结构化，例如：

```text
verdict: pass | flag | fail | unknown
confidence
evidence_refs
justification
required_followup
```

---

## 6. Portfolio Manager 的两阶段决策

`portfolio_manager.py` 先做 risk control，生成 `optimal_position_ratio`，再读取最近决策记忆并生成具体 Buy/Sell/Hold 和 shares。

重要细节：

| 机制 | 作用 |
|---|---|
| 单标的最大仓位 | `2 / num_tickers` 四舍五入到 0.05 | 防止单票过度集中 |
| ratio clamp | 小于 0 设为 0，大于上限设为上限 | 修正 LLM 风控输出 |
| tradable_shares | 根据现金、当前持仓、目标仓位计算可交易股数 | 防止 LLM 随便报 shares |
| decision_memory | 读取最近 5 次决策 | 保持跨日一致性 |

这说明即使让 LLM 决策，也要让代码掌握硬约束：价格、现金、持仓、仓位上限、可卖数量。

---

## 7. 数据库优先的 Arena 设计

DeepFund 的数据库有四类核心表：Config、Portfolio、Decision、Signal。README 也强调数据库用于实时监控交易状态和存储 LLM reasoning，方便未来分析和 traceback。

这对当前项目非常重要：如果要评测 Agent 的投资/审计能力，就不能只保存最终报告。至少要保存：

| 对象 | 为什么保存 |
|---|---|
| config | 同一策略不同配置必须分开比较 |
| signal | 分析师角色是否有效需要后验统计 |
| decision | 决策理由和动作需要回看 |
| portfolio | 收益、回撤、换手和仓位风险来自组合状态 |
| prompt | 复现实验和定位幻觉 |

---

## 8. 迁移到 A 股时的改造点

DeepFund 当前主要用 Alpha Vantage/YFinance，美股字段和 A 股差异较大。迁移时要改：

1. `APISource` 增加 A 股 provider，如本地 data lake、Tushare、OpenAshare、Wudao MCP。
2. `technical_agent` 的交易日、复权、涨跌停、停牌处理改为 A 股口径。
3. Portfolio Manager 增加 lot size、涨跌停不可成交、T+1、停牌、交易成本。
4. Analyst 增加公告、龙虎榜、北向、题材、互动易、解禁等 A 股特有角色。
5. Signal 落库增加 `source_date` 和 `data_quality`，避免最新数据污染历史交易日。

---

## 9. 值得直接吸收的原则

1. 金融回放必须按交易日单调推进，禁止时间倒跑。
2. 多 Agent 输出必须统一 schema，否则无法评测。
3. 组合状态应数据库持久化，不应只存在内存。
4. LLM 决策前必须经过代码风控边界。
5. 决策记忆应参与下一次决策，避免频繁自相矛盾。
6. Planner 只能从注册表选择角色，不能臆造 Agent。
7. prompt、signal、decision、portfolio 都要落库，才能做 arena 级评测。
