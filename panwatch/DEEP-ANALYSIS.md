# PanWatch 深度分析

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


> self-hosted watch assistant · TradingAgents adapter · provider orchestration · alert engine · strategy state
> 源码: `src/PanWatch/`
> 原始仓库: <https://github.com/TNT-Likely/PanWatch>

## 1. 架构定位

PanWatch 是一个完整的 Web/PWA 盯盘系统，而不是单一 Agent 脚本。后端 FastAPI + SQLAlchemy + 调度器，前端 React + Tailwind + shadcn/ui，部署上支持 Docker 一键自托管。

后端核心分层：

```text
Web API
    src/web/app.py + src/web/api/*

Runtime entry
    server.py

Agent layer
    BaseAgent
    daily_report / intraday_monitor / chart_analyst / premarket_outlook / tradingagents

Provider layer
    quote / kline / capital_flow / events orchestrators

State layer
    SQLAlchemy models, analysis_history, suggestion_pool, strategy runs

Notification layer
    NotifierManager, notify_policy, notify_dedupe

Schedulers
    AgentScheduler, PriceAlertScheduler, PaperTradingScheduler, ContextMaintenanceScheduler
```

## 2. FastAPI API surface

`src/web/app.py` 注册了大量路由，其中只有认证和市场指数是公共接口，其余 API 都挂 `Depends(get_current_user)`：

```text
/api/auth
/api/market
/api/stocks
/api/quotes
/api/klines
/api/insights
/api/accounts
/api/agents
/api/providers
/api/channels
/api/datasources
/api/settings
/api/logs
/api/history
/api/context
/api/news
/api/suggestions
/api/templates
/api/feedback
/api/discovery
/api/price-alerts
/api/recommendations
/api/dashboard
/api/factors
/api/health
/api/paper-trading
/api/chat
```

这个 surface 说明 PanWatch 已经是“盯盘操作系统”：股票、账户、数据源、Agent、通知、建议、历史、模拟盘都有一等 API。

## 3. server.py: 启动时的产品化细节

`server.py` 做了很多容易被忽略但生产必需的工作：

| 模块 | 细节 |
|------|------|
| Proxy | 外部环境变量 > UI app_settings > `.env`，统一写入 HTTP_PROXY/HTTPS_PROXY |
| SSL | 企业代理 CA 合并到 certifi bundle |
| Logging | console 按级别过滤，DB handler 永远 DEBUG，全量供 UI 日志板查询 |
| Uvicorn logs | 清掉 uvicorn 自带 handler，统一走 root logger |
| Playwright | Docker 下安装到 data/playwright，可用 env 跳过 |
| Seed data | 首次启动写入示例股票和内置 Agent 配置 |
| Global schedulers | Agent、价格提醒、模拟盘、上下文维护全部作为全局实例 |

这些不是模型能力，却决定自托管产品能不能排查问题和稳定运行。

## 4. BaseAgent: Agent 标准生命周期

`src/agents/base.py` 定义：

```text
AgentContext
    ai_client
    notifier
    config
    portfolio
    model_label
    notify_policy
    suppress_notify

AnalysisResult
    agent_name
    title
    content
    notify_content
    raw_data
    images
    timestamp
```

`BaseAgent.run()` 的标准流程是：

```text
collect(context)
analyze(context, data)
if suppress_notify: mark skipped
if should_notify:
    check quiet hours
    check dedupe ttl by agent type
    send notification
return result
```

不同 Agent 的通知去重 TTL 不同：日报/盘前 12 小时，新闻 60 分钟，技术分析 6 小时，盘中 30 分钟，TradingAgents 12 小时。这个差异化策略很值得迁移。

## 5. TradingAgentsAgent: 第三方多 Agent 框架的产品化适配

`src/agents/tradingagents/agent.py` 是 PanWatch 最重要的文件。

### 5.1 collect 阶段

`collect()` 并发拉 4 类数据：

```text
quotes_t = get_quote_orchestrator().fetch(req)
klines_t = get_kline_orchestrator().fetch(kline_req)
capital_t = get_capital_flow_orchestrator().fetch(req)
events_t = get_events_orchestrator().fetch(events_req)
await asyncio.gather(...)
```

事件窗口扩大到 30 天，因为深度分析需要更多个股新闻。A 股还会额外拉财务摘要和技术指标。失败时不会直接崩整个 collect，而是记录 warning 并返回可用部分。

### 5.2 analyze 阶段

`analyze()` 的关键护栏：

```text
availability check
same-day cache unless force_refresh
monthly budget check
build_ta_llm_config(deep_model, quick_model)
create progress handler(trace_id)
build stock metadata context
build portfolio context
run TradingAgentsGraph in thread with hard timeout
map state to AnalysisResult
save history
save suggestion
optional emit paper-trading signal
```

这套链路解决了 TradingAgents 原始框架缺少产品边界的问题：成本、缓存、超时、进度、落库、建议、模拟盘信号全部补齐。

## 6. 数据注入和 monkeypatch

`_run_tradingagents_sync()` 里有三个关键 patch：

