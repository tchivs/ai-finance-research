# TradingAgents-AShare 深度分析

> A 股智能投研多智能体系统 · LangGraph 状态图编排、可追溯辩论、A 股数据路由与结构化交易决策
> 源码: `/root/source/docs/aaa/src/TradingAgents-AShare/`
> 原始仓库: <https://github.com/KylinMountain/TradingAgents-AShare>

## 1. 为什么 TradingAgents-AShare 重要

TradingAgents-AShare 的重点不是让一个 LLM 写股票摘要，而是把投研过程拆成可见的专业分工：行情、舆情、新闻、基本面、宏观、资金和量价先各自取数、出报告；多头与空头研究员围绕同一组论点辩论；研究总监汇总为投资计划；交易员给出执行方案；再由激进、保守、中性三种风险立场审查，风险裁决者可以把方案退回交易员重写。README 将其描述为“14 名专业 Agent 的多空辩论与风控博弈”，这正是它相对单次问答式投研工具的工程价值。

它还把分析做成面向产品的完整闭环：`POST /v1/analyze` 创建异步任务，`GET /v1/jobs/{job_id}/events` 推送 SSE 事件，结果存入数据库并由 `/v1/reports` 检索；前端可以展示逐 token 的 Agent 发言、研究与风控辩论、历史报告、自选股、持仓及定时任务。它不是券商级数据或回测引擎，README 也明确提示数据可能延迟、结论不构成投资建议；但它是把“数据—论证—建议—跟踪”产品化的可运行样本。

对当前项目，最值得吸收的是**决策过程可分层、可流式观察、可被风险环节否决**这一模式。LLM 输出若只保存最终“买/卖”，无法判断数据缺失、研究分歧还是仓位约束导致结论；本项目通过 `AgentState`、`InvestDebateState`、`RiskDebateState` 和事件流保留了这些中间层。另一方面，任何接入都应补上历史回测、数据版本与事实校验；本仓库的 `backtest_service.py` 是产品接口，不能把存在 `/v1/backtest` 等同于已经验证每条 Agent 建议的历史有效性。

## 2. 高层组件

整体可按下列四层理解：

