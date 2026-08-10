# UI/UX 设计借鉴总表 — 金融研究与量化工作台

这份文档把各项目里的 UI、交互和用户体验设计从“按项目介绍”改成“按用户任务组织”。适合后续设计 HermesAlpha、ashare-audit 或其它金融研究/量化工作台时直接查表。

核心判断：这些项目里最有价值的 UI 不是营销页，而是高密度、可反复使用的操作台。用户要快速知道数据是否可信、任务跑到哪里、哪个信号值得看、为什么 AI 这么判断，以及下一步能做什么。

---

## 一、项目 UI 形态总览

| 项目 | UI 形态 | 最值得借鉴 | 适合迁移到 |
|---|---|---|---|
| UZI-Skill | 单文件 HTML 深度报告 | SVG 图表原语、66 评委 Panel、数据质量 Banner、多空辩论 | 静态报告、审计报告、可分享研究结论 |
| Vibe-Trading | React SPA + Agent 运行态 | SSE、Thinking Timeline、Conversation Timeline、MessageBubble 重试提示 | Agent 对话、长任务透明化、回测运行台 |
| daily_stock_analysis | Web + Desktop + Bot 多端应用 | Shell/Layout、组件库、RunFlow、Settings、报告 Drawer | 完整业务后台、策略筛选、系统配置页 |
| tickflow-stock-panel | React 实时量化工作台 | 看板/策略/回测/监控同台、单 SSE 事件总线、能力降级 | 自托管量化工作台、监控告警、盘后复盘 |
| OpenAshare | Next.js + FastAPI 本地研究台 | `/work` 研究入口、股票/热点/新闻/持仓/Agent 连续跳转、SSE 分析进度 | 轻量研究台、个股研究、Agent 会话记忆 |
| QuantDinger | Web/mobile AI Trading OS | Agent Gateway token scope、paper-only/live gate、job stream、策略沙箱和交易运行态 | Agent 交易工作台、策略实验、工具权限面板 |
| trade-skills | 本地 Fastify + React 图表应用 | 图表 JSON 落档、个股 Cockpit、盘中行情 SSE、可回放图表 | 交易日志、图表驾驶舱、研究资产归档 |
| DeepEar | 报告/HTML 输出为主 | 信号生命周期、checkpoint、update-run 逻辑演化 | 事件驱动研究报告、信号追踪页 |
| x2t | 数据/后台为主，可派生看板 | Leaderboard、Equity Curve、Calibration Panel、Flip Radar | 信源战绩榜、观点转向告警、校准面板 |
| daily_stock_data | 无主要 UI | 数据契约和运行日志可视化潜力 | 数据健康页、采集状态页 |
| a-stock-data | 无主要 UI | 端点分层和踩坑记录可转成数据源控制台 | 数据源能力矩阵、Provider Policy 页 |
| JCP | Wails 桌面研究台 | Moderator 会议室、专家队列、股票记忆 | 个股研究桌面版、多 Agent 会议室 |
| PanWatch | React/PWA 盯盘台 | 自选/提醒/建议池/模拟盘、预算和冷却状态 | 自托管盯盘、持仓监控 |
| magpie | CLI/HTTP daemon | watchlist、alert rule、trigger history、digest 预览 | 最小监控控制面 |
| hhxg-market | Markdown/JSON/OpenAPI | 数据日期、schema/cache、最近交易日提示 | 快照数据页、只读数据工具 |
| snowball-cli | JSON CLI | public/auth 命令分层、token 状态 | Provider 设置页、外部数据源状态 |
| Privora Examples | Python quickstart | token scope、response shape、DEK 状态 | Agent API 设置/诊断页 |

---

## 二、信息架构：不要做孤岛页面

