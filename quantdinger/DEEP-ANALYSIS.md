# QuantDinger 深度代码分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/brokermr810/QuantDinger.git
> 分析基线：
> - `QuantDinger`：commit `e64e1c227bf3174e441a42143620179b286387e1`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/QuantDinger`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `QuantDinger`：`23b1aad65c87` → `e64e1c227bf3`

提交摘要：
- e64e1c2 fix live order safety and refresh strategy templates
- f53eb09 fix live order reconciliation and runtime pricing
- 75f5b6e Align indicator contract with Pine capabilities
- 07767f4 fix: harden position coexistence safeguards
- e820a74 fix: restore backend CI guardrails
- ae2d6d8 fix: protect user positions during strategy execution
- f5804c6 Bump the python-runtime group in /backend_api_python with 35 updates (#188)
- 8fafc74 Bump github/codeql-action from 4 to 4.37.3 (#187)
受影响路径：
- `M	.github/workflows/basic-ci.yml`
- `M	.github/workflows/docker-publish.yml`
- `A	.github/workflows/mcp-ci.yml`
- `M	.github/workflows/openapi-ci.yml`
- `M	.github/workflows/security-ci.yml`
- `M	README.md`
- `M	backend_api_python/README.md`
- `M	backend_api_python/app/data_providers/__init__.py`
- `M	backend_api_python/app/data_sources/crypto.py`
- `M	backend_api_python/app/data_sources/factory.py`
- `M	backend_api_python/app/observability/http.py`
- `M	backend_api_python/app/routes/agent_v1/__init__.py`
- 其余 183 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> 开源 AI Trading OS · Human API / Agent Gateway 双入口 · MCP 薄封装 · 指标/策略沙箱 · 回测/实验/纸面/实盘执行闭环
> 源码: `src/QuantDinger/`
> 原始仓库: <https://github.com/brokermr810/QuantDinger>
> 源码复核：2026-07-10，详见 [首批源码落地验证](../19-首批源码落地验证.md#5-quantdinger)

---

## 1. 总体架构

### 1.1 技术栈

| 层 | 技术 | 作用 |
|---|---|---|
| 后端 API | Flask / flask-smorest / flask-cors | 人类 OpenAPI 路由、Agent Gateway、CORS、JSON provider |
| 数据库 | PostgreSQL 18 | 用户、策略、指标、凭证、持仓、交易、回测、Agent jobs/audit |
| 缓存/协调 | Redis 8 optional | 部分缓存和部署预留，核心 Agent jobs 仍用 PG + 进程内 executor |
| 策略执行 | Python + pandas/numpy | 指标脚本、`on_bar(ctx, bar)` 脚本策略、回测和 live loop |
| 数据源 | 自定义 factory + provider | Crypto/USStock/CNStock/HKStock/Forex/Futures/MOEX |
| 实盘连接 | REST clients | Binance/OKX/Bitget/Bybit/Coinbase/Kraken/Gate/HTX/IBKR/Alpaca |
| Agent 接口 | `/api/agent/v1` | scope token、rate limit、audit、idempotency、jobs、SSE |
| MCP | FastMCP + httpx | Agent Gateway 的工具层薄封装 |
| 前端 | GHCR 预构建 Vue SPA + mobile H5 | Web 端和移动 H5，docker compose 直接拉镜像 |
| 部署 | Docker Compose | PostgreSQL、Redis、backend、frontend、mobile |

### 1.2 目录分层

```text
backend_api_python/app/
  __init__.py                  Flask app factory, CORS, DB bootstrap, route registration
  routes/                      human OpenAPI routes + agent_v1 gateway
  routes/agent_v1/             versioned Agent Gateway
  services/                    strategy, backtest, experiment, live trading, credentials
  services/live_trading/       direct broker/exchange clients
  data_sources/                market data provider factory and implementations
  utils/                       auth, agent_auth, agent_jobs, safe_exec, DB, logs
  migrations/init.sql          canonical PostgreSQL schema

mcp_server/src/quantdinger_mcp/
  server.py                    FastMCP tools that call /api/agent/v1
  security.py                  MCP-side JSON/code guards and secret redaction
