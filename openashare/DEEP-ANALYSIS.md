# OpenAshare 深度分析

> 本地优先研究台 · FastAPI 服务层 · SSE 进度 · Agent Memory · 热点/持仓/策略闭环
> 源码: `/root/source/tmp/OpenAshare/`
> 原始仓库: <https://github.com/ZhiweiChen-coder/OpenAshare>

---

## 1. 总体架构

OpenAshare 是 Next.js 前端 + FastAPI 后端。后端入口 `api/main.py` 实例化一组服务：

| 服务 | 作用 |
|---|---|
| `StockAnalysisService` | 股票搜索、行情抓取、技术指标、AI 分析 |
| `NewsService` | 个股新闻、全球新闻、去重和缓存 |
| `HotspotService` | 热点主题、热度分解、关联股票 |
| `MarketService` | 市场状态和指数快照 |
| `PortfolioService` | 本地组合和持仓分析 |
| `StrategyService` | 策略候选、策略持股和复盘动作 |
| `WebSearchService` | Google News RSS 和 DuckDuckGo HTML 搜索 |
| `AgentService` | 规则或 PydanticAI Agent 研究问答 |

这是一种“服务聚合型工作台”，不是单一股票分析脚本。

---

## 2. API 层工程细节

### 2.1 ETag 与缓存

`_cached_json_response()` 会对 payload 做 JSON canonicalization 后生成 weak ETag，并设置：

```text
Cache-Control: public/private, max-age=N, stale-while-revalidate=M
ETag: W/"sha1"
```

如果请求 `if-none-match` 命中，直接返回 304。这个模式适合热点、新闻、行情快照等频繁刷新但短时间稳定的数据。

### 2.2 Demo Access

`DEMO_ACCESS_CODE` 和 `DEMO_ACCESS_SECRET` 启用后，设置、AI 分析、持仓、策略持股等敏感功能需要 cookie 解锁。token 是 `issued_at.signature`，signature 用 HMAC-SHA256。

这对公开演示金融研究工具很实用：页面可以开放，涉及个人配置或成本的功能受控。

### 2.3 全局异常处理

`global_exception_handler()` 生成 `request_id`，服务端记录完整异常，客户端只返回 `Internal server error` 和 request_id，避免泄露内部错误。

---

## 3. 单股分析流

`StockAnalysisService.build_analysis_bundle()` 的流程：

```text
normalize_stock_code
    ↓
stock_searcher.get_stock_info
    ↓
StockAnalyzer.fetch_data
    ↓
calculate_indicators
    ↓
analyze_single_stock
    ↓
SignalAnalyzer.analyze_all_signals
    ↓
可选 generate_single_stock_analysis
    ↓
StockAnalysisResponse
```

返回内容包括：

| 字段 | 内容 |
|---|---|
| `quote` | 当前价、涨跌、开高低、成交量、振幅 |
| `technical_indicators` | MA、RSI、MACD、KDJ、BOLL |
| `signal_summary` | overall_score、overall_signal、分类信号 |
| `technical_commentary` | 规则技术分析建议 |
| `ai_insight` | AI 文本、provider、model、error |
| `chart_series` | 最近约 5 年日 K |
| `metadata` | 数据点数量、source、generated_at |

服务层使用 TTL cache。AI 分析缓存 key 包含模型名，避免换模型后命中旧结论。

---

## 4. SSE 进度流

`/api/stocks/{stock_code}/analysis/stream` 用 `asyncio.Queue` 输出 SSE。事件包括：

| kind | 含义 |
|---|---|
| `start` | 已接收请求 |
| `progress` | 阶段进度 |
| `token` | AI 流式增量 |
| `result` | 最终结果 |
| `error` | 错误 |
| `done` | 流结束 |

源码里有一个细节：结束哨兵 `None` 也通过同一个 `loop.call_soon_threadsafe(queue.put_nowait, None)` 入队，避免它插队到 result/done 之前导致客户端丢事件。

这是可以直接迁移的 SSE 可靠性经验。

---

## 5. Agent Memory

`AgentMemoryStore` 用 SQLite 存三张表：

| 表 | 内容 |
|---|---|
| `agent_memory` | 每轮 user/agent 对话、intent、stock_code、stock_name |
| `agent_profile` | preferred_market、last_stock、watchlist、pinned_memory、active_goal |
| `agent_profile_summary` | heartbeat 时间、次数、summary_text、memory_markdown_path |

关键函数：

| 函数 | 作用 |
|---|---|
| `append_turn()` | 追加对话 turn |
| `get_recent_history()` | 取最近上下文 |
| `update_profile()` | 更新偏好、最后标的、watchlist、目标 |
| `_maybe_run_heartbeat()` | 到时间后生成摘要并写 Markdown |
| `_write_memory_markdown()` | 将 profile、summary、pinned、watchlist、recent context 写到 `data/agent_memory/*.md` |

这个设计比“只把 history 放浏览器”更稳：Agent 可以跨会话保留用户研究偏好和关注标的，同时把摘要落为可读 Markdown。

---

## 6. 新闻与热点服务

`NewsService` 对全球新闻采用多源并发但带超时：财联社、财联社快讯、新浪财经、同花顺。每个源失败就跳过，最终按 impact_level 和发布时间排序去重。

`HotspotService` 用主题模板把新闻、告警、股票池、topic keywords 聚合为热点。它不完全依赖 LLM，而是有规则模板和 stock pool 映射。

这种“规则热度底座 + AI 解释”的方式比纯 LLM 生成热点更稳定。

---

## 7. Agent 引擎回退

`_get_pydantic_agent()` 根据运行时 settings 里的 `llm_api_key/base_url/model` 创建 PydanticAI agent。没有 key 或创建失败时返回 None，后续可以走 deterministic 规则路径。

这类回退对本地工具很重要：

1. 没配置 LLM 时仍能查行情和技术指标。
2. LLM 失败时前端显示“切换到规则分析”。
3. 设置更新后会清空缓存并重建 agent。

---

## 8. 对当前项目的落地建议

| 目标 | 迁移方案 |
|---|---|
| 长分析有反馈 | 统一 SSE progress schema，至少包含 start/progress/token/result/error/done |
| 研究上下文连续 | 引入 SQLite `agent_memory` 和 Markdown heartbeat |
| 公开演示安全 | 加 HMAC demo access cookie，保护 AI/持仓/设置 |
| 降低接口压力 | 对热点/新闻/分析结果加 ETag + TTL cache |
| LLM 不可用降级 | 所有 AI 功能都保留 deterministic fallback |
| 页面间不断上下文 | Agent profile 记录 last_stock、watchlist、active_goal |

OpenAshare 的价值不在数据深度，而在“研究流产品化”。它适合和 `a-stock-data` 的数据底座、`tickflow-stock-panel` 的策略回测、`DeepEar` 的信号评分组合起来。
