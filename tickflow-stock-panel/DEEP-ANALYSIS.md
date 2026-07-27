# tickflow-stock-panel 深度代码分析

> 自托管 A 股量化工作台 · 能力探测 · Parquet 本地数据湖 · Polars 指标流水线 · 策略/监控/回测复用 · AI 复盘与报告
> 源码: `/root/source/tmp/tickflow-stock-panel/`
> 原始仓库: <https://github.com/shy3130/tickflow-stock-panel>
> 分析基线：`3656fedc628f84b3f14e41d17f9e5529bd9dc800`（2026-07-06）
> 源码复核：2026-07-10，详见 [首批源码落地验证](../19-首批源码落地验证.md#4-tickflow-stock-panel)

---

## 1. 总体架构

### 1.1 技术栈

| 层 | 技术 | 作用 |
|---|---|---|
| 后端 API | FastAPI / Pydantic v2 / sse-starlette | HTTP API、SSE、认证中间件、静态前端托管 |
| 调度 | APScheduler | 盘前维表、盘后管道、扩展拉取、财务同步入口 |
| 计算 | Polars / NumPy | 指标、选股、回测信号、板块聚合 |
| 查询 | DuckDB in-memory | 直接把 Parquet 目录注册成只读视图 |
| 存储 | Parquet + JSON/JSONL | 行情、指标窄表、财务、扩展表、用户配置、告警记录 |
| 回测 | 自研 `BacktestEngine` + 旧 vectorbt 边界 | 策略组合撮合、因子回测、旧信号回测 |
| 前端 | React 18 / Vite / TypeScript / Tailwind / TanStack Query | 多页面量化工作台 |
| 图表 | ECharts / lightweight-charts | K 线、盘面、指标图表 |
| AI | OpenAI compatible / Codex CLI | 策略生成、个股分析、财务分析、大盘复盘 |
| 部署 | Docker 单容器 | 前端 dist 拷进后端镜像，后端托管静态文件 |

### 1.2 目录分层

```text
backend/app/
  main.py                 FastAPI 生命周期与路由装配
  config.py               环境变量、数据目录、静态目录
  api/                    HTTP API 路由
  tickflow/               TickFlow SDK、能力探测、Repository
  jobs/                   盘前/盘后调度任务
  indicators/             enriched 指标与关键价位计算
  strategy/               策略引擎、自定义信号、监控规则、AI 生成
  backtest/               自研回测引擎、因子回测、策略回测
  services/               业务服务: 行情、财务、复盘、扩展数据、告警等

frontend/src/
  router.tsx              页面路由
  pages/                  工作台页面
  components/             通用组件和领域组件
  lib/api.ts              统一 API 类型与请求入口
  lib/useQuoteStream.ts   全局 SSE 客户端
```

### 1.3 运行时启动顺序

核心入口是 `backend/app/main.py` 的 `lifespan()`。启动顺序很关键：

1. 初始化访问密码：`auth.bootstrap_from_env()` 只在未设密码时读取 `AUTH_PASSWORD`。
2. 创建数据层：`DataStore()` 建目录并注册 DuckDB 视图，`KlineRepository()` 管缓存。
3. 异步预热 enriched：`repo.refresh_cache(background=True)` 让大表指标计算不阻塞启动。
4. 能力探测：`detect_capabilities()` 写入 `app.state.capabilities`。
5. 加载自定义数据源：`app.data_providers.custom.load_all()`，失败不阻塞启动。
6. 创建实时行情服务：`QuoteService()` 注入 repo，后续负责行情、SSE、监控触发。
7. 创建旧策略监控服务和五档盘口服务：`StrategyMonitorService`、`DepthService`。
8. 启动盘前/盘后调度：`daily_pipeline.start_scheduler(repo, capset)`。
9. 启动扩展数据拉取调度：`pull_scheduler.start()`。
10. 初始化内置扩展表配置：`ensure_builtin_presets()` 只建配置，不自动拉数据。
11. 初始化财务同步调度器：`financial_scheduler.start()`，手动触发为主。
12. 创建策略引擎：加载 `strategy/builtin/`、`data/strategies/custom/`、`data/strategies/ai/`。
13. 创建通用监控规则引擎：加载 `data/user_data/monitor_rules/*.json`，注入策略引擎和历史 loader。

这套启动方式的优点是“功能失败不拖垮主服务”：自定义源、财务、盘口、调度器出错都只记 warning，主 API 仍可用。

---

## 2. 数据底座: Parquet + DuckDB + Polars 缓存

### 2.1 DataStore 是唯一存储入口

`backend/app/tickflow/repository.py` 的 `DataStore` 启动时创建一组固定目录：

| 目录 | 用途 |
|---|---|
| `kline_daily/` | A 股日 K 原始/不复权数据 |
| `kline_daily_enriched/` | A 股 enriched 窄表分区 |
| `kline_index_daily/`, `kline_index_enriched/` | 指数数据 |
| `kline_etf_daily/`, `kline_etf_enriched/`, `kline_etf_minute/` | ETF 数据 |
| `kline_minute/` | 个股分钟 K |
| `adj_factor/`, `adj_factor_etf/` | 除权因子 |
| `financials/{metrics,income,balance_sheet,cash_flow}/` | 财务表 |
| `instruments/`, `instruments_index/`, `instruments_etf/` | 标的维表 |
| `ext_data/` | 用户扩展数据表配置与 Parquet |
| `user_data/` | 监控规则、自定义信号、偏好等用户配置 |
| `depth5/` | 五档盘口 sealed 旁路数据 |

`DataStore` 使用 `duckdb.connect(database=":memory:")`，不落 `.db` 文件。所有视图都从 Parquet glob 读取，例如 `kline_daily`, `kline_enriched`, `financials_metrics`, `depth5`。这意味着磁盘真相是 Parquet，DuckDB 只是查询层。

### 2.2 DuckDB 视图不是热路径

源码注释明确分层：

```text
DuckDB 视图        冷查询、统计、元数据、用户 SQL
Polars 内存缓存     热路径，最新 enriched 和 instruments
Polars scan_parquet 历史日K、分钟K、predicate pushdown
```

`KlineRepository.execute_all()` 和 `execute_one()` 给 DuckDB 加锁，因为单 connection 非线程安全。热路径尽量不走 DuckDB，避免并发读写互相影响。

### 2.3 enriched 是“窄表存储，宽表运行时”

`backend/app/indicators/pipeline.py` 定义的 `ENRICHED_STORAGE_COLS` 只有 14 列：

```text
symbol, date, open, high, low, close,
volume, amount,
raw_close, raw_high, raw_low,
turnover_rate,
consecutive_limit_ups, consecutive_limit_downs
```

完整指标列包括 MA、EMA、MACD、BOLL、KDJ、ATR、RSI、动量、波动率、涨跌停信号、自定义信号等。这些不全量落盘，而是在读取时即时计算并缓存。

好处：

1. 指标公式变更时不用迁移历史宽表。
2. Parquet 分区更小，适合个人 VPS 或桌面版。
3. 选股、回测、AI 都能共用同一套计算函数，减少口径漂移。

代价：

1. 启动或首次访问时需要预热指标。
2. `filter_history` 策略依赖历史窗口缓存，否则会退到较慢的 `scan_parquet + compute_indicators`。

### 2.4 KlineRepository 的缓存策略

`KlineRepository.refresh_cache(background=True)` 在启动时同步刷新维表，但把 enriched 重计算丢到 daemon 线程：

- `instruments/index/ETF instruments` 同步刷新，毫秒级。
- `enriched` 后台预热，低配机器可能几十秒。
- 预热期间 `get_enriched_latest()` 可优雅降级为空表。
- 盘后管道完成后用 `background=False` 同步刷新，保证数据一致。

这是一个很实用的自托管策略：服务先可用，重计算慢慢补齐。

---

## 3. 能力探测与套餐解耦

### 3.1 CapabilitySet 是业务真相

`backend/app/tickflow/capabilities.py` 定义 `Cap` 枚举，例如：

| Capability | 说明 |
|---|---|
| `quote.by_symbol` | 按标的实时行情 |
| `quote.batch` / `quote.pool` | 批量行情 / 标的池行情 |
| `kline.daily.by_symbol` / `kline.daily.batch` | 日 K 单只 / 批量 |
| `kline.minute.*` | 分钟 K |
| `depth5`, `depth5.batch` | 五档盘口 |
| `financial` | 财务表 |
| `adj_factor` | 除权因子 |
| `websocket` | WebSocket 订阅能力 |

业务代码调用 `capset.has(Cap.KLINE_DAILY_BATCH)`，而不是写 `if tier == "pro"`。

### 3.2 tiers.yaml 只做探测参考

`tiers.yaml` 的注释强调“业务代码永远不读这张表，只读运行时探测出的 CapabilitySet”。它主要用于：

1. 启动期决定探测顺序。
2. UI 反查友好档位标签。
3. 没有响应头限流信息时给默认 rpm/batch。

### 3.3 真实探测避免 Key 误判

`backend/app/tickflow/policy.py` 的 `_probe_real()` 强制用付费端点验证 API Key，避免“旧缓存是 none 档，所以走 free server，乱填 key 也看似可用”的循环误判。

档位判定逻辑：

| 判定 | 结果 |
|---|---|
| 连单只日 K 都不可用 | invalid key，归 none |
| 有单只日 K、无复权因子 | free |
| 有复权因子 | starter+，再用 signature capability 判断 starter/pro/expert |

### 3.4 none/free 的端点分流

`backend/app/tickflow/client.py` 把端点分成：

- `none`: 无 key / 无效 key，走 `TickFlow.free()`，仅历史日 K。
- `free`: 有免费有效 key，历史日 K 仍走 free-api，实时自选按标的走付费端点。
- `starter/pro/expert`: 付费 key，走 `api.tickflow.org` 或用户测速切换端点。

这个分流比“有 key 就用付费端点”更细，能把免费用户的历史数据能力和实时小能力区分开。

---

## 4. 盘后管道与指标流水线

### 4.1 daily_pipeline.run_now 的阶段

`backend/app/jobs/daily_pipeline.py` 的 `run_now()` 是手动和调度共用的盘后主流程：

1. 同步个股维表 `sync_instruments`。
2. 解析标的池：有 batch 能力走 `CN_Equity_A`，否则用 instruments + watchlist + demo 兜底。
3. 同步 A 股日 K：
   - 今天已有数据且有 `quote.pool`，用实时行情覆写今天。
   - 有历史数据，按缺口补齐。
   - 首次启动，拉近一年。
4. 同步除权因子：按日 K 拉取范围或最近 15 天兜底。
5. 计算 enriched：全量、向后增量、除权影响个股重算三种路径。
6. 同步指数 / ETF：由设置开关控制，物理分开存储。
7. 同步分钟 K：可选，需 `kline.minute.batch`。
8. 刷新 DuckDB 视图与缓存。
9. 返回 `skipped_stages` 给前端展示能力或配置导致的跳过。

### 4.2 enriched 全量与增量规则

`indicators/pipeline.py` 的 `run_pipeline()` 支持三种模式：

| 模式 | 触发场景 | 行为 |
|---|---|---|
| 全量 | 首次同步、往前扩展历史 | 读全部 `kline_daily`，重写 enriched 分区 |
| 向后增量 | 新增晚于现有 enriched 的日期 | 只计算新日期，并可重算受除权影响个股 |
| 除权因子增量 | 无新日 K 但除权因子变化 | 只重算受影响 symbol 的全部日期并合并回分区 |

这个设计处理了 A 股复权的一个真实问题：除权因子改变的是累积链，不只是当天一根 K 线。

### 4.3 涨跌停计算很细

`_limit_price()` 用“分”为单位的整数算术来算涨跌停价，避免浮点误差，例如 `18.90 * 0.95` 变成 `17.954999...` 后四舍五入错误。

这是金融系统里非常值得保留的细节：交易规则里的价格精度不能直接依赖二进制浮点。

### 4.4 自定义信号注入

`backend/app/strategy/custom_signals.py` 把 UI 配置的 `字段 + 运算符 + 右值` 编译成 Polars 表达式，并注入为 `csg_{id}` 列。

设计要点：

- 信号列名前缀 `csg_`，避免和内置 `signal_` 冲突。
- 字段白名单和运算符白名单，避免任意表达式注入。
- 自定义信号进入 enriched 运行时宽表后，选股、回测、监控都能按列名直接使用。

---

## 5. 策略系统

### 5.1 当前源码策略数量

当前 `backend/app/strategy/builtin/` 下有 18 个策略文件，排除 `__init__.py`。`docs/strategy.md` 的“18 个”与源码一致，`docs/features.md` 的“20 个”是文档滞后。

代表策略包括：

```text
trend_breakout, ma_golden_cross, macd_golden, boll_breakout,
volume_price_surge, consecutive_limit_ups, broken_board_recovery,
limit_up_momentum, near_limit_up, high_turnover_surge,
oversold_bounce, oversold_reversal, n_day_low_reversal,
low_volatility_leader, pullback_to_support, pullback_ma20_bounce,
strong_open, bullish_alignment
```

### 5.2 StrategyDef 是统一策略契约

`backend/app/strategy/engine.py` 加载每个 `.py` 策略文件，归一成 `StrategyDef`：

| 字段 | 作用 |
|---|---|
| `META` | id、name、description、params、scoring、limit 等 |
| `BASIC_FILTER` | 价格、市值、成交额、ST、板块等基础过滤 |
| `filter(df, params)` | 单日 Polars 表达式过滤 |
| `filter_history(df, params)` | 多日窗口策略，返回 DataFrame |
| `LOOKBACK_DAYS` | 历史窗口长度 |
| `ENTRY_SIGNALS` / `EXIT_SIGNALS` | 回测和监控使用的信号列 |
| `STOP_LOSS`, `MAX_HOLD_DAYS` 等 | 策略级风控参数 |

### 5.3 执行流程

`StrategyEngine.run()` 的执行链是：

```text
加载 enriched 最新日或历史窗口
    ↓
合并策略默认 basic_filter 与用户 overrides
    ↓
基础过滤
    ↓
股票池 pool 过滤
    ↓
策略 filter / filter_history
    ↓
scoring 归一评分
    ↓
排序、limit、JSON 安全清洗
```

`run_all()` 会共享同一天 enriched 和历史窗口，并按 `basic_filter` hash 做缓存，避免每个策略重复基础过滤。

### 5.4 ScreenerService 的双轨历史

`backend/app/services/screener.py` 里还有一份 `PRESET_STRATEGIES`，这是早期内置预设路径；API 会先返回这些 preset，再补 StrategyEngine 中未重复的策略。当前代码形成“双轨”：

- `PRESET_STRATEGIES`: 旧预设，直接在 service 中写 Polars 表达式。
- `strategy/builtin/*.py`: 新策略文件体系，走 `StrategyEngine`。

文档和产品上最好逐步收敛到后一种，否则策略数量和能力描述容易不一致。

### 5.5 AI 策略生成有边界

`backend/app/strategy/ai_generator.py` 读取 `strategy/prompts/strategy-guide.md`，调用 `ai_provider.generate_ai_text()` 生成单文件策略。安全限制比较明确：

- 只允许 `import polars` 和 `__future__`。
- 禁止 `open`, `exec`, `eval`, `compile`, `__import__`, `getattr`, `setattr` 等危险调用。
- `META` 用 `ast.literal_eval` 解析，不执行代码。
- 生成策略落在 `data/strategies/ai/`，不允许改源码目录。

这是一种务实的“AI 生成代码但不越权”的模式。

---

## 6. 回测系统

### 6.1 三条回测路径

`backend/app/api/backtest.py` 提供：

| 路径 | 说明 | 主要实现 |
|---|---|---|
| `/api/backtest/run` | 旧信号回测 | `services/backtest.py` + vectorbt |
| `/api/backtest/factor/run` | 因子 IC/IR 与分层回测 | `backtest/factor.py` |
| `/api/backtest/strategy/run` | 策略组合回测 | `backtest/strategy.py` + `backtest/engine.py` |
| `/api/backtest/strategy/stream` | SSE 策略回测 | 后台线程 + job cache |

README/功能文档把回测概括为 vectorbt，但策略回测主路径已经是自研撮合引擎。vectorbt 是可选 extra，主要服务旧接口。

### 6.2 策略回测复用 StrategyDef

`StrategyBacktestService.run()` 的关键点：

1. 通过 `strategy_engine.get(strategy_id)` 拿同一个策略定义。
2. 加载含 warmup 的 panel，warmup 用于指标和形态计算，不参与正式交易。
3. `basic_filter` 只影响买入候选，不删除行情行，避免持仓 mark 和卖出失真。
4. 候选过滤、评分、入场信号、出场信号分层处理。
5. 传给 `BacktestEngine` 做撮合。
6. 返回净值、回撤、benchmark、交易明细、个股统计。

这解决了一个常见错误：不能为了选股过滤直接把行情面板删掉，否则回测持仓期间的价格序列会断。

### 6.3 自研撮合更贴近 A 股

`BacktestEngine.simulate_portfolio()` 处理了很多 vectorbt 默认不够贴近 A 股的约束：

- `entry_fill` / `exit_fill` 可分别选择 `close_t` 或 `open_t+1`。
- `open_t+1` 会把信号右移到同一 symbol 的下一根 K。
- 一字涨停不能买，一字跌停不能卖。
- 停牌或无效价格跳过。
- 手续费、印花税、滑点分买卖方向处理。
- 最大持仓数、最大敞口、资金不足、整手限制、当天卖出后不重复买入。
- 止损、止盈、移动止损、最大持仓天数。
- `execution_stats` 记录无法成交原因，便于解释回测差异。

### 6.4 SSE 回测任务模型

`/api/backtest/strategy/stream` 使用参数 hash 生成 job key：

- 相同参数只启动一个后台线程。
- 断开连接不取消任务。
- 进度存在 `job.progress` 列表，新连接可从头回放。
- 结果保留 5 分钟。
- `/strategy/cancel` 根据同一 query string 算 job key 并设置 `cancel_event`。

前端 `frontend/src/lib/backtestTask.ts` 用模块级 store + `localStorage` 保存 reconnect query，切页或刷新后能重连同一任务。

---

## 7. 实时行情、SSE 与监控

### 7.1 QuoteService 是盘中核心单例

`backend/app/services/quote_service.py` 的职责很重，但边界清楚：

```text
后台线程拉行情
    ↓
写 kline_daily 当日分区
    ↓
增量计算 today enriched
    ↓
替换 KlineRepository 最新日缓存
    ↓
评估 MonitorRuleEngine
    ↓
广播 SSE: quotes_updated / strategy_alert / depth_updated / review_progress
```

不同档位有不同实时模式：

- `none`: 不允许实时行情。
- `free`: 自选股实时。
- `starter+`: 全市场实时。

轮询间隔也按档位限制：expert 1s、pro 2s、starter 3s、free 6s，最大 60s。

### 7.2 SSE 订阅者设计修过多客户端竞态

旧问题：多个 SSE 连接共用服务级 Event 和 pending 列表，先醒来的连接会把告警 pop 掉，其他标签页收不到。

当前设计：每个连接一个 `QuoteSubscriber`，内部有独立 Event 和队列。`QuoteService` 广播事件到所有 subscriber。

这对多标签页、多设备的个人看板很重要。

### 7.3 通用监控规则引擎

`backend/app/strategy/monitor.py` 的 `MonitorRuleEngine` 支持五类规则：

| 类型 | 含义 |
|---|---|
| `strategy` | 跑策略选股，对比上期选股池，产生新入选/移出 |
| `signal` | 布尔信号列触发，如 `signal_macd_golden` |
| `price` | 单股价格或指标阈值 |
| `market` | 全市场条件，如跌幅超过阈值 |
| `ladder` | 连板梯队封单监控，依赖五档盘口能力 |

规则持久化在 `data/user_data/monitor_rules/*.json`，校验逻辑在 `strategy/monitor_rules.py`。触发时按 `(rule_id, symbol)` 做 cooldown 去重。

### 7.4 策略监控的实时回显

`MonitorRuleEngine._match_strategy()` 会把每轮策略选股结果暂存在 `_latest_strategy_results`，供 `/api/screener/cached` 读取。这样策略页不需要为实时监控再跑第二遍选股。

对于 `filter_history` 策略，监控引擎会把历史窗口和今日实时行情拼起来再跑，避免“反包”等历史形态策略盘中永不触发。

### 7.5 告警落盘

`backend/app/services/alert_store.py` 用 JSONL 追加写：

- 路径：`data/user_data/alerts.jsonl`。
- 每行一个事件。
- 保留近 7 天和最多 5000 条。
- 每 20 次写入触发 prune。
- 读写都加锁，避免 prune/clear 重写时读到截断文件。

---

## 8. 扩展数据与自定义数据源

### 8.1 两种“外部数据”概念

项目里有两套容易混淆的扩展机制：

| 机制 | 位置 | 作用 |
|---|---|---|
| 自定义行情数据源 | `backend/app/data_providers/custom/`, `docs/custom-data-source.md` | 用 YAML 接入 daily / adj_factor / realtime，替代或补充 TickFlow 行情源 |
| 扩展分析表 | `backend/app/services/ext_data.py`, `api/ext_data.py` | 上传/拉取任意第三方字段，挂菜单、做板块、投影到选股结果 |

文档应该把这两者分开说明，否则用户会误以为“自定义数据源”只能接行情，或以为扩展表能替代 K 线源。

### 8.2 扩展分析表的数据模型

`ExtConfig` 包含：

- `id`, `label`, `description`
- `mode`: `snapshot` 或 `timeseries`
- `fields`: 字段名、类型、展示 label
- `symbol_map` / `code_map`: 标的代码映射规则
- `pull`: HTTP 定时拉取配置

存储结构：

```text
data/ext_data/{id}/config.json
data/ext_data/{id}/part.parquet
data/ext_data/{id}/timeseries/date=YYYY-MM-DD/part.parquet
```

### 8.3 扩展表的写入方式

支持三种写入：

1. CSV / Excel 上传：`parse_upload_file()` 处理 UTF-8/GBK/GB18030/Big5 编码和 symbol 列识别。
2. JSON 批量写入：`rows_to_parquet()`。
3. HTTP 定时拉取：`PullConfig` + `ext_pull.fetch_and_ingest()`。

`normalize_symbol()` 优先用 instruments 维表做 `code -> symbol` 映射，查不到再按 6 开头 SH、其他 SZ 兜底。

### 8.4 扩展表进入业务分析

扩展表不是孤立展示：

- `api/screener.py` 的 `_load_ext_value_maps()` 可以把扩展字段投影到选股结果行。
- `market_overview_builder.py` 会从扩展表里识别“概念/行业”字段，聚合领涨领跌。
- `rps_rotation.py` 复用同一套概念映射，构建概念涨幅 RPS 轮动矩阵。
- `analysis.py` 和前端 `AnalysisDetail` 支持把扩展表配置成动态菜单。

这就是“自由接入第三方数据并同台分析”的实际代码支撑。

---

## 9. AI 功能边界

### 9.1 统一 AI Provider

`backend/app/services/ai_provider.py` 支持两类 provider：

| Provider | 说明 |
|---|---|
| `openai_compat` | OpenAI 兼容 Chat Completions，支持流式 |
| `codex_cli` | 调本机 `codex exec --sandbox read-only`，只读临时空工作区 |

`generate_ai_text()` 用于一次性生成，`stream_ai_text()` 用于流式报告。Codex CLI 不是真流式，会在命令结束后吐一个完整 chunk。

### 9.2 三类报告流式协议一致

个股分析、财务分析、大盘复盘都使用 NDJSON 风格事件：

```text
{"type":"meta", ...}
{"type":"delta", "content":"..."}
{"type":"error", "message":"..."}
{"type":"done"}
```

| 功能 | 实现 | 数据上下文 |
|---|---|---|
| 个股分析 | `services/stock_analyzer.py` | 日 K、技术指标、关键价位、轻量财务 |
| 财务分析 | `services/financial_analyzer.py` | metrics / income / balance_sheet / cash_flow |
| 大盘复盘 | `services/market_recap.py` | `market_overview_builder` 同源市场总览 |

### 9.3 AI 不直接写业务状态

AI 的输出要么是文本报告，要么是策略代码草稿。真正落盘前仍经过：

- API 层保存动作。
- 策略 AST 安全校验。
- 报告历史存储服务。
- 前端显式交互。

这是适合个人量化产品的安全边界：AI 提供生成能力，不直接操纵数据底座。

---

## 10. 前端工作台结构

### 10.1 路由和页面

`frontend/src/router.tsx` 挂了一个 `OnboardingGuard`，未完成向导时跳 `/onboarding`。主页面包括：

| 路由 | 页面 |
|---|---|
| `/` | Dashboard 看板 |
| `/watchlist` | 自选 |
| `/screener` | 策略选股 |
| `/backtest` | 回测 |
| `/stock-analysis` | 个股分析 |
| `/limit-ladder` | 连板梯队 |
| `/concept-analysis` | 概念分析 |
| `/industry-analysis` | 行业分析 |
| `/financials` | 财务分析 |
| `/monitor` | 监控中心 |
| `/review` | 盘后复盘 |
| `/indices` | 指数 |
| `/trading` | 交易占位/外部交易 |
| `/data` | 数据状态 |
| `/settings` | 设置 |

### 10.2 Layout 负责全局状态

`frontend/src/components/Layout.tsx` 不只是布局，还负责：

- 菜单、动态菜单、隐藏路由。
- TickFlow 档位徽标和 AI 配置徽标。
- 指数行情侧边栏。
- 实时行情开关。
- 监控未读徽标。
- 挂载 `useQuoteStream()`。
- 挂载 `ToastContainer` 和 `AlertToastContainer`。

### 10.3 API 客户端集中但文件过大

`frontend/src/lib/api.ts` 集中了大量类型和函数，文件超过 2000 行。好处是类型入口统一；坏处是领域边界不清，后续维护可以按模块拆成 `api/backtest.ts`, `api/screener.ts`, `api/settings.ts` 等。

### 10.4 SSE 前端处理

`frontend/src/lib/useQuoteStream.ts` 监听：

- `quotes_updated`: 按用户设置选择性 invalidate TanStack Query key。
- `depth_updated`: 刷新连板梯队和看板封单数据。
- `strategy_alert`: 弹监控专用 toast，刷新告警列表和未读数。
- `review_progress`: 喂给复盘 store，支持定时复盘边生成边显示。

告警 toast 在 `AlertToast.tsx` 里做批量入队，一批只响一声，并受最大可见数量限制。

---

## 11. 部署与工程治理

### 11.1 单容器部署

`Dockerfile` 是两阶段加一个插件阶段：

1. `frontend-builder`: Node 20 alpine 构建 Vite dist。
2. `stocksdk-builder`: 安装 `backend/app/plugins/stocksdk` 的 Node 依赖。
3. `runtime`: Python 3.11 slim，安装 Node.js 运行时、uv、后端依赖，拷前端 dist 到 `/app/static`。

最终 `uvicorn app.main:app` 同时提供 API 和前端静态资源。

### 11.2 数据卷保护

`docker-compose.yml` 强制设置 `DATA_DIR=/app/data`，并挂载 `./data:/app/data`。注释里明确说明这样做是为了避免 `.env` 里的相对路径在容器内解析到未挂载目录，导致重建容器后数据丢失。

这是很实用的部署防错设计。

### 11.3 测试覆盖现状

`backend/tests/` 当前主要覆盖：

- 回测成本模型、组合回测、尾部模拟、策略回测正确性。
- AI provider。
- stock-sdk provider。

缺口：

- 盘后管道缺少端到端回归测试。
- MonitorRuleEngine 的规则类型和 cooldown 缺少系统测试。
- ext_data 的上传/拉取/投影缺少覆盖。
- 前端没有看到 E2E 测试配置。

对一个功能面很宽的工作台来说，回测测试优先级做对了，但数据管道和监控还需要补测试。

---

## 12. 可迁移到当前项目的设计模式

### 12.1 Capability First

不要把产品能力写死成套餐名，而是：

```text
探测真实能力 → CapabilitySet → API 和 UI 都按能力启停
```

这适合任何有外部 API 配额、Key 档位或插件能力差异的系统。

### 12.2 本地数据湖优先

对个人量化工具，Parquet + DuckDB + Polars 可能比 PostgreSQL 更合适：

- 少运维。
- 批量扫表快。
- 文件可备份、可迁移。
- 和 Python/Arrow 生态贴合。

### 12.3 窄表持久化，宽表运行时

对指标频繁迭代的项目，先不要把每个指标都固化到存储。可以持久化稳定事实字段，运行时补指标，并把最新窗口做内存缓存。

### 12.4 策略一次定义，多场景执行

把策略文件设计成声明式/半声明式契约，而不是“只服务某个页面”的函数。`StrategyDef` 同时给：

- 选股页跑结果。
- 监控页跑实时 diff。
- 回测页生成 entry/exit mask。
- AI 生成器提供约束。

### 12.5 SSE 事件总线

个人工作台不一定需要 WebSocket。一个标准 SSE 通道加事件名，已经能覆盖：

- 行情刷新通知。
- 告警推送。
- 长任务进度。
- AI 流式报告。
- 后台修正通知。

### 12.6 扩展表进入核心分析

不要只做“上传 CSV 展示表格”。更有价值的是把扩展字段并入：

- 选股结果列。
- 看板维度聚合。
- 复盘上下文。
- 动态菜单。

`ext_data` 这一点值得重点借鉴。

---

## 13. 代码风险与文档补充建议

### 13.1 文档需修正的点

1. `features.md` 的内置策略数量应从 20 改为 18，或改成“以策略页实际加载为准”。
2. 回测文档应区分旧 `vectorbt` 信号回测和当前自研 `BacktestEngine` 策略回测。
3. 自定义行情源和扩展分析表应拆成两个章节。
4. 监控文档应补充 `ladder` 类型、cooldown 键、JSONL 保留策略。
5. AI 文档应说明 `codex_cli` provider 的只读沙箱和非真流式行为。

### 13.2 代码可优化点

| 问题 | 影响 | 建议 |
|---|---|---|
| `frontend/src/lib/api.ts` 过大 | 类型和请求边界难维护 | 按领域拆分 API 模块 |
| `QuoteService` 职责偏重 | 行情、落盘、指标、监控、通知都在一个类 | 中长期拆出 event bus / monitor dispatcher |
| Screener 双轨策略 | 文档和数量容易不一致 | 逐步把 `PRESET_STRATEGIES` 迁入策略文件体系 |
| ext_data 与 data_provider 命名接近 | 用户理解成本高 | 文档和 UI 用“行情源”“扩展分析表”明确区分 |
| 部分核心流程缺测试 | 管道和监控回归风险 | 补 pipeline、monitor、ext_data 的 focused tests |

### 13.3 仍然很强的工程点

即使有上述可优化点，这个项目已经具备个人量化产品很难同时做到的几个能力：

- 数据同步、实时行情、策略、回测、监控、AI 报告在一个本地闭环里。
- 能力探测和配置降级做得细，不是简单“有 key/没 key”。
- 回测撮合逻辑开始贴近 A 股真实约束。
- 扩展数据不是装饰功能，而是真能进入分析主链。

### 13.4 源码复核后的边界

1. `detect_capabilities()` 的最外层异常会统一降级为 `none` 档。稳定启动的代价是网络、配置和 provider 故障可能被压成“无能力”，迁移时应保留结构化失败原因。
2. `StrategyDef` 的共享已经落到真实调用链，但执行语义不同：选股做过滤和评分，监控比较候选池变化，回测额外执行 entry/exit、成本和撮合。应通过跨执行器一致性测试约束，而不是只共享一个类型。
3. `JobStore` 只把成功/失败终态写 JSON；pending/running、进度和 `_active_id` 位于进程内。它是单实例本地任务模型，不适合作为多进程队列。

---

## 14. 对 HermesAlpha / ashare-audit 的启发

| 当前项目需求 | 可借鉴设计 |
|---|---|
| A 股数据底座 | `DataStore` 目录契约 + DuckDB 视图 + Polars 缓存 |
| 策略/因子快速迭代 | enriched 窄表 + 运行时指标宽表 |
| 多源能力差异 | `CapabilitySet` 统一能力模型 |
| 策略回测一致性 | `StrategyDef` 共享定义，另用跨执行器测试约束选股、监控和回测语义 |
| 用户扩展数据 | `ext_data` 快照/时序表 + symbol 标准化 |
| 监控告警 | `MonitorRuleEngine` + JSONL 触发记录 + SSE toast |
| AI 报告 | NDJSON `meta/delta/error/done` 协议 |
| 自托管部署 | 前后端单容器 + 数据卷强制绝对路径 |

最值得优先吸收的是三件事：

1. **能力模型**: 任何外部数据/API/插件都统一抽象为 capability。
2. **数据窄表**: 先保证稳定事实字段可靠，指标和信号在运行时统一计算。
3. **策略契约**: 策略文件不绑定 UI，天然可被选股、监控、回测复用。
