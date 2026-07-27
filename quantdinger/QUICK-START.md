# QuantDinger 快速概览

> 开源 AI Trading OS · Flask + PostgreSQL + Redis + Vue 预构建前端 · Agent Gateway + MCP · 策略沙箱、回测、纸面/实盘执行与监控一体化
> 源码: `/root/source/tmp/QuantDinger/`
> 原始仓库: <https://github.com/brokermr810/QuantDinger>
> 分析基线：`fc33395cbbf162e0145372341740b9ae4bac3f6a`（2026-07-03）
> 源码复核：2026-07-10，详见 [首批源码落地验证](../19-首批源码落地验证.md#5-quantdinger)

---

## CREDITS

- Upstream: <https://github.com/brokermr810/QuantDinger>
- Product: QuantDinger by Open Byte Inc.
- License: Apache License 2.0
- 本文档只做架构学习、模式提炼和当前项目借鉴，不复制上游代码。

---

## 一句话定位

`QuantDinger` 是一个把 AI 策略生成、指标代码、回测、纸面交易、实盘执行、持仓监控、Agent API 和 MCP 工具打进同一套自托管栈里的交易操作系统。它不是单纯的行情面板，也不是一个只会生成策略代码的 Agent，而是围绕“策略从生成到运行”的完整产品闭环。

它最值得学习的不是某个交易所适配器，而是三条边界：人用 Web API 和 Agent Gateway 分离；AI 生成代码必须经过策略/指标契约和沙箱校验；真实交易默认被 token、scope、paper_only 和部署级 kill switch 多重阻断。

---

## 最高价值借鉴点

| 借鉴点 | 代码位置 | 可复用价值 |
|---|---|---|
| Human API 与 Agent Gateway 分离 | `backend_api_python/app/routes/__init__.py`, `routes/agent_v1/` | 人类 JWT 会话和机器 token 权限不混用，审计边界清楚 |
| 6 类 Agent scope | `backend_api_python/app/utils/agent_auth.py` | R/W/B/N/C/T 把读取、写入、回测、通知、凭证、交易拆开授权 |
| Agent 调用全量审计 | `agent_auth.py`, `migrations/init.sql` | `qd_agent_audit` 记录 route、method、scope、状态码、请求/响应摘要 |
| Agent job submit + poll/stream | `backend_api_python/app/utils/agent_jobs.py`, `routes/agent_v1/jobs.py` | 长回测/实验不阻塞 HTTP，请求可 idempotent replay，可 SSE 进度流 |
| 交易默认 paper-only | `routes/agent_v1/quick_trade.py` | Agent 下单先写 `qd_agent_paper_orders`，实盘需 T scope + paper_only=false + 环境 kill switch |
| MCP 只是 Gateway 薄封装 | `mcp_server/src/quantdinger_mcp/server.py` | 安全边界留在 REST Gateway，MCP 不重新实现权限系统 |
| 指标作者契约 | `services/indicator_workspace.py` | AI 写代码前先读 machine-readable contract，要求四列信号和 output 结构 |
| Python 沙箱执行 | `utils/safe_exec.py` | builtins 白名单、import 白名单、AST/危险方法拦截、超时和可选内存限制 |
| 回测与实盘 strict_mode 对齐 | `services/backtest_execution.py`, `services/backtest.py` | 严格模式映射为下一根 K 线开盘成交，减少回测/实盘口径漂移 |
| Broker/市场兼容矩阵 | `services/broker_market_policy.py` | 交易所、市场、market_type、方向、bot_type 统一校验，前后端共用 |
| 多市场数据源工厂 | `app/data_sources/factory.py` | Crypto/USStock/CNStock/HKStock/Forex/Futures/MOEX 明确路由，避免靠 symbol 猜市场 |
| LLM 多轮策略实验 | `services/experiment/runner.py`, `scoring.py` | regime 检测、候选参数、批量回测、评分排名、OOS 验证和早停 |

---

## 源码入口图

| 层 | 入口 | 说明 |
|---|---|---|
| 应用工厂 | `backend_api_python/app/__init__.py` | 初始化 Flask、CORS、JWT 警告、数据库、路由和启动 hooks |
| 路由装配 | `backend_api_python/app/routes/__init__.py` | `init_openapi(app)` 注册人类 API，再挂载 `/api/agent/v1` |
| Agent Gateway | `backend_api_python/app/routes/agent_v1/` | health/markets/strategies/backtests/indicators/experiments/runtime/jobs/quick_trade |
| Agent 认证 | `backend_api_python/app/utils/agent_auth.py` | token hash、scope、market/instrument allowlist、rate limit、audit、idempotency |
| Agent jobs | `backend_api_python/app/utils/agent_jobs.py` | ThreadPoolExecutor、PostgreSQL job row、进度 ring buffer、SSE resume |
| 指标工作区 | `backend_api_python/app/services/indicator_workspace.py` | authoring contract、validate、save、indicator_config auto-link |
| 安全执行 | `backend_api_python/app/utils/safe_exec.py` | 沙箱 `exec`、限制 import/builtin/危险属性、timeout、RLIMIT_AS |
| 回测服务 | `backend_api_python/app/services/backtest.py` | K 线获取、指标执行、信号规范化、回测存储、warmup 估计 |
| 实盘执行 | `backend_api_python/app/services/trading_executor.py` | 运行中策略线程、signal dedup、price cache、script callback timeout |
| 交易客户端 | `backend_api_python/app/services/live_trading/` | Binance/OKX/Bitget/Bybit/Coinbase/Kraken/Gate/HTX/IBKR/Alpaca |
| 数据源工厂 | `backend_api_python/app/data_sources/factory.py` | market normalize、数据源实例化、fd guard、日志去重 |
| MCP Server | `mcp_server/src/quantdinger_mcp/server.py` | 24+ MCP tools 映射 Agent Gateway，环境变量传 base URL/token |
| 部署 | `docker-compose.yml` | PostgreSQL 18、Redis 8、Flask backend、GHCR frontend/mobile、Nginx |

---

## 核心运行流

```text
Human Web UI / Mobile H5
    -> human OpenAPI routes + JWT
    -> shared services / PostgreSQL

External Agent / MCP client
    -> /api/agent/v1 + Bearer qd_agent_* token
    -> scope / allowlist / rate limit / audit
    -> shared services / qd_agent_jobs / qd_agent_audit

Indicator or Script code
    -> authoring contract
    -> safe validation / sandbox execution
    -> qd_indicator_codes or qd_script_sources
    -> backtest / strategy runtime / paper-live execution
```

关键设计：Agent 和人类最终复用同一批 service，避免出现“Web 路径能跑、Agent 路径结果不同”的双实现；但入口认证、权限、审计和长任务语义完全分开。

---

## Agent Gateway 权限模型

| Scope | 含义 | 典型接口 |
|---|---|---|
| `R` | Read | markets、price、klines、jobs、runtime、portfolio、indicator read |
| `W` | Workspace write | save indicator、create/update strategy |
| `B` | Backtest / simulation | submit backtest、experiment pipeline、structured tune |
| `N` | Notifications / misc side effects | 通知类副作用预留 |
| `C` | Credentials | credential/admin 类能力，管理员高风险 |
| `T` | Trading / capital | quick trade、stop runtime 等资本相关动作 |

`T` scope 也不是实盘下单充分条件。HTTP Agent Gateway 还要求 token 的 `paper_only=false` 和服务端 `AGENT_LIVE_TRADING_ENABLED=true`。`confirm_order/confirm_live_trading` 由 MCP 工具额外检查，HTTP 路由本身不检查确认字段。

---

## 和其它项目的差异

| 项目 | 偏重点 | QuantDinger 的不同 |
|---|---|---|
| `tickflow-stock-panel` | 本地 A 股数据湖 + 策略/监控/回测工作台 | QuantDinger 更偏交易 OS，PostgreSQL 运行态、跨市场 broker、Agent Gateway 更完整 |
| `Vibe-Trading` | Agent 化交易实验、LangGraph/MCP/技能生态 | QuantDinger 把 Gateway/MCP 接到真实策略库、凭证、订单和纸面/实盘边界 |
| `PanWatch` | TradingAgents 产品化盯盘、预算/冷却/建议池 | QuantDinger 更接近执行端，强调策略代码、回测、订单和 broker policy |
| `joinquant-skill` | 聚宽策略生成与 AST lint | QuantDinger 是平台内策略生成和运行，不只输出到外部平台 |
| `quant-buddy-skill` | 公式执行与 session/version 审计 | QuantDinger 把 idempotency、jobs、audit 作为 Agent Gateway 基础设施 |
| `Privora Examples` | API quickstart、scope、response shape | QuantDinger 是完整应用里的 Agent API，可参考其 scope + audit + paper-only 组合 |

---

## 直接可借鉴模块

1. **Agent Gateway 双入口**: 人类 API 和 Agent API 分开认证、分开审计，但复用后端 service。
2. **Scope 不是字符串装饰**: 每个路由绑定 R/W/B/N/C/T，token 还能限制 markets、instruments 和 rate limit。
3. **Agent long job 语义**: 回测、实验、调参全部返回 `job_id`，支持 `/jobs/{id}` 查询和 `/jobs/{id}/stream` SSE。
4. **paper-only 默认值**: HTTP 实盘路径由 `T` scope、token `paper_only=false` 和环境 kill switch 解锁；MCP 再增加显式确认。自己的 Gateway 应在服务端统一强制确认。
5. **指标作者契约**: 给 AI 一个可机器读取的 authoring contract，比在 prompt 里反复说“请按格式写”稳定。
6. **四向信号列**: `open_long/close_long/open_short/close_short` 比老式 `buy/sell` 更适合同时支持多空和 spot/swap。
7. **回测范围 policy**: 不同市场和 timeframe 有不同 provider 限制，提前返回结构化建议，别等数据源 400。
8. **Broker policy 单真源**: broker-market-direction-bot 兼容性只写一处，CRUD、worker、前端都读它。
9. **MCP 不抢安全边界**: MCP server 只封装 Gateway；真正权限、审计、scope 都留在后端。
10. **PostgreSQL 运行态表**: strategy/trade/position/backtest/job/audit/paper_order 分表，适合长期运行和审计。

---

## 需要注意的风险和取舍

- Agent jobs 使用本进程 `ThreadPoolExecutor`，低运维但多进程/多实例部署时要注意单例 worker、进度 ring buffer 和分布式锁问题；项目自己的 `docs/CONCURRENCY_MODEL.md` 也把这列为审计重点。
- `safe_exec.py` 是实用沙箱，不等于强隔离容器。用于策略/指标校验时很有价值，但高风险多租户场景仍应考虑独立进程、容器或 WASM/RestrictedPython 等更硬隔离。
- Docker Compose 默认 PostgreSQL/Redis/backend/frontend/mobile 多容器，产品完整但比纯 CLI/skill 项目重。适合交易 OS，不适合只想快速接一个只读数据源的场景。
- live trading 代码覆盖很多 broker/market_type 差异，迁移时应优先借鉴 policy、paper-only 和审计模型，而不是直接复制交易所适配器。
- `with_idempotency()` 查询失败会 fail-open，同步下单又是先执行副作用再写完成记录；它是 best-effort replay guard，不是严格事务幂等。
- `safe_exec_isolated()` 已实现但当前无调用者，主路径仍通过 `safe_exec_code()` 在当前进程执行。
