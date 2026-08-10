# OpenAshare 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/ZhiweiChen-coder/OpenAshare.git
> 分析基线：
> - `OpenAshare`：commit `bcdaabdaf936cd90ea556651172936d168d89127`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/OpenAshare`
<!-- source-sync:end -->


> 本地优先 A 股 AI 研究工作台 · Next.js + FastAPI · SQLite 会话记忆 · 多市场搜索 · SSE 进度流
> 源码: `src/OpenAshare/`
> 原始仓库: <https://github.com/ZhiweiChen-coder/OpenAshare>

---

## 一句话定位

`OpenAshare` 是一个把个股分析、热点、新闻、持仓、策略观察和 Agent 对话放到同一条链路里的 A 股研究工作台。它不是多 Agent 炫技项目，而是一个本地优先、可自托管、模型可替换的前后端应用。

它最值得学习的是产品化研究流：从股票代码、热点主题、持仓组合、策略候选、Agent 问答之间连续跳转，减少研究上下文断裂。

---

## 最高价值借鉴点

| 借鉴点 | 代码位置 | 可复用价值 |
|---|---|---|
| FastAPI 服务聚合 | `api/main.py`, `api/services.py` | 股票、新闻、热点、持仓、策略、Agent 统一服务层 |
| SSE 分析进度 | `/api/stocks/{code}/analysis/stream` | 单股分析可实时显示阶段和 token |
| ETag 缓存响应 | `_cached_json_response()` | 对行情/新闻/热点做 HTTP 缓存和 stale-while-revalidate |
| Demo Access Cookie | `DEMO_ACCESS_*` | 公开演示时保护 AI/持仓等敏感功能 |
| Agent 会话记忆 | `AgentMemoryStore` | SQLite 保存对话、profile、watchlist、pinned memory、heartbeat summary |
| 心跳总结 | `_maybe_run_heartbeat()` | 定期把近期对话写成 Markdown 记忆 |
| 多市场统一搜索 | `ashare.stock_pool` 调用 | A 股、港股、美股同一搜索入口 |
| 智能引擎回退 | `_get_pydantic_agent()` + deterministic path | LLM 不可用时回退规则分析 |

---

## 页面与能力

| 页面 | 作用 |
|---|---|
| `/work` | 研究工作台 |
| `/stocks` | 股票搜索与单股分析 |
| `/charts` | K 线图 |
| `/news` | 市场消息与个股新闻 |
| `/hotspots` | 热点主题与关联标的 |
| `/portfolio` | 本地持仓组合与风险分析 |
| `/agent` | 统一 Agent 研究对话 |
| `/settings` | 模型与服务配置 |

---

## 后端服务结构

```text
api/main.py
  FastAPI app, CORS, demo access, SSE, ETag, routes, memory store

api/services.py
  StockAnalysisService
  NewsService
  HotspotService
  MarketService
  PortfolioService
  StrategyService
  WebSearchService

ashare/
  analyzer, monitor, search, signals, stock_pool
```

---

## 可直接迁移的设计

1. **研究工作台入口**: 个股、热点、新闻、持仓、Agent 不应是孤立页面。
2. **SSE 分析进度**: 长分析必须有阶段进度，而不是等 HTTP 请求挂住。
3. **会话记忆结构化**: 记 last_stock、watchlist、pinned_memory、active_goal。
4. **Heartbeat Markdown**: 把会话摘要落到本地 Markdown，供后续 Agent 读取。
5. **Demo 访问保护**: 公开部署时保护设置、AI、持仓、策略持股。
6. **规则回退**: LLM 配置缺失或失败时仍返回基础技术分析。

---

## 和 tickflow-stock-panel 的差异

| 维度 | tickflow-stock-panel | OpenAshare |
|---|---|---|
| 核心 | 本地数据湖 + 策略/监控/回测 | 研究工作台 + Agent 对话 |
| 数据 | Parquet/DuckDB/Polars | AkShare/pandas + SQLite 配置 |
| 实时性 | 盘中 quote service 和监控 | 分析进度 SSE，行情分析缓存 |
| 策略 | StrategyDef 复用选股/回测/监控 | CAN SLIM 筛选和策略持股观察 |
| AI | 报告和策略生成 | 页面内统一研究问答和会话记忆 |

两者适合组合：tickflow 做量化数据/策略底座，OpenAshare 做轻量研究台和 Agent 交互层。