```

### 1.3 启动链路

核心入口是 `backend_api_python/app/__init__.py:create_app()`：

1. 创建 Flask app，替换 JSON provider，统一处理 datetime、NaN、Inf。
2. 配置 CORS，默认允许 `localhost:8888/8000` 和移动端 scheme。
3. 检查 JWT secret 配置警告。
4. 对 IBKR 的 `ib_insync` 做 asyncio patch，避免本地 TWS/Gateway 连接不稳。
5. `_bootstrap_database()` 初始化数据库、保证管理员账号、升级内置指标样例。
6. `register_routes(app)` 先初始化 human OpenAPI，再注册 Agent Gateway。
7. `run_startup_hooks(app)` 启动 pending order worker、portfolio monitor、grid poller 等运行态 hooks。

这条链路体现了 QuantDinger 的产品定位：不是一次性脚本，而是一个长时间运行的交易系统。启动时必须恢复状态、启动 worker、修复 schema，而不只是挂几个 HTTP endpoint。

---

## 2. 双 API 面：Human routes 与 Agent Gateway

### 2.1 路由装配

`backend_api_python/app/routes/__init__.py` 非常短，但架构含义很强：

```text
register_routes(app)
    -> init_openapi(app)                 # human web/mobile routes
    -> agent_v1.register(app)            # /api/agent/v1
```

Agent Gateway 在 `routes/agent_v1/__init__.py` 挂载，导入子模块让 decorators 生效：

```text
health, markets, strategies, backtests, experiments,
portfolio, runtime, quick_trade, jobs, indicators,
admin, me_tokens
```

这种双面设计避免了几个常见问题：

1. Agent 不复用浏览器 JWT session，不会把用户登录态暴露给外部自动化。
2. Agent 入口可以强制 scope、rate limit、idempotency、audit。
3. Human UI 和 Agent API 仍复用 service 层，避免业务结果双实现。

### 2.2 Agent envelope

Agent 子路由统一通过 `agent_required(scope)` 包装，并用 `_helpers.envelope/error` 返回结构化响应。比起让 Agent 解析人类 UI 的杂散响应，这种接口更适合 MCP、Codex、Claude Code 或自定义自动化。

可迁移原则：**Agent API 不应只是把 Web API 暴露给机器，而应有自己的认证、错误、审计和长任务语义。**

---

## 3. Agent Gateway 权限、安全与审计

### 3.1 token 与 scope

`backend_api_python/app/utils/agent_auth.py` 是 Agent Gateway 的核心治理层。它明确和 `app.utils.auth` 分离：

| Scope | 名称 | 语义 |
|---|---|---|
| `R` | Read | 读取市场、价格、K 线、策略、jobs、runtime、portfolio |
| `W` | Workspace write | 保存指标、创建/更新策略等工作区写入 |
| `B` | Backtest / simulation | 回测、实验、结构化调参 |
| `N` | Notifications | 通知和一般副作用 |
| `C` | Credentials | 凭证/admin 高风险能力 |
| `T` | Trading / capital | 交易、停止运行态等资本相关动作 |

token 以 `qd_agent_` 开头，完整 token 只展示一次，数据库只存 SHA-256 hash 和 prefix。

### 3.2 token row 本身也是权限策略

`qd_agent_tokens` 不只存 hash，还存：

| 字段 | 用途 |
|---|---|
| `scopes` | R/W/B/N/C/T capability class |
| `markets` | token 允许访问的市场列表，`*` 表示全部 |
| `instruments` | token 允许访问的 symbol 列表，`*` 表示全部 |
| `paper_only` | 默认 TRUE，控制 Agent 是否只能纸面交易 |
| `rate_limit_per_min` | 每 token 每分钟 in-process 限流 |
| `status/expires_at/last_used_at` | 生命周期管理 |

这比“给 Agent 一个 API key”更接近生产权限模型：能力、数据范围、交易风险和频率分开控制。

### 3.3 审计日志

`qd_agent_audit` 记录：

```text
user_id, agent_token_id, agent_name,
route, method, scope_class, status_code,
idempotency_key,
request_summary, response_summary,
duration_ms, created_at
```

`agent_auth.py` 内置 `_redact()`，会对 password、secret、token、api_key、authorization 等字段脱敏，并限制深度，避免审计日志本身变成泄密源。

可迁移原则：Agent 工具调用必须记录 route/params/response shape/status，而不是只记录最终自然语言总结。

### 3.4 schema runtime guard

虽然 canonical schema 在 `migrations/init.sql`，`agent_auth.py:_ensure_schema()` 仍会在运行时幂等创建 agent tables。这对开源自托管项目很实用：老安装升级后第一次使用 Agent Gateway，不会因为缺表直接 500。

---

## 4. Agent jobs：submit + poll + stream

### 4.1 为什么不用同步 HTTP

回测、实验管道和结构化调参都是 CPU/IO 重任务。`backend_api_python/app/utils/agent_jobs.py` 的设计是：

```text
POST /api/agent/v1/backtests
    -> qd_agent_jobs 插入 queued row
    -> ThreadPoolExecutor 执行 runner
    -> 返回 job_id
    -> GET /jobs/{job_id} 或 /jobs/{job_id}/stream
