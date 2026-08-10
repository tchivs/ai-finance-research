# wudao-mcp 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/jcdreamjc/wudao-mcp.git
> 分析基线：
> - `wudao-mcp`：commit `6874ef9b2f0be95ec6db1e26b1fefc28615ea0cd`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/wudao-mcp`
<!-- source-sync:end -->


> A 股数据 MCP 产品化 · Agent 工具发现 · workflow/atomic 双层工具面
> 源码: `src/wudao-mcp/`
> 原始仓库: <https://github.com/jcdreamjc/wudao-mcp>

---

## 1. 项目形态

`wudao-mcp` 的仓库不是传统 SDK，而是“远端 MCP 服务 + GitHub Pages 文档 + Skill 引导”。核心信息集中在：

| 文件 | 作用 |
|---|---|
| `README.md` | 定位、安装、工具领域、profile、安全边界 |
| `skills/wudao-stock-data/SKILL.md` | Agent 触发条件、MCP 配置、使用纪律 |
| `docs/openclaw-hermes-a-share-review.md` | 面向 OpenClaw/Hermes 的复盘 workflow 文档 |
| `index.html`, `llms.txt`, `sitemap.xml` | 面向人和 Agent 的公开发现入口 |

这种形态适合做“外部能力接入层”：仓库本身不需要暴露服务端源码，也能让 Agent 明确知道如何接入、何时使用、如何验证以及不能做什么。

---

## 2. 设计核心: 让 Agent 先发现工具，而不是猜 API

`SKILL.md` 明确要求：MCP 可用时先调用 `tools/list`，不要臆造工具名和参数。这个规则对金融 Agent 特别关键，因为 A 股数据工具常常字段多、口径复杂、命名变化快。

可迁移成当前项目的工具使用协议：

```text
1. connect MCP/data service
2. tools/list or manifest
3. choose workflow tool for broad task
4. use atomic tool only for drilldown
5. preserve source/time/boundary in final answer
```

这比让 LLM 直接写 URL 或调用散落函数可靠，因为 schema 是运行时事实，Agent 不需要凭记忆猜字段。

---

## 3. Workflow 工具和 Atomic 工具的分层

README 把能力拆成两类：

| 层级 | 示例 | 适合场景 |
|---|---|---|
| workflow tools | market replay, stock research, limit-up review, theme research | 盘后复盘、个股研究、题材研究等宽任务 |
| atomic tools | K 线、资金流、龙虎榜、公告、财务摘要 | 用户追问细节、验证某个结论 |

这对当前项目的启发是：不要只暴露 `get_quote`, `get_report`, `get_moneyflow`。应该提供领域级入口，例如：

```text
review_market(date)
research_stock(symbol, date_range)
review_limit_up(date)
research_theme(theme, date_range)
watchlist_digest(user_id, date)
```

内部可以再调用原子数据源，但 Agent 的默认交互面应该是任务语义，而不是低层接口。

---

## 4. Profile 裁剪是一种安全和效率机制

项目支持 `profile=short_term`, `auction_review`, `theme_research`, `stock_research`, `market_replay`, `personal`, `workflows`, `all`。

这解决两个问题：

1. 工具数量多时，LLM 选错工具概率上升。
2. 不同客户端或场景不需要看到完整能力面。

建议当前项目为 MCP/Skill 数据服务设计如下 profile：

| Profile | 工具范围 |
|---|---|
| `audit` | 财务、公告、研报、风险事件、审计证据 |
| `market_replay` | 指数、涨跌分布、资金流、题材、涨停生态 |
| `short_term` | 打板、龙虎榜、竞价、异动、短线催化 |
| `fundamental` | 财务三表、估值、股东、公告、研报 |
| `watchlist` | 自选股、持仓风险、事件提醒 |
| `workflows` | 只暴露组合工作流，隐藏原子工具 |

---

## 5. 安全边界的工程价值

`wudao-mcp` 反复强调只读、不交易、不投资建议、不承诺收益。这不是免责声明模板，而是 MCP 工具设计的一部分。

建议当前项目把安全边界写入三个层面：

| 层面 | 要求 |
|---|---|
| tool description | 每个工具声明 read-only 和输出性质 |
| runtime response | 返回 source、fetched_at、data_quality |
| Agent prompt | 禁止把数据摘要升级成下单指令 |

这可以防止工具链未来接入券商或模拟交易时，数据工具被误用为执行工具。

---

## 6. 对当前项目的落地方案

### 6.1 Manifest 优先

建立一个数据能力 manifest：

```text
tool_name
domain
profile
inputs
outputs
source
latency_class
data_quality_fields
safety_boundary
```

每次新增数据源或 workflow 都先更新 manifest，再实现工具。

### 6.2 Workflow 包装

将现有采集和分析能力包装为组合工具：

```text
market_replay = overview + sector + flow + limit_up + news
stock_research = quote + kline + valuation + report + announcement + investor_qa
theme_research = concept_ranking + concept_stocks + flow + news + limit_events
audit_context = financial_summary + announcements + shareholder + legal/events + reports
```

### 6.3 Agent 行为规范

把 `SKILL.md` 的行为纪律迁移为项目级规则：

1. 先查 manifest/tool list。
2. 大任务优先 workflow。
3. 细节追问再 atomic。
4. 输出必须保留来源和时间。
5. 不把只读数据解释成交易建议。

---

## 7. 值得直接吸收的原则

1. 数据服务如果面向 Agent，就必须有 machine-readable discovery。
2. 工具越多，越需要 profile 裁剪和 workflow 优先级。
3. MCP 数据工具应默认只读，交易执行必须是另一类权限工具。
4. 宽任务不要让 LLM 自己拼 URL，应给 workflow 级入口。
5. README/Skill/manifest 是 Agent 数据产品的一部分，不是附属文档。
