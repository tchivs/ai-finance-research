# Financial-API 深度分析

> 同花顺官方 A 股数据接入层 · REST/MCP/CLI/Python/DuckDB 一套认证与多端路由
> 源码: `/root/source/docs/aaa/src/Financial-API/`
> 原始仓库: <https://github.com/HiThink-Tech/Financial-API>

## 1. 为什么 Financial-API 重要

Financial-API 的定位不是量化策略、回测器或“问财式”问答产品，而是把同花顺金融数据服务包装成可被人、脚本和 AI Agent 稳定调用的数据底座。根目录 `README.md` 明确将 API、托管 MCP、`hithink-finance` CLI、Python toolkit、本地 `marketdb` 和 Agent Skill 组织为一套服务：同一 API Key、同一 `thscode` 代码约定、不同执行环境的不同入口。

其价值在于将“找对证券—取得数据—控制结果规模—转入本地研究”拆成明确契约。原始 REST 数据端点均为 `GET`，位于 `https://fuyao.aicubes.cn`，以 `X-api-key` 请求头认证；业务成功必须同时满足信封 `code == 0`，不能只依据 HTTP 200。调用前应先以 `/api/meta/tickers/search` 将名称或不完整代码消歧为带交易所后缀的唯一 `thscode`，如 `600519.SH`；这避免了调用方从 6 位数字猜 `.SH`、`.SZ` 或 `.BJ`。

当前公开数据面覆盖 A 股最新快照、单标的历史日 K 和公司行动/复权因子，利润表、资产负债表、现金流量表与财务指标，A 股估值快照、交易日历、同花顺指数/板块及成分股，公募基金资料、披露持仓、净值、收益、持有人与 ETF/LOF 行情，以及涨停、连板、当日异动、飙升榜、热股榜、龙虎榜。`docs/api/capability-map.md` 列出 34 个 REST 端点，其中 Market Dumps 返回全市场日 K、近 10 日增量日 K 和复权事件的预签名 Parquet 下载地址，适合建库而非逐证券拉取。

边界同样清晰：仓库文档和 `skills/hithink-finance/SKILL.md` 都明确不提供分钟 K、tick、Level-2、港美股、期货期权、宏观数据、新闻公告原文、研报、回测引擎或确定性投资建议。因此，项目没有公开的“问财问答”或宏观数据接口；Agent 可用数据工具完成自然语言意图路由和取数，但投资解释、问答生成和策略研究应由上层系统实现，不能误写为服务能力。

## 2. 高层组件

仓库是一个有边界的 monorepo。根 `AGENTS.md` 把职责划为 Node.js CLI、Python、REST/MCP 文档与可发布 Agent Skill 四块；它们不复制彼此的字段契约，`docs/api/` 才是 REST 参数、响应字段和错误码的唯一仓内事实源。

```text
自然语言金融任务
    -> skills/hithink-finance/SKILL.md：意图识别、凭据复用、接入方式选择
    -> MCP / REST / hithink-finance CLI / Python toolkit
    -> 同花顺金融数据服务（X-api-key、{code,message,request_id,data}）
    -> 小结果结构化返回；大结果落盘
    -> marketdb DuckDB：历史日线、复权、面板、SQL、导出
```

| 层次 | 真实路径与对象 | 职责 |
| --- | --- | --- |
| REST 契约 | `docs/api/README.md`、`capability-map.md` | 定义 34 个端点、信封、错误码、时间/分页和资产边界。 |
| Agent 路由 | `skills/hithink-finance/SKILL.md` | 把名称、时间窗口、复权、数据规模映射到 CLI、MCP、REST 或 Python 主路径。 |
| MCP | `docs/mcp.md` | 托管 `hithink-finance-a-share`、`-a-share-index`、`-meta`、`-fund` 四个 HTTP 服务；固化快照共 30 个工具。 |
| Node CLI | `hithink-finance-cli/src/` | 面向终端、CI、Agent 的命令树、能力发现、凭据、统一 JSON 信封和 DuckDB 操作。 |
| Python 远端适配 | `python/toolkit/fuyao/scripts/fuyao_client.py`、`fuyao.py` | typed Python 函数与只把业务 JSON 写至 stdout 的 argparse CLI。 |
| 本地研究库 | `python/marketdb/` | DuckDB schema、Parquet 导入、复权计算、同步、Typer CLI 和 `MarketDB` pandas SDK。 |