```

这对 LLM/Agent 特别重要：模型可以提交任务、等待、轮询、断线恢复，而不是把 HTTP 请求挂到超时。

### 4.2 进度模型

每个 job 有两层进度：

| 层 | 作用 |
|---|---|
| 进程内 ring buffer | 保存最近 200 条事件，低延迟 SSE 推送 |
| `qd_agent_jobs.progress` JSONB | 保存最新 snapshot，断线或新客户端可读基线 |

`routes/agent_v1/jobs.py` 的 `/jobs/<job_id>/stream` 会先发 snapshot，再发 progress，最后发 result。支持 `since` 或 `Last-Event-ID` 恢复。

### 4.3 idempotency

`qd_agent_jobs` 有 `(agent_token_id, kind, idempotency_key)` 部分唯一索引。Agent backtest/experiment/quick_trade 路由可用 `Idempotency-Key` 降低普通重试造成重复 job 或订单的概率。

边界是：`with_idempotency()` 查询失败会 fail-open；同步 quick trade 先产生订单副作用，再调用 `record_completed_job()` 写完成记录。并发同 key 或数据库故障下，它不是严格的事务幂等。高风险实现应先事务预占 key，再执行具有稳定 `client_order_id` 的外部动作。

### 4.4 取舍

这个实现故意不用 Celery/RQ，适合本地优先部署。风险是多进程、多实例部署时 in-process buffer 和 worker ownership 需要额外协调。项目自己的 `docs/CONCURRENCY_MODEL.md` 已经明确指出：本地单进程可以依赖进程内锁，生产多进程需要 DB/Redis/advisory lock。

---

## 5. MCP server：薄封装，而不是第二个后端

`mcp_server/src/quantdinger_mcp/server.py` 明确写道：REST `/api/agent/v1` 是 source of truth，MCP 只是薄封装。

### 5.1 工具覆盖

`MCP_TOOL_NAMES` 覆盖：

```text
whoami, check_health, list_markets, search_symbols, get_klines, get_price,
list_strategies, get_strategy, runtime_overview, stop_strategy,
place_quick_order,
list_jobs, get_job, wait_for_job, stream_job_until_done,
get_indicator_authoring_contract, validate_indicator_code, save_indicator,
list_indicators, get_indicator,
create_strategy, update_strategy, submit_backtest,
regime_detect, submit_experiment_pipeline, submit_structured_tune,
submit_ai_optimize, list_portfolio_positions, list_paper_orders
```

工具数量多，但每个工具基本是 HTTP wrapper：`_get/_post/_patch -> _unwrap`。`_unwrap` 会把 response 的 `data` 拿出来并脱敏。

### 5.2 安全边界在哪里

MCP server 需要环境变量：

```text
QUANTDINGER_BASE_URL
QUANTDINGER_AGENT_TOKEN
```

真正的 scope、market allowlist、instrument allowlist、paper_only、rate limit、audit 都在后端 Gateway。这样有两个好处：

1. MCP、REST、未来 CLI 都共享同一安全模型。
2. 不需要在每个 Agent client 里复制权限判断。

可迁移原则：MCP 是工具发现和调用体验，不应成为独立权限系统。

---

## 6. 指标与策略代码契约

### 6.1 Indicator authoring contract

`backend_api_python/app/services/indicator_workspace.py:get_indicator_authoring_contract()` 给外部 AI 返回 machine-readable contract。它要求：

| 要求 | 说明 |
|---|---|
| globals | `my_indicator_name`, `my_indicator_description` |
| DataFrame | 开头 `df = df.copy()` |
| 四向信号 | `open_long`, `close_long`, `open_short`, `close_short` |
| output | `{'name', 'plots', 'signals'}`，list 长度与 df 一致 |
| params | 每个 `# @param` 都通过 `params.get()` 读取 |
| forbidden | 不写自然语言、禁止 os/sys/requests/subprocess、不要新代码使用老 `buy/sell` |

