# TradingAgents Family 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/TauricResearch/TradingAgents.git
> 分析基线：
> - `TradingAgents`：commit `a33fd4c0f134485a43553a2c23a63cb14adbd88f`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/TradingAgents`
<!-- source-sync:end -->


> 多 Agent 投研状态机 · LangGraph 条件边 · A 股 Web/API 产品化 · 决策日志与 checkpoint
> 源码: `src/TradingAgents/`, `src/TradingAgents-AShare/`
> 原始仓库: [TradingAgents](https://github.com/TauricResearch/TradingAgents) · [TradingAgents-AShare](https://github.com/KylinMountain/TradingAgents-AShare)

## 1. 架构总览

TradingAgents 原版的核心类是 `TradingAgentsGraph`。它负责：

```text
config/env overrides
    -> LLM client factory
    -> ToolNode registry
    -> ConditionalLogic
    -> GraphSetup.setup_graph()
    -> Propagator initial state
    -> LangGraph invoke/stream
    -> state log + decision memory + signal processing
```

TradingAgents-AShare 沿用图执行核心，但在外围加上 FastAPI、数据库、用户配置、任务状态、事件流、自选股、持仓导入、定时任务和前端可视化。

两个仓库合起来可以理解成：原版证明“投研组织结构可以映射成 Agent graph”，A 股 fork 证明“这个 graph 可以包装成一个可用产品”。

## 2. 原版 LangGraph 设计

`GraphSetup.setup_graph()` 是整个项目最值得读的文件。它没有把流程藏在 prompt 里，而是显式构建 StateGraph：

```text
START
  -> selected analysts in sequence
  -> Bull Researcher / Bear Researcher conditional debate
  -> Research Manager
  -> Trader
  -> Aggressive / Conservative / Neutral conditional debate
  -> Portfolio Manager
  -> END
```

### Analyst 顺序执行

每个 analyst 都有三类节点：

| 节点 | 作用 |
|------|------|
| agent_node | LLM 分析，可能发起 tool call |
| tool_node | 对应 ToolNode 执行工具 |
| clear_node | 清理 messages，保留结构化 report 字段 |

`ConditionalLogic.should_continue_market/social/news/fundamentals()` 检查最后一条消息是否有 tool_calls，有则回到工具节点，否则进入清理节点。这种模式可以避免“模型想查数据但工具没执行”的半成品状态。

### Debate 条件边

投资辩论由 `InvestDebateState` 保存：

```text
bull_history
bear_history
history
current_response
judge_decision
count
```

`should_continue_debate()` 用 `count >= 2 * max_debate_rounds` 控制结束，否则根据 current_response 的 speaker 在 Bull 和 Bear 间切换。风险辩论同理，只是三方轮转：Aggressive -> Conservative -> Neutral -> Portfolio Manager。

这个设计的关键点是：辩论不是普通聊天记录，而是业务状态。未来审计时可以直接检查 bull/bear/risk 的每一轮内容。

## 3. AgentState 的边界设计

原版 `AgentState` 继承 LangGraph `MessagesState`，同时加入业务字段：

```text
company_of_interest
asset_type
instrument_context
trade_date
market_report
sentiment_report
news_report
fundamentals_report
investment_debate_state
investment_plan
trader_investment_plan
risk_debate_state
final_trade_decision
past_context
```

这比只传 messages 更强，因为每个节点的产物有明确字段，最终 `_log_state()` 可以把全链路写成 JSON。对 HermesAlpha 来说，应当仿照这个 state 设计，把财务模型、估值模型、新闻证据、风险审计、反方意见、组合建议分字段保存。

## 4. 工具分组和数据供应商配置

`TradingAgentsGraph._create_tool_nodes()` 按职责创建 ToolNode：

| ToolNode | 工具 |
|----------|------|
| market | stock data、indicators、verified snapshot |
| social | ticker news |
| news | news、global news、insiders、macro、prediction markets |
| fundamentals | fundamentals、balance sheet、cashflow、income statement |

`DEFAULT_CONFIG` 中还用 `data_vendors` 和 `tool_vendors` 区分 category-level 和 tool-level provider。它明确写了：配置的 vendor chain 不会静默路由到未选择 vendor。这个边界对金融系统很重要，因为“数据来自哪里”本身就是审计事实。

## 5. 可靠性机制

### 5.1 Checkpoint resume

`propagate()` 在 `checkpoint_enabled` 时为 ticker 创建 SqliteSaver，并把 thread id 绑定到：

```text
ticker + trade_date + analysts + debate rounds + risk rounds + asset type
```

这解决了两个问题：

1. 长任务中断后可以从上一个 LangGraph 节点恢复。
2. Agent 选择、轮数或资产类型变化时旧 checkpoint 自动失效。

这比简单按 ticker/date 复用缓存更稳，因为图形状变了，旧状态就不再可信。

### 5.2 决策记忆和后验反思

每次完成后 `memory_log.store_decision()` 保存 final_trade_decision。下一次同 ticker 运行前 `_resolve_pending_entries()` 会拉取未来 holding period 的 raw return 和 alpha return，然后用 `Reflector.reflect_on_final_decision()` 生成 2-4 句 lesson。

这个模式非常适合 ashare-audit：审计系统不是只记录“当时怎么说”，还要记录“后来事实如何，哪条判断成立/失败”。

### 5.3 Deterministic instrument context

`resolve_instrument_context()` 在图运行前解析 ticker identity，并注入给所有 Agent，避免 LLM 根据价格图胡乱识别公司。A 股系统同样需要在 Agent 前置阶段固定：代码、简称、交易所、行业、上市状态、复权口径、是否 ST、是否停牌。

## 6. A 股 fork 的产品化扩展

TradingAgents-AShare 最重要的新增不是多几个 Agent，而是完整任务系统。

### 6.1 IntentParser

`parse_intent()` 先让 LLM 输出 JSON，再用正则 fallback 抽取：

```text
objective: 建仓 / 加仓 / 减仓 / 止损 / 持有处理 / 观察
risk_profile: 保守 / 平衡 / 激进
investment_horizon: 短线 / 波段 / 中线 / 长期
current_position_pct: 满仓/重仓/半仓/轻仓/空仓 或百分比
cash_available
average_cost
max_loss_pct
constraints: 不加杠杆 / 不融资 / 不追高 / 只做T+1 等
```

这非常适合当前项目的交互入口：用户不应被迫填表，系统可以把自然语言转换为结构化分析上下文。

### 6.2 FastAPI 任务接口

README 暴露的核心 API：

| 接口 | 含义 |
|------|------|
| `POST /v1/analyze` | 触发分析，返回 job_id |
| `GET /v1/jobs/{job_id}` | 查询状态 |
| `GET /v1/jobs/{job_id}/result` | 获取结果 |
| `GET /v1/jobs/{job_id}/events` | SSE/事件流 |
| `GET /v1/reports` | 历史报告 |
| `POST /v1/reports/latest-by-symbols` | 批量最新报告 |
| `GET/POST/DELETE /v1/portfolio/imports` | 持仓导入 |
| `GET /v1/dashboard/tracking-board` | 跟踪看板 |
| `PATCH /v1/scheduled/batch` | 批量定时任务 |
| `POST /v1/config/warmup` | 模型 warmup |

这说明生产化投研 Agent 的入口应该是 job API，而不是同步 HTTP 长请求。

### 6.3 并发与启动保护

`api.main` 在 lifespan 中提高 AnyIO thread limiter 和 asyncio default executor worker，预加载交易日历和股票映射，并在 `TA_APP_SECRET_KEY` 缺失时警告。这些细节说明 A 股 fork 已经遇到过多任务并发、akshare/V8 线程安全和密钥安全问题。

## 7. 当前项目的迁移蓝图

### 7.1 HermesAlpha Graph

```text
DataIntegrity Analyst
    -> Financial Statement Analyst
    -> Valuation Analyst
    -> Capital Flow Analyst
    -> News/Event Analyst
    -> Technical/Timing Analyst
    -> Bull/Bear thesis debate
    -> Research Manager
    -> Portfolio Context Adapter
    -> Conservative/Neutral/Aggressive Risk debate
    -> Final Decision
