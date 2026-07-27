# JCP 深度分析

> Wails desktop · Go ADK · Moderator-led meeting · stock memory · OpenClaw service
> 源码: `/root/source/tmp/jcp/`
> 原始仓库: <https://github.com/run-bigpig/jcp>

## 1. 架构定位

JCP 是一个本地优先的 A 股研究桌面应用。后端用 Go 承载行情、AI、记忆和工具注册，前端用 React/Wails 展示自选股、K 线和会议室。

核心分层可以概括为：

```text
Desktop shell
    Wails + React

Market/data layer
    MarketService / F10Service / NewsService / ResearchReportService / HotTrendService

Agent layer
    ExpertAgent / Moderator / ADK ModelFactory / Tool Registry

Memory layer
    StockMemory / FileStorage / Relevance / LLMSummarizer

External tool layer
    OpenClaw HTTP service / MCP manager
```

它不是一个纯 Agent demo，而是一个完整的本地产品：AI 配置、策略配置、自选股、市场状态、布局持久化、实时行情和 Agent 讨论都在一个进程里协同。

## 2. Meeting Service: 长链路编排中心

`internal/meeting/service.go` 的 `Service` 是核心对象，持有：

```text
ModelFactory
ToolRegistry
MCP Manager
MemoryManager
memoryAIConfig
moderatorAIConfig
AIConfigResolver
retryCount
selectionStyle
enableSecondRound
meetingStates
```

这几个字段体现了一个成熟 Agent 产品需要的控制点：工具面、模型选择、记忆模型、主持人模型、重试策略、选人偏好和中断恢复状态都可以独立配置。

## 3. Moderator: 先拆问题，再找专家

`internal/meeting/moderator.go` 的 `Moderator.Analyze()` 构造提示词，让 LLM 输出：

```json
{
  "intent": "意图",
  "selected": ["id1", "id2"],
  "tasks": {"id1": "该专家需要分析的具体问题"},
  "topic": "议题",
  "opening": "开场白"
}
```

它的价值在 `tasks` 字段。很多多 Agent 系统只是“把同一个问题发给所有 Agent”，JCP 则先按专家角色拆成不同任务。这样技术分析师、基本面分析师、资金面专家和风控专家不会重复回答同一套话。