这比自然语言 prompt 更稳，因为 Agent 可以先调用 contract，再按 contract 生成代码，再调用 validate。

### 6.2 IndicatorStrategy 与 ScriptStrategy

QuantDinger 有两类策略代码：

| 类型 | 入口 | 适合场景 |
|---|---|---|
| `IndicatorStrategy` | 指标代码生成四向信号列 | 技术指标、信号型策略、回测和执行复用 |
| `ScriptStrategy` | `def on_bar(ctx, bar)` | 需要状态、下单动作和运行时上下文的脚本策略 |

`indicator_workspace.py` 会识别 `def on_bar(...)`，把这种代码归为 `script_template`，避免它出现在普通指标 IDE 列表中。这个小设计很关键：同样是 Python 代码，但资产类型不同，UI 和执行入口不应混在一起。

### 6.3 策略持久化

`services/strategy.py:create_strategy()` 会把用户 payload 规范化后写入 `qd_strategies_trading`：

| 字段 | 作用 |
|---|---|
| `strategy_type` | IndicatorStrategy / ScriptStrategy |
| `market_category` | Crypto / USStock / CNStock / HKStock / Forex / Futures / MOEX |
| `execution_mode` | signal / live 等 |
| `exchange_config` | broker 配置，credential_id 场景会剥离 raw secret |
| `indicator_config` | 指标配置，IndicatorStrategy 可 auto-save / link |
| `trading_config` | symbol、timeframe、strict_mode、risk、bot 参数等 |
| `strategy_mode/strategy_code` | script/bot 扩展字段 |

创建时会调用 `broker_market_policy.validate_strategy_config()`，避免前端、CRUD、worker 对 broker 支持范围各说各话。

---

## 7. Python 沙箱与安全执行

`backend_api_python/app/utils/safe_exec.py` 是 QuantDinger 对 AI/用户代码最重要的防线。

### 7.1 白名单 builtins

只允许计算型 builtins，例如类型构造、数学、迭代、字符串、异常、`staticmethod/classmethod/property/super/object`。明确排除 `open/eval/exec/getattr/type/__import__` 等危险能力；`__import__` 被替换成受限 importer。

### 7.2 import 白名单

允许：

```text
numpy, pandas, math, json, datetime, time,
collections, functools, itertools, statistics,
decimal, fractions, copy
```

同时额外封禁 pandas/numpy 的危险子模块和 I/O 绕过路径，例如 pandas `io`、numpy `ctypeslib`、各种 `read_*`、`to_*`、`load/save/memmap`。

### 7.3 AST / 属性拦截

`safe_exec.py` 拦截：

| 类别 | 示例 |
|---|---|
| dunder escape | `__class__`, `__subclasses__`, `__globals__`, `__code__`, `__mro__` |
| frame/traceback | `f_globals`, `tb_frame`, `gi_frame`, `cr_frame` |
| pandas/numpy I/O | `read_csv`, `to_pickle`, `read_sql`, `fromfile`, `memmap` |
| evaluator | `eval`, `query` |
| operator accessors | `attrgetter`, `itemgetter`, `methodcaller` |

### 7.4 timeout 与内存

`safe_exec_code()` 默认 timeout 30 秒、内存 500MB。Unix 主线程使用 `signal.SIGALRM`，非主线程/Windows 走 timer + ctypes 异常注入。`SAFE_EXEC_ENABLE_RLIMIT=true` 时会启用 `RLIMIT_AS`。

### 7.5 取舍

这是面向本地自托管的实用沙箱，足以显著降低 AI 生成指标/策略的风险。但它仍运行在 Python 进程里，不应被误解成强多租户隔离。若当前项目要接受不可信第三方代码，应把这层再包进独立进程、容器或更严格 runtime。

源码中另有 `safe_exec_isolated()`，使用 multiprocessing、timeout 和 Linux `RLIMIT_AS`，但当前没有调用者。主调用链仍是 `safe_exec_with_validation() -> safe_exec_code()` 的进程内执行，不能把未接入函数当作现有生产隔离能力。

