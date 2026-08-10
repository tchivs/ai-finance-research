# Vibe-Research 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/simonlin1212/Vibe-Research.git
> 分析基线：
> - `Vibe-Research`：commit `d8c80d4ac60e43c1f096c0c486355b19800f16d7`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Vibe-Research`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `Vibe-Research`：`37a23f8c96da` → `d8c80d4ac60e`

提交摘要：
- d8c80d4 fix(chat): 支持 智谱 baseUrl , baseURL 白名单加入 /v4，避免 /v4 结尾被误补成 /v4/v1 (#22)
- 3f060a3 fix: 畸形响应校验到底 + turnover 补回 float_cap（codex 第四轮）
- 8864304 fix: 搜索端点必须校验响应结构才收手（codex 复审）
- 9489f9d fix: 三个用户报告的 bug + 版本号治理 (#26 #27 #28)
- be99807 fix: 版本读取失败的警告改走 stderr，不污染 MCP 协议（codex 复审）
- 3ec179a fix: MCP serverInfo 也走同一个版本来源（codex 审计补漏，#20）
- 50346be fix: 版本号从 package.json 单一来源读取，不再三处硬编码 (#20)
- 3eae02d Merge v0.3.0: Ask AI Markdown 渲染 + 对话持久化 + 港股现金流量表
受影响路径：
- `A	CHANGELOG.md`
- `M	README.md`
- `M	README_en.md`
- `M	a-stock-data/CHANGELOG.md`
- `M	a-stock-data/README.md`
- `M	a-stock-data/README_en.md`
- `M	a-stock-data/SKILL.md`
- `M	backend/README.md`
- `M	backend/app.py`
- `M	backend/chat.py`
- `M	backend/gstock.py`
- `M	backend/mcp_server.py`
- 其余 17 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> A 股数据层 HTTP API · function calling loop · local CLI bridge · stdio MCP · privacy-first portfolio
> 源码: `src/Vibe-Research/`
> 原始仓库: <https://github.com/simonlin1212/Vibe-Research>

## 1. 架构总览

Vibe-Research 后端是一个单体 FastAPI，但边界很清楚：

```text
app.py
    -> astock: A 股行情、估值、公告、财务、研报、K 线等
    -> gstock: 美股/港股/全球指数
    -> market: 市场情绪和板块资金流
    -> newsradar: RSS 资讯雷达
    -> portfolio: 本地持仓
    -> chat: AI function calling
    -> cli_runtime: local AI CLI bridge
    -> mcp_server: external Agent tools
