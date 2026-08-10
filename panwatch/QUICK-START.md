# PanWatch 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/TNT-Likely/PanWatch.git
> 分析基线：
> - `PanWatch`：commit `c1b064fee9f0cae60731a6e19def2817f06cec09`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/PanWatch`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `PanWatch`：`5b5ac168ce0c` → `c1b064fee9f0`

提交摘要：
- c1b064f feat(dashboard): 首页视觉改版 + 指数/美股K线数据源修复 + 首屏提速
受影响路径：
- `M	frontend/packages/api/src/dashboard.ts`
- `M	frontend/packages/api/src/portfolio.ts`
- `A	frontend/src/components/BenchChart.tsx`
- `A	frontend/src/components/Sparkline.tsx`
- `M	frontend/src/pages/Dashboard.tsx`
- `M	packages/marketdata/src/marketdata/client.py`
- `M	packages/marketdata/src/marketdata/vendors/kline.py`
- `M	packages/marketdata/tests/test_index_methods.py`
- `M	packages/marketdata/tests/test_kline_vendors.py`
- `M	src/core/portfolio_benchmark.py`
- `M	src/web/api/market.py`
- `M	tests/conftest.py`
- 其余 3 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> 自托管 AI 盯盘助手 · FastAPI + React PWA · TradingAgents 集成 · 价格提醒 · 持仓/模拟盘/通知闭环
> 源码: `src/PanWatch/`
> 原始仓库: <https://github.com/TNT-Likely/PanWatch>

## 1. 一句话定位

PanWatch 是一个自托管的个人/小团队盯盘系统，覆盖 A 股、港股、美股的自选股、持仓、价格提醒、Agent 调度、通知推送和 TradingAgents 深度分析。

它最值得学的是“Agent 投研能力产品化”：不是把 TradingAgents 简单包一层按钮，而是接入本地 provider、持仓上下文、预算检查、同日缓存、进度回调、历史落库、建议池、模拟盘信号和自动触发。

## 2. 核心工作流

```text
User / Scheduler / Alert trigger
    -> AgentContext(ai_client, notifier, app config, portfolio, notify_policy)
    -> BaseAgent.run()
        -> collect provider data
        -> analyze with LLM or TradingAgentsGraph
        -> save history / suggestions
        -> notify with dedupe and quiet-hour policy
```

TradingAgents 深度分析路径：

```text
TradingAgentsAgent.collect()
    -> quote + kline + capital flow + events concurrently
    -> optional A-share financial abstract
    -> technical indicators

TradingAgentsAgent.analyze()
    -> same-day cache check
    -> monthly budget check
    -> build TA config
    -> inject stock metadata + portfolio context
    -> patch route_to_vendor to use PanWatch data
    -> run TradingAgentsGraph in worker thread with timeout
    -> map result to AnalysisResult
    -> save history + suggestion + optional paper-trading signal
```

## 3. 关键文件

| 文件 | 作用 |
|------|------|
| `server.py` | 统一服务入口，初始化 DB、日志、代理、调度器、内置 Agent |
| `src/web/app.py` | FastAPI app 和路由注册，登录保护 API surface |
| `src/agents/base.py` | AgentContext、PortfolioInfo、AnalysisResult、BaseAgent 标准执行与通知去重 |
| `src/agents/tradingagents/agent.py` | TradingAgents 深度分析适配器 |
| `src/agents/tradingagents/portfolio_context.py` | 把持仓/账户上下文注入 TradingAgents past_context |
| `src/agents/tradingagents/auto_trigger.py` | 盘中涨跌幅阈值自动触发 TradingAgents |
| `src/core/price_alert_engine.py` | 条件组合价格提醒、交易时段、冷却、通知和命中落库 |
| `src/core/strategy_engine.py` | 策略信号、候选排序、风险约束、后验评估和权重统计 |

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| Provider Orchestrator | quote/kline/capital/events 并发拉取 | Agent collect 阶段应并发且可部分失败 |
| TradingAgents patch | monkeypatch route_to_vendor，让上游框架读本地 A 股数据 | 适配第三方 Agent 框架不一定要 fork |
| Portfolio context | 用 past_context 注入持仓、成本、风格、现金 | AI 决策必须个性化到用户仓位 |
| Budget guard | 月度预算、超预算 reject/warn/continue | 高成本 Agent 要有显式成本闸门 |
| Same-day cache | 同标的同日复用历史结果 | 降低重复深度分析成本 |
| Progress handler | trace_id + LangChain/LangGraph callbacks | 深度分析必须可见进度 |
| Suggestion pool | BUY/HOLD/SELL 进入建议池，有 24h 过期 | 结论应变成 UI 可消费状态 |
| Auto trigger | 急涨急跌触发深度分析，带冷却和预算 | 事件驱动分析，而非只靠用户点击 |
| PriceAlertEngine | AND/OR 条件、交易时段、日限、冷却、once/repeat | 提醒系统要有完整触发治理 |
| DBLogHandler | UI 日志板保留完整 DEBUG，控制台过滤噪音 | 运维排查和用户界面可共用日志事实 |

## 5. 对 HermesAlpha 的借鉴

1. **把外部多 Agent 框架适配到本地数据层**：TradingAgents 的框架可保留，但数据工具、ticker 解释、持仓上下文必须本地化。
2. **给高成本分析加预算/缓存/超时**：深度研究不是每次都跑，应该有成本状态和复用策略。
3. **分析结果落入多个消费面**：历史报告、建议池、持仓页徽章、模拟盘信号、通知都应从同一 AnalysisResult 派生。
4. **自动触发要有护栏**：阈值、冷却、预算、同日历史检查缺一不可。
5. **前端需要进度与诊断**：尤其是 TradingAgents 这类 3-5 分钟任务，要显示阶段、成本、toolkit diagnostic。

## 6. 对 ashare-audit 的借鉴

1. **审计第三方框架适配**：route_to_vendor patch 是否真的让 A 股工具命中本地数据，而不是 fallback 到美股数据源。
2. **审计持仓上下文注入**：PM 决策是否看到成本价、仓位、现金和交易风格。
3. **审计预算与冷却**：自动触发是否绕过月度预算或同日缓存。
4. **审计提醒规则**：AND/OR 条件、日触发上限、交易时段、once/repeat 是否正确执行。
5. **审计建议池过期**：TradingAgents 结论是否有有效期，是否过期后仍被 UI 当作新建议。

## 7. 不该照搬的部分

- `patch_route_to_vendor` 和 `patch_propagator` 是实用 hack，迁移时要包成稳定 adapter 并加版本兼容测试。
- 默认 CORS `allow_origins=["*"]` 适合自托管简单部署，多用户公网产品要收紧。
- TradingAgents 深度分析给出 BUY/HOLD/SELL，合规场景应改为风险分层、观察动作或情景建议。
- 自动触发 fire-and-forget 需要任务队列/幂等键，否则并发重启时可能重复执行。

## 8. 结论

PanWatch 的价值是把 AI 投研做成一个完整的盯盘产品。它连接了持仓、数据、提醒、Agent、历史、通知和模拟盘，尤其值得当前项目学习“深度分析如何进入真实用户工作流”。
