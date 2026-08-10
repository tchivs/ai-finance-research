# Financial-API 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/HiThink-Tech/Financial-API.git
> 分析基线：
> - `Financial-API`：commit `f8cdea908469b1b3b8bfb88dbb4d4a3959b1905c`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Financial-API`
<!-- source-sync:end -->


> HiThink-Tech · 同花顺官方 A 股金融数据服务 · REST/MCP/Node.js CLI/Python 3.11+/DuckDB
> 源码: `src/Financial-API/`
> 原始仓库: <https://github.com/HiThink-Tech/Financial-API>

## 1. 一句话定位

Financial-API 是同花顺金融数据服务的多入口数据底座：一套 API Key 将 A 股、指数/板块、公募基金和特色市场数据接入 REST、托管 MCP、`hithink-finance` CLI、Python toolkit 与本地 DuckDB。它提供数据和数据治理，不提供回测引擎、宏观数据、问财问答、新闻研报或投资建议。

## 2. Financial-API 覆盖的链路

```text
名称 / ticker / thscode
    -> meta 搜索与资产类别消歧
    -> REST / MCP / CLI / Python 选择一个主入口
    -> X-api-key 调用；检查业务信封 code == 0
    -> 小结果结构化返回；全市场和长窗口结果落盘
    -> Market Dumps / auto_sync
    -> DuckDB 原始日线、复权视图、SQL、pandas 面板研究
```

远端覆盖最新/历史日 K、公司行动、三大财务报表与指标、估值、交易日历、指数/板块、基金资料与净值、涨停连板、异动、热榜和龙虎榜。名称必须先解析成完整 `thscode`，如 `600519.SH`。认证推荐使用 `HITHINK_FINANCE_API_KEY`；REST/MCP 成功看 `code=0`，CLI 则看退出码 0 与 `ok=true`。分钟 K、tick、Level-2、港美股、期货期权、宏观、问财问答和回测均不在公开能力内。

## 3. 核心模块

| 模块 | 作用 | 对当前项目的价值 |
| --- | --- | --- |
| `docs/api/` | 唯一 REST 契约源；34 个端点、`X-api-key`、`{code,message,request_id,data}` 与错误码 | 固化数据口径；避免把 HTTP 200 误判为成功。 |
| `skills/hithink-finance/SKILL.md` | 识别意图，复用凭据，在 CLI/MCP/REST/Python 间选主路径 | 为金融 Agent 提供“先消歧、后取数、控制大结果”的统一路由。 |
| `docs/mcp.md` | 4 个托管服务：A 股、指数、元信息、基金；共用认证 | Chat/IDE 可直接调用，无须自建 MCP Server。 |
| `hithink-finance-cli/src/cli/program.ts` | `createProgram()` 注册认证、行情、财务、基金、数据和数据库命令 | `capabilities`、`schema`、JSON 信封和 stderr 诊断适合自动化。 |
| `hithink-finance-cli/src/commands/remote.ts` | `registerRemoteCapabilityGroup()` 校验参数，`market.history` 可本地优先、远端回退 | 复用能力描述符和数据源策略，避免代码/凭据 stdin 冲突。 |
| `python/toolkit/fuyao/scripts/fuyao_client.py` | `_get()` 重试与业务错误收口；`tickers_search()`、`prices_historical()` 等端点适配 | Python/Notebook 可直接取最新行情、财报、估值、指数、基金与特色数据。 |
| `python/marketdb/sdk.py` | `MarketDB.get_daily()`、`get_panel()`、`query_sql()` 读取 DuckDB 复权视图 | 全市场研究使用顺序扫描面板，不做数千只股票的远端循环。 |
| `python/marketdb/updaters/auto.py` | `decide()`、`auto_sync()` 选择全量/10 日增量/跳过，并每次刷新复权事件 | 让历史数据、复权因子和本地研究库保持可追溯同步。 |

最小使用方式：终端/Agent 先运行 `hithink-finance capabilities --format json` 再查目标 `schema`；Python 研究通过 `MarketDB.open()` 读本地历史；需要最新或基本面数据时调用 `fuyao_client.py` 的 typed 函数或 JSON CLI。全市场、多标的、分页全集和长窗口一律落盘，只返回路径、行数、时间窗和摘要。
