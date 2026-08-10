# 跨项目综合提炼 — 通用设计模式与行动建议

## 阅读结论

这 42 个项目并没有证明“更复杂的 Agent 更好”，而是反复证明了以下顺序更可靠：

1. **先稳定数据契约**：字段、时间、来源、缓存和缺失值语义必须明确。
2. **再统一工具边界**：CLI、MCP、Skill 和 Gateway 都应留下可重放的调用记录。
3. **然后引入 Agent 编排**：简单任务保持单 Agent；多角色只用于确实需要冲突、复核或状态回放的场景。
4. **最后做产品化交互**：UI 要展示数据日期、降级状态、任务进度、证据和失败原因，而不只是最终答案。
5. **高风险动作默认受限**：认证、持仓、策略执行和交易从最小 scope、只读或 `paper_only` 开始。

### 建议优先级

| 优先级 | 应先建立 | 暂不优先 |
|--------|----------|----------|
| P0 | 数据契约、来源追踪、工具调用 envelope、敏感数据边界 | 自动实盘、复杂多 Agent 状态机 |
| P1 | 静态快照、Provider health、引用链、任务状态、质量 Banner | 大规模实时行情、全量技能生态 |
| P2 | Moderator、盯盘闭环、策略统一契约、工作台运行流 | 多市场完整交易 OS |

### 适用边界

