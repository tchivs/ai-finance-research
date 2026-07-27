# Agentic China Data Tooling 深度分析

> MCP stock tools · OpenClaw plugin runner · source health · DuckDB MarketDB · typed Fuyao client
> 源码: `/root/source/tmp/stock-sdk-mcp/`, `/root/source/tmp/openclaw-data-china-stock/`, `/root/source/tmp/Financial-API/`
> 原始仓库: [stock-sdk-mcp](https://github.com/chengzuopeng/stock-sdk-mcp) · [openclaw-data-china-stock](https://github.com/shaoxing-xie/openclaw-data-china-stock) · [Financial-API](https://github.com/HiThink-Tech/Financial-API)

## 1. 合并视角

这三个项目覆盖 Agent 数据层的三个平面：

```text
MCP interaction plane
    stock-sdk-mcp: tools/resources/prompts

Plugin execution plane
    openclaw-data-china-stock: tool_runner + plugins + metrics + source health

Local data plane
    Financial-API marketdb: DuckDB + parquet dumps + REST typed client
```

对当前项目来说，它们合起来形成一条完整数据链：在线 API/SDK 不是直接喂给 LLM，而是经过本地缓存、质量检查、工具封装、MCP/runner 暴露和审计 envelope。

## 2. stock-sdk-mcp: MCP 三能力

`src/server.ts` 创建 MCP Server：

```text
capabilities: tools + resources + prompts
StockSDK instance
getAllTools/createAllHandlers
getAllResources/createResourceHandlers
getAllPrompts/createPromptHandlers
```

### 2.1 Tools

`tools/index.ts` 聚合：

```text
quotes
kline
search
batch
board
extended
futures
options
compound
fundflow
northbound
hotspot
margin
```

这种模块化导出方式让工具分类清楚，也便于 profile 裁剪。

### 2.2 Resources

Server 支持静态 resources 和 URI templates。`matchUriTemplate()` 用 `{param}` 占位符匹配动态 URI。对金融 Agent 来说，resources 可用于暴露“字段说明、市场列表、工具文档、缓存状态”等不需要工具调用的内容。

### 2.3 Prompts

`prompts/index.ts` 把 workflow 注册为 MCP prompts：

```text
stock-analyst
stock-screener
market-overview
realtime-monitor
smart-money-tracker
futures-overview
```

这说明 MCP 不只是 RPC 工具目录，也可以是可复用操作流程的入口。

## 3. stock-sdk-mcp 复合工具

`tools/compound.ts` 是最值得学的部分。

### 3.1 analyze_stock

一次返回：

```text
K-line with MA/MACD/KDJ/RSI/BOLL
fund flow
dividends
individual fund flow history
northbound holding
```

它使用 `Promise.allSettled()`，然后输出：

```text
dataStatus: each block fulfilled/rejected
kline: total/latest/last60
fundFlow
fundFlowHistory recent20
northboundHolding recent20
dividends recent5
```

这种 partial failure 模式非常适合金融数据。北向失败不应让 K 线和资金流也失败。

### 3.2 scan_market

流程：

```text
getAllAShareQuotes(batchSize=500, concurrency=7)
normalize amount unit from 万元 to 元
filter by change/volume/amount/turnover/PE
sort with explicit switch
return totalScanned/totalMatched/data
```

显式 switch 避免 string index 强转，PE null 排到末尾。这些小细节能减少 Agent 工具输出的口径错误。

### 3.3 get_market_overview

聚合指数、行业、概念、港股指数、北向、涨停池、跌停池、板块异动，并返回每块 dataStatus。

## 4. openclaw tool_runner

`tool_runner.py` 是 Python 插件工具的统一入口。

### 4.1 ToolSpec

```text
module_path
function_name
params_model
param_mapping
```

`TOOL_MAP` 将工具名路由到具体模块函数。`ALIASES` 将旧工具名转换为新工具名并注入参数，用来兼容 cron/工作流。

### 4.2 参数输入

CLI 支持：

```text
python3 tool_runner.py <tool_name> '{...json...}'
python3 tool_runner.py <tool_name> @path/to/args.json
```

如果 `params_model` 存在，会用 Pydantic 校验并输出结构化 `VALIDATION_ERROR`。

### 4.3 统一 envelope

每次执行都会补：

```text
elapsed_ms
plugin_version
```

并尝试记录 tool metrics。ImportError 和 RuntimeError 都输出：

```text
error
error_code
module/function 或 type
captured_stdout/captured_stderr tail
```

这对 Agent 很重要：模型看到的是机器可判断错误，而不是一段混乱 traceback。

## 5. openclaw source health

`probe_source_health.py` 做 import-level smoke：

```text
source_ids default: akshare,sina,yfinance,eastmoney,tushare
akshare/yfinance import version check
write_snapshot optional
append JSONL event/history sample
include_catalog_digest optional
```

返回 `_meta` 中包含：

```text
schema_name
schema_version
quality_status
error_code
```

这个设计值得直接迁移：数据源健康不是日志里的附带信息，而是 Agent 可以主动查询的工具。

## 6. openclaw 技术指标和因子筛选

### 6.1 TechnicalIndicatorEngine

后端选择顺序：

```text
source_chains.technical_indicators provider_tags
    -> talib
    -> pandas_ta
    -> builtin
```

如果用户显式要求 `talib` 或 `pandas_ta` 而不可用，则抛错；auto 模式按 catalog 顺序降级。

这说明计算引擎应该暴露“使用了哪个后端”，否则不同部署环境会产生不同指标。

### 6.2 equity_factor_screening

多因子选股工具特点：

```text
ALLOWED_FACTORS from registry
universe: hs300/zz500/zz1000/a_share/custom
config_hash for reproducibility
ThreadPoolExecutor parallel historical fetch
percentile ranks with NaN median fallback
industry mapping for neutralization
quality_score / degraded / plugin_version
```

未知因子直接返回失败，并列出允许因子。这比让 Agent 传任意字符串安全。

## 7. Financial-API MarketDB

`Financial-API/marketdb` 是本地 A 股数据库样板。

### 7.1 Schema 管理

`schema.py`：

```text
init_schema(): schema.sql + views.sql + _meta
rebuild_views()
set_meta_many()
check_compatibility(): schema major version fail-fast
```

`_meta` 保存 schema_version、project_version、initialized_at、data_root 和同步 release tags。

### 7.2 Parquet import

`importers/parquet.py` 处理 timezone：dump 已按 Asia/Shanghai 00:00 对齐，导入时通过 `epoch_ms(date_ms + 8h)` 转 DATE。

日线导入逻辑：

```text
overwrite=True: INSERT OR REPLACE full dump
overwrite=False: 先删除 parquet window，再插入 incremental rows
record batch start/finish
set last_kline_daily_batch_id
```

调整事件导入则是 full snapshot：先 `DELETE raw_adjustment_events`，再重插，保证服务端删除也反映到本地。

### 7.3 Auto sync decision

`updaters/auto.py` 的核心决策：

```text
if local_max is None: full
elif lag == 0: skip
elif lag <= 7: incremental
else: full
```

调整事件每次都刷新，不用 release_tag 短路，因为文件名只有日期，日内内容变更可能同 tag。

这个细节非常成熟：数据同步不能只看文件名。

### 7.4 Quality checks

`checks/quality.py` 检查：

```text
raw_kline_daily non-empty
thscode/date not null
primary key unique
high >= low
OHLC non-negative
volume/turnover non-negative warn
raw_adjustment_events pk unique
```

`checks/freshness.py` 计算本地最大日期到目标交易日的 lag，超过阈值拒绝增量更新。

## 8. Fuyao typed client

`toolkit/fuyao/scripts/fuyao_client.py` 的设计 contract：

```text
每个能力是 top-level typed function
client-side 参数约束先于 HTTP call
>10 年窗口自动切片
本地 ticker cache TTL 12h
返回 plain list[dict]/dict
token 只来自 env
business errors raise FuyaoApiError(code,message,request_id)
```

这非常适合 Agent：函数签名、参数约束、错误类型都明确，避免模型把 token 当参数传来传去。

## 9. 统一数据工具契约建议

结合三者，当前项目可以定义：

```json
{
  "success": true,
  "message": "ok",
  "data": {},
  "data_status": {},
  "error_code": null,
  "quality_status": "ok|degraded|error",
  "source_ids": [],
  "schema_name": "tool_name",
  "schema_version": "1",
  "plugin_version": "x.y.z",
  "elapsed_ms": 123,
  "cache": {"hit": true, "ttl_seconds": 300}
}
```

## 10. 当前项目迁移蓝图

```text
Layer 1: Provider clients
    Fuyao/Akshare/Eastmoney/Tushare/TDX typed wrappers

Layer 2: MarketDB
    DuckDB raw tables + adjustment factors + views + _meta

Layer 3: Tool runner
    ToolSpec + aliases + Pydantic + envelope + metrics

Layer 4: Compound tools
    stock_overview / market_overview / factor_screen / portfolio_risk

Layer 5: MCP
    tools + resources + prompts

Layer 6: Audit
    source health + freshness + quality + dataStatus checks
```

## 11. 风险和限制

- MCP prompt 文案中如果出现“操作建议”，需要按当前产品合规要求改写。
- Tool runner 通过动态 import 执行，生产环境要加工具白名单、版本锁和执行权限隔离。
- Source health 的 import smoke 不等于真实端点可用，还要加轻量 API probe。
- MarketDB 的 FULL/INCREMENTAL/SKIP 依赖交易日历可信，交易日历本身也要版本化。

## 12. 结论

这组项目给出的关键经验是：金融 Agent 的数据层必须“工具化 + 本地化 + 可观测 + 可审计”。当数据源失败、字段口径变化、缓存过期、增量落后时，系统应显式告诉 Agent，而不是让模型在不完整数据上继续生成确定语气的结论。
