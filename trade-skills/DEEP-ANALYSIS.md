# trade-skills 深度分析

> 真实交易研究仓库 · Agent Skill 编排 · Markdown 落档 · 实时图表驾驶舱
> 源码: `/root/source/tmp/trade-skills/`
> 原始仓库: <https://github.com/Innei/trade-skills>

---

## 1. 项目形态

`trade-skills` 明确说自己是“交易日志仓库”，不是产品。这个定位反而让它很有学习价值：它不是为了展示功能，而是为了支持真实日常研究。

核心资产有三类：

| 资产 | 位置 | 说明 |
|---|---|---|
| 每日札记 | `journal/` | 盘后资金轮动、盯盘报告、主题记录 |
| 个股笔记 | `stocks/` | 单票六维研究，增量更新不重写 |
| 图表数据 | `journal/charts/data/` | 每张图一个 JSON，带 schema version |

数据库不是核心。研究资料以 Markdown/JSON 文件为主，便于 git、搜索、人工阅读和 Agent 直接读写。

---

## 2. Skill 层

自研 skill 位于 `.claude/skills/`：

| Skill | 作用 |
|---|---|
| `capital-rotation` | 盘后 cohort 资金轮动扫描 |
| `fred` | 宏观时间序列 |
| `gdelt` | 全球新闻流和情绪 |
| `intraday-signal` | 单票短线多周期钻取 |
| `market-session-tracker` | 盘中观察清单跟踪 |
| `sec-edgar` | SEC 文件和 Form 4 |
| `stock-deep-dive` | 单票六维研究 |
| `trump-truth-monitor` | Truth Social 监控与归档 |
| `chart` | 调本地图表应用出图 |
| `_shared` | env、缓存客户端、输出协议 |

共享约定很清楚：成功输出 `{"ok": true, "data": ..., "meta": ...}`，失败输出 `{"ok": false, "error": ..., "hint": ...}`，诊断走 stderr。

这个约定适合迁移到所有 Agent Skill：自然语言可变，但工具输出必须结构化。

---

## 3. 工作流层

工作流不增加新数据源，而是把工具调用按研究纪律编排。

| 工作流 | 用途 | 落档 |
|---|---|---|
| `stock-deep-dive` | 新票首次研究，业务/基本面/技术面/催化剂/上下游/自审 | `stocks/{SYMBOL}.md` |
| `capital-rotation` | 盘后扫固定 cohort 资金流 | `journal/YYYY-MM-DD-flow.md` |
| `market-session-tracker` | 盘中跟踪观察清单 | `journal/YYYY-MM-DD-<theme>.md` |
| `intraday-signal` | 单票短线多周期入场/止损/目标 | chart JSON + journal |
| `sepa-strategy` | Minervini 趋势模板和 VCP | chart JSON |
| `earnings-preview/recap` | 财报前瞻和复盘 | journal/stocks |

设计重点：工作流不是 prompt 集合，而是“调用顺序 + 防错纪律 + 落档位置”的组合。

---

## 4. 图表应用

`app/` 是 pnpm workspace，分三包：

| 包 | 作用 |
|---|---|
| `shared/` | 跨 server/web 的类型和时间工具 |
| `server/` | Fastify + TypeScript，调用 Longbridge CLI、计算指标、提供 REST/SSE |
| `web/` | Vite + React，渲染图表和个股驾驶舱 |

单进程模式很务实：Fastify 以内嵌 Vite middleware 托管前端源码，开发时无需单独 build。服务端自己实算指标，不把关键计算放到浏览器。

### 4.1 图表类型

| type | 内容 |
|---|---|
| `flow` | 单标的日内资金流累计曲线 |
| `cohort` | 跨标的资金净额 signed bar 对比 |
| `sepa` | 52 周高低、均线、RS、趋势模板、支撑阻力、入场计划 |
| `intraday` | 5m/15m/1h K 线、MACD、均线、三情景推演、新闻和市场 context |

### 4.2 自动标注

intraday 面板自动检测 MACD 结构、1-2-3 形态、背离/背驰、14 种 K 线形态、盘前/盘后时段覆盖。这些都在 server 重算，前端负责展示。

---

## 5. AI 哨兵与 CLI 参谋

`app/README.md` 对 AI 分层非常清晰：

| 层 | 触发 | 视野 | 成本 | 产出 |
|---|---|---|---|---|
| server commentator | 自动 60 秒扫描/事件触发 | 窄数据包 | 低 | 一两句点评 |
| server analyst | 升级触发/手动 | 固定多周期数据 + 新闻 | 中 | 新 intraday 图和点评 |
| CLI + skill | 手动会话 | 全仓库上下文和全部工具 | 高 | 完整研判、图、日志、笔记更新 |

这解决了金融 Agent 常见成本问题：不能让强模型全天盯盘，也不能让低成本模型承担完整决策。

迁移建议：当前项目也应区分 `sentinel` 和 `analyst`。前者只负责发现“有事发生”，后者才负责重新研判。

---

## 6. 数据存储分层

图表应用后期引入 SQLite，但仍保留文件为核心资产：

| 存储 | 内容 |
|---|---|
| JSON 文件 | 图表文档，历史研判快照 |
| SQLite `comments` | 盘中点评流水 |
| SQLite `ai_usage` | AI 成本流水 |
| SQLite `chart_meta` | 图表索引，可从文件目录重建 |
| SQLite `outcomes` | 已了结预测结局缓存 |

关键原则：实时数据不落盘，只有 POST/PATCH 的研判快照写入文件。这样历史图表代表“当时的判断”，不会被后来的实时行情污染。

---

## 7. 安全写入约束

研究笔记 deep-dive 功能允许 server 触发 AI 代理更新 `stocks/{SYMBOL}.md`，但写入约束很硬：

| 约束 | 目的 |
|---|---|
| `write_note` 只写固定目标文件 | 代理传不了任意路径 |
| bash 工具拒绝重定向、tee、rm、mv、cp | 防止绕过写工具 |
| `read_file` 只能读仓库内文件 | 限制读取范围 |
| 跑前/跑后检查 `git status` | 发现目标文件以外的意外改动 |
| 默认 smoke 写临时目录 | 验证逻辑不污染真实笔记 |

这套约束可迁移到任何“AI 自动更新研究笔记”的功能。

---

## 8. 对当前项目的落地方案

1. 建立 `journal/` 和 `stocks/` 双层研究记录。
2. 所有图表/分析结果落 JSON，带 `schema_version`。
3. 把 Skill 输出统一成 `{ok,data,meta}` / `{ok,error,hint}`。
4. 建立 `sentinel -> analyst -> human` 三层响应模型。
5. 每个交易日自动生成 recap，存在则追加或跳过，不覆盖。
6. 给 AI 成本单独落表，页面可查。
7. 研究笔记自动写入必须白名单路径和 git 状态校验。