`parseDecision()` 对 LLM 输出做了多层 JSON 抽取：直接 JSON、```json 代码块、普通 fenced block、从第一个 `{` 开始做括号匹配，最后才回退简单首尾匹配。这类健壮解析对实际 LLM 产品很重要。

## 4. Smart Meeting: 串行、可恢复、可流式反馈

`RunSmartMeetingWithCallback()` 的主线是：

```text
create meeting timeout context
create main LLM
create moderator LLM or fallback
set MemoryManager LLM
load StockMemory
emit moderator start
Moderator.Analyze
emit opening response
filter selected agents
for each selected agent:
    create agent-specific LLM
    build previous discussion context
    merge memory context
    select task from decision.Tasks
    retryRun(runSingleAgent with timeout)
    on success: append response/history
    on failure: emit error, cache MeetingState, interrupt
optional second review round
Moderator.Summarize
save memory asynchronously
return responses
```

几个细节值得迁移：

| 细节 | 作用 |
|------|------|
| `MeetingTimeout = 10min` | 控制整轮会议成本和等待 |
| `AgentTimeout = 3min` | 单专家不能无限阻塞 |
| `ModeratorTimeout = 2min` | 主持人阶段也有边界 |
| `retryRun()` | 网络或 API 临时错误指数退避 |
| `MeetingStateTTL` | 中断状态不会永久占内存 |
| `ProgressCallback` | 前端能展示工具调用和流式输出 |
| `MeetingModeSmart` / `Direct` | 智能编排与用户指定专家分开 |

## 5. OpenClaw sync path

`RunSmartMeetingSync()` 是 OpenClaw 专用路径，只返回最终 summary，不缓存中断状态，专家失败时跳过继续。

这个路径适合“外部 Agent 调用 JCP 作为工具”：外部只需要一个最终分析摘要，不需要 UI 流式讨论。

`internal/openclaw/server.go` 提供：

```text
GET /health
GET /status
POST /analyze
```

`handleAnalyze()` 做的事情很窄：校验 method/body、解析股票、解析 AI 配置、获取全部专家、构造 `meeting.ChatRequest`，然后调用 `RunSmartMeetingSync()`。

迁移时可以把它升级为：返回 `summary + selected_agents + tool_trace + data_quality + memory_refs`，使外部审计能看到过程。

## 6. Tool Registry: Agent 可用能力集中声明

`internal/adk/tools/registry.go` 统一注册工具：

```text
get_stock_realtime
get_market_status
get_market_indices
get_index_fund_flow
get_stock_moves
get_board_fund_flow
get_board_leaders
get_kline_data
get_orderbook
get_news
search_stocks
get_research_report
get_report_content
get_stock_announcements
get_f10_*
get_hottrend
get_longhubang
get_longhubang_detail
```

每个工具有 name、description 和 creator。这个设计让工具面可枚举、可裁剪、可展示给 Moderator，也便于审计“某个专家为什么能调用某类数据”。

## 7. MarketService: 行情源、缓存和解析

`internal/services/market_service.go` 以 TDX 为 primary provider，以 Sina 为 fallback provider。实时行情路径中：

```text
GetStockDataWithOrderBook(codes)
    -> sort codes for stable cache key
    -> check cache
    -> fetchStockDataWithFallback
    -> parse stock + orderbook
    -> update cache
```

K 线缓存按周期差异设置 TTL，`1m` 分时缓存只有 2 秒，其他默认 30 秒。缓存清理循环每 30 秒清一次过期项。

这说明实时行情工具要按数据类型区分新鲜度，不能用一个全局 TTL。

## 8. MemoryManager: 股票级长期记忆

`internal/memory/manager.go` 的记忆结构由三部分组成：

```text
Summary        历史讨论摘要
KeyFacts       关键事实/观点/决策
RecentRounds   最近几轮讨论
```

`BuildContext()` 会把历史摘要、相关关键事实和近期讨论拼成文本。相关事实由 `Relevance.FindRelevant()` 基于当前 query 召回。

`AddRound()` 添加新讨论后，如果 RecentRounds 达到压缩阈值，会把旧轮次压缩进 Summary，并只保留最近几轮。

异步保存通过 `saveCh` 完成，避免会议主流程被 IO 阻塞。缺点是通道满时直接丢弃保存，生产版需要告警或 backpressure。

## 9. 对当前项目的关键迁移模式

### 9.1 Moderator Contract

HermesAlpha 可以定义一个强制 JSON contract：

```json
{
  "intent": "risk_review | stock_research | factor_debug | portfolio_check",
  "selected_agents": [],
  "tasks": {},
  "required_data": [],
  "risk_mode": "conservative | balanced | aggressive"
}
```

ashare-audit 则审计 contract 是否完整、专家是否覆盖关键风险维度。

### 9.2 Recoverable Agent Runs

JCP 的 `MeetingState` 提醒我们：长链路 Agent 不应只有 success/fail。中间状态应该包含：

```text
selected agents
completed responses
failed index
remaining agents
memory context
created_at
```

这样 UI 可以展示“继续分析”按钮，审计系统也能看到中断点。

### 9.3 Tool Surface Governance

Registry 模式适合把数据工具能力变成 profile：

```text
basic_quote_profile
deep_research_profile
risk_audit_profile
f10_profile
hottrend_profile
```

每个 Agent 只拿自己需要的工具，减少 hallucinated tool calls 和数据越权。

## 10. 风险与改造建议

| 风险 | 建议 |
|------|------|
| LLM summary 可能给出直接交易建议 | 改成研究结论、风险边界和情景条件 |
| OpenClaw sync path 过程不可见 | 返回 structured trace 或写入审计表 |
| 文件记忆缺 schema version | 加 version、source、timestamp、model_id |
| 异步保存满通道丢弃 | 加 metrics、drop counter、持久队列 |
| 工具过多 | 按 Agent profile 裁剪暴露 |

## 11. 结论

JCP 给出了一个很实用的本地研究产品范式：行情工作台提供上下文，多 Agent 会议室提供推理，股票记忆提供长期连续性，OpenClaw HTTP 入口让桌面产品又能成为外部 Agent 的工具。它对 HermesAlpha 的价值是编排和交互闭环，对 ashare-audit 的价值是可审计的专家选择、工具面和记忆边界。