本文归纳的是可迁移模式，不代表所有上游能力都达到生产成熟度。具体实现前，应通过 [项目索引](00-INDEX.md#项目目录) 回到对应 `DEEP-ANALYSIS.md` 检查版本、依赖、占位实现和已知限制；涉及技术分叉时使用 [模式决策矩阵](18-模式决策矩阵.md)，涉及排期时使用 [落地路线图](17-落地路线图.md)。

## 一、42 个项目揭示的通用设计模式

### 模式 1: Pipeline 式分析流程

多个项目不约而同选择了 `collect → analyze → score → render` 的分阶段管道架构。

| 项目 | 实现 |
|------|------|
| UZI-Skill | collect→score→synthesize→renderer |
| daily_stock_analysis | StockAnalysisPipeline |
| Vibe-Trading | LangGraph 状态机（有向图） |
| QuantDinger | AI研究→指标代码→回测→纸面/实盘执行→监控 |
| ai-berkshire | 信息评估→团队并行→交叉验证→审计准出 |
| tickflow-stock-panel | 盘前维表→盘后 enriched→策略/监控/回测/复盘 |
| JCP | MarketService→Moderator选人→专家串行讨论→二轮复核→汇总 |
| PanWatch | BaseAgent.collect→analyze→notify，外接 TradingAgents 结果 |
| Awesome Finance Skills | search/stock/sentiment/forecast/report 分 skill 流水线 |
| Privora Examples | public ping→token verify→dataasset query→portfolio snapshot |

**原则**: 每阶段职责单一、输出纯数据、可独立重跑和 Mock。

### 模式 2: 数据源策略层 + 自动 Fallback

所有项目都需要多数据源，核心问题都是：**一个源挂了不拖垮整体**。

| 项目 | 方案 |
|------|------|
| daily_stock_analysis | 策略模式 + 优先级系统 + 自动降级 |
| daily_stock_data | Tushare -> TickFlow -> baostock 日线顺序 + CSV/PostgreSQL 双后端 |
| UZI-Skill | 22 fetcher + Playwright 兜底 + self-review |
| Vibe-Trading | 18 源联邦 + opt-key 模式 |
| JCP | TDX/Sina/OpenClaw 多入口行情与分析 fallback |
| PanWatch | TradingAgents 数据适配 + 持仓上下文 + same-day cache |
| Awesome Finance Skills | akshare/yfinance/东方财富直连 fallback + SQLite 缓存 |
| magpie | Sina/Tencent/Eastmoney worker + SQLite quote_cache |
| hhxg-market | 静态 JSON + 网络重试 + `~/.cache/hhxg-market` 兜底 |
| snowball-cli | public request 与 cookie request 分离 |

**原则**: `can_handle()` 路由 + 有序 backends + 单点失败独立降级。

### 模式 3: 多 Agent 对抗 / 多角色并行

从多个角度分析同一标的，产生冲突+共识。

| 项目 | 机制 |
|------|------|
| UZI-Skill | 66 评委按流派分类 + School Lock |
| ai-berkshire | 4 大师角色并行团队 + Team Lead 汇总 |
| Vibe-Trading | LangGraph Swarm 团队 |
| JCP | Moderator 意图识别、专家选择、串行会议、二轮复核 |
| TradingAgents Family / PanWatch | 分析师、多空、风控辩论，并产品化为盯盘 Agent |
| DeepFund | 多 Analyst + Portfolio Manager 时间顺序回放 |

**原则**: 角色有明确分析框架（不仅仅是「分析一下」），冲突输出比共识更有价值。

### 模式 4: 质量门控 + 自检

| 项目 | 机制 |
|------|------|
| UZI-Skill | agent_analysis.json 闭环 + HARD-GATE |
| ai-berkshire | financial_rigor + report_audit 双工具 |
| daily_stock_analysis | 验证矩阵 + 稳定性护栏 |
| daily_stock_data | ruff + py_compile + pytest + shell syntax + 私有路径泄漏检查 |
| Agent-Reach | Doctor 诊断系统 |
| tickflow-stock-panel | CapabilitySet 能力探测 + AI 策略 AST 白名单校验 |
| QuantDinger | Agent scope/audit/idempotency + 指标/策略 safe_exec + paper-only live gate |
| joinquant-skill | JQ001-JQ005 AST lint、未来函数和 API 幻觉拦截 |
| quant-buddy-skill | session/task_id/data_id/version/TopN 排序审计 |
| PanWatch | 月预算、冷却时间、same-day cache、enable gate |
| Privora Examples | scope 矩阵、response shape 验证、DEK 错误识别 |
| hhxg-market | schema_version、缓存命中、最近交易日日期提示 |

**原则**: LLM 输出的内容必须经过可重复的验证流程，不做「看起来对」的假设。

### 模式 5: MCP / CLI / Agent Gateway / Skill Gateway 服务化

Vibe-Trading 和 Agent-Reach 都在做 MCP 暴露；后续项目又补上了 CLI、Agent Gateway、Skill Gateway 和只读 OpenAPI 等更轻量的 Agent 接口形态。

| 接口形态 | 项目 | 价值 |
|---|---|---|
| MCP | Vibe-Trading / Agent-Reach / wudao-mcp / joinquant-skill / QuantDinger | 标准工具发现和调用 |
| JSON CLI | snowball-cli / quant-buddy-skill | Agent 可脚本化调用，易记录命令 provenance |
| Scoped Agent Gateway | QuantDinger / Privora Examples | token scope、idempotency、audit、paper-only 等高风险边界 |
| Skill Gateway | Privora Examples | `skillId + params` 统一入口，scope 可绑定能力 |
| OpenClaw/OpenCode Skill | Awesome Finance Skills / magpie / hhxg-market | 安装即用，触发词和回答范式写进 `SKILL.md` |
| 只读 OpenAPI | hhxg-market / PanWatch | 可自动生成工具，适合非 consequential 数据读取 |

### 模式 6: 数据契约先行

`daily_stock_data` 把 CSV/PostgreSQL 表字段、主键、时间语义和规模边界写进 `docs/SCHEMAS.md`；UZI-Skill 用 `data-contracts.md` 约束 5 个 Task 之间的 JSON 产物；tickflow-stock-panel 则把 `DataStore` 目录、DuckDB 视图和 `ENRICHED_STORAGE_COLS` 固化为本地数据湖契约。后续项目把这个模式延伸到工具调用层：Privora 明确 `success/data/totalElements` response shape，hhxg-market 明确 `schema_version`，snowball-cli 明确 JSON-only CLI 输出，joinquant-skill 明确 JoinQuant API 子集和 lint 规则，QuantDinger 明确 Agent token scope、job、audit、paper order 的运行态契约。一个偏数据表，一个偏 Agent 任务产物，一个偏可交互应用的数据底座，一个偏工具调用 envelope，本质都是把“下游可以依赖什么”显式化。

**原则**: 采集、分析、渲染、交易之间不要靠隐式 DataFrame 列名或 prompt 约定传递关键结构；契约文档要成为一等接口。

### 模式 7: 本地数据湖 + 实时工作台

tickflow-stock-panel 补上了此前几个项目之间缺少的一层：它不是单独的数据采集脚本，也不是纯研究 Agent，而是把本地数据湖、策略执行、实时行情和 Web 工作台放在同一个自托管应用里。

| 项目 | 方案 |
|------|------|
| daily_stock_data | CSV/PostgreSQL 双后端，强调轻量落盘和迁移对账 |
| tickflow-stock-panel | Parquet 分区 + DuckDB 只读视图 + Polars 热缓存 + SSE 工作台 |
| Vibe-Trading | API/SPA/MCP 暴露交易与回测运行态 |
| QuantDinger | PostgreSQL 运行态 + Agent jobs/audit + 策略/订单/回测/纸面订单闭环 |

**原则**: 数据真相落在可迁移的文件或表里，热路径用内存/向量化计算，实时 UI 只消费明确的事件流，不直接绑死采集实现。

### 模式 8: 盯盘系统从“分析”走向“触发-冷却-记录”

第五批项目共同说明：盯盘不是把分析报告定时跑一遍，而是一个有状态的触发系统。

| 项目 | 机制 |
|------|------|
| PanWatch | PriceAlertEngine 支持 AND/OR/composite 条件，auto_trigger 有预算、冷却、enable gate |
| magpie | SQLite watchlist/alert_rules/alert_history，gte/lte/breakout/breakdown + cooldown |
| a-share-watch-butler | 盘前/盘中/盘后/周末链路，三层输出和权重再校准 |
| tickflow-stock-panel | MonitorRuleEngine 复用 StrategyDef 入场/离场信号 |

**原则**: 任何提醒都必须有触发条件、冷却窗口、历史记录和测试触发入口；否则就是会重复打扰用户的脚本。

### 模式 9: 金融能力拆成可安装 skill，而不是塞进一个 Agent

Awesome Finance Skills、joinquant-skill、quant-buddy-skill、hhxg-market、magpie、snowball-cli 都把“怎么调用、什么时候调用、回答边界是什么”写进 `SKILL.md`。

| 项目 | Skill 边界 |
|------|-----------|
| Awesome Finance Skills | stock/search/sentiment/predictor/reporter/visualizer 分能力包 |
| joinquant-skill | 聚宽 API、模板、AST lint、因子实验、MCP 工具 |
| quant-buddy-skill | fast_query、公式批量执行、session/version/TopN 规则 |
| snowball-cli | 先用免登录命令，失败再提示用户自行登录 |
| hhxg-market | 按用户问题选择 snapshot/calendar/margin/news 脚本，并强制日期提示 |

**原则**: Agent 的“能力”应该有安装边界、触发边界、权限边界和输出边界；prompt 只是其中一部分。

### 模式 10: 静态快照适合 Agent，实时计算适合服务端

hhxg-market 把 A 股日报、两融、日历、快讯预生成成静态 JSON；Agent 只读、格式化、说明日期。这个模式和 tickflow-stock-panel 的 Parquet/DuckDB 数据湖类似，都是把复杂计算从 Agent 即兴执行中移走。

**原则**: 高频变化、口径敏感、计算成本高的数据，应先形成可版本化快照；Agent 负责选择和解释，而不是每次临场拼接数据源。

### 模式 11: 认证与敏感数据必须成为一等接口

第六批项目把认证边界讲得更清楚：snowball-cli 明确不要代用户登录，Privora 用 Bearer Token scope 控制 skill gateway，持仓字段通过 per-tenant DEK 解密，quant-buddy 用 session/task_id 防串任务。QuantDinger 进一步把 Agent Gateway 接到交易系统，要求 R/W/B/N/C/T scope、market/instrument allowlist、idempotency、审计日志和 paper-only 默认值。

**原则**: Agent 可以协助调用，但不能模糊认证、scope、token、敏感字段、跨会话状态这些边界。凡是会影响隐私或账户状态的调用，都要有可审计 envelope。

---

## 二、对当前项目的行动建议

### HermesAlpha

| 建议 | 来源 | 优先级 |
|------|------|--------|
| 分析流程改为 Pipeline（collect→score→synthesize→render） | UZI-Skill | P1 |
| 建立本地数据底座：CSV 默认、PostgreSQL 长期、both 迁移对账 | daily_stock_data | P1 |
| 数据源层引入 fallback 链（akshare→efinance→yfinance） | daily_stock_analysis | P1 |
| 建立 Parquet 数据湖 + Polars 热缓存，给策略/监控/回测共用 | tickflow-stock-panel | P1 |
| 策略定义统一成一份契约，同时服务选股、监控和回测 | tickflow-stock-panel | P1 |
| 多 Agent 对抗分析（bull vs bear 辩论）集成到 report_daily | UZI-Skill | P2 |
| MCP Server 暴露（mcp_server.py 参考 Vibe-Trading） | Vibe-Trading | P2 |
| 引入 Doctor 命令检查所有模块健康 | Agent-Reach | P2 |
| 密码提示/保护误操作：写入 prompt seed 策略时加校验 | ai-berkshire | P1 |
| /doctor 命令统一检查：LLM provider、数据源、通知渠道 | Agent-Reach | P2 |
| 报告结构借鉴 UZI-Skill 的 SVG 可视化组件 | UZI-Skill | P3 |
| 策略定义改为 YAML 声明式 | daily_stock_analysis | P3 |
| 回测集成参考 Shadow Account 模式 | Vibe-Trading | P3 |
| 引入 Moderator 会议室：意图识别→专家选择→串行讨论→总结 | JCP | P2 |
| 建立持仓上下文、提醒规则和建议池，把 TradingAgents 产品化 | PanWatch | P1 |
| 将金融能力拆成 market/search/sentiment/forecast/report skills | Awesome Finance Skills | P1 |
| 外部数据源先封 JSON CLI，公开接口优先，登录按需 | snowball-cli | P2 |
| 盘后日报/两融/日历先产静态 JSON 快照供 Agent 读取 | hhxg-market | P1 |
| 对外 Agent API 使用 `skillId + params` gateway 和 scope 矩阵 | Privora Examples | P1 |

### ashare-audit

| 建议 | 来源 | 优先级 |
|------|------|--------|
| 数据质量自检 + 自动降级机制（类似 Playwright 兜底） | UZI-Skill | P1 |
| 审计输入/中间表引入 CSV 原子写、append-upsert 和数据契约 | daily_stock_data | P1 |
| 把审计中间结果落成 Parquet 窄表，并用 DuckDB 做冷查询 | tickflow-stock-panel | P1 |
| 把监控/审计规则抽成 JSON 规则目录，保留触发记录 | tickflow-stock-panel | P1 |
| financial_rigor.py 的市值/估值验证直接复用 | ai-berkshire | P1 |
| akshare_provider.py 拆分参考 Channel 模式（base+each file） | Agent-Reach | P1 |
| AGENTS.md 加入质量护栏+验证矩阵 | daily_stock_analysis | P1 |
| LLM provider 验证引入 Doctor 诊断 | Agent-Reach | P2 |
| 多源交叉验证工具（3 个数据源比对） | ai-berkshire | P2 |
| 审计报告结构参考 report_audit 抽检模式 | ai-berkshire | P2 |
| 对 tool/skill 调用建立 session、version、response-shape 审计 | quant-buddy-skill / Privora Examples | P1 |
| 对 Agent Gateway 建立 scope、idempotency、audit、paper-only 高风险闸门 | QuantDinger | P1 |
| 对聚宽策略生成加入 AST lint、未来函数、交易成本和 API 幻觉检查 | joinquant-skill | P1 |
| 对外部 CLI 数据源审计认证边界、原始 JSON 和社交观点来源 | snowball-cli | P1 |
| 对静态快照审计 date/schema/cache/最近交易日提示 | hhxg-market | P1 |
| 对报告中的搜索引用、预测调整和模型权重来源做 skill 边界审计 | Awesome Finance Skills | P1 |

### 所有项目通用

| 建议 | 来源 |
|------|------|
| AGENTS.md / CLAUDE.md 坚持一个真源 | ai-berkshire / daily_stock_analysis |
| 单点失败不级联（数据源、通知、LLM 各负责各的错误） | 所有项目 |
| 先 fetch 最新代码，再动手修改（CI gate 前置） | daily_stock_analysis |
| 模块间通过 JSON/文件 IPC，不共享内存状态 | UZI-Skill |
| 添加 /doctor 通用诊断入口 | Agent-Reach |
| MCP 作为标准服务接口 | Vibe-Trading / Agent-Reach |
| 报告命名遵循统一规范（类别+公司+日期） | ai-berkshire |
| 数据表/JSON 产物先写契约，再让 Agent 和下游实现读取 | daily_stock_data / UZI-Skill |
| CI 检查私有路径、密钥习惯和本地 dump 痕迹，防止个人项目开源泄漏 | daily_stock_data |
| 用 CapabilitySet/feature gate 表达真实可用能力，避免业务代码散落套餐判断 | tickflow-stock-panel / Agent-Reach |
| 实时事件统一走一个 SSE/事件总线，前端按事件类型分发 | tickflow-stock-panel / Vibe-Trading |
| 高风险 Agent API 默认 paper/sandbox，实动作需 scope、环境开关和显式确认 | QuantDinger |
| 对外部工具统一记录命令或 `skillId + params`，不要只记录最终文本 | snowball-cli / Privora Examples / quant-buddy-skill |
| 盯盘提醒必须有触发条件、冷却、历史和 synthetic test-fire | PanWatch / magpie |
| 静态日报快照要强制标注数据日期和是否来自缓存 | hhxg-market |
| 金融 skill 要拆清 deterministic tool、Agent judgment、SQLite memory、citation trail | Awesome Finance Skills |