| 用户任务 | 推荐界面结构 | 来源项目 | 设计要点 |
|---|---|---|---|
| 从股票进入完整研究 | 搜索 → 个股页 → 新闻/热点/持仓/策略/Agent 问答互跳 | OpenAshare | `stocks`, `news`, `hotspots`, `portfolio`, `agent` 不应孤立 |
| 盘中盯盘和回测验证 | 看板 → 策略 → 回测 → 监控 → 复盘 | tickflow-stock-panel | 同一套导航承载数据、策略、监控、回测和 AI 报告 |
| 深度阅读研究结论 | 摘要 → 证据卡 → 多视角评分 → 风险/反方 → 附录数据 | UZI-Skill | 报告不是纯 Markdown，要有视觉层级和证据定位 |
| 个人交易复盘 | 今日看板 → 个股 Cockpit → 图表快照 → Markdown 日志 | trade-skills | 每次研究必须落档，图表可回放 |
| Agent 长任务操作 | 会话 → 工具步骤 → 运行日志 → 产物/报告 | Vibe-Trading | 对话流旁边必须有任务进度和工具调用可见性 |
| Agent 提交回测/实验 | submit → job_id → stream progress → result → audit | QuantDinger | 长任务要能断线恢复、看幂等重放和最终产物 |
| 多 Agent 个股讨论 | 问题 → Moderator 选专家 → 专家发言队列 → 总结 | JCP | 让用户看到谁在分析、为什么参与、引用了什么记忆 |
| 盯盘提醒闭环 | 自选 → 规则 → 触发历史 → 冷却状态 → test-fire | PanWatch、magpie | 监控 UI 要显示状态和历史，而不是只显示“已开启” |
| 静态快照阅读 | 日期 Banner → 分板块 Markdown → 原始 JSON | hhxg-market | 用户必须先知道数据是哪天、是否缓存、是否最近交易日 |

### 设计原则

1. 金融研究 UI 要围绕“研究路径”而不是“功能列表”。
2. 个股、热点、新闻、持仓、策略、Agent 之间要能互跳。
3. 看板首页不要放宣传文案，直接显示今日状态、待处理信号和最近产物。
4. 报告页要能回到数据源、任务日志和原始证据。

---

## 三、首页/工作台首屏

| 模块 | 建议内容 | 可借鉴来源 |
|---|---|---|
| 市场状态条 | 交易中/休市、最后更新时间、数据源健康、能力状态 | UZI-Skill 市场 pulse、tickflow CapabilitySet |
| 今日待看 | 监控告警、策略命中、观点 flip、信号变强/变弱 | tickflow、x2t、DeepEar |
| 快速入口 | 输入股票、搜索热点、打开持仓、发起 Agent 分析 | OpenAshare |
| 实时区 | 行情 SSE、任务进度、正在运行的分析 | tickflow、Vibe-Trading、trade-skills |
| 最近产物 | 最近报告、图表快照、交易日志、回测结果 | trade-skills、UZI-Skill、Vibe-Trading |
| 触发状态 | 今日触发、冷却中、预算剩余、test-fire 入口 | PanWatch、magpie |
| 快照状态 | 数据日期、schema 版本、缓存状态、最近交易日 | hhxg-market |

首屏应该回答四个问题：现在市场状态是什么？有哪些新信号？哪些任务还在跑？我下一步可以点哪里？

---

## 四、报告阅读体验

| 能力 | 推荐做法 | 来源项目 | 可复用价值 |
|---|---|---|---|
| 数据质量提示 | 顶部 Banner + 缺失维度 chip + 严重性颜色 | UZI-Skill | 用户先知道报告可信度，而不是读完才发现数据缺口 |
| 多视角结论 | 评委/角色矩阵 + Top Bull/Bear + 点击滚动到理由 | UZI-Skill | 把多 Agent/多规则结果变成可浏览结构 |
| 冲突呈现 | Great Divide 多空辩论 | UZI-Skill | 冲突比单一结论更能帮助决策 |
| 图表原语 | sparkline、gauge、radar、donut、candlestick、PE band | UZI-Skill | 静态报告也能有高信息密度图形 |
| 报告抽屉 | 概览、Markdown、诊断、新闻、策略、详情分区 | daily_stock_analysis | 避免长报告一页到底 |
| 证据回链 | 每个关键判断能回到 source、run、raw data | DeepEar、trade-skills | 研究结论可追溯 |
| 引用稳定 key | URL/title/source 生成 citation key，参考文献可追踪 | Awesome Finance Skills | Agent 报告引用不应只靠自然语言描述 |
| 专家发言回链 | 每个专家观点可回到任务、前序发言和股票记忆 | JCP | 多 Agent 报告要能解释“为什么这位专家这么说” |

