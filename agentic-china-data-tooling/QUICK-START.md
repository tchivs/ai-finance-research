# Agentic China Data Tooling 快速概览

> openclaw-data-china-stock + stock-sdk-mcp + Financial-API · Agent 数据工具层与本地 MarketDB
> 源码: `/root/source/tmp/openclaw-data-china-stock/`, `/root/source/tmp/stock-sdk-mcp/`, `/root/source/tmp/Financial-API/`
> 原始仓库: [openclaw-data-china-stock](https://github.com/shaoxing-xie/openclaw-data-china-stock) · [stock-sdk-mcp](https://github.com/chengzuopeng/stock-sdk-mcp) · [Financial-API](https://github.com/HiThink-Tech/Financial-API)

## 1. 一句话定位

这组项目共同回答一个问题：如何把中国市场数据变成 Agent 可以安全、稳定、可审计调用的工具层。`stock-sdk-mcp` 偏 MCP server 和复合工具，`openclaw-data-china-stock` 偏插件化 tool runner/source health/factor screening，`Financial-API` 偏本地 DuckDB MarketDB 和 typed REST client。

合并后的模式是：

```text
Upstream sources
    -> typed client / SDK
    -> local MarketDB / cache
    -> tool runner / MCP server
    -> compound tools / prompts / resources
    -> source health / quality / freshness
    -> Agent workflows
```

## 2. 三个项目各自贡献

| 项目 | 定位 | 最值得学 |
|------|------|----------|
| stock-sdk-mcp | TypeScript MCP server for stock-sdk | tools/resources/prompts 三能力、复合工具、`Promise.allSettled` dataStatus |
| openclaw-data-china-stock | OpenClaw 插件式 A 股工具包 | `tool_runner.py`、别名兼容、Pydantic 参数、统一 envelope、source health |
| Financial-API | Fuyao typed API + DuckDB marketdb | FULL/INCREMENTAL/SKIP 自动同步、Parquet import、quality/freshness checks |

## 3. 核心工作流

```text
Agent asks for market/factor task
    -> search/select tool or MCP prompt
    -> validate args / schema gate
    -> call SDK or local MarketDB
    -> collect partial dataStatus
    -> return compact structured JSON
    -> log metrics/source health/quality status
```

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| MCP tools/resources/prompts | `stock-sdk-mcp` 同时暴露三类能力 | Agent 不只需要工具，还需要资源和 workflow prompt |
| Compound tools | 一次 `analyze_stock` 聚合 K 线、指标、资金、分红、北向 | 减少 LLM 多轮工具调用成本 |
| dataStatus | 每个上游块用 fulfilled/rejected/error 标注 | 部分失败也能返回可用结果 |
| Tool runner map | `TOOL_MAP` 映射工具名到 module/function/params_model | Python 插件工具可集中调度 |
| Aliases | 旧工具名注入参数后路由到新工具 | 兼容 cron/工作流，不破坏老入口 |
| Unified envelope | elapsed_ms、tool、plugin_version、error_code | Agent 可按机器字段分支处理错误 |
| Source health | import-level probe + snapshot/history JSONL | 数据源可用性成为可观测对象 |
| Engine fallback | TA-Lib -> pandas-ta -> builtin | 指标计算要有后端降级链 |
| MarketDB sync decision | FULL/INCREMENTAL/SKIP | 本地数据同步不能每次全量拉 |
| Quality checks | rowcount、PK、OHLC、负数、adjustment PK | 数据库应有可运行质量门 |
| Typed Fuyao client | 参数约束、分页、长窗口切片、env token | API client 适合直接给 Agent 用 |

## 5. 对 HermesAlpha 的借鉴

1. **统一工具契约**：所有数据工具输出 `success/message/data/error_code/quality_status/elapsed_ms`。
2. **优先做复合工具**：如“个股全景”一次返回 quote、K 线指标、资金流、公告、估值、财务摘要，减少 Agent 工具循环。
3. **引入 dataStatus**：允许估值成功、北向失败、公告成功，不要因为一块失败丢掉全部结果。
4. **建立本地 MarketDB**：日线、复权因子、调整事件用 DuckDB/Parquet 管理，在线 API 只做补充。
5. **做 source health 面板**：akshare、eastmoney、tushare、sina、yfinance 等源的可用性和最近错误要可见。

## 6. 对 ashare-audit 的借鉴

1. **审计工具返回契约**：是否有 schema version、plugin version、elapsed_ms、error_code。
2. **审计部分失败处理**：LLM 是否知道哪些数据块失败，而不是把缺失数据当 0。
3. **审计 MarketDB 新鲜度**：本地最大交易日是否落后超过阈值。
4. **审计质量门**：OHLC、主键、调整事件、负成交量等数据问题是否被检测。
5. **审计 source health**：报告中引用的数据源当时是否可用。

## 7. 不该照搬的部分

- `stock-sdk-mcp` 的 prompt 有些会直接“给建议”，迁移到合规产品时要改成分析/观察/风险，不给操作建议。
- `openclaw-data-china-stock` 工具体系很大，不能全量暴露给模型，应按 workflow/profile 裁剪。
- `Financial-API` 依赖 Fuyao token 和指定 dump 机制，迁移时要抽象成 provider interface。
- MarketDB 的 quality checks 只是基础层，生产还要补交易日连续性、停复牌、复权一致性和供应商交叉校验。

## 8. 最小可迁移方案

```text
Phase 1: Tool envelope
    success/message/data/error_code/quality_status/elapsed_ms

Phase 2: Compound tools
    stock_overview / market_overview / factor_screen

Phase 3: Local MarketDB
    DuckDB + raw tables + views + _meta

Phase 4: Source health
    probe + snapshot + history

Phase 5: MCP surface
    tools + resources + workflow prompts
```

## 9. 结论

Agentic China Data Tooling 的核心不是“哪个数据源更全”，而是数据工具如何被 Agent 安全消费：参数要校验、结果要结构化、部分失败要显式、源健康要可观测、本地数据要有质量门。这是当前项目数据层最该吸收的一组模式。
