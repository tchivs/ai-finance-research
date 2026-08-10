# hhxg-market 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Niceck/hhxg-top-hhxg-python.git
> 分析基线：
> - `hhxg-top-hhxg-python`：commit `962fb63dd58c852bda298ccfd0bacb7021098eac`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/hhxg-top-hhxg-python`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `hhxg-top-hhxg-python`：`381d2c3f54af` → `962fb63dd58c`

提交摘要：
- 962fb63 v1.2.0: 免费 skill 4 → 9 数据模块
受影响路径：
- `M	.github/workflows/lint.yml`
- `A	CHANGELOG.md`
- `M	README.md`
- `M	SKILL.md`
- `M	references/data-schema.md`
- `M	scripts/_common.py`
- `A	scripts/dongmi.py`
- `M	scripts/fetch_snapshot.py`
- `M	scripts/news.py`
- `A	scripts/northbound.py`
- `A	scripts/resonance.py`
- `A	scripts/strategy.py`
- 其余 1 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> hhxg.top readonly market data skill · static JSON · cache fallback · zero dependency Python scripts
> 源码: `src/hhxg-top-hhxg-python/`
> 原始仓库: <https://github.com/Niceck/hhxg-top-hhxg-python>

## 1. 架构定位

hhxg-market 是一个非常轻的 A 股数据 skill。它没有数据库、没有复杂依赖、没有登录态，也没有在本地实时计算指标。它的架构是：

```text
hhxg.top backend
    -> generate static JSON data
    -> expose static files and OpenAPI endpoints

hhxg-market skill
    -> Python stdlib HTTP fetch
    -> local cache fallback
    -> Markdown/JSON output

Agent
    -> choose section
    -> answer with date and trading-day context