### 报告页建议骨架

```text
顶部: 标的 / 时间 / 数据质量 / 运行状态
摘要: 一句话结论 + 置信度 + 主要风险
证据: 价格 / 财务 / 新闻 / 资金 / 行业卡片
观点: 多角色评分 / bull-bear 冲突 / 策略匹配
行动: 监控规则 / 加入观察 / 启动回测 / 生成复盘
附录: 原始数据 / 任务日志 / prompt / 模型信息
```

---

## 五、实时流与长任务进度

| 场景 | 推荐交互 | 来源项目 |
|---|---|---|
| 行情更新 | 单 SSE 通道广播 quote、alert、review progress、depth correction | tickflow-stock-panel |
| Agent 推理 | Thinking Timeline 展示工具调用、状态、耗时、失败步骤 | Vibe-Trading |
| 单股分析 | `/analysis/stream` 实时显示阶段和 token | OpenAshare |
| 图表刷新 | 图表级 SSE，60 秒重算推送 | trade-skills |
| 分析流程 | RunFlow 图 + 节点详情 + 事件日志 | daily_stock_analysis |
| 告警触发 | alert_triggered + cooldown_remaining + rule_id | PanWatch、magpie |
| 批量公式执行 | SSE 批量流 + resume + TopN 校验状态 | quant-buddy-skill |
| Agent 回测/实验 job | queued/running/progress/result + Last-Event-ID 恢复 | QuantDinger |

### 事件设计建议

```text
event.type      quote_updated | alert_triggered | task_progress | task_done | task_error
event.id        用于去重和断线恢复
event.scope     symbol | portfolio | strategy | run_id
event.payload   只放当前事件需要的数据
event.time      server timestamp
```

原则：前端不应该到处散落轮询。长任务和实时行情都走统一事件模型，组件按事件类型和 scope 订阅。

---

## 六、图表与驾驶舱

| 图表/面板 | 用途 | 来源项目 | 借鉴点 |
|---|---|---|---|
| ScoreGauge | 情绪/评分仪表盘 | daily_stock_analysis | 适合首页、策略命中、信号质量 |
| K 线 + 技术指标 | 个股行情和入场结构 | tickflow、trade-skills | 技术图和策略信号同屏 |
| Flow / Cohort / SEPA / Intraday | 资金流、同组对比、交易形态、盘中结构 | trade-skills | 图表类型要对应真实交易问题 |
| Equity Curve | 回测或信源战绩曲线 | Vibe-Trading、x2t | 不只展示收益，也展示回撤和样本数 |
| Calibration Panel | AI confidence 是否校准 | x2t | 金融 AI 不能只给置信度，必须回看准不准 |
| Signal Evolution | 旧信号变强/变弱/证伪 | DeepEar | 报告不是一次性产物，要能更新对比 |

### 图表资产化原则

trade-skills 的关键经验是“图表数据和渲染分离”：`journal/charts/data/*.json` 带 schema version，历史判断不会被后来的实时行情污染。适合迁移到所有研究系统：图表不是临时 UI 状态，而是可回放的研究资产。

---

## 七、数据质量、能力降级与可信度

