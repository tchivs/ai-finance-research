# trade-skills 快速概览

> 个人美股交易研究工作台 · Markdown 交易日志 · Agent Skills · 本地实时图表应用
> 源码: `/root/source/tmp/trade-skills/`
> 原始仓库: <https://github.com/Innei/trade-skills>

---

## 一句话定位

`trade-skills` 是一个真实个人交易研究仓库，不是对外发布的软件产品。它把美股研究拆成三层：数据源 Skill、编排工作流、Markdown/JSON 落档，再用本地 Fastify + React 图表应用渲染 K 线、资金流、SEPA 仪表盘、短线多周期预测和个股驾驶舱。

它最值得学习的是“研究必须落档”的纪律：每个工作流最后都写入 `journal/`、`stocks/` 或 `journal/charts/data/`，图表和笔记都是可回放资产。

---

## 最高价值借鉴点

| 借鉴点 | 位置 | 可复用价值 |
|---|---|---|
| 三层结构 | `README.md` | 数据源、工作流、落档严格分工 |
| 自研 Skill | `.claude/skills/` | FRED、SEC、GDELT、Trump、盘中信号、资金轮动等 |
| 共享输出协议 | `.claude/skills/_shared/` | 成功/失败 JSON 统一，stderr 放诊断 |
| 图表应用 | `app/README.md` | Fastify + Vite middleware 单进程，本地图表实时刷新 |
| 图表 JSON 落档 | `journal/charts/data/` 约定 | 前端代码可变，历史数据不丢 |
| Cockpit 个股驾驶舱 | `app/` | 预测、环境、消息、复盘、AI 点评同屏 |
| AI 高频哨兵 vs CLI 参谋 | `app/README.md` | 低成本自动盯盘和高成本深度研判分层 |
| 数据纪律 | README “贯穿全局的纪律” | 不模糊描述、数字溯源、YoY 必带 QoQ、只给情景 |

---

## 三层结构

```text
数据源层
  Longbridge / FRED / SEC EDGAR / GDELT / Truth Social / Yahoo
    ↓
编排工作流层
  stock-deep-dive / capital-rotation / market-session-tracker / sepa-strategy / earnings
    ↓
落档层
  journal/*.md / stocks/*.md / journal/charts/data/*.json
    ↓
本地图表应用
  Cockpit / flow / cohort / sepa / intraday / SSE realtime
```

---

## 图表应用能力

| 页面/API | 作用 |
|---|---|
| `/` | 今日盘中看板和跨标的图表 |
| `/symbol/:sym` | 个股驾驶舱 |
| `/api/charts` | 图表 CRUD |
| `/api/symbols/:sym/flow` | 当日资金流曲线 |
| `/api/symbols/:sym/latest` | 最新 intraday 分析和持仓对照 |
| `/api/stream/quotes` | 10 秒行情 SSE |
| `/api/stream/charts/:id` | 图表数据 60 秒重算推送 |

图表类型：`flow`, `cohort`, `sepa`, `intraday`。

---

## 直接可借鉴的纪律

1. **每个工作流必须落档**：不允许只在聊天上下文里留下结论。
2. **图表数据和渲染分离**：历史 JSON 带 schema version，前端永远用最新代码渲染。
3. **数字溯源**：业绩数据以公司原文/8-K/OHLCV 为准，社区帖不能当公司口径。
4. **GAAP 与 non-GAAP 分开**：一致预期通常是 non-GAAP，不能和 GAAP EPS 混用。
5. **YoY 必带 QoQ**：避免高基数或低基数造成误判。
6. **只给情景，不给点位预测**：Bull/Base/Bear 三档，概率合计 100%，附触发条件。
7. **用户方向不附和**：用户说突破/回调时，必须重新拉报价核验。

---

## 对当前项目的启发

| 当前需求 | 可借鉴设计 |
|---|---|
| 研究记录持久化 | `journal/` + `stocks/` Markdown |
| 图表回放 | `journal/charts/data/*.json` schema version |
| 盘中自动监控 | server 内置 commentator/analyst 双层 AI |
| Agent Skill 规范 | `_shared` 输出协议、缓存、限流、env |
| 个股长期跟踪 | `stocks/{SYMBOL}.md` 六维笔记 |
| 成本控制 | 高频便宜模型，低频强模型，花费落 SQLite |
