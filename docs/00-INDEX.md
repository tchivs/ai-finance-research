# AI + 金融开源项目研究库索引

本资料库汇总 71 个开源项目的架构、数据、Agent、策略、审计和 UI/UX 设计经验，主要服务于 HermesAlpha 与 ashare-audit 的方案设计和实施决策。

> 本资料库是研究与决策参考，不是生产实现规范。采用任何模式前，应回到对应项目的 `DEEP-ANALYSIS.md` 核对证据、限制和适用条件。

## 从这里开始

| 需求 | 推荐入口 | 结果 |
|------|----------|------|
| 5 分钟了解结论 | [跨项目综合提炼](10-SYNTHESIS.md) | 掌握共性模式与首要原则 |
| 设计量化工作台 | [量化工作台设计 PRD](22-量化工作台设计PRD.md) | 查看产品目标、技术栈、服务边界和分布式演进 |
| 制定实施计划 | [落地路线图](17-落地路线图.md) | 获得 HermesAlpha / ashare-audit 分阶段任务与验收标准 |
| 做技术选型 | [模式决策矩阵](18-模式决策矩阵.md) | 比较接口、存储、编排、实时性与审计方案 |
| 开始编码前 | [首批源码落地验证](19-首批源码落地验证.md) | 核对 commit、真实调用链、失败路径和不可照搬边界 |
| 跟踪开发任务 | [开发实施 TODO](20-开发实施TODO.md) | 按依赖顺序执行任务并记录阶段验收 |
| 判断项目价值 | [项目价值评估与方法论](21-项目价值评估与方法论.md) | 查看项目评级、Top 10 和最佳方法论 |
| 查专题 | [专题导航](#专题导航) | 按工程、策略、数据、Agent、UI 定向阅读 |
| 查单个项目 | [项目目录](#项目目录) | 先读快速概览，再按需进入深度分析 |
| 维护资料库 | [知识库使用与维护指南](01-知识库使用与维护指南.md) | 了解文档层级、术语、来源和更新规则 |

## 文档层级

```text
产品层：22-量化工作台设计PRD.md
   ↑ 产品目标、范围、用户流程、技术栈和验收标准
决策层：18-模式决策矩阵.md
   ↑ 取舍和默认方案
执行层：17-落地路线图.md
   ↑ 阶段、交付物和验收标准
综合层：10-SYNTHESIS.md、06~16 专题文档
   ↑ 跨项目归纳和主题证据
验证层：19-首批源码落地验证.md
   ↑ 固定 commit、核对调用链和失败边界
证据层：<project>/QUICK-START.md、<project>/DEEP-ANALYSIS.md
   ↑ 单项目事实、实现细节、风险和限制
```

发生冲突时，事实判断以固定 commit 的源码验证为准，其次是项目证据层；当前项目的执行顺序以路线图为准；架构分叉以决策矩阵为准。

## 按目标阅读

| 目标 | 阅读顺序 |
|------|----------|
| 规划 HermesAlpha | [路线图](17-落地路线图.md) → [决策矩阵](18-模式决策矩阵.md) → [Agent 专题](09-Agent-协作与设计哲学篇.md) → [UI/UX 总表](16-UI-UX设计借鉴总表.md) |
| 规划 ashare-audit | [路线图](17-落地路线图.md) → [工程治理](06-工程治理篇.md) → [数据底座](15-数据底座与采集底座篇.md) → [决策矩阵](18-模式决策矩阵.md) |
| 建数据底座 | [数据底座](15-数据底座与采集底座篇.md) → [数据采集与流水线](08-数据采集与流水线篇.md) → daily-stock-data / tickflow / hhxg-market 项目文档 |
| 建 Agent 工具层 | [Agent 专题](09-Agent-协作与设计哲学篇.md) → [工程治理](06-工程治理篇.md) → QuantDinger / Agent-Reach / wudao-mcp 项目文档 |
| 做策略与信号 | [策略与信号](07-策略与信号系统篇.md) → Qlib / AlphaAgent / QuantDinger / joinquant-skill 项目文档 |
| 做工作台 UI | [UI/UX 总表](16-UI-UX设计借鉴总表.md) → [UI/UX 交互设计](11-UI-UX交互设计.md) → tickflow / JCP / PanWatch 项目文档 |

## 核心文档

| 文档 | 职责 | 何时更新 |
|------|------|----------|
| [10-SYNTHESIS.md](10-SYNTHESIS.md) | 跨项目共性模式和通用行动建议 | 新证据改变通用判断时 |
| [17-落地路线图.md](17-落地路线图.md) | 当前项目阶段、任务、依赖和验收 | 执行优先级或范围变化时 |
| [18-模式决策矩阵.md](18-模式决策矩阵.md) | 技术分叉、适用条件和默认选择 | 新模式改变选型结论时 |
| [19-首批源码落地验证.md](19-首批源码落地验证.md) | 关键参考源码的基线、调用链和实现边界 | 参考仓库升级或新增源码验证批次时 |
| [20-开发实施TODO.md](20-开发实施TODO.md) | 可勾选任务、阶段门禁、交付物和完成定义 | 每周更新进度或实施范围变化时 |
| [21-项目价值评估与方法论.md](21-项目价值评估与方法论.md) | 项目价值评级、Top 10、最佳方法论和按目标选型 | 新增项目或价值排序变化时 |
| [22-量化工作台设计PRD.md](22-量化工作台设计PRD.md) | 多市场量化工作台的产品、技术、服务和分布式架构基线 | 产品范围、技术栈或验收标准变化时 |
| [01-知识库使用与维护指南.md](01-知识库使用与维护指南.md) | 文档约定、术语、来源和维护检查 | 资料库结构或规则变化时 |

## 专题导航

| 文档 | 主题 | 核心内容 |
|------|------|----------|
| [06-工程治理篇.md](06-工程治理篇.md) | 工程治理 | 自检门控、缓存、预检、scope、audit、CapabilitySet |
| [07-策略与信号系统篇.md](07-策略与信号系统篇.md) | 策略与信号 | Signal Engine、因子、StrategyDef、回测、建议池 |
| [08-数据采集与流水线篇.md](08-数据采集与流水线篇.md) | 数据流水线 | Fetcher Registry、fallback、并发、增量采集、Agent jobs |
| [09-Agent-协作与设计哲学篇.md](09-Agent-协作与设计哲学篇.md) | Agent 协作 | 多角色、Moderator、MCP、Skill、Agent Gateway |
| [11-UI-UX交互设计.md](11-UI-UX交互设计.md) | UI/UX 交互 | 报告、工作台、SSE、运行流和状态反馈 |
| [12-剩余深度素材.md](12-剩余深度素材.md) | 工程素材 | 报告引擎、数据契约、测试、CI/CD |
| [13-终极提炼.md](13-终极提炼.md) | 防再犯工程 | BUGS-LOG、特征隔离、方法日志、交易闸门 |
| [14-跨项目深层精华.md](14-跨项目深层精华.md) | 深层比较 | 技能生态、工作台、Trading OS、工具化闭环 |
| [15-数据底座与采集底座篇.md](15-数据底座与采集底座篇.md) | 数据底座 | CSV/PG、Parquet/DuckDB/Polars、快照与数据契约 |
| [16-UI-UX设计借鉴总表.md](16-UI-UX设计借鉴总表.md) | UI/UX 选型 | 按用户任务整理页面、状态和可信度设计 |

## 项目目录

每个项目目录包含两份文档：`QUICK-START.md` 用于快速判断价值，`DEEP-ANALYSIS.md` 用于核对架构、实现和风险。

### 研究与 Agent 系统

| 项目 | 重点 | 快速概览 | 深度分析 |
|------|------|----------|----------|
| UZI-Skill | Pipeline、评委对抗、质量门控、报告 | [阅读](../uzi-skill/QUICK-START.md) | [阅读](../uzi-skill/DEEP-ANALYSIS.md) |
| ai-berkshire | 价值投资方法、技能体系、质量筛选 | [阅读](../ai-berkshire/QUICK-START.md) | [阅读](../ai-berkshire/DEEP-ANALYSIS.md) |
| daily-stock-analysis | 多源联邦、LLM 分析、Web/Desktop/Bot | [阅读](../daily-stock-analysis/QUICK-START.md) | [阅读](../daily-stock-analysis/DEEP-ANALYSIS.md) |
| DeepEar | 信号追踪、ISQ、checkpoint、逻辑演化 | [阅读](../deepear/QUICK-START.md) | [阅读](../deepear/DEEP-ANALYSIS.md) |
| DeepFund | 多 Analyst、时间回放、组合决策 | [阅读](../deepfund/QUICK-START.md) | [阅读](../deepfund/DEEP-ANALYSIS.md) |
| TradingAgents Family | 多 Agent 辩论、风控、状态机 | [阅读](../tradingagents-family/QUICK-START.md) | [阅读](../tradingagents-family/DEEP-ANALYSIS.md) |
| ai-hedge-fund | 投资流派信号、组合约束、回测 | [阅读](../ai-hedge-fund/QUICK-START.md) | [阅读](../ai-hedge-fund/DEEP-ANALYSIS.md) |
| JCP | Moderator 会议室、股票记忆、桌面应用 | [阅读](../jcp/QUICK-START.md) | [阅读](../jcp/DEEP-ANALYSIS.md) |
| PanWatch | 盯盘、持仓上下文、预算、建议池 | [阅读](../panwatch/QUICK-START.md) | [阅读](../panwatch/DEEP-ANALYSIS.md) |
| OpenAshare | 本地研究台、SSE、热点、持仓闭环 | [阅读](../openashare/QUICK-START.md) | [阅读](../openashare/DEEP-ANALYSIS.md) |
| Vibe-Research | 本地投研看板、NDJSON、MCP | [阅读](../vibe-research/QUICK-START.md) | [阅读](../vibe-research/DEEP-ANALYSIS.md) |
| DojoAgents | Agent Runtime、Skills/Plugins、Gateway、Dashboard | [阅读](../dojoagents/QUICK-START.md) | [阅读](../dojoagents/DEEP-ANALYSIS.md) |
| PA_Agent | 两阶段 LLM 分析、数据门控、paper 审批与执行账本 | [阅读](../pa-agent/QUICK-START.md) | [阅读](../pa-agent/DEEP-ANALYSIS.md) |

### 量化、策略与研究自动化

| 项目 | 重点 | 快速概览 | 深度分析 |
|------|------|----------|----------|
| Vibe-Trading | 技能生态、MCP、回测引擎、Shadow Account | [阅读](../vibe-trading/QUICK-START.md) | [阅读](../vibe-trading/DEEP-ANALYSIS.md) |
| tickflow-stock-panel | 本地数据湖、StrategyDef、监控、回测 | [阅读](../tickflow-stock-panel/QUICK-START.md) | [阅读](../tickflow-stock-panel/DEEP-ANALYSIS.md) |
| QuantDinger | Agent Gateway、沙箱、paper-only、审计 | [阅读](../quantdinger/QUICK-START.md) | [阅读](../quantdinger/DEEP-ANALYSIS.md) |
| vn.py（VeighNa） | 事件引擎、Gateway、OMS、因子研究与组合回测 | [阅读](../vnpy/QUICK-START.md) | [阅读](../vnpy/DEEP-ANALYSIS.md) |
| PyPortfolioOpt | 组合优化、风险模型、Black-Litterman、HRP、离散分配 | [阅读](../pyportfolioopt/QUICK-START.md) | [阅读](../pyportfolioopt/DEEP-ANALYSIS.md) |
| Lean | 事件驱动研究/回测/执行、Insight 到 target 的分层框架 | [阅读](../lean/QUICK-START.md) | [阅读](../lean/DEEP-ANALYSIS.md) |
| Qlib | 实验记录、Signal、IC、回测、执行 | [阅读](../qlib/QUICK-START.md) | [阅读](../qlib/DEEP-ANALYSIS.md) |
| AlphaAgent | A 股因子 DSL、FactorZoo、IC 评估 | [阅读](../alphaagent/QUICK-START.md) | [阅读](../alphaagent/DEEP-ANALYSIS.md) |
| AlphaMaster | 强化学习公式搜索、StackVM、walk-forward、实时信号 | [阅读](../alphamaster/QUICK-START.md) | [阅读](../alphamaster/DEEP-ANALYSIS.md) |
| Alpha Evolution Lab | 策略 DSL、变异、复测、奖励 | [阅读](../alpha-evolution-lab/QUICK-START.md) | [阅读](../alpha-evolution-lab/DEEP-ANALYSIS.md) |
| Quant Autoresearch | 策略代码演化、安全回测、Playbook | [阅读](../quant-autoresearch/QUICK-START.md) | [阅读](../quant-autoresearch/DEEP-ANALYSIS.md) |
| QuantaAlpha | 平行方向、轨迹池、因子血缘 | [阅读](../quantaalpha/QUICK-START.md) | [阅读](../quantaalpha/DEEP-ANALYSIS.md) |
| RD-Agent | 假设、实验、编码、运行、反馈闭环 | [阅读](../rd-agent/QUICK-START.md) | [阅读](../rd-agent/DEEP-ANALYSIS.md) |
| joinquant-skill | 聚宽模板、AST lint、因子实验 | [阅读](../joinquant-skill/QUICK-START.md) | [阅读](../joinquant-skill/DEEP-ANALYSIS.md) |
| quant-buddy-skill | 公式执行、session/version、TopN 审计 | [阅读](../quant-buddy-skill/QUICK-START.md) | [阅读](../quant-buddy-skill/DEEP-ANALYSIS.md) |
| Kronos + FinCast | 时序基础模型、分位数预测、Qlib | [阅读](../financial-timeseries-foundation/QUICK-START.md) | [阅读](../financial-timeseries-foundation/DEEP-ANALYSIS.md) |

### 数据、接口与工具层

| 项目 | 重点 | 快速概览 | 深度分析 |
|------|------|----------|----------|
| daily-stock-data | CSV/PG 双后端、采集契约、CI | [阅读](../daily-stock-data/QUICK-START.md) | [阅读](../daily-stock-data/DEEP-ANALYSIS.md) |
| a-stock-data | A 股数据端点、数据源优先级与限流 | [阅读](../a-stock-data/QUICK-START.md) | [阅读](../a-stock-data/DEEP-ANALYSIS.md) |
| Agent-Reach | Channel 抽象、Probe、Doctor、MCP | [阅读](../agent-reach/QUICK-START.md) | [阅读](../agent-reach/DEEP-ANALYSIS.md) |
| wudao-mcp | 只读 MCP、工具目录、profile 裁剪 | [阅读](../wudao-mcp/QUICK-START.md) | [阅读](../wudao-mcp/DEEP-ANALYSIS.md) |
| Agentic China Data Tooling | MCP、MarketDB、source health | [阅读](../agentic-china-data-tooling/QUICK-START.md) | [阅读](../agentic-china-data-tooling/DEEP-ANALYSIS.md) |
| TDX Market Data Clients | 协议、连接池、离线数据、F10 | [阅读](../tdx-market-data-clients/QUICK-START.md) | [阅读](../tdx-market-data-clients/DEEP-ANALYSIS.md) |
| snowball-cli | 雪球 JSON CLI、公开/认证边界 | [阅读](../snowball-cli/QUICK-START.md) | [阅读](../snowball-cli/DEEP-ANALYSIS.md) |
| hhxg-market | 静态快照、交易日历、缓存、只读 API | [阅读](../hhxg-market/QUICK-START.md) | [阅读](../hhxg-market/DEEP-ANALYSIS.md) |
| Privora Python Examples | Bearer scope、Skill Gateway、敏感数据 | [阅读](../privora-python-examples/QUICK-START.md) | [阅读](../privora-python-examples/DEEP-ANALYSIS.md) |

### Polymarket 与预测市场链路

| 项目 | 重点 | 快速概览 | 深度分析 |
|------|------|----------|----------|
| polymarket-ts-sdk | 官方统一 TypeScript SDK、REST/WebSocket、workspace | [阅读](../polymarket-ts-sdk/QUICK-START.md) | [阅读](../polymarket-ts-sdk/DEEP-ANALYSIS.md) |
| polymarket-py-sdk | 官方统一 Python SDK、同步/异步和长操作 handle | [阅读](../polymarket-py-sdk/QUICK-START.md) | [阅读](../polymarket-py-sdk/DEEP-ANALYSIS.md) |
| polymarket-clob-client-v2 | TypeScript CLOB v2、L1/L2、订单签名 | [阅读](../polymarket-clob-client-v2/QUICK-START.md) | [阅读](../polymarket-clob-client-v2/DEEP-ANALYSIS.md) |
| polymarket-py-clob-client-v2 | Python CLOB v2、订单和费用 | [阅读](../polymarket-py-clob-client-v2/QUICK-START.md) | [阅读](../polymarket-py-clob-client-v2/DEEP-ANALYSIS.md) |
| polymarket-real-time-data-client | WebSocket topic/type/filter 事件流 | [阅读](../polymarket-real-time-data-client/QUICK-START.md) | [阅读](../polymarket-real-time-data-client/DEEP-ANALYSIS.md) |
| polymarket-cli | Rust CLI、JSON 输出、钱包和 CTF 操作 | [阅读](../polymarket-cli/QUICK-START.md) | [阅读](../polymarket-cli/DEEP-ANALYSIS.md) |
| polymarket-agent-skills | Agent 渐进式披露、交易/行情/CTF 参考 | [阅读](../polymarket-agent-skills/QUICK-START.md) | [阅读](../polymarket-agent-skills/DEEP-ANALYSIS.md) |
| polymarket-subgraph | activity、FPMM、OI、PnL 和链上 GraphQL | [阅读](../polymarket-subgraph/QUICK-START.md) | [阅读](../polymarket-subgraph/DEEP-ANALYSIS.md) |
| polymarket-resolution-subgraph | UMA/CTF resolution 生命周期索引 | [阅读](../polymarket-resolution-subgraph/QUICK-START.md) | [阅读](../polymarket-resolution-subgraph/DEEP-ANALYSIS.md) |
| polymarket-go-market-events | Go Polygon RPC 事件 watcher | [阅读](../polymarket-go-market-events/QUICK-START.md) | [阅读](../polymarket-go-market-events/DEEP-ANALYSIS.md) |
| polymarket-ctf-exchange-v2 | CTF Exchange V2、订单匹配和链上结算 | [阅读](../polymarket-ctf-exchange-v2/QUICK-START.md) | [阅读](../polymarket-ctf-exchange-v2/DEEP-ANALYSIS.md) |
| polymarket-uma-ctf-adapter | UMA Optimistic Oracle resolution adapter | [阅读](../polymarket-uma-ctf-adapter/QUICK-START.md) | [阅读](../polymarket-uma-ctf-adapter/DEEP-ANALYSIS.md) |
| polymarket-neg-risk-ctf-adapter | 多结果市场、position conversion、抵押物 | [阅读](../polymarket-neg-risk-ctf-adapter/QUICK-START.md) | [阅读](../polymarket-neg-risk-ctf-adapter/DEEP-ANALYSIS.md) |
| polymarket-poly-market-maker | Bands/AMM 做市 keeper、订单簿协调 | [阅读](../polymarket-poly-market-maker/QUICK-START.md) | [阅读](../polymarket-poly-market-maker/DEEP-ANALYSIS.md) |

### 量化运行时、数据平台与编排

| 项目 | 重点 | 快速概览 | 深度分析 |
|------|------|----------|----------|
| nautilus-trader | Rust/Python 事件驱动交易引擎、回测与 live parity | [阅读](../nautilus-trader/QUICK-START.md) | [阅读](../nautilus-trader/DEEP-ANALYSIS.md) |
| vectorbt | 矩阵化回测、IndicatorFactory、Portfolio/Records | [阅读](../vectorbt/QUICK-START.md) | [阅读](../vectorbt/DEEP-ANALYSIS.md) |
| hummingbot | 交易所连接器、Controller/Executor、做市与 bot runtime | [阅读](../hummingbot/QUICK-START.md) | [阅读](../hummingbot/DEEP-ANALYSIS.md) |
| ccxt | 多语言加密交易所/预测市场统一 API | [阅读](../ccxt/QUICK-START.md) | [阅读](../ccxt/DEEP-ANALYSIS.md) |
| openbb | Provider/Fetcher、金融数据路由、REST/MCP 复用 | [阅读](../openbb/QUICK-START.md) | [阅读](../openbb/DEEP-ANALYSIS.md) |
| akshare | A/H/美股等财经数据函数式采集接口 | [阅读](../akshare/QUICK-START.md) | [阅读](../akshare/DEEP-ANALYSIS.md) |
| dagster | 数据资产、lineage、materialization 和编排控制面 | [阅读](../dagster/QUICK-START.md) | [阅读](../dagster/DEEP-ANALYSIS.md) |
| temporal | durable workflow、事件历史、重试和任务队列 | [阅读](../temporal/QUICK-START.md) | [阅读](../temporal/DEEP-ANALYSIS.md) |

### 轻量技能、监控与内容系统

| 项目 | 重点 | 快速概览 | 深度分析 |
|------|------|----------|----------|
| trade-skills | Markdown 研究日志、图表、哨兵/参谋分层 | [阅读](../trade-skills/QUICK-START.md) | [阅读](../trade-skills/DEEP-ANALYSIS.md) |
| a-share-watch-butler | 盘前/盘中/盘后链路、三层输出 | [阅读](../a-share-watch-butler/QUICK-START.md) | [阅读](../a-share-watch-butler/DEEP-ANALYSIS.md) |
| magpie | SQLite 盯盘、提醒冷却、digest | [阅读](../magpie/QUICK-START.md) | [阅读](../magpie/DEEP-ANALYSIS.md) |
| Awesome Finance Skills | 金融技能拆包、研究记忆、RAG | [阅读](../awesome-finance-skills/QUICK-START.md) | [阅读](../awesome-finance-skills/DEEP-ANALYSIS.md) |
| x2t | 观点标注、战绩结算、统计校准 | [阅读](../x2t/QUICK-START.md) | [阅读](../x2t/DEEP-ANALYSIS.md) |

## 使用提醒

1. 先确定问题属于数据、工具、Agent、策略、UI 还是审计，再进入专题或项目文档。
2. 综合文档中的数字和能力描述可能随上游项目变化；实施前检查来源版本和限制。
3. 不复制完整架构，只吸收能解决当前问题的层级和契约。
4. 涉及交易、认证、持仓或敏感数据时，默认采用最小权限、只读或 paper 模式，并保留审计记录。