| 问题 | 推荐 UI | 来源项目 |
|---|---|---|
| 数据缺失 | 橙色/红色 Banner + 缺失维度 chip | UZI-Skill |
| 功能不可用 | 能力不足时灰显/隐藏，并显示缺哪个 capability | tickflow-stock-panel |
| LLM 不可用 | 规则分析回退，并清楚标注“非 AI 深度分析” | OpenAshare |
| 数据源失败 | 单源失败不阻断，页面显示降级来源和更新时间 | daily_stock_analysis |
| 信源可信度 | Leaderboard + Wilson 区间 + Brier score | x2t |
| 快照过期 | 顶部显示“最近交易日数据”，并标明更新规则 | hhxg-market |
| 认证缺失 | 区分 public 可用、auth 不可用、token 过期、scope 不足 | snowball-cli、Privora Examples |
| 交易权限不足 | 显示缺 scope、paper_only、live kill switch、confirm 参数哪一项未满足 | QuantDinger |
| 冷却/预算限制 | 提醒按钮显示 cooldown 或 budget exhausted，而不是静默不触发 | PanWatch、magpie |

### 必须避免

1. 不要只显示“分析完成”，还要显示用了哪些数据源、哪些失败、哪些降级。
2. 不要把 AI 置信度当真可信度，至少要有历史校准或数据质量说明。
3. 不要用绿色/红色只表达涨跌，同时还表达成功/失败，金融 UI 里语义会冲突。

---

## 八、空状态、错误状态、加载状态

| 状态 | 推荐设计 | 来源项目 |
|---|---|---|
| 空搜索 | 给出示例股票/主题/持仓导入入口 | OpenAshare |
| 空报告 | 显示缺少哪个前置数据或能力，而不是空白卡片 | tickflow、UZI-Skill |
| 任务运行中 | 步骤级进度 + 最近日志 + 可取消/重试 | Vibe-Trading、daily_stock_analysis |
| API 错误 | ApiErrorAlert + 自动推断 retry hint | daily_stock_analysis、Vibe-Trading |
| 部分失败 | 产出可用部分，同时列出失败维度和重跑入口 | UZI-Skill |

错误文案应该包含三件事：发生了什么、影响哪些结果、用户现在能做什么。

---

## 九、设置页、权限与演示模式

| 能力 | 推荐做法 | 来源项目 |
|---|---|---|
| 模型配置 | Provider、API Key、模型、测试连接集中管理 | OpenAshare、Vibe-Trading |
| 数据源配置 | 每个 provider 显示健康、限流、可用字段 | daily_stock_analysis、a-stock-data |
| Demo 保护 | Cookie/访问码保护 AI、持仓、策略等敏感功能 | OpenAshare |
| 自托管密码 | 简单访问密码适合个人部署 | tickflow-stock-panel |
| 通知配置 | 按报告类型/告警类型路由到不同渠道 | daily_stock_analysis |
| 成本可见 | AI 调用成本落库，页面可查 | trade-skills |
| Token scope | 展示当前 token 可调用哪些 skill，缺哪个 scope | Privora Examples |
| Agent trading scope | 展示 R/W/B/N/C/T、market/instrument allowlist、paper_only、rate limit、last_used | QuantDinger |
| Cookie 状态 | 显示雪球 public/auth 命令差异、token 保存时间和验证结果 | snowball-cli |
| 预算/冷却配置 | 自动分析预算、触发间隔、same-day cache 状态 | PanWatch |

设置页不应只是表单堆叠。更好的结构是：连接状态、能力检测、使用成本、敏感功能保护、测试按钮、最近错误。

---

## 十、AI 交互边界

| 场景 | UI 应该怎样限制 AI | 来源项目 |
|---|---|---|
| 策略生成 | AI 生成候选，后端 AST 白名单校验后才能保存 | tickflow-stock-panel |
| 研究问答 | 保存 last_stock、watchlist、pinned memory、active goal | OpenAshare |
| 高频盯盘 | 便宜模型做评论/哨兵，强模型做低频深度判断 | trade-skills |
| 观点标注 | AI 输出必须过 schema 校验，进入结算系统 | x2t |
| 信号筛选 | 先判断 `has_valid_signals=false`，无效就停止 | DeepEar |
| Agent 会议室 | Moderator 先选专家和任务，UI 显示专家选择依据 | JCP |
| 自动盯盘 | AI 建议进入 suggestion pool，启用/交易需用户确认 | PanWatch |
| 工具调用 | UI 展示 command 或 `skillId + params`，不要只展示自然语言总结 | snowball-cli、Privora Examples、quant-buddy-skill |
| 交易 Agent | UI 明确 paper order / live order，并把 scope、kill switch、确认字段列为闸门 | QuantDinger |