---

## 8. 回测系统：信号规范化与执行假设

### 8.1 BacktestService 主职责

`backend_api_python/app/services/backtest.py` 负责：

1. 从 `DataSourceFactory` 拉 K 线。
2. 估算指标 warmup bars，避免长周期指标一开始不稳定。
3. 执行指标代码并提取信号。
4. 把老 `buy/sell` 兼容映射到四向信号。
5. 根据 strict/aggressive 执行假设模拟成交。
6. 存储 `qd_backtest_runs`, `qd_backtest_trades`, `qd_backtest_equity_points`。
7. 返回 signal diagnostics、execution assumptions、equity/trade result。

### 8.2 四向信号规范化

`_signal_diagnostics()` 同时统计：

```text
buy/sell/open_long/close_long/open_short/close_short
```

如果老代码只给 `buy/sell`，会根据 `trade_direction` 映射：

| direction | buy | sell |
|---|---|---|
| long | open_long | close_long |
| short | close_short | open_short |
| both | open_long | open_short |

新生成代码则推荐直接输出四向列。这个模型比二元 `buy/sell` 更适合同时支持现货、合约、多空和 close-only 行为。

### 8.3 strict_mode 对齐

`services/backtest_execution.py` 把 live strict_mode 映射成 backtest execution：

| strict_mode | backtest signalTiming | 语义 |
|---|---|---|
| true | `next_bar_open` | 已收盘 K 线确认，下一根开盘成交 |
| false | `same_bar_close` 或 1m 子周期 | 更激进，近似盘中/低周期执行 |

这解决一个常见坑：回测用当根收盘成交，实盘却只能下一根执行，导致收益虚高。

### 8.4 Backtest range policy

`services/backtest_limits.py` 根据 market + timeframe 限制数据窗口。例如 USStock 1m/3m 只有 7 天，5m/15m/30m 约 60 天；Crypto 默认按 engine workload 限制。超限返回结构化建议，包括推荐 start/end。

这比等上游 provider 报错更好，UI 和 Agent 可以直接给用户“缩短日期或提高周期”的可执行建议。

---

## 9. 实盘执行与 broker policy

### 9.1 broker_market_policy 单真源

`backend_api_python/app/services/broker_market_policy.py` 明确写着：broker x market x market_type x trade_direction x bot_type 兼容矩阵是单一真源。它被 strategy CRUD、pending order worker 和前端读取。

核心规则包括：

| 规则 | 示例 |
|---|---|
| live markets | 目前 live 只认 Crypto、USStock |
| broker-market | IBKR/Alpaca 支持 USStock spot，crypto venues 支持 Crypto |
| market_type | Alpaca crypto 是 spot-only，perpetual 要用 Binance/OKX/Bybit/Bitget |
| long-only brokers | IBKR/Alpaca 当前 QuantDinger 实现为 long-only |
| crypto short | crypto short 必须是 swap，spot 不能 short |
| bot_type | grid/martingale 只适合 Crypto，dca/trend 可 Crypto/USStock |

可迁移价值：把这些规则散落在 UI、API、worker 会非常快地变成事故来源。QuantDinger 用一张矩阵收住了复杂性。

### 9.2 live_trading factory

`services/live_trading/factory.py:create_client()` 根据 `exchange_config.exchange_id` 和 `market_type` 创建 broker client。支持 demo/testnet/paper 的多种字段别名：

```text
enable_demo_trading, simulated_trading, use_testnet,
sandbox, paper_trading, network/environment/env, paper
```

这个兼容层很实际：不同前端、交易所、旧配置会使用不同字段名。集中规范化能减少“测试连接成功、实盘创建失败”的漂移。

### 9.3 信号到订单

`services/live_trading/execution.py:place_order_from_signal()` 把 `open_long/close_short` 这类信号转换为交易所订单：

1. `order_intent_from_signal()` 解析 side、position side、reduce_only。
2. spot 买入优先 quote amount，卖出会 clamp free base balance。
3. futures/swap 按不同 client 调用 `place_market_order`，传 reduce_only/pos_side/client_order_id。
4. spot 禁止 short signal。

### 9.4 TradingExecutor

`services/trading_executor.py` 维护运行中策略线程：