```text
React/Vite 前端
    -> FastAPI `/v1/*`、SSE job events、SQLAlchemy 报告/自选/持仓/定时任务
    -> TradingAgentsGraph (LangGraph StateGraph + MemorySaver)
    -> 7 个并发分析节点 -> 多空辩论 -> 投资计划 -> 交易计划 -> 三方风控 -> 风险裁决
    -> DataCollector / Provider Registry -> AkShare、BaoStock、Investoday、yfinance、Alpha Vantage
```

| 层次 | 真实模块 | 职责 |
|------|----------|------|
| Agent 编排 | `tradingagents/graph/trading_graph.py`、`graph/setup.py` | 构建 `StateGraph(AgentState)`、创建 ToolNode、决定并行和回环边 |
| 状态与辩论契约 | `agents/utils/agent_states.py`、`agents/utils/debate_utils.py` | 保存各报告、claim、轮次、未解决 claim、风险约束和“要求修订”反馈 |
| 数据层 | `graph/data_collector.py`、`dataflows/interface.py`、`dataflows/providers/` | 一次采集、多 Agent 共享；按方法路由供应商并自动尝试后备供应商 |
| 后端与持久化 | `api/main.py`、`api/database.py`、`api/services/` | FastAPI API、任务生命周期、JWT/API Token、报告/自选/持仓/定时任务服务 |
| 前端 | `frontend/src/App.tsx`、`stores/analysisStore.ts`、`hooks/useSSE.ts` | React Router 页面、Zustand 状态、SSE 流消费、协作和报告视图 |
| 定时运行 | `scheduler/main.py` | 在中国交易日轮询待执行任务，限流、恢复陈旧运行状态并发通知 |

### 14 个基础角色与当前代码的扩展

README 的“14 名”对应最初的六类分析师、两名研究员、研究总监、交易员、三名风险辩手和风险裁决者。当前代码已经新增 `Volume Price Analyst`：`GraphSetup.setup_graph()` 的默认 `selected_analysts` 和前端 `initialAgents` 都包含它。因此当前默认运行图与 UI 都是 **15 个命名角色**，不是文档营销文案中的 14 个；知识库应以代码为准。

| 团队 | 14 个基础角色 | 实现与职责 |
|------|---------------|------------|
| 分析师 | Market、Social、News、Fundamentals、Macro、Smart Money | `create_market_analyst` 读取均线、RSI、MACD、布林、ATR、VWMA；`create_social_media_analyst` 消费个股新闻、涨停池、雪球热榜；`create_news_analyst` 汇总个股与全局新闻；`create_fundamentals_analyst` 使用基本资料及三大表；`create_macro_analyst` 使用板块资金流和新闻；`create_smart_money_analyst` 审查个股资金、龙虎榜和 VWMA。 |
| 研究 | Bull Researcher、Bear Researcher、Research Manager | `create_bull_researcher` 与 `create_bear_researcher` 围绕 `claims`、`focus_claim_ids`、`unresolved_claim_ids` 交替陈述；`create_research_manager` 阅读辩论、各报告及记忆，生成 `investment_plan`。 |
| 交易 | Trader | `create_trader` 将研究计划和市场/舆情/新闻/基本面报告、历史相似记忆、风险反馈汇总为 `trader_investment_plan`。 |
| 风控 | Aggressive、Conservative、Neutral、Risk Manager | 三个 `*_debator` 维护带 `RISK_STATE` 标记的 claim；`create_risk_manager` 解析 `RISK_JUDGE`，产出 verdict、硬/软约束、执行前提、降风险触发器与是否退回。 |

新增的第 15 个角色是 `agents/analysts/volume_price_analyst.py::create_volume_price_analyst`。它不再单独远程抓取，而是读取预计算的 `vpa_indicators` 与 K 线池，输出 `volume_price_report`。前端在 `frontend/src/stores/analysisStore.ts` 将风险裁决 UI 标成 `Portfolio Manager`，但后端图节点名为 `Risk Judge` 且实际工厂是 `create_risk_manager`；这是展示命名与运行实现之间需要注意的差异。

## 3. 核心实现细节

### 3.1 LangGraph 如何组织“先并发、后辩论、再风控”

`GraphSetup.setup_graph()` 将每个所选分析师建为“分析节点—工具节点—完成节点”，从 `START` 对全部分析节点 fan-out；每个节点可由 `ConditionalLogic.should_continue_*` 进入对应 `ToolNode` 继续取数，或进入完成节点。所有完成节点 join 后才进入多头研究员。核心边直接写在 `tradingagents/graph/setup.py`：

```python
# 每位已选分析师并发起跑，全部完成后才能进入研究辩论
for analyst_type in selected_analysts:
    workflow.add_edge(START, f"{analyst_display_name(analyst_type)} Analyst")

workflow.add_edge(
    [f"{analyst_display_name(analyst_type)} Analyst Done" for analyst_type in selected_analysts],
    "Bull Researcher",
)
```

随后 Bull 与 Bear 依据 `should_continue_debate` 往返，达到 `max_debate_rounds` 后进 `Research Manager`；默认值由 `DEFAULT_CONFIG["max_debate_rounds"]` 的环境变量 `TA_MAX_DEBATE` 控制，缺省为 2。研究经理用深度模型，其他研究员和交易员主要使用快速模型，见 `TradingAgentsGraph.__init__()` 对 `deep_thinking_llm`、`quick_thinking_llm` 的初始化。

风控不是最终报告的装饰层。边顺序为 `Trader -> Aggressive Analyst -> Conservative Analyst -> Neutral Analyst`，三者依照 `should_continue_risk_analysis` 循环，随后 `Risk Judge` 通过 `should_revise_after_risk_judge` 选择回到 `Trader` 或 `END`：

```python
workflow.add_conditional_edges(
    "Risk Judge",
    self.conditional_logic.should_revise_after_risk_judge,
    {"Trader": "Trader", "END": END},
)
```

`update_debate_state_with_payload()` 从模型回复里的 `<!-- INVESTMENT_STATE: {...} -->` 或 `<!-- RISK_STATE: {...} -->` 提取结构化 payload，累积 claim、支持/反驳关系、未解决项和轮次摘要；`extract_risk_judge_result()` 再读取 `RISK_JUDGE`。这比仅拼接自然语言历史更适合前端按轮展示，也为后续接入论点事实核查留下了稳定字段。

### 3.2 数据采集、缓存和供应商回退

`DataCollector.collect(ticker, trade_date)` 以 `ticker_trade_date` 为 cache key，用每 key 锁避免同一标的/日期重复抓取。`_fetch_all()` 同时提交行情、新闻、全局新闻、板块及个股资金流、龙虎榜、高管交易、涨停池、热股、基础资料和三大财务报表；它为计算长均线拉取 365 天行情，最多 10 个线程，受 `TA_DATA_FETCH_TIMEOUT`（默认 300 秒）限制。返回 K 线只解析一次：本地用 `stockstats.wrap()` 算 50/200 日均线、RSI、MACD、布林、ATR、VWMA，再用 `_compute_vpa_indicators()` 生成量价指标。分析师只从同一数据池按 14 天短线或 90 天中线窗口取视图，避免多 Agent 重复访问第三方站点。

工具调用经过 `dataflows/interface.py::route_to_vendor()`。`DataProviderRegistry.build_default_registry()` 注册 `CnAkshareProvider`、`CnBaoStockProvider`、`CnInvestodayProvider`、`YFinanceProvider`、`AlphaVantageProvider` 和兼容用的 `CnStubProvider`；`DEFAULT_CONFIG["data_vendors"]` 的 A 股默认链路把核心行情、技术、基本面、新闻优先指向 `cn_akshare,cn_baostock,cn_investoday,yfinance`，实时行情优先 `cn_akshare,cn_investoday`。这不是所有供应商都有全量能力：例如 `CnBaoStockProvider` 的三大表和新闻方法明确 `NotImplementedError`，路由的回退设计因此是必要条件，不是优化。

A 股主来源 `CnAkshareProvider` 提供 `get_stock_data()`、`get_indicators()`、`get_fundamentals()`、三大表、新闻、实时行情、板块/个股资金流、`get_lhb_detail()`、`get_zt_pool()` 和 `get_hot_stocks_xq()`。其 `_AkshareLock` 总并发上限为 5，定时任务最多占 3 个槽，并回收超时持有者，意在兼顾反爬、线程安全和前端优先。可选 `INVESTODAY_API_KEY` 启用 `CnInvestodayProvider` 的实时价、前复权 K 线、新闻、公司画像、三大表和高管持股变动；`XQ_A_TOKEN` 用于提升雪球相关的 AkShare 请求稳定性。生产集成仍需对日期、复权、停牌、数据缺口和供应商口径做独立审计。

### 3.3 API、实时体验与定时分析

`api/main.py::_run_job_inner()` 先创建数据库报告、设置 job 为 `running`，再发出 `job.running` 与 `agent.snapshot`。有自然语言 query 时，先用 `parse_intent` 推断标的、周期和用户上下文，再调用共享 `DataCollector`；之后使用 `graph.astream()` 消费每个 LangGraph chunk。`AgentProgressTracker` 经 `current_tracker_var` 注入异步节点，因此分析师、研究员、交易员和风控辩手能发出 token、辩论和里程碑事件，而无需污染需序列化的 `AgentState`。

前端是 React 18、Vite、TypeScript、Tailwind 与 Zustand 的组合。`App.tsx` 定义仪表盘、分析、报告、持仓、跟踪看板、设置和反馈路由；`analysisStore.ts` 定义 15 角色的状态，`useSSE.ts` 消费事件。后端还会在构建产物存在时把 `frontend/dist` 挂在同一 FastAPI 进程，开发模式则可由 Vite 独立运行。认证使用邮箱验证码换 JWT，用户可创建 Bearer API Token；`TA_APP_SECRET_KEY` 用于加密用户 LLM Key 和签发 JWT，部署文档要求生产环境设置且不应随意更改。

`scheduler/main.py` 是可独立启动的调度进程。它按 `Asia/Shanghai` 每分钟检查、只在交易日和设定的非盘中运行窗口处理待执行项，通过 `SCHEDULER_CONCURRENCY` 信号量控制并发，调用与手动分析相同的 `_run_job()`，记录成功/失败，并可发送邮件或企业微信通知。单容器镜像可同时启动 API 与 scheduler；`docker-compose.split.yml` 则通过 `TA_DISABLE_SCHEDULER=1` 和 `TA_DISABLE_API=1` 分开部署，Redis 只在需要跨进程共享 job/SSE 状态时使用，报告仍存共享数据库。

## 4. 对当前项目的价值

1. **采用“并行证据—对抗论证—可否决执行”的决策契约。** 可以借鉴 `AgentState` 的分报告字段与 debate state 的 claim/未解决项，而不是让所有 Agent 互相转发大段自由文本。保留 `risk_feedback_state`，让风控能要求重做方案而非只追加风险免责声明。
2. **复用采集池，但把质量变成一等输出。** `DataCollector` 的一次抓取、超时和本地指标预计算降低成本；当前项目若采纳，应额外记录供应商、取数时间、原始响应哈希、复权规则、失败/回退链，防止同一份报告混入不同时点的事实。
3. **把流式可观测性作为产品能力。** 参考 `_run_job_inner()`、`AgentProgressTracker` 和前端 SSE 状态，让用户看到数据抓取、哪些角色参与、哪条论点未解决、最终裁决为何发生。注意这只能提高可解释性，不会自动提高结论准确性。
4. **分离产品调度与分析内核。** API 与 scheduler 共享 `_run_job()`，单体易部署、分体可伸缩；这比在 Web 请求中直接跑长 LLM 工作流更可靠。可继续补充幂等 job、队列、分布式锁与完整 trace artifact。
5. **不要直接照搬“交易建议”。** 本仓库默认模型、提示词和数据供应商均可由用户配置，且输出是语言模型推理。当前项目应把它的多 Agent 结构作为研究编排参考，再用独立的事实检索、回测、风险暴露、仓位和执行约束验证最终策略。