原则：AI 负责生成候选解释、结构化草稿和研究辅助；保存、执行、交易、告警、策略启用必须走确定性校验路径。

---

## 十一、按当前项目的落地建议

### HermesAlpha

| 优先级 | 建议 | 来源 |
|---|---|---|
| P1 | 做研究工作台首屏：今日市场、待看信号、最近报告、运行中任务 | OpenAshare、tickflow |
| P1 | 报告页加数据质量 Banner、证据卡、bull/bear 冲突区 | UZI-Skill |
| P1 | 长分析走 SSE + Thinking Timeline，不要让 HTTP 请求静默等待 | Vibe-Trading、OpenAshare |
| P2 | 个股 Cockpit：K 线、资金、新闻、策略、笔记同屏 | trade-skills |
| P2 | AI 成本和模型调用记录做设置/审计面板 | trade-skills |
| P2 | 信源/策略历史表现做 Leaderboard 和校准面板 | x2t |
| P1 | 盯盘页显示规则、触发历史、冷却、预算、test-fire | PanWatch、magpie |
| P2 | 个股研究加入 Moderator 会议室和专家发言队列 | JCP |
| P1 | 快照数据页强制显示日期、schema、cache、最近交易日 | hhxg-market |
| P1 | Provider 设置页区分 public/auth/token/scope/DEK 状态 | snowball-cli、Privora Examples |
| P1 | Agent Gateway 设置页显示 scope、allowlist、paper_only、rate limit、audit trail | QuantDinger |

### ashare-audit

| 优先级 | 建议 | 来源 |
|---|---|---|
| P1 | 审计报告顶部必须有数据质量 Banner 和缺口 chip | UZI-Skill |
| P1 | 审计运行页用 RunFlow：采集、校验、补数、LLM 审查、报告 | daily_stock_analysis |
| P1 | 数据源能力矩阵：每个字段来自哪个 provider、是否降级 | a-stock-data、tickflow |
| P2 | 问题发现后给“重跑该维度/查看原始数据/加入回归”操作 | UZI-Skill |
| P2 | 把历史审计图表和报告快照落 JSON/Markdown，可回放 | trade-skills |
| P1 | 审计工具调用页展示 command/skillId、参数、response shape、版本 | quant-buddy-skill、Privora Examples |
| P1 | 静态快照审计页显示 date/schema/cache 和源更新时间 | hhxg-market |

---

## 十二、最小可执行 UI 规格

如果只做第一版，不要试图覆盖所有页面。最小可执行规格如下：

| 页面 | 必须有 |
|---|---|
| 工作台首页 | 市场状态、数据源健康、待处理信号、运行中任务、最近产物 |
| 个股/对象页 | 概览、价格/指标、新闻/事件、策略/信号、AI 分析入口、历史记录 |
| 报告页 | 数据质量 Banner、摘要、证据卡、多空/多角色、附录与原始数据 |
| 运行页 | RunFlow/Timeline、日志、失败重试、产物链接 |
| 设置页 | Provider 测试、能力检测、模型配置、成本、敏感功能保护 |
| 盯盘页 | 规则列表、触发历史、冷却状态、预算、test-fire、digest 预览 |
| 工具调用页 | command/skillId、参数、版本、response shape、原始 JSON、错误诊断 |

第一版的 UI 成功标准：用户不用翻日志就知道系统在做什么、用了什么数据、哪里降级了、下一步能点什么。