接入选择不是功能重复：Chat/IDE 已接入服务时走托管 MCP；零依赖服务端集成走 REST；终端、自动化或远端/本地一体化走 `hithink-finance`；Notebook 和研究脚本走 Python。`python/toolkit/README.md` 进一步规定：最新行情、财报、指数和特色数据走远端，已有且足够新的历史 OHLCV、复权与全市场面板走本地 `marketdb`。

## 3. 核心实现细节

### 3.1 认证、协议与错误边界

统一凭据逻辑在 `python/marketdb/credentials.py`。`resolve_api_key()` 的优先级是 `HITHINK_FINANCE_API_KEY`、平台用户配置目录下的 `hithink-finance/credentials.env`，再到兼容旧变量 `FUYAO_TOKEN` 与 `API_KEY`；`credential_file_path()` 在 Linux 默认解析为 `~/.config/hithink-finance/credentials.env`。这一实现把远端访问的秘钥从项目文件和数据文件中移开。

Python client 的 `_get()` 是协议收口点：创建复用的 `requests.Session`，传入 `X-api-key`，过滤空参数，检查业务 `code`，并只对网络错误、`4001` 和 `5001/5002/5003` 以最多三次指数退避重试。非零业务码抛出带 `code`、`message`、`request_id` 的 `FuyaoApiError`，故调用方可记录问题而非把 `data: null` 当作成功空集。

```python
# python/toolkit/fuyao/scripts/fuyao_client.py
headers = {"X-api-key": _token()}
payload = resp.json()
if payload.get("code", -1) == 0:
    return payload.get("data") or {}
raise FuyaoApiError(code=code, message=payload.get("message", ""),
                    request_id=payload.get("request_id"))
```

### 3.2 Python 数据接口：校验、缓存、分页和切窗

`fuyao_client.py` 不是泛化 ORM，而是一组与端点一一对应的轻量函数。`tickers_search()` 优先使用由 `tickers_list(refresh_cache=True)` 写入的 12 小时本地代码缓存，缓存缺失、过期或未命中才访问远端；它可按交易所和资产类别筛选，解决名称到唯一 `thscode` 的第一步。行情层的 `prices_snapshot()` 区分代码批量、单页和全市场分页三种模式，禁止同时给代码与 `fetch_all_market=True`。`prices_historical()` 校验单一 `thscode`、仅允许 `1d`、校验前/后/不复权，并把超过十年的窗口切段请求、按 `date_ms` 去重排序后合并。

财务函数 `financials_income_statements()`、`financials_balance_sheets()`、`financials_cash_flow_statements()` 复用 `_financials()`；`financials_indicators()` 接受如 `2025-4` 的报告期。另有 `a_share_valuations_snapshot()`、`calendar_trading_days()`、`index_catalog_ths_index_list()`、`fund_performance_nav()` 与 `special_data_dragon_tiger_list()` 等函数。`fuyao.py` 将它们映射为 `tickers-search`、`prices-historical`、`financials-income`、`fund-nav`、`dragon-tiger-list` 等 argparse 子命令，成功业务数据写 JSON stdout，便于 shell、CI 和 subprocess 组合。

```python
hit = tickers_search("贵州茅台", limit=1)[0]
bars = prices_historical(hit["thscode"], start_ms, end_ms, adjust="forward")
income = financials_income_statements(hit["thscode"], period="annual", limit=4)
```

### 3.3 marketdb：远端全量数据变成本地研究面板

`python/marketdb/` 是与远端 client 相补的本地历史层，依赖 DuckDB、PyArrow、pandas、Typer、Rich 和 requests。数据模型保留 `raw_kline_daily` 与 `raw_adjustment_events` 两张事实表，计算 `calc_adjust_factor_daily`，并提供 `v_daily`、`v_daily_qfq`、`v_daily_hfq`、`v_symbol` 视图。`MarketDB.get_daily()` 根据 `adjust` 选择视图，以单条参数化 SQL 的 `IN (...)` 读取一个或一篮子标的；`get_panel()` 不做逐证券过滤，按日期窗口顺序扫描全市场，适合截面因子研究；`query_sql()` 返回 pandas `DataFrame`。

```python
from marketdb import MarketDB

with MarketDB.open("data/market.duckdb") as db:
    daily = db.get_daily("600519.SH", start="2025-01-01", adjust="forward")
    panel = db.get_panel(start="2026-01-01", end="2026-01-31")
```

