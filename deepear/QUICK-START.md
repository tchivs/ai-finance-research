# DeepEar 快速概览

> 金融 Deep Research 与信号追踪框架 · 多 Agent · ISQ 信号质量评分 · 新闻感知 Kronos · 逻辑演化对比
> 源码: `/root/source/tmp/DeepEar/`
> 原始仓库: <https://github.com/HKUSTDial/DeepEar>

---

## 一句话定位

`DeepEar` 把新闻、社媒、搜索结果等非结构化信息转成可评分、可追踪、可生成报告的投资信号。它的重点不是“问一个股票怎么样”，而是从公共舆情里发现可能影响市场的事件，再经过 TrendAgent、FinAgent、ReportAgent、ForecastAgent 形成投资逻辑链。

它最值得学习的是信号生命周期：发现、筛选、结构化、评分、报告、更新、演化对比。

---

## 最高价值借鉴点

| 借鉴点 | 代码位置 | 可复用价值 |
|---|---|---|
| 主工作流编排 | `src/main_flow.py` | Trend -> Fin -> Report，带 checkpoint/resume/update |
| 双模型路由 | `utils.llm.router` 调用 | 推理模型和工具模型分开，降低成本 |
| LLM 信号筛选 | `_llm_filter_signals()` | 先判是否有有效信号，避免无效新闻浪费分析 token |
| 主动搜索 | `search_tools.search_list()` | 用户 query 明确时主动补外部搜索结果 |
| ISQ 评分框架 | `src/schema/isq_template.py` | 情绪、确定性、强度、预期差、时效性统一评分 |
| 投资信号结构 | `src/schema/models.py` | transmission_chain、impact_tickers、sources 都是结构化字段 |
| checkpoint/resume | `utils.checkpointing` 调用 | 分析中断后可从 report 或 analysis 继续 |
| update_run | `SignalFluxWorkflow.update_run()` | 旧信号刷新行情后做逻辑演化对比 |
| Agent Skill 化 | `skills/deepear` | 可作为 OpenCode/Claude/OpenClaw Skill 触发完整流程 |

---

## 核心流程

```text
用户 query / 定时扫描
    ↓
IntentAgent 解析意图与搜索词
    ↓
TrendAgent 从财经/社媒/科技源抓热点
    ↓
SearchTools 主动搜索补充信号
    ↓
LLM Filter 筛出高价值信号
    ↓
FinAgent 按 ISQ 解析投资逻辑、标的、传导链、风险
    ↓
ReportAgent Map-Reduce 写报告并转 HTML
    ↓
update_run 时刷新行情并追踪信号演化
```

---

## ISQ 信号质量维度

| 维度 | 取值 | 含义 |
|---|---|---|
| `sentiment` | -1 到 1 | 看空/中性/看多方向 |
| `confidence` | 0 到 1 | 来源和逻辑可信度 |
| `intensity` | 1 到 5 | 影响量级 |
| `expectation_gap` | 0 到 1 | 预期差和博弈空间 |
| `timeliness` | 0 到 1 | 反应窗口紧迫度 |

综合评分公式来自模板：`confidence * 0.35 + intensity/5 * 0.30 + expectation_gap * 0.20 + timeliness * 0.15`。

---

## 和现有项目的差异

| 项目 | 偏重点 | DeepEar 的不同 |
|---|---|---|
| `daily_stock_analysis` | 多源行情 + 定时分析 + 推送 | DeepEar 更强调新闻/舆情信号的逻辑链和演化 |
| `UZI-Skill` | 单票深度报告 | DeepEar 从热点事件出发，不一定先有股票代码 |
| `ai-berkshire` | 大师投资方法论 | DeepEar 更偏事件驱动和信号质量评分 |
| `x2t` | 信源战绩结算 | DeepEar 评分单条信号，x2t 评价信源长期可信度 |

---

## 可直接迁移的设计

1. **Signal Schema**: 把每条新闻/事件转成 `InvestmentSignal`，而不是只存自然语言分析。
2. **ISQ Template**: 将信号评分维度做成可配置模板，而不是写死在 prompt 里。
3. **Run Checkpoints**: 每轮保存 `intent`, `search_signals`, `high_value_signals`, `analyzed_signals`, `report`。
4. **Update Mode**: 对旧报告重新刷新行情和信号逻辑，输出“逻辑变强/变弱/证伪”。
5. **Dual Model Routing**: 工具调用/搜索摘要用便宜模型，关键推理/报告用强模型。
6. **No Valid Signal Gate**: LLM 筛选先返回 `has_valid_signals=false` 时直接停止。

---

## 注意事项

- README 里的 News-aware Kronos 是强概念，但正式迁移前要验证预测数据和回测效果。
- `main_flow.py` 里并发分析对 DB 写入做了主线程写回处理，这是值得保留的并发边界。
- `resume_from=report` 和 `resume_from=analysis` 是两个不同层级，适合长任务调试。
- ISQ 分数不应被当成收益预测，它是信号质量评分。