| 机制 | 用途 |
|---|---|
| `running_strategies` + lock | 管理策略线程 |
| price cache TTL 默认 10s | 降低行情重复请求 |
| signal dedup | 防止同一 K 线重复下单 |
| script callback timeout 默认 5s | 防止 `on_bar` 阻塞 live loop |
| warmup warning | 指标历史不足时写 strategy log |
| max threads env | `STRATEGY_MAX_THREADS` 控制本机负载 |

这一层的工程价值在于“实盘不是只调用 place_order”：它要防重复信号、限制脚本耗时、管理线程、记录日志、和仓位/交易表同步。

---

## 10. Agent quick trade：纸面默认，实盘硬闸

`routes/agent_v1/quick_trade.py` 是最值得迁移的高风险接口设计。

### 10.1 默认路径

Agent quick trade 默认写 `qd_agent_paper_orders`：

```text
market, symbol, side, order_type, qty, limit_price,
fill_price, fill_value, status, paper=true
```

fill price 来自最新 1m K 线，目的是让 Agent workflows 可以完整演练“下单 -> 记录 -> 查询”闭环，但不触碰交易凭证。

### 10.2 实盘解锁条件

实盘必须同时满足：

1. route 要求 `SCOPE_T`。
2. token row 的 `paper_only=false`。
3. 服务端环境变量 `AGENT_LIVE_TRADING_ENABLED=true`。
4. 需要 credential_id，并通过 broker/policy/client 校验。

`confirm_order` 和 `confirm_live_trading` 由 MCP 的 `place_quick_order()` 检查，HTTP `place_order()` 本身不检查确认字段。因此确认门禁属于 MCP 客户端层，而不是 Gateway 的统一服务端约束。自己的实现应在服务端再次强制确认或审批令牌。

这是金融 Agent 接口的正确保守默认：让“能调用工具”和“能动用资金”之间有明确断层。

---

## 11. 数据源工厂与市场类别

`app/data_sources/factory.py` 明确声明：K 线/报价使用哪个接口由调用方传入 `market` 决定，不根据 symbol 字符串猜测。

### 11.1 canonical markets

```text
Crypto, Forex, Futures, USStock, CNStock, HKStock, MOEX
```

`normalize_market()` 支持常见别名，例如 `ashare/a_stock/china -> CNStock`，`stock/equity/alpaca -> USStock`。空 market 仍向后兼容回退到 Crypto，但会 warning，提示未来应成为 hard error。

### 11.2 get_source

| market | source |
|---|---|
| Crypto | `CryptoDataSource` |
| CNStock | `CNStockDataSource` |
| HKStock | `HKStockDataSource` |
| USStock | `USStockDataSource` |
| Forex | `ForexDataSource` |
| Futures | `FuturesDataSource` |
| MOEX | `MOEXDataSource` |

### 11.3 资源保护

`get_kline()` 调用前会执行 `assert_fd_available()`，遇到 fd exhaustion 会进入 resource guard 和日志去重。对自托管系统很实用：行情 provider 和交易所 SDK 很容易在异常重试里耗尽 fd。

可迁移原则：不要靠 symbol 猜市场；显式 market 是数据契约的一部分。

---

## 12. LLM 策略实验管道

`services/experiment/runner.py:ExperimentRunnerService.run_ai_pipeline()` 是 QuantDinger 里最接近“AI 自优化策略”的部分。

### 12.1 单轮流程

每一轮做：

```text
indicator code + params + regime + previous results
    -> build_round_prompt
    -> LLM proposes N candidates
    -> backtest each candidate
    -> StrategyScoringService.score_result
    -> rank
    -> keep global best
```

默认 `maxRounds=3`，`candidatesPerRound=5`，`earlyStopScore=82`。

### 12.2 OOS 验证

runner 会对窗口做 70/30 out-of-sample split。训练阶段用前 70%，最终 ranked list 再在 held-out 后 30% 验证。窗口太短则自动关闭。

这比只让 LLM 调参然后看同一段回测分数更稳，虽然仍不能替代严格 walk-forward。

### 12.3 regime-aware scoring

`services/experiment/scoring.py` 把回测结果压成 7 个分量：

```text
return, annual_return, sharpe, profit_factor, win_rate, drawdown, stability
```

并按 regime 调整权重：

| regime | 权重倾向 |
|---|---|
| bull_trend | 更重 return / annual_return / sharpe |
| bear_trend | 更重 sharpe / drawdown / profit_factor |
| range_compression | 更重 win_rate / stability / profit_factor |
| high_volatility | 更重 drawdown / profit_factor |