```

设计目标不是机构级投研平台，而是本地自托管的个人研究台。

## 2. FastAPI 接口层

`app.py` 的接口全部在 `/api` 下。启动时：

```text
pf.start_scheduler(1800)
```

每半小时刷新持仓时间戳。

### 2.1 部署边界

```text
VR_ALLOW_ORIGINS: CORS 白名单，默认 *
VR_API_KEY: 若设置，/api/* 除 health 外必须 Bearer token
```

这非常适合自托管产品：默认本地友好，公网部署时可收紧。

### 2.2 代码校验

所有个股接口共用 `_validate(code)`：必须是 6 位数字。它不是完整证券识别系统，但足以防止接口被随意传入无关字符串。

### 2.3 接口分组

| 分组 | 接口例子 | 说明 |
|------|----------|------|
| health | `/api/health` | 服务状态 |
| chat | `/api/chat` | NDJSON 流式 AI 对话 |
| portfolio | `/api/portfolio/*` | 本地持仓/清仓/刷新 |
| market | `/api/market/overview`, `/api/market/emotion` | 市场级情绪和资金 |
| quote | `/api/quote`, `/api/indices` | 实时行情和指数 |
| valuation | `/api/valuation`, `/api/valuation/percentile` | 估值和历史分位 |
| reports/news | `/api/reports`, `/api/news`, `/api/announcements` | 研报、新闻、公告 |
| fundamentals | `/api/financials`, `/api/info`, `/api/finance` | 财务和基本面 |
| capital/event | `/api/fund-flow`, `/api/margin`, `/api/dragon-tiger`, `/api/lockup` | 资金、两融、龙虎榜、解禁 |
| sector | `/api/blocks`, `/api/hot-concepts`, `/api/industry` | 板块/概念/行业 |

大量接口都有 5-30 分钟 TTL cache，避免对免费数据源高频冲击。

## 3. Chat function-calling 层

`chat.py` 的核心是 `SYSTEM_PROMPT` 和 `TOOLS`。

### 3.1 合规系统提示

系统提示硬性规定：

```text
只做信息整理、数据解读与多视角分析
不推荐具体买卖
不预测涨跌与价位
不给买卖时机
不承诺收益
不打分排名
需要数据时先调工具
不要编造数字
```

这类边界对金融产品很关键。它不仅是免责声明，而是每轮回答的行为约束。

### 3.2 五维投研框架

当用户要求分析个股时，模型按固定五维组织：

```text
估值
资金面
财报质量
行业景气
事件催化与风险
```

输出规则强调结论先行、关键数据速览、小表格、关键观察和风险点，但仍禁止买卖结论。

### 3.3 工具定义

工具只有四个：

| 工具 | 数据 |
|------|------|
| `query_quote` | A 股实时行情 |
| `query_valuation` | 完整估值 |
| `query_reports` | 近期研报列表 |
| `query_news` | 近期新闻 |

少量高价值工具比暴露 60 个工具更稳。模型先拿最核心数据，再回答。

### 3.4 非流式循环

`run_chat()` 最多 6 轮：

```text
call LLM with tools
if no tool_calls: return content
for each tool_call:
    parse args
    execute tool
    append tool result capped to 6000 chars
after max rounds: final no-tool answer
```

### 3.5 流式循环

`run_chat_stream()` 解析上游 SSE delta，并向前端输出：

```text
{type: "delta", text}
{type: "tool", tool, args}
{type: "done", trace, rounds}
{type: "error", message}
```

它还处理非标准 OpenAI-compatible 网关不返回 `tool_calls[].index` 的情况，通过 id 或最后槽位拼接 arguments。

## 4. CLI subscription bridge

`cli_runtime.py` 支持：

```text
claude
qwen
codex
```

三种 prompt 投递方式：

| delivery | 用法 |
|----------|------|
| system-file | Claude：system 写临时文件，user 走 stdin |
| stdin | Qwen/Gemini/Codex：system+user 合并 stdin |
| arg | DeepSeek：system+user 作为位置参数 |

Claude 调用时显式禁用 Read/Write/Edit/Glob/Grep/Bash/WebFetch/WebSearch/Task 等工具，只让它根据已给 context 输出文字。

这个设计非常实用：订阅 CLI 不做 function calling，数据必须由页面预先塞进 context。

## 5. MCP server

`mcp_server.py` 是纯标准库 JSON-RPC over stdio。

它复用 `chat.TOOLS`：

```text
OpenAI tool format
    -> MCP_TOOLS {name, description, inputSchema}
```

支持方法：

```text
initialize
ping
notifications/initialized
```

`tools/call` 直接调用 `chat._exec_tool()`，返回 MCP `content` 和 `isError`。

这个桥接说明：只要工具定义干净，同一份数据工具可以同时服务 App 内聊天、外部 MCP Agent 和 CLI 工作流。

## 6. Portfolio 本地隐私模型

`portfolio.py` 的设计原则写得很清楚：

```text
持仓是用户主动录入
存本地 .cache/portfolio.json
不预置任何标的
不做推荐
```

关键实现：

| 函数 | 行为 |
|------|------|
| `add_holding()` | 同代码按加权平均成本合并 |
| `remove_holding()` | 删除持仓 |
| `close_position()` | 记录已实现盈亏 |
| `get_portfolio()` | 叠加实时行情算浮盈浮亏 |
| `_save()` | 先写 tmp，再 `os.replace` 原子替换 |
| `start_scheduler()` | daemon 线程定时刷新 timestamp |

对当前项目来说，持仓数据应当视为用户敏感资产，不能和公共研究数据混在一起。

## 7. Market 聚合层

`market.py` 做市场级数据：

```text
涨跌家数
涨停/跌停/真实涨停
市场宽度分档
投机情绪分档
行业资金流
短线情绪
连板梯队
封板率/炸板率/晋级率
成交额榜
全球指数
```

早期注释强调“零个股名”，后续又调整为“展示客观榜单但不推荐/不预测/不评分”。这说明金融产品的合规边界会随产品定位变化，必须在代码注释和接口层明确同步。

## 8. 当前项目迁移方案

### HermesAlpha

```text
Data API layer
    quote / valuation / reports / news / fund-flow / portfolio

AI layer
    OpenAI-compatible function calling
    local CLI subscription mode
    MCP tools for external agents

UI layer
    NDJSON event stream
    tool event timeline
    compliance-aware answer renderer
```

### ashare-audit

审计规则：

| 对象 | 审计点 |
|------|--------|
| prompt | 是否禁止荐股/预测/买卖时机 |
| answer | 是否引用未查证数字 |
| tool trace | 是否先查数据再回答 |
| portfolio | 是否本地存储、原子写、未上传 |
| CLI mode | 是否禁工具，只用 context |
| API deploy | 公网是否配置 API key 和 CORS 白名单 |

## 9. 风险和限制

- `VR_API_KEY` 是全局 key，不是用户级鉴权；多用户部署需要账号、权限和数据隔离。
- 工具结果截断到 6000 字符简单有效，但可能截掉关键上下文，生产应返回结构化摘要。
- `mcp_server.py` 没有鉴权，适合本地 stdio，不适合远程暴露。
- 免费数据源不稳定，所有 502/501 都要在前端清晰展示数据缺失，而不是让模型补数字。

## 10. 结论

Vibe-Research 的核心贡献是把个人投研工具的边界做清楚：数据只读、持仓本地、AI 可调工具但不越界、回答流式可观察、外部 Agent 可通过 MCP 复用数据。它是当前项目做“合规型 AI 投研入口”的重要参考。
