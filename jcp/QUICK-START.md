# JCP 快速概览

> 韭菜盘 / JCP AI · Wails 桌面股票分析系统 · 多 Agent 会议室 · 股票记忆 · OpenClaw HTTP 分析服务
> 源码: `/root/source/tmp/jcp/`
> 原始仓库: <https://github.com/run-bigpig/jcp>

## 1. 一句话定位

JCP 是一个 Go + React + Wails 的本地桌面股票研究台。它把实时行情、K 线、盘口、F10、研报、热点舆情和多 Agent 会议室放在一个桌面应用里，让用户围绕单只股票发起“专家讨论”。

最值得学的不是 UI，而是它的 Agent 编排方式：一个 Moderator 先判断问题意图并选择专家，再让专家按顺序发言，后续专家可以参考前面发言和股票历史记忆，最后由 Moderator 汇总结论。

## 2. 核心工作流

```text
User asks about a stock
    -> MarketService resolves quote / K-line / orderbook / F10 context
    -> Moderator.Analyze chooses experts and per-expert tasks
    -> selected ExpertAgents run with ADK tools
    -> optional second review round
    -> Moderator.Summarize
    -> MemoryManager saves compressed stock-specific context
    -> UI streams progress and messages
```

OpenClaw 集成走更窄的同步路径：

```text
POST /analyze {stockCode, query}
    -> auth check
    -> stockResolver
    -> aiResolver
    -> resolve all agents
    -> RunSmartMeetingSync
    -> return final summary
```

## 3. 关键文件

| 文件 | 作用 |
|------|------|
| `internal/meeting/service.go` | 会议室服务，超时、重试、专家串行/并行、恢复状态、二轮复议 |
| `internal/meeting/moderator.go` | 小韭菜 Moderator，意图识别、专家选择、总结、JSON 抽取 |
| `internal/agent/container.go` | 专家容器，按 ID 加载和查询 ExpertAgent |
| `internal/memory/manager.go` | 按股票隔离的长期记忆、相关事实召回、异步保存、压缩摘要 |
| `internal/adk/tools/registry.go` | ADK 工具注册表，行情、K 线、盘口、新闻、研报、F10、热点、龙虎榜 |
| `internal/services/market_service.go` | TDX/Sina 行情 provider、缓存、盘口/K线/市场状态 |
| `internal/openclaw/server.go` | OpenClaw HTTP 服务启动、停止、鉴权路由 |
| `internal/openclaw/analyze.go` | `/analyze` 入口，把外部请求映射为会议室分析 |

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| Moderator 决策 | 输出 intent、selected agents、topic、opening、per-agent tasks | 多 Agent 不要全员乱聊，先做任务分配 |
| 选人风格 | conservative / aggressive / balanced | 研究系统可以让用户选择风险偏好 |
| 串行专家讨论 | 后一个专家看到前面观点 | 比纯并行更容易形成观点递进 |
| 失败恢复 | 某专家失败后缓存 MeetingState | 长链路 Agent 任务应能继续，而不是整轮作废 |
| 细粒度进度 | agent_start、tool_call、streaming、meeting_interrupted | 前端可解释“卡在哪里” |
| 股票记忆 | 每只股票一个 StockMemory | 防止跨标的污染上下文 |
| 记忆压缩 | RecentRounds 超阈值后压缩进 Summary | 长期跟踪要控 token |
| Tool Registry | 工具名、描述、creator 统一注册 | 给 LLM 的工具面应集中管理 |
| 多 provider 行情 | TDX primary + Sina fallback | 行情源必须假设会失败 |
| OpenClaw API | 本地 HTTP 分析入口 | 桌面产品可以反向变成 Agent 工具服务 |

## 5. 对 HermesAlpha 的借鉴

1. **做一个“研究会议室”编排层**：先由 Moderator 把问题拆给技术、基本面、资金、风控等专家，而不是直接调用所有 Agent。
2. **每个专家拿到不同任务**：同一用户问题应拆成角色专属任务，减少重复观点。
3. **引入股票记忆**：按股票代码存历史讨论摘要、关键事实、最近结论，让复盘能接上前文。
4. **实时进度事件标准化**：把思考、工具调用、流式输出、专家开始/结束变成统一事件。
5. **将桌面/本地系统暴露为 HTTP 工具**：OpenClaw 模式可作为 HermesAlpha 调用外部研究台的参考。

## 6. 对 ashare-audit 的借鉴

1. **审计 Moderator JSON**：是否选择了合理专家，是否给每位专家分配明确任务。
2. **审计失败恢复**：专家失败时是否记录 FailedIndex、History、Responses、Remaining agents。
3. **审计记忆污染**：股票记忆是否按 symbol 隔离，是否误把别的标的历史带进来。
4. **审计工具白名单**：专家可用工具是否来自 Registry，而不是自由调用任意函数。
5. **审计超时与重试**：会议总超时、单专家超时、Moderator 超时是否都有边界。

## 7. 不该照搬的部分

- JCP 面向个人桌面使用，直接迁移到多用户 Web 产品前要补认证、租户隔离和审计日志。
- OpenClaw `/analyze` 返回最终 summary，适合工具化，但不保留完整讨论 trace；生产审计要落全量过程。
- “投资建议”表达需要改写成合规的“风险观察/研究观点/情景分析”。
- 记忆异步保存通道满时会丢弃保存，生产版应有可观测告警或持久队列。

## 8. 结论

JCP 的价值在于把本地行情工作台和多 Agent 会议室打通。它展示了一个实用的产品模式：实时数据作为上下文，Moderator 做任务分配，专家顺序讨论，股票记忆长期积累，最后还能通过 OpenClaw HTTP 入口变成其他 Agent 的工具。