同步策略实现在 `python/marketdb/updaters/auto.py`。`decide()` 比较本地 `raw_kline_daily` 最大日期与官方交易日历：空库为 `full`，落后不超过 `MAX_INCREMENTAL_LAG = 7` 个交易日为 `incremental`，更久则 `full`，无滞后为 `skip`。`auto_sync()` 在全量时下载 `DAILY_K`，增量时下载 `DAILY_K_10D`；无论 K 线是否跳过，都刷新复权事件、重建复权因子和视图，并记录 release tag 与时间到 `_meta`。这避免复权事件同日更新导致 `v_daily_qfq` 静默漂移。

### 3.4 hithink-finance CLI：面向人类和 Agent 的运行时收口

`hithink-finance-cli` 是独立的 Node.js 22.12+ 子项目，运行时不依赖 Python。`src/cli/program.ts` 的 `createProgram()` 使用 Commander 注册 `auth`、`symbol`、`market`、`financials`、`index`、`fund`、`valuation`、`special`、`data`、`db`、`capabilities`、`schema` 等命令组，并通过全局 `--format`、`--profile`、`--source auto|local|remote`、`--db`、`--api-key-stdin`、`--debug` 统一运行语义。`createCliContext()` 生成 request ID 并把 stdout/stderr 从命令实现中隔离；`successEnvelope()` / `errorEnvelope()` 定义 CLI 自身的 `ok` 信封，因此 CLI 成功标准是退出码 0 且 `ok=true`，不是直接沿用上游 `code`。

`src/commands/remote.ts` 的 `registerRemoteCapabilityGroup()` 从 `RemoteCapabilityDescriptor` 动态挂载 options 和远端子命令，先用 Zod schema 验证输入，再解析认证并交给 `executeRemoteQuery()`。对 `market.history`，它检查本地 DuckDB 是否覆盖请求时间窗：完整覆盖即以 `getHistory()` 本地返回，否则回退 Fuyao API。批量代码支持 `--codes-file` 或 `--codes-stdin`，同时显式拒绝两者并用、以及它们和 `--api-key-stdin` 争用同一个 stdin；大结果的 `--output` 写完整 JSON 信封到文件，stdout 只返回路径和计数。

```bash
hithink-finance capabilities --format json
hithink-finance schema market.snapshot --format json
hithink-finance market snapshot --thscodes 600519.SH --format json
hithink-finance financials income --thscode 600519.SH --limit 4 --format json
```

`capabilities` 与 `schema <id>` 是给 Agent 的关键设计：调用方先获得本版本机器可读能力，再读取目标参数 schema，避免从 README 猜命令参数。人类表格可用 `--format table`，JSON/NDJSON/CSV 则由输出层处理；诊断只进 stderr，防止污染机器可读 stdout。

## 4. 对当前项目的价值

1. **建立数据源边界。** 把同花顺作为一等正式数据源时，应保留数据源、请求 ID、快照时间、报告期、复权口径和 `thscode`，并严格区分 API 返回的数据事实与上层模型给出的分析结论。
2. **复用“先消歧、后取数”链路。** 名称输入先经 `tickers_search()` 或 MCP 元信息服务确认，再按 `asset_type` 路由股票、指数/板块或基金，减少同名标的和交易所后缀错误。
3. **用本地面板替代批量远端循环。** 多年、全市场或因子任务应经 Market Dumps、`auto_sync()` 和 `MarketDB.get_panel()`，小型、最新或财务任务才走远端；这同时控制延迟、限流和 Agent 上下文成本。
4. **把能力发现变成 Agent 工具契约。** 可借鉴 `capabilities`、`schema`、稳定 JSON envelope、request ID 和分类错误，让 Agent 不凭文档幻觉参数，并能追溯失败阶段。
5. **不越过公开边界。** 此仓库不替代回测、宏观/新闻抓取或问答模型；当前项目若需要这些能力，应在数据层之上独立接入并标明来源，不能将缺失功能用静态样例或近似数据伪装为实时结果。

Financial-API 最值得吸收的是“多入口而不多套真相”：REST 契约集中在 `docs/api/`，Skill 负责路由，CLI/Python 只维护运行语义，本地 DuckDB 承担重数据研究。这样既能让 Agent 自然语言接入，又不牺牲数据口径、认证安全和大规模研究的可复现性。
对于研究工程，最稳妥的集成方式是把每一次查询的输入、数据版本、返回元数据与落盘产物关联到同一研究任务，使结果能够复查、复跑并在权限失败时准确定位。