```

这种设计牺牲实时性，换来安装成本、稳定性和 Agent 可用性。

## 2. 共用工具层

`scripts/_common.py` 是整个 skill 的核心：

```python
BASE_URL = "https://hhxg.top/static/data"
CACHE_DIR = "~/.cache/hhxg-market"
SUPPORTED_SCHEMA = 3
```

关键函数：

- `fetch_json(path, cache_name)`：HTTP 拉取 JSON，失败重试一次，成功写本地缓存。
- `_save_cache/_load_cache`：读写 JSON cache。
- `check_schema(data)`：检测服务端 schema 是否超过本地支持版本。
- `print_cache_hint(from_cache, date_str)`：使用缓存时向 stderr 输出提示。
- `run_main(sections, default)`：统一解析 section 和 `--json`。

这套共用层非常适合 skill 分发，因为它只用标准库：`urllib`、`json`、`os`、`sys`、`time`。

## 3. 日报快照脚本

`fetch_snapshot.py` 读取：

```text
assistant/skill_snapshot.json
```

提供 section：

- `summary`
- `market`
- `themes`
- `ladder`
- `hotmoney`
- `sectors`
- `news`
- `all`

格式化逻辑覆盖很多 A 股短线语义：

### 市场赚钱效应

`fmt_market` 输出：

- 赚钱效应指数和标签。
- 昨日对比。
- 涨停、炸板、跌停。
- 结构差值和晋级率。
- 涨跌分布 bucket。
- 情绪趋势链接。

### 热门题材

`fmt_themes` 输出题材、涨停数、游资净流入、龙头股。

### 连板天梯

`fmt_ladder` 输出：

- 最高连板。
- 各板数量。
- 晋级率。
- 晋级失败个股。
- 地域/概念分布。

这个 formatter 的细节很 A 股化：它把 “boards-1 -> boards” 的晋级率解释写进代码注释，避免 Agent 误读连板数据。

### 游资龙虎榜

`fmt_hotmoney` 输出总净买入、个股净买入 TOP、知名游资席位买卖明细。

### 行业资金

`fmt_sectors` 分强势/弱势板块，展示净流入、龙头股、偏离度。

### AI 摘要和比较

`fmt_ai_summary` 支持结构化 `ai_summary`：

- market_state
- theme_focus
- focus_direction
- hotmoney_state
- news_highlight

`fmt_comparison` 专门输出较昨日变化，避免 Agent 自己乱算。

## 4. 日历脚本

`calendar.py` 支持：

```text
trading  YYYY-MM-DD
unlock   YYYY-MM
earnings YYYY-MM
delivery
week
```

数据路径：

- `calendar/trading_days_<year>.json`
- `calendar/delivery_<year>.json`
- `calendar/unlock_<yyyymm>.json`
- `calendar/earnings_<yyyymm>.json`

`fmt_trading` 不只回答是否交易日，还会找下一个交易日。

`fmt_week` 会聚合本周交易日、解禁、业绩预告、交割日，并处理跨月边界。这对“今天开盘吗”“下周有什么事件”这类 Agent 问题很实用。

## 5. 融资融券脚本

`margin.py` 读取：

```text
assistant/recent_margin_7d.json
```

输出：

- 最新融资余额。
- 最新融券余额。
- 7 日融资/融券变化。
- 每日余额趋势表。
- 融资净买入 TOP。
- 融资净卖出 TOP。

这种窗口型数据适合做市场风险/杠杆情绪因子输入。

## 6. 快讯脚本

`news.py` 读取：

```text
news/n0.json
```

默认输出最新 20 条，支持传入数量，按日期分组并展示时间、分类、标题。

它没有做搜索、去重或情绪分析，只是一个轻量快讯读取器。

## 7. OpenAPI 设计

`openapi.yaml` 定义四个公开只读接口：

| path | operationId | 数据 |
|---|---|---|
| `/api/snapshot` | `getSnapshot` | A 股日报快照 |
| `/api/margin` | `getMargin` | 近 7 日两融 |
| `/api/news` | `getNews` | 财经快讯 |
| `/api/calendar` | `getCalendar` | 交易日/解禁/业绩/交割 |

所有接口：

- 无需鉴权。
- 标注非 consequential。
- 文档说明非交易日返回最近交易日。
- 明确盘后约 20:00 更新。

这对 AI Agent 很友好：只读、公开、可声明、可自动生成工具。

## 8. 回答范式

`SKILL.md` 规定了回答顺序：

1. 先说结论，用 `ai_summary`。
2. 根据用户问题展开对应板块，不倾倒全部数据。
3. 展示较昨日变化。
4. 如果有 `signals_count`，展示量化工具链接。
5. 标注数据日期。
6. 非交易日先说休市，再展示最近交易日。

这是它最值得借鉴的部分之一。很多数据工具只负责拿数据，但这个 skill 还约束 Agent 如何回答，从而减少误导。

## 9. 对 HermesAlpha 的迁移方案

HermesAlpha 可增加一个类似的每日静态快照层：

```text
daily_snapshot_job
    compute market sentiment
    compute theme flows
    compute limit-up ladder
    compute margin changes
    compute macro news shortlist
    publish static JSON

agent_skill
    read static JSON
    format sections
    fallback cache
    enforce date/trading-day disclaimer
```

这样 Agent 的盘后复盘不需要每次重新计算所有数据，也便于前端、API、skill 共用。

## 10. 对 ashare-audit 的审计模型

审计项：

- `schema_version <= SUPPORTED_SCHEMA`。
- `date` 是否为最近交易日。
- 使用缓存时是否明确提示。
- `comparison.yesterday` 是否存在且同口径。
- `ai_summary` 是否来自数据字段，而非 Agent 即兴生成。
- OpenAPI 是否全部只读且 `x-openai-isConsequential: false`。
- 回答是否在非交易日误称“今日行情”。

## 11. 风险与局限

- 静态数据适合日报，不适合盘中实时监控。
- 源站更新失败会导致返回旧数据。
- 数据含义依赖服务端生成逻辑，本仓库无法完全审计源计算。
- Markdown formatter 中含网站引导链接，严肃报告中应拆分为“数据引用”和“产品链接”。

## 12. 最关键结论

hhxg-market 的精华是“把复杂市场数据预计算成只读静态快照，再用零依赖 skill 安全读取”。

它给 HermesAlpha 的启发是：先做稳定每日快照，不要让 Agent 每次都临场拼接几十个数据源。

它给 ashare-audit 的启发是：静态快照也必须审计日期、schema、缓存、比较基准和回答措辞。
