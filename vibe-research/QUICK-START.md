# Vibe-Research 快速概览

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


> 本地自托管 A 股投研看板 · FastAPI / NDJSON chat / MCP / portfolio cache
> 源码: `src/Vibe-Research/`
> 原始仓库: <https://github.com/simonlin1212/Vibe-Research>

## 1. 一句话定位

Vibe-Research 是一个个人 A 股投研数据工作台：后端用 FastAPI 暴露行情、估值、公告、研报、资金流、市场情绪、持仓等只读/本地数据接口，并提供 OpenAI-compatible function calling、订阅 CLI 接入和 MCP server 三种 AI 调用通道。

它最值得学的是“投研产品的合规边界和数据通道设计”：工具只返回客观数据，模型只做信息整理，不预置标的、不荐股、不预测涨跌、不自动下单。

## 2. 核心结构

```text
frontend
    -> /api/* FastAPI
        -> astock / gstock / market / newsradar / portfolio
        -> /api/chat NDJSON streaming
        -> chat.py function-calling loop
        -> cli_runtime.py local subscription CLIs
        -> mcp_server.py JSON-RPC over stdio
```

## 3. 关键文件

| 文件 | 作用 |
|------|------|
| `backend/app.py` | FastAPI endpoints、CORS、可选 API Key、缓存 |
| `backend/chat.py` | 系统 prompt、工具定义、function-calling、流式输出 |
| `backend/mcp_server.py` | 零依赖 JSON-RPC MCP server |
| `backend/portfolio.py` | 本地持仓 JSON、原子写、后台刷新 |
| `backend/market.py` | 市场情绪、板块资金流、短线情绪聚合 |
| `backend/cli_runtime.py` | 调本机 Claude/Qwen/Gemini/DeepSeek/Codex CLI |

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| API Key optional | 本地开放，设 `VR_API_KEY` 后保护 `/api/*` | 自托管产品可兼容本地和公网部署 |
| 客观数据边界 | 工具只查行情/估值/研报/新闻 | AI 金融产品先固定“数据”和“判断”边界 |
| Analysis framework | 系统 prompt 固定估值/资金/财报/行业/事件五维 | 弱模型也能输出结构化投研分析 |
| Function calling loop | 最多 6 轮工具调用，工具结果 cap 6000 chars | 防止工具循环和 token 爆炸 |
| NDJSON streaming | 输出 `{type: tool|delta|done|error}` | 前端可以展示工具调用过程和流式答案 |
| CLI subscription | 调用户本机已登录 CLI，不吃产品 API cost | 自托管产品可复用用户自己的 AI 订阅 |
| MCP server | 复用 chat.TOOLS 暴露给 Claude Code 等 Agent | 同一数据层可同时服务 App 和外部 Agent |
| Portfolio local file | `.cache/portfolio.json` 本地保存，原子写 | 用户持仓敏感数据不上传 |
| Shared TTL cache | 市场/估值/公告等按 5-30 分钟缓存 | 降低免费数据源压力和封禁风险 |

## 5. 对 HermesAlpha 的借鉴

1. **三通道 AI 接入**：API function calling、local CLI subscription、MCP external agent 可以共用同一工具定义。
2. **把合规边界写进系统 prompt 和工具边界**：工具返回客观数据，回答只做多视角分析，不给买卖结论。
3. **用 NDJSON 事件流输出投研过程**：前端显示 tool call、增量文本、done trace，比同步返回报告更可观察。
4. **持仓只存在本地或用户私有空间**：成本、股数、清仓记录不进入公共云端。
5. **市场情绪做聚合口径**：连板、炸板、封板率、行业资金流可以先做市场级数据，再进入个股分析。

## 6. 对 ashare-audit 的借鉴

1. **审计回答是否越界**：是否出现荐股、预测价位、买卖时机、收益承诺。
2. **审计工具结果来源**：模型回答中的数字是否来自 `query_quote/query_valuation/query_reports/query_news`。
3. **审计私有持仓处理**：portfolio 文件是否本地、原子写、未进入仓库。
4. **审计 CLI 调用风险**：本机 CLI 是否禁用了读写/执行工具，是否只接受已注入 context。

## 7. 不该照搬的部分

- CORS 默认 `*` 适合本地自托管，公网必须配置白名单和 API Key。
- `mcp_server.py` 是零依赖简化版 JSON-RPC，生产 MCP 生态可考虑标准 SDK。
- 聊天工具只有行情/估值/研报/新闻四类，完整投研系统还要公告、财报、资金流、行业、持仓风险等工具。
- `chat.py` 的 OpenAI-compatible streaming 兼容逻辑很实用，但生产要加请求超时、限流、用户隔离和日志脱敏。

## 8. 结论

Vibe-Research 是“个人投研产品化”的好样板：它不追求复杂多 Agent，而是把数据接口、本地隐私、AI 工具调用、流式体验和合规语言边界做清楚。对当前项目最有价值的是 AI 接入层和产品边界。