```

每个 Analyst 输出固定 schema：

```text
evidence
metrics_used
assumptions
uncertainties
red_flags
confidence
data_quality_notes
```

### 7.2 ashare-audit 审计点

审计规则可以直接映射到 state 字段：

| 字段 | 审计问题 |
|------|----------|
| instrument_context | 是否识别错标的/交易所/行业 |
| market_report | 价格和指标是否来自 verified snapshot |
| fundamentals_report | 财务口径是否一致 |
| investment_debate_state | 多空论据是否真实对抗，还是重复结论 |
| risk_debate_state | 风险方是否覆盖流动性、波动、仓位、事件 |
| final_trade_decision | 最终建议是否引用了不在前文出现的证据 |
| memory reflection | 历史同类判断是否被正确吸收 |

## 8. 与其他已吸收项目的组合方式

| 组合 | 价值 |
|------|------|
| TradingAgents + wudao-mcp | 多 Agent 图使用 MCP 数据工具，工具只读且可 profile 裁剪 |
| TradingAgents + a-share-watch-butler | 盯盘任务触发 TradingAgents 子图，输出三层报告 |
| TradingAgents + DeepFund | TradingAgents 做单标的研究，DeepFund 做组合层时间回放 |
| TradingAgents + x2t | Agent 观点可结算，形成信源/Agent 战绩 |
| TradingAgents + Qlib | LLM 投研输出可进入量化 backtest/record pipeline |

## 9. 风险和限制

- 多角色架构会放大数据错误。如果 market snapshot 错，后面的 debate 只是在错数据上辩论。
- Debate 不天然提升正确性，必须保存结构化反驳点，并用审计系统检查是否出现“同质化观点”。
- LLM 输出的 final decision 需要强 schema 或后处理，否则交易方向、目标价、止损位、仓位建议很难稳定消费。
- A 股 fork 的生产安全还要补强默认密钥、API key 加密、用户权限、推送渠道和 rate limit。

## 10. 结论

TradingAgents Family 的核心贡献是把投研组织结构变成可执行的状态图。对当前项目最有价值的不是具体 prompt，而是：显式节点、结构化 state、条件边、checkpoint、决策记忆、后验反思和任务 API。这些机制能让 AI 金融分析从“生成一篇报告”升级为“可恢复、可审计、可结算的研究流程”。
