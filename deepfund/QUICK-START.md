# DeepFund 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/HKUSTDial/DeepFund.git
> 分析基线：
> - `DeepFund`：commit `e31f1c2eae845b8627fe65621ba4febaf55c2385`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/DeepFund`
<!-- source-sync:end -->


> LLM 基金投资 Arena · LangGraph 多 Analyst · Portfolio Manager · Supabase/SQLite 追踪
> 源码: `src/DeepFund/`
> 原始仓库: <https://github.com/HKUSTDial/DeepFund>

---

## 一句话定位

`DeepFund` 是一个研究型 LLM 基金投资评测环境。它让 LLM 在统一环境里读取外部信息，驱动多 Agent 分析团队，并通过 Portfolio Manager 做买/卖/持有决策。系统把配置、组合、决策、信号存入数据库，用于后续 arena 展示、回溯和评测。

对当前项目最有价值的是“投资决策可回放”：每个交易日必须按时间顺序运行，组合状态从数据库复制并更新，Analyst 信号和 Portfolio 决策分别落库，避免只看最后一段总结。

---

## 最高价值借鉴点

| 借鉴点 | 位置 | 可复用价值 |
|---|---|---|
| Chronological replay | `src/main.py` | 强制交易日期按顺序运行，避免未来数据穿越 |
| LangGraph 工作流 | `src/graph/workflow.py` | 多 Analyst 并行输入 Portfolio Manager |
| Analyst Registry | `src/agents/registry.py` | 分析角色可注册、可裁剪、可由 planner 选择 |
| 统一 Signal 格式 | `src/graph/schema.py` | Bullish/Bearish/Neutral + justification |
| Portfolio 决策结构 | `Decision` | Buy/Sell/Hold + shares + price + justification |
| 风控先于下单 | `portfolio_manager.py` | 先生成最优仓位比例，再限制交易股数 |
| 双数据库模式 | README / `database/` | Supabase 用于在线监控，SQLite 用于本地复现 |

---

## Agent 角色

| Agent | 作用 | 输出 |
|---|---|---|
| `technical` | 趋势、均值回归、RSI、波动率、量价、支撑阻力 | `AnalystSignal` |
| `fundamental` | 盈利能力、成长、现金流、财务健康 | `AnalystSignal` |
| `insider` | 内部人交易活动 | `AnalystSignal` |
| `company_news` | 公司新闻和媒体覆盖 | `AnalystSignal` |
| `macroeconomic` | GDP、CPI、利率、失业等宏观指标 | `AnalystSignal` |
| `policy` | 财政和货币政策新闻 | `AnalystSignal` |
| `planner` | 从可用 Analyst 中选择本次运行角色 | analyst list |
| `portfolio manager` | 汇总信号、风控、决策、落库 | `Decision` |

---

## 工作流

```text
main.py
  -> load config and trading_date
  -> initialize DB
  -> verify chronological order
  -> AgentWorkflow(config, config_id)
      -> copy latest portfolio into new trading_date
      -> for each ticker:
           planner selects analysts OR use all configured analysts
           StateGraph: START -> analysts -> portfolio manager -> END
           update portfolio position/cashflow
      -> update portfolio in DB
```

这个流程适合做历史回放和 live arena，因为组合状态不是临时变量，而是数据库中的时间序列。

---

## 最适合迁移的模块

1. **Trading-date Guard**: 所有回放必须按时间顺序，禁止后跑早日期。
2. **Signal Schema**: 多 Agent 输出统一为方向 + 理由，便于汇总和评测。
3. **Decision Memory**: Portfolio Manager 读取最近若干决策，避免日内/跨日自相矛盾。
4. **Position Risk Gate**: 先算目标仓位比例，再限制买卖股数。
5. **Planner Mode**: 让高成本 Analyst 按标的和任务选择性运行，而不是每次全跑。
6. **DB-first Evaluation**: 信号、prompt、decision、portfolio 全部落库，支持后验分析。

---

## 注意事项

- 当前实现主要面向美股数据源，如 Alpha Vantage、YFinance；迁移到 A 股需要替换 API Router 和字段口径。
- Portfolio Manager 仍由 LLM 做决策，生产系统需要更强的规则校验和下单隔离。
- `agent_call()` 失败会返回 Pydantic 默认对象，评测时必须把这种默认输出标记为低质量或失败样本。
- 技术指标里存在一些实现细节需要复核，例如均值回归阈值判断和异常数据处理。