同时样本数太小会扣分，避免只交易几次就拿高分。

可迁移价值：策略实验不要只排序收益率；至少要把收益、风险、稳定性、样本数和市场状态分开评分。

---

## 13. PostgreSQL schema：运行态而不是缓存

`migrations/init.sql` 展示了 QuantDinger 的产品边界。关键表包括：

| 表 | 作用 |
|---|---|
| `qd_users` | 用户和管理员 |
| `qd_strategies_trading` | 策略主表，含 strategy_type、execution_mode、market、trading_config |
| `qd_script_sources` | 可复用脚本源码资产 |
| `qd_strategy_positions` | 策略持仓 |
| `qd_strategy_trades` | 策略成交记录 |
| `qd_strategy_review_reports` | 策略 AI 复盘报告历史 |
| `qd_account_positions` | 交易所账户持仓镜像 |
| `qd_indicator_codes` | 指标库/社区指标/本地私有指标 |
| `qd_indicator_code_versions` | 指标版本历史 |
| `qd_watchlist` | 自选 |
| `qd_analysis_tasks` | 分析任务 |
| `qd_backtest_runs` | 回测 run 元数据和 result JSON |
| `qd_backtest_trades` | 回测交易明细 |
| `qd_backtest_equity_points` | 回测 equity curve |
| `qd_exchange_credentials` | 加密后的交易所凭证 |
| `qd_manual_positions` | 人工持仓 |
| `qd_position_alerts` | 持仓提醒规则 |
| `qd_position_monitors` | 持仓监控任务 |
| `qd_market_symbols` / aliases | 多市场标的 seed 和别名 |
| `qd_agent_tokens` | Agent token 权限 |
| `qd_agent_jobs` | Agent 长任务 |
| `qd_agent_audit` | Agent 调用审计 |
| `qd_agent_paper_orders` | Agent 纸面订单 |

这套 schema 的启发是：交易产品的“运行态”必须落库。策略、持仓、交易、回测、Agent 调用、纸面订单都应该能审计和恢复，而不是只存在内存里。

---

## 14. 并发模型

`docs/CONCURRENCY_MODEL.md` 是少见但很有价值的项目文档。它把会产生副作用的域列出并给 serialization key。

| Domain | Serialization key | 保护 |
|---|---|---|
| Strategy lifecycle | `strategy_id` | start/stop lock、状态修复 |
| Strategy symbol execution | `strategy_id:symbol:side` | execution lock、持仓 reconciliation |
| Quick trade | `user_id:credential_id:market:symbol:side` | idempotency key、client order id |
| Pending order dispatch | `pending_order_id` + venue order id | claim-before-dispatch、retry dedupe |
| Grid resting orders | `strategy_id:symbol:cell_index` | DB unique cell、fill reconciliation |
| Account mirror | `credential_id:market_type:inst_id:side` | upsert、禁止 partial data 盲删 |
| Backtest jobs | `job_id` | bounded worker pool |
| Agent jobs | token + kind + idempotency key | DB unique index |
| SSE streams | `job_id:user_id` | heartbeat、disconnect handling |

最重要的原则是：任何会改变交易、支付、job 或账户状态的操作都必须 idempotent 或显式串行化。

这对当前项目非常可借鉴：并发模型应该写成一等文档，不要等事故后才从代码里反推。

---

## 15. 部署模型

`docker-compose.yml` 的默认栈：

```text
postgres 18.3-alpine
redis 8-alpine
backend Flask/Python 3.12
frontend GHCR Nginx SPA, port 8888
mobile GHCR Nginx H5, port 8889
```

几个值得学习的部署细节：

| 设计 | 价值 |
|---|---|
| backend 本地 build，frontend/mobile 预构建拉 GHCR | 用户不用装 Node，也能改后端 |
| `SECRET_KEY` 默认值禁止启动 | 防止自托管用户带弱 secret 上线 |
| PG/Redis/Backend/Frontend 都有 healthcheck | compose 层能观察依赖是否 ready |
| DB/Redis 默认只绑 `127.0.0.1` | 减少默认暴露面 |
| `DB_POOL_MAX`, `GUNICORN_THREADS`, `AGENT_JOBS_MAX_WORKERS` 等可配置 | 自托管环境可按机器规模调节 |
| `ALLOW_LOCAL_DESKTOP_BROKERS` | SaaS/云端可禁用 IBKR 这类本地桌面 broker |

