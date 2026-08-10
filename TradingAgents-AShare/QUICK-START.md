# TradingAgents-AShare 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/KylinMountain/TradingAgents-AShare.git
> 分析基线：
> - `TradingAgents-AShare`：commit `fef942f94081885a7e6956c71645dbaf3b93b811`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/TradingAgents-AShare`
<!-- source-sync:end -->


> KylinMountain · 面向 A 股的多智能体投研与交易建议系统 · Python、LangGraph、FastAPI、React、Vite
> 源码: `src/TradingAgents-AShare/`
> 原始仓库: <https://github.com/KylinMountain/TradingAgents-AShare>

## 1. 一句话定位

TradingAgents-AShare 是把 A 股数据采集、专业分工、多空辩论、交易计划和风控裁决串成 LangGraph 状态图的投研应用：用户用自然语言或 `POST /v1/analyze` 发起任务，系统以 SSE 展示每名 Agent 的取数和论证，持久化结构化报告，并支持自选、持仓、跟踪看板及定时运行。

README 沿用“14 名专业 Agent”的产品表述：六类分析师、两名研究员、研究总监、交易员、三名风险辩手和风险裁决者。当前源码已增加 `Volume Price Analyst`，`GraphSetup.setup_graph()` 的默认图和 `frontend/src/stores/analysisStore.ts` 都登记 15 个角色；使用时应以当前 15 角色实现为准。

## 2. TradingAgents-AShare 覆盖的链路

```text
自然语言/股票代码 + 交易日期
    -> parse_intent / 用户上下文
    -> DataCollector 一次并发抓取、缓存、技术指标与 VPA 预计算
    -> 市场/舆情/新闻/基本面/宏观/资金/量价七类分析师并行
    -> Bull Researcher <-> Bear Researcher 多空 claim 辩论
    -> Research Manager 投资计划 -> Trader 执行计划
    -> 激进 -> 保守 -> 中性风险辩论 -> Risk Judge
    -> 退回 Trader 修订，或输出 final_trade_decision / 结构化报告 / SSE 事件
```

数据层通过 `dataflows/interface.py::route_to_vendor()` 路由并回退：默认注册 AkShare、BaoStock、Investoday、yfinance、Alpha Vantage。`DataCollector._fetch_all()` 会采集 K 线、新闻、资金流、龙虎榜、涨停池、热度、基本资料和三大报表；用 365 天 K 线本地计算 SMA、RSI、MACD、布林、ATR、VWMA 与量价指标，再按短线 14 天或中线 90 天供 Agent 使用。

## 3. 核心模块

| 模块 | 作用 | 对当前项目的价值 |
|------|------|------------------|
| `tradingagents/graph/setup.py` | 用 `StateGraph(AgentState)` 建立分析并行、研究辩论、风控循环与回退 Trader 的有向图 | 直接借鉴“证据并行—论证—执行—可否决风控”边界 |
| `agents/analysts/` | 市场、舆情、新闻、基本面、宏观、主力资金、量价七份独立报告 | 用领域报告字段替代 Agent 间随意拼接长文本 |
| `agents/researchers/`、`managers/research_manager.py` | 多空围绕结构化 claim 辩论，研究总监形成 `investment_plan` | 把分歧、未解决论点和裁决依据保留为可审计状态 |
| `agents/risk_mgmt/`、`managers/risk_manager.py` | 三方风险博弈；解析 `RISK_JUDGE` 中的约束、前提和降风险触发器 | 风控可以要求策略改写，而不是仅在结尾加风险提示 |
| `graph/data_collector.py` | 每标的/日期的缓存、超时、批量抓取、本地技术/VPA 计算 | 减少第三方数据重复请求；可扩展数据版本和质量 artifact |
| `dataflows/providers/` | AkShare、BaoStock、Investoday 等供应商的统一方法与回退 | A 股数据源要声明口径、失败与回退，不能假设任一源完整可靠 |
| `api/main.py`、`scheduler/main.py` | FastAPI 任务/API/SSE/报告；交易日定时分析、限流和陈旧任务恢复 | 将长时工作流从 Web 请求解耦，支持单体或 API/调度器分体部署 |
| `frontend/src/` | React/Vite 页面、Zustand 状态、`useSSE.ts`、报告和协作界面 | 将 Agent 轨迹与辩论实时呈现给用户，而非只展示最终建议 |

## 4. 最值得学的设计

`TradingAgentsGraph` 在 `trading_graph.py` 中为深度与快速模型、五类 `FinancialSituationMemory` 及共享 `DataCollector` 初始化运行时；`AgentState` 将报告、投资辩论、风险辩论和用户上下文显式建模。`Risk Judge` 可经 `should_revise_after_risk_judge` 回到 `Trader`，是整个图最关键的闭环。

数据质量仍是接入风险：`CnBaoStockProvider` 明确未实现财报和新闻，AkShare 受并发/反爬约束，Investoday 需要 API Key。当前项目应吸收其编排、缓存与可视化，不应把 LLM 输出直接当作经过回测或可实盘执行的结论。