```text
apply_compat_patches()
inject_api_key_env(ai_client)
with patch_route_to_vendor(), panwatch_data_context(panwatch_data, trace_id):
    graph = TradingAgentsGraph(...)
    _inject_graph_callbacks(graph, progress_handler)
    patch_propagator(graph, portfolio_context_text)
    final_state, decision = graph.propagate(symbol, date_str)
```

`patch_route_to_vendor()` 让 TradingAgents 内部工具调用读 PanWatch 已采集的数据，而不是去调用原始美股/外部 vendor。

`patch_propagator()` 修改 `create_initial_state()`，把持仓上下文拼进 `past_context`。这是上游官方扩展字段，所以比直接改 prompt 更稳。

## 7. Portfolio context: 决策个性化

`portfolio_context.py` 注入两类信息：

```text
Stock Metadata
    ticker
    company name
    market
    industry
    current price
    instruction: do not guess company from ticker

User Portfolio Context
    quantity
    average cost
    total cost basis
    trading style
    unrealized P&L
    available cash
    position ratio
```

对 A 股尤其重要：六位数字 ticker 容易让 LLM 乱猜公司，必须显式传 company name 和 market。

## 8. Auto trigger: 事件驱动深度分析

`auto_trigger.py` 提供盘中联动：当 `intraday_monitor` 检测到急涨/急跌后，可自动触发 TradingAgents。

护栏包括：

| 护栏 | 实现 |
|------|------|
| 显式开启 | `AgentConfig.raw_config.auto_trigger.enabled` |
| 涨跌幅阈值 | 默认 `abs(change_pct) >= 5%` |
| 冷却 | 查 `AnalysisHistory`，默认 24h |
| 预算 | 复用 `cost_tracker.check_budget` |
| 非阻塞 | `fire_and_forget_trigger()` 异步触发 |
| trace | `auto-{source_agent}-{symbol}-{timestamp}` |

这比“盘中异动就直接跑深度分析”安全得多。

## 9. PriceAlertEngine: 条件组合提醒

`src/core/price_alert_engine.py` 是一个完整规则引擎。

支持条件：

```text
price
change_pct
turnover
volume
volume_ratio
```

支持操作符：

```text
> >= < <= == != between/in
```

`eval_rule()` 对 rule 的 condition_group 做 AND/OR 汇总，返回 `RuleEvalResult(matched, hits, snapshot)`。`scan_once()` 的流程是：

```text
query enabled rules
batch fetch quotes by market
for each rule:
    check stock exists and quote exists
    _can_trigger(rule, now)
    eval_rule
    dry_run? return would_trigger
    insert PriceAlertHit
    send notify
    update last_trigger_at / trigger_count_today / trigger_date
    disable once rule if needed
```

`_can_trigger()` 覆盖 disabled、expired、trading_only、daily limit、once、cooldown。这个规则治理层比单纯阈值判断更值得借鉴。

## 10. StrategyEngine: 建议和机会排序的治理

`strategy_engine.py` 非常大，但开头已经展示其职责：信号生成、后验评估、调权与统计。

值得注意的规则：

| 规则 | 作用 |
|------|------|
| 持仓且 BUY -> add | 区分新建仓和加仓 |
| 未持仓且 HOLD -> watch | 避免对未持仓标的说“持有” |
| buy/add 但无 entry plan 降分 | 没有入场计划的强建议不应高分 |
| high risk ratio cap | 控制高风险候选占比 |
| single strategy share cap | 防止单策略支配机会池 |
| compact meta | 限制 payload 长度，避免 UI/DB 膨胀 |

这说明 PanWatch 不只是“AI 说买就买”，而是把 AI 输出转成受约束的产品状态。

## 11. 对当前项目的迁移清单

| 目标 | 迁移动作 |
|------|----------|
| HermesAlpha 深度研究 | 引入 collect/analyze/result 标准生命周期 |
| A 股 TradingAgents | 用 adapter 注入本地 quote/kline/news/financial data |
| 持仓个性化 | 统一 PortfolioContext 文本或结构化 state |
| 成本治理 | 每个高成本 Agent 配 budget/cache/timeout |
| 提醒系统 | 条件组合 + 冷却 + 日限 + once/repeat + dry_run |
| 审计 | 将 trace_id、toolkit diagnostic、cost_usd 写入 history |

## 12. 风险与改造建议

| 风险 | 建议 |
|------|------|
| monkeypatch 上游对象可能随版本失效 | 加版本检测和 adapter contract tests |
| fire-and-forget 任务不够可靠 | 引入队列和幂等 task key |
| BUY/HOLD/SELL 合规风险 | 改为观察、减仓风险、增配条件等中性语言 |
| CORS 过宽 | 公网部署收紧 origin |
| 数据部分失败 | 在 UI 和报告中显式显示 data coverage |

## 13. 结论

PanWatch 最大价值是“产品化闭环”。它把 TradingAgents 这种研究框架放进真实盯盘场景里，补齐了持仓上下文、预算、缓存、超时、进度、历史、建议、提醒和模拟盘。这些都是 HermesAlpha 从研究原型走向可用产品时必须补的工程层。