取舍：这比单容器应用重，但对 Trading OS 是合理的，因为 PostgreSQL 是运行态真相，不只是缓存。

---

## 16. UI/UX 可借鉴点

本次仓库没有直接包含 Vue 源码目录，Docker Compose 默认拉 GHCR frontend/mobile 镜像；但从后端接口、README 和路由结构仍能看出 UI 信息架构。

### 16.1 应该如何学习 QuantDinger 的 UI

| UI 能力 | 后端对应 | 借鉴点 |
|---|---|---|
| 策略创建向导 | `StrategyService.create_strategy`, `broker_market_policy` | UI 应读取统一 policy，不要自己硬编码 broker 支持矩阵 |
| 指标 IDE | `indicator_authoring_contract`, `validate_indicator_code`, `qd_indicator_codes` | AI 生成代码要先 validate，再保存；错误要显示 contract 违例 |
| 回测运行页 | Agent jobs / `qd_backtest_runs` / equity/trades | 长任务用 job/timeline，不要只 spinner |
| Agent 设置 | `qd_agent_tokens`, scopes, paper_only | token scope、market/instrument allowlist、paper-only 状态必须可见 |
| 纸面/实盘切换 | `quick_trade.py`, `AGENT_LIVE_TRADING_ENABLED` | 交易 UI 要显示三重闸门状态，避免用户误以为 Agent 可实盘 |
| 运行态监控 | `TradingExecutor`, runtime routes, strategy logs | 策略是否运行、线程/日志/最近心跳要可见 |
| 实验管道 | `ExperimentRunnerService` progress callback | 多轮 LLM 调参要显示每轮候选、分数、OOS 结果和早停原因 |

### 16.2 对 HermesAlpha / ashare-audit 的启发

- HermesAlpha 若做 Agent 研究台，可以借鉴 token scope + paper-only，把“能看数据”和“能触发提醒/建议/交易”分层。
- ashare-audit 若做工具调用审计，可以借鉴 `qd_agent_audit` 的 request_summary/response_summary 和 idempotency_key 记录。
- 策略 UI 不应让用户在不可执行组合上浪费时间；broker policy 应作为后端接口驱动表单可选项。

---

## 17. 当前项目可迁移设计

| 能力 | 迁移建议 | 优先级 |
|---|---|---|
| Agent Gateway | HermesAlpha/ashare-audit 共享 `/agent/v1` 或 Tool Gateway，分 R/W/B/T scope | P1 |
| ToolCall audit | 记录 route/tool、scope、params summary、response summary、duration、status | P1 |
| Idempotent jobs | 长任务统一 `submit -> job_id -> poll/stream` | P1 |
| paper-only 高风险默认 | 任何交易/通知/外部写入都先 paper/sandbox，实动作需多重确认 | P1 |
| Indicator contract | AI 生成策略/规则前先读 contract，保存前 validate | P1 |
| Python code validator | 借鉴 builtins/import/AST/timeout 结构，但高风险场景换独立隔离 | P1 |
| Broker policy 单真源 | provider/market/action 兼容矩阵后端化，UI 只消费 policy | P1 |
| Backtest execution assumption | 明确 same-bar / next-bar / slippage / warmup，写入结果 | P1 |
| Regime-aware scoring | 策略候选按收益、回撤、稳定性、样本数和 regime fit 评分 | P2 |
| Concurrency model doc | 为订单、job、策略运行、提醒、快照写 serialization key | P1 |

---

## 18. 最终提炼

QuantDinger 的核心价值可以压成一句话：**把 Agent 能力接进真实交易系统时，必须先有权限、审计、沙箱、job、paper-only 和并发模型，再谈策略智能。**

它给当前资料库补上的模式是“Agent-ready Trading OS”：既不是只读数据 skill，也不是多 Agent 投研框架，而是把 AI 生成代码、回测、交易执行和运行态审计放在同一个自托管产品里。对 HermesAlpha 来说，它适合借鉴 Agent Gateway、策略实验和交易风险闸门；对 ashare-audit 来说，它适合借鉴 tool envelope、scope 审计、idempotency 和并发模型。
