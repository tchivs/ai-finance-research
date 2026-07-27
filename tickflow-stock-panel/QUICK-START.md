# tickflow-stock-panel 快速概览

> 自托管 A 股「选股 + 监控 + 回测 + 复盘」工作台 · FastAPI + React + Polars/DuckDB/Parquet · TickFlow 能力探测与扩展数据同台分析
> 源码: `/root/source/tmp/tickflow-stock-panel/`
> 原始仓库: <https://github.com/shy3130/tickflow-stock-panel>
> 分析基线：`3656fedc628f84b3f14e41d17f9e5529bd9dc800`（2026-07-06）
> 源码复核：2026-07-10，详见 [首批源码落地验证](../19-首批源码落地验证.md#4-tickflow-stock-panel)

---

## 一句话定位

`tickflow-stock-panel` 不是单纯的行情看板，而是一个个人量化研究工作台：后端把 TickFlow / 第三方数据落成 Parquet 数据湖，用 Polars 计算指标，用 DuckDB 做冷查询，再把策略选股、实时监控、回测、AI 个股分析和盘后复盘统一挂到 React 工作台里。

它最值得学习的地方不是某个页面，而是把「本地数据底座 + 策略系统 + 实时事件 + AI 报告」压进一个单容器、自托管、低运维产品里的工程组织方式。

---

## 最高价值借鉴点

| 借鉴点 | 代码位置 | 可复用价值 |
|---|---|---|
| 能力探测驱动产品降级 | `backend/app/tickflow/capabilities.py`, `policy.py`, `tiers.yaml` | 业务代码不写套餐判断，只读 `CapabilitySet` |
| Parquet 窄表 + Polars 热缓存 + DuckDB 视图 | `backend/app/tickflow/repository.py` | 本地数据湖适合个人量化，部署比数据库轻 |
| 盘后管道增量重算 | `backend/app/jobs/daily_pipeline.py`, `indicators/pipeline.py` | 按新日期、除权变化、历史扩展选择全量/增量 |
| 实时行情单例服务 | `backend/app/services/quote_service.py` | 一个后台线程同时服务看板、监控、策略页和 SSE |
| 策略定义复用选股/监控/回测 | `backend/app/strategy/engine.py`, `backtest/strategy.py` | 策略只写一次，多个执行场景复用 |
| 真实 A 股撮合约束 | `backend/app/backtest/engine.py` | T+1、涨跌停、停牌、仓位上限、手续费、滑点 |
| 通用监控规则引擎 | `backend/app/strategy/monitor.py`, `monitor_rules.py` | signal/price/market/strategy/ladder 统一规则模型 |
| 扩展数据表 | `backend/app/services/ext_data.py`, `api/ext_data.py` | CSV/Excel/JSON/HTTP 拉取并入同一分析体系 |
| AI 适配层 | `backend/app/services/ai_provider.py` | OpenAI 兼容接口与本机 Codex CLI 共用一套生成协议 |
| 单容器部署 | `Dockerfile`, `docker-compose.yml` | 前端 dist、FastAPI、Node 插件运行时合并成一个服务 |

---

## 源码入口图

| 层 | 入口 | 说明 |
|---|---|---|
| 应用启动 | `backend/app/main.py` | 创建 DataStore/Repository、能力探测、调度器、QuoteService、StrategyEngine、MonitorRuleEngine |
| 配置 | `backend/app/config.py` | `.env`、桌面版路径、静态前端目录、数据目录 |
| 数据存储 | `backend/app/tickflow/repository.py` | `DataStore` 管目录和 DuckDB 视图，`KlineRepository` 管缓存和读写 |
| 数据同步 | `backend/app/jobs/daily_pipeline.py` | 盘前/盘后任务、手动跑管道、增量 enriched 计算 |
| 指标计算 | `backend/app/indicators/pipeline.py` | 前复权、MA/EMA/MACD/RSI/KDJ/BOLL/涨跌停/自定义信号 |
| 策略系统 | `backend/app/strategy/engine.py` | 加载策略文件、基础过滤、策略过滤、评分排序 |
| 回测系统 | `backend/app/backtest/engine.py` | 自研账户级撮合引擎；旧信号接口仍有 vectorbt 边界 |
| 实时行情 | `backend/app/services/quote_service.py` | 拉行情、落盘、增量指标、广播 SSE、触发监控 |
| 前端路由 | `frontend/src/router.tsx` | 看板、自选、策略、回测、个股分析、监控、复盘、设置等页面 |
| API 客户端 | `frontend/src/lib/api.ts` | 前端所有 HTTP 类型和请求函数集中定义 |
| 全局 SSE | `frontend/src/lib/useQuoteStream.ts` | 监听行情更新、监控告警、复盘进度、盘口修正 |

---

## 核心数据流

```text
TickFlow / 自定义数据源
    ↓
盘前维表 + 盘后日K / 除权 / 指数 / ETF / 分钟K 同步
    ↓
data/ 下 Parquet 分区
    ↓
DuckDB 只读视图 + Polars scan_parquet
    ↓
enriched 窄表存储 14 列基础字段
    ↓
运行时即时补全技术指标和信号列
    ↓
看板 / 选股 / 监控 / 回测 / AI 分析 / 复盘
```

关键设计：`kline_daily_enriched` 落盘时不存所有指标，只存 OHLCV、原始价、换手率、连板数等 14 列。完整指标在服务读取时用 Polars 即时计算，最新日和历史窗口会进入内存缓存。这减少了落盘体积，也避免指标定义变更时迁移全量宽表。

---

## 和其它项目的差异

| 项目 | 偏重点 | tickflow-stock-panel 的不同 |
|---|---|---|
| `daily_stock_data` | 数据采集底座 | tickflow 直接面向应用，把数据采集、指标、策略、页面打通 |
| `daily_stock_analysis` | 多源 + LLM 分析 | tickflow 的 AI 是附加层，核心还是本地量化工作台 |
| `UZI-Skill` | 深度报告流水线 | tickflow 的报告更轻，但更强调交互、监控和回测闭环 |
| `Vibe-Trading` | Agent + 交易能力 | tickflow 暂不追求复杂 Agent，强在自托管与个人可用性 |

---

## 直接可借鉴模块

1. **能力探测模型**: 用 `Cap` 枚举和 `CapabilitySet` 替代硬编码套餐，功能按能力开启/灰显。
2. **数据目录契约**: `DataStore` 统一创建 `kline_daily/`, `kline_daily_enriched/`, `financials/`, `ext_data/`, `user_data/` 等目录。
3. **窄表 enriched**: 落盘只存稳定字段，指标列运行时计算，适合频繁调整因子的早期产品。
4. **StrategyDef 复用**: 选股、监控、回测共享策略定义和候选逻辑；回测另有 entry/exit 与撮合语义，监控使用候选池 diff，不应假定三者结果天然一致。
5. **实时事件总线**: 一个 `/api/intraday/stream` SSE 通道承载行情刷新、告警、复盘进度、五档修正。
6. **扩展数据表**: 把任意第三方字段作为 `ext_data/{id}` 表挂进菜单、选股结果和板块聚合。
7. **AI 只做有边界的生成**: 策略生成经过 AST 白名单校验，分析报告走 NDJSON 流式协议，AI 不直接触碰业务状态。

---

## 需要注意的文档滞后

- `docs/features.md` 写“20 个内置策略”，当前源码 `backend/app/strategy/builtin/` 是 18 个策略文件，`docs/strategy.md` 的“18 个”更接近源码。
- README 把回测概括为 vectorbt，但源码里策略回测主路径已经是 `app.backtest.engine.BacktestEngine` 自研撮合；`vectorbt` 主要保留在旧的信号回测服务 `app/services/backtest.py`。
- 自定义数据源有两套概念：`docs/custom-data-source.md` 讲的是行情源 YAML；代码里的 `ext_data` 讲的是可挂菜单、可上传/拉取的扩展分析表，两者应在正式文档里明确区分。
- `detect_capabilities()` 捕获所有探测异常后降级到 `none`，自己的实现应保留 network/config/provider 等失败原因，避免把故障误报成无能力。
- `JobStore` 只持久化终态，活跃任务和锁都在进程内，适用于单实例工作台，不是多 worker 任务协调器。
