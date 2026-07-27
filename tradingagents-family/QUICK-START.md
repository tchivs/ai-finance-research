# TradingAgents Family 快速概览

> TradingAgents + TradingAgents-AShare · 多 Agent 投研与交易决策框架 · LangGraph debate / risk review / Web API
> 源码: `/root/source/tmp/TradingAgents/`, `/root/source/tmp/TradingAgents-AShare/`
> 原始仓库: [TradingAgents](https://github.com/TauricResearch/TradingAgents) · [TradingAgents-AShare](https://github.com/KylinMountain/TradingAgents-AShare)

## 1. 一句话定位

TradingAgents 把一份股票交易判断拆成“分析师团队 -> 多空研究员辩论 -> 交易员 -> 三方风控辩论 -> 组合经理裁决”的 LangGraph 流程。TradingAgents-AShare 在此基础上产品化为 A 股投研系统：14 名 Agent、自然语言意图解析、辩论 Drawer、报告库、自选股、持仓导入、定时分析、REST API 和 Web 前端。

对当前项目来说，它的价值不在“让 Agent 直接给交易建议”，而在于如何把 LLM 投研流程拆成可观察、可恢复、可审计的多角色状态机。

## 2. 核心工作流

```text
Market/Sentiment/News/Fundamentals Analysts
    -> Bull Researcher <-> Bear Researcher debate
    -> Research Manager
    -> Trader
    -> Aggressive / Conservative / Neutral Risk debate
    -> Portfolio Manager
    -> final_trade_decision + memory log + reports
```

A 股 fork 增强为：

```text
自然语言 query
    -> IntentParser: ticker / horizon / focus / position context
    -> TradingAgentsGraph
    -> job/event stream
    -> structured report storage
    -> watchlist / portfolio / scheduled analysis / tracking board
```

## 3. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| LangGraph 状态机 | `GraphSetup.setup_graph()` 显式添加节点和条件边 | 把 AI 流程变成可重放 DAG，而不是一段大 prompt |
| 角色分层 | Analyst、Researcher、Trader、Risk、PM 分工 | 让不同 Agent 只产出自己的证据/反驳/裁决 |
| Debate state | `InvestDebateState` 与 `RiskDebateState` 保存历史、当前发言、裁决 | 多轮对抗不能只存在 messages 中，要结构化落状态 |
| ToolNode 分类 | market/social/news/fundamentals 各有独立工具组 | 工具暴露按职责收口，降低乱调用 |
| Checkpoint resume | per ticker SQLite checkpoint + graph-shape signature | 长链路 LLM 任务需要断点恢复和变更失效 |
| Decision memory | 决策落 `trading_memory.md`，后续按真实收益反思 | 形成“决策 -> 结果 -> lesson -> 下次注入”的闭环 |
| A 股 IntentParser | LLM JSON 解析 + 正则 fallback | 中文自然语言交易意图可以双轨解析 |
| Web/API productization | job id、events stream、reports、scheduled、portfolio imports | 投研 Agent 应该以任务系统暴露，不只是 CLI |

## 4. 对 HermesAlpha 的借鉴

1. **把分析拆成状态图**：财务、估值、新闻、技术、资金、风险、组合建议可以成为节点，而不是一个 monolithic analyst。
2. **引入双层辩论**：先做 thesis 的 bull/bear debate，再做风险方的 conservative/neutral/aggressive debate。
3. **输出结构化中间态**：不要只保存最终报告，保存每个 Agent 的 report、debate history、judge decision 和 tool trace。
4. **做 checkpoint signature**：分析日期、ticker、Agent 选择、辩论轮数、资产类型变化时必须重新跑，不能复用旧 checkpoint。
5. **做自然语言持仓上下文解析**：用户说“我半仓被套，成本 32，短线是否止损”，要解析成 objective、position_pct、average_cost、horizon、constraints。

## 5. 对 ashare-audit 的借鉴

1. **审计对象从最终结论扩展到决策链**：检查 market_report、fundamentals_report、debate_state、risk_debate_state 是否互相支持。
2. **用风险辩论做审计规则模板**：激进、保守、中性三方分别提出 max loss、liquidity、volatility、event risk 的异议。
3. **决策日志可结算**：把每次审计结论后续表现回填，形成“哪类审计判断常错”的反馈数据。
4. **报告库而不是单次文件**：A 股 fork 的 report_service / list_reports / latest-by-symbols 适合做审计历史查询。

## 6. 不该照搬的部分

- 原版默认依赖 Yahoo/AlphaVantage 等海外数据，A 股生产环境需要本地数据底座或 wudao-mcp / a-stock-data / OpenAshare 风格的数据层。
- 多角色 debate 容易消耗 token，生产版要按股票重要性、数据质量和用户权限动态裁剪 Agent。
- A 股 fork 是完整 Web 产品，迁移时不应先复制前端，而应先复制 job/report/state contracts。
- 交易建议必须保留“研究用途”和“不自动下单”边界，尤其是 API 输出被第三方系统调用时。

## 7. 最小可迁移方案

```text
Phase 1: AgentState + GraphSetup
    定义 report/debate/risk/final_decision 结构

Phase 2: Analyst nodes
    每个节点只绑定自己的工具组和输出字段

Phase 3: Debate loops
    bull/bear 与 risk 三方用计数器控制轮数

Phase 4: Job + Event stream
    每个节点完成时推送事件，最终报告入库

Phase 5: Memory reflection
    决策到期后回填真实收益和反思 lesson
```

## 8. 结论

TradingAgents Family 是目前最适合学习“多 Agent 投研流程如何工程化”的样板。它给出的不是更聪明的单个模型，而是角色、状态、工具、恢复、报告、历史学习之间的系统边界。
