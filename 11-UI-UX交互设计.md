# 补充五：UI/UX 交互设计 — 报告渲染、前端组件、用户体验

## 来源项目
- UZI-Skill (124KB HTML 报告模板、SVG 图表原语、66 评委 panel、数据质量 Banner)
- Vibe-Trading (React 19 + ECharts、SSE 实时流、Thinking Timeline、暗黑主题)
- daily_stock_analysis (完整 React 组件库、Auth+Layout+Dashboard、RunFlow 可视化)
- tickflow-stock-panel (React 工作台、行情 SSE、监控告警、回测/复盘进度)
- JCP / PanWatch / magpie (桌面会议室、盯盘工作台、轻量 daemon 控制面)
- hhxg-market / snowball-cli / Privora Examples (无 UI 或轻 UI 的工具边界，可转化为设置/状态/权限面板)
- QuantDinger (Agent Gateway token scope、paper-only/live gate、job stream、策略/回测/交易运行台)
- DojoAgents (FastAPI 金融工作台、OpenAI 兼容聊天、SSE、工具 trace 与跨渠道对话)

---

## 0. DojoAgents：将 Agent 运行状态暴露为工作台协议

DojoAgents Dashboard 以 FastAPI 承载金融域 router，在启动阶段预加载离线数据和领域 store。聊天接口同时接受 OpenAI `messages` 和旧 payload，流式输出使用 SSE，并能附加 phase、文本 delta、tool start/result、thinking、done 等事件。

### 借鉴点

- 先稳定 `ChatRequest` 和事件 schema，再让 CLI、工作台和渠道 Gateway 共享同一个 Agent 入口。
- 界面应显示工具调用、截断与 artifact，而不是把它们藏在服务端日志中。
- 保持 OpenAI 兼容基础事件，额外能力使用版本化扩展字段，降低前端和外部客户端迁移成本。
- 会话页面应能导出 transcript、结构化 messages、usage 和 tool trace，支持复盘而非仅浏览聊天记录。

### 边界

Dashboard 的开放 CORS 适合默认本地场景，不构成多用户 Web 服务的认证方案。对外部署前，必须补齐 origin policy、登录、授权、限流与脱敏。

---

## 一、UZI-Skill: Bloomberg 风格 HTML 报告系统

### 整体设计哲学

**Bento + Brutalism + Glassmorphism** 三层风格叠加，支持 Light/Dark 双主题。

```
    124KB 单文件 HTML（无外部依赖，除了 Google Fonts）
    内嵌全部 CSS + SVG 渲染
    无 JavaScript 零依赖——"打印友好、截图友好、微信分享友好"
```

### 1.1 CSS 变量主题系统

```css
:root {
  /* Light Theme — Bloomberg Light Terminal */
  --bg-void:     #f1f5f9;    /* page edge */
  --bg-card:     #ffffff;     /* pure white card */
  --neon-cyan:   #0891b2;
  --neon-gold:   #d97706;
  --bull-green:  #059669;
  --bear-red:    #dc2626;
  --text-main:   #1e293b;    /* slate-800 */
}

[data-theme="dark"] {
  /* Dark Theme — Bloomberg Dark Terminal */
  --bg-void:     #0a0e14;    /* obsidian */
  --bg-card:     #161b22;    /* gh-dark card */
  --neon-cyan:   #22d3ee;
  --neon-gold:   #facc15;
  --bull-green:  #34d399;
  --bear-red:    #f87171;
  --text-main:   #c9d1d9;
}
```

**颜色语义体系**：
| Token | 意义 | HEX (Light) | HEX (Dark) |
|-------|------|-------------|------------|
| neen-cyan | 品牌主色/数据 | #0891b2 | #22d3ee |
| neon-gold | 高亮/gauge | #d97706 | #facc15 |
| bull-green | 看多/正向 | #059669 | #34d399 |
| bear-red | 看空/负向 | #dc2626 | #f87171 |
| bull-tint | 看多浅底色 | #d1fae5 | rgba(52,211,153,0.18) |
| bear-tint | 看空浅底色 | #fee2e2 | rgba(248,113,113,0.18) |

### 1.2 19 个 SVG 图表原语

无 JS 依赖，纯 Python 生成 SVG 字符串嵌入 HTML。

| 函数 | 用途 | 调用点 |
|------|------|--------|
| `svg_sparkline()` | 微型走势图 | 股价/ROE 趋势 |
| `svg_h_bar_compare()` | 双值横向对比条 | 行业对比 |
| `svg_donut()` | 环形图 | 股东结构/营收构成 |
| `svg_gauge()` | 仪表盘 | DCF 评分/安全边际 |
| `svg_radar()` | 雷达图 | 多维度对比/竞争分析 |
| `svg_signal_lights()` | 信号灯组 | 8 维度信号汇总 |
| `svg_candlestick()` | 简易 K 线 | 周线/月线 |
| `svg_pe_band()` | PE 估值带 | 历史估值百分位 |
| `svg_bars()` | 柱状图 | 财务数据对比 |
| `svg_progress_row()` | 进度条行 | 覆盖率/完成度 |
| `svg_thermometer()` | 温度计 | 热度指标 |

### 1.3 22 维数据卡片系统

每张维度的数据卡片有特化可视化（`_viz_xxx` 函数）：

```python
# 从 assemble_report.py 抽离的视觉组件
def _viz_financials(raw) -> str:     # 财务：sparkline + 关键指标
def _viz_kline(raw) -> str:          # K线：svg_candlestick + MA
def _viz_valuation(raw) -> str:      # 估值：PE Band + 同行对比
def _viz_capital_flow(raw) -> str:   # 资金流：迷你柱状图
def _viz_industry(raw) -> str:       # 行业：产业链 SVG
def _viz_trap(raw) -> str:           # 杀猪盘：风险灯+emoji
def _viz_chain(raw) -> str:          # 供应链：流向图
def _viz_peers(raw) -> str:          # 同行：svg_peer_table
```

`DIM_VIZ_RENDERERS` 字典分发：`dim_key → viz_function`。

### 1.4 66 评委 Panel 可视化

**评委座位矩阵**：
```html
<div class="jury-board">
  <div class="jury-row-label">A · 价值</div>
  <div class="jury-seats">
    <div class="seat bullish" data-target="msg-1">
      <img src="avatars/buffett.svg" class="seat-avatar">
      <span class="seat-name">巴菲特</span>
      <span class="seat-score">86</span>
    </div>
    <!-- 每派 5-10 个座位 -->
  </div>
</div>
```

- 看多（绿边框+浅绿底）、看空（红）、中性（灰）
- 点击头像 → 滚动到对应详细评语（微信气泡式）
- 66 个独立 SVG 头像（`assets/avatars/*.svg`）
- Top 3 Bull / Top 3 Bear 高亮

**多空辩论**：
```
┌──────────────────────────────────┐
│  GREAT DIVIDE                    │
│  金句：茅台国际化仍处在早期...  │
│                                  │
│  R1 多头：护城河在加深          │
│  R1 空头：年轻人不喝白酒        │
│  R2 多头：提价空间大            │
│  R2 空头：经销商库存过高        │
│  R3 多头：分红率提升            │
│  R3 空头：增长动力切换不明      │
└──────────────────────────────────┘
```

**School Lock Banner**：锁定单一流派时顶部渲染锁定横幅。

### 1.5 数据质量 Banner 三级体系

```html
<!-- 橙色（数据缺口） -->
<div class="data-gap-banner">
  <span class="icon">⚠️</span>
  <div class="body">
    <div class="title">数据可靠性警告</div>
    <div class="subtitle"><strong>5 个维度</strong>数据来自低优先级源</div>
    <div class="list">
      <span class="chip">营收历史</span>
      <span class="chip">现金流</span>
    </div>
  </div>
</div>

<!-- 蓝色（信息性提示，如基金类型） -->
<div class="data-gap-banner fund-type">...</div>

<!-- 红色（低可信度） -->
<div class="data-gap-banner low-confidence">...</div>
```

对比度原则：v3.4.4 用户反馈橙底橙字看不清 → 改为深棕字+实色橙底，通过 WCAG AA。

### 1.6 其他 UX 细节

| 特性 | 实现 | 用户价值 |
|------|------|---------|
| Topbar "红绿灯" 点 | 3 个 dot (red/yellow/green) + pulse | 模拟 macOS 窗口，营造专业感 |
| 市场状态 Pulse | 交易中 = 绿色脉冲动画 | 一眼知道数据时效 |
| Jargon 悬浮定义 | `.jargon:hover::after` tooltip | 金融术语零门槛 |
| QR 分享卡片 | 报告底部二维码占位 | 微信/手机分享 |
| 数据缺口 Chip | 标签式列出缺失维度 | 一眼知道缺什么 |
| 基金类型 Banner | 蓝色调区分橙色警告 | 避免混淆信息类型 |

### 借鉴点
- **当前项目报告模块**可直接复用 SVG 原语层（Python 生成 SVG 字符串）
- 数据质量 Banner 三级体系 → HermesAlpha 的审计报告可引入
- 颜色语义体系（bull/bear 固定色值）→ 保持所有 UI 一致

---

## 二、Vibe-Trading: React 前端系统

### 2.1 技术栈
```
React 19 + TypeScript + Vite + Vitest
Tailwind CSS 3.4 (CSS 变量主题)
ECharts 6 (charting)
Zustand 5 (state)
i18next 26 (internationalization)
lucide-react (icons)
react-markdown + remark-gfm + rehype-highlight
sonner (toast)
```

### 2.2 暗黑主题实现

```ts
// tailwind.config.ts
darkMode: "class",  // 通过 CSS class 切换
theme: {
  extend: {
    colors: {
      border: "hsl(var(--border))",
      background: "hsl(var(--background))",
      // ... 所有颜色都是 CSS 变量
      success: "hsl(var(--success))",
      danger: "hsl(var(--danger))",
    },
    fontFamily: {
      sans: ["Inter", "system-ui", "sans-serif"],
      mono: ["JetBrains Mono", "ui-monospace", "monospace"],
    },
  },
}
```

### 2.3 SSE 实时流

核心 Hook：`useSSE` 支持：
- **自动重连** + 指数退避（1s → 30s）
- **LRU 去重**（最多 500 条 event ID）
- **Last-Event-ID 恢复**（断线续接）
- 已知事件类型注册（20+ 种）

```typescript
const knownTypes = [
  "text_delta", "reasoning_delta", "tool_call", "tool_result",
  "tool_heartbeat", "tool_progress", "llm_usage",
  "swarm.started", "swarm.event",
  "mandate.proposal", "mandate.committed",
  "heartbeat", "done",
];
```

### 2.4 Conversation Timeline

固定右侧的纵向导航点：
```
┌───────────────────────────┐
│  用户消息 1  ·········· ● │ ← active
│  Agent 回复               │
│  用户消息 2  ·········· ○ │
│  Agent 回复               │
│  用户消息 3  ·········· ○ │
└───────────────────────────┘
```
- 滚动时自动高亮最靠近视口中央的用户消息
- 点击圆点 → smooth scroll 到对应消息

### 2.5 Thinking Timeline

Agent 思考过程的可视化：

```
▼ Agent 思考中...
  ├─ ✅ 获取行情数据 (240ms)
  ├─ 🔄 分析技术指标 (running...)
  ├─ ○ 生成建议 (等待中)
  └─ 总耗时: 1.2s
```

- 可折叠/展开
- 最近一步自动展开
- 状态图标：`CheckCircle2` / `XCircle` / `Circle` / `Loader2`
- 工具名称 i18n 本地化

### 2.6 MessageBubble 细节

- Markdown 渲染（react-markdown + GFM + 代码高亮）
- 复制按钮（hover 渐变出现，复制后 ✅ 图标 1.5s）
- 错误消息 → 自动推断重试提示（检测 timeout/429/5xx）
- Agent 头像组件

### 2.7 页面结构

| 页面 | 功能 |
|------|------|
| Home | 仪表盘 |
| Agent | 对话界面 |
| Runtime | 运行监控 |
| Reports | 历史报告 |
| AlphaZoo | 量化因子库 |
| Compare | 对比分析 |
| Correlation | 相关性矩阵 |
| Settings | 配置 |

### 借鉴点
- `useSSE` Hook（reconnect + dedup + resume）→ 实时数据推送
- Conversation Timeline 纵向导航 → 长对话/报告的章节导航
- Thinking Timeline → 分析过程的透明度和可视性
- MessageBubble 的 retry hint → 用户出错友好提示
- Tailwind dark mode + CSS 变量 → 双主题实现模板

---

## 三、daily_stock_analysis: 完整前端生态

### 3.1 页面结构

| 页面 | 代码量 | 功能 |
|------|--------|------|
| PortfolioPage | 69.2K | 持仓管理、盈亏分析、调仓建议 |
| SettingsPage | 66.0K | 系统设置、数据源配置、通知配置 |
| StockScreeningPage | 62.0K | 股票筛选、技术信号、基本面扫描 |
| ChatPage | 55.0K | AI 对话分析 |
| HomePage | 41.1K | 大盘概览、自选股看板 |
| DecisionSignalsPage | 35.3K | 决策信号汇总 |
| BacktestPage | 29.3K | 回测评估与控制台 |
| AlertsPage | 13.6K | 预警规则管理 |
| LoginPage | 12.2K | 登录 |
| TokenUsagePage | 13.4K | LLM Token 用量统计 |

### 3.2 20+ 通用组件库

| 组件 | 说明 |
|------|------|
| ScoreGauge | 情绪仪表盘（动画环形、三色梯度、Light/Dark 自适应 SVG 发光） |
| Button | 多 variant 按钮 |
| Input | 表单输入（含校验） |
| Select | 下拉选择 |
| Card | 卡片容器 |
| Badge | 徽标 |
| Tooltip | 悬浮提示 |
| Drawer | 侧边抽屉 |
| ConfirmDialog | 确认对话框 |
| Pagination | 分页 |
| JsonViewer | JSON 结构化展示 |
| StatCard | 统计数值卡片 |
| EmptyState | 空状态占位 |
| Loading | 加载动画 |
| ScrollArea | 自定义滚动容器 |
| PageHeader | 页面标题区 |
| Collapsible | 折叠面板 |
| ApiErrorAlert | API 错误提示 |
| ParticleBackground | 粒子背景动画 |

### 3.3 Layout 系统

```
<Shell>
  ├── <SidebarNav />       (左侧导航)
  ├── <ShellHeader />      (顶部栏：搜索、主题、用户)
  └── <RouteBoundary />    (路由边界：404、权限)
```

### 3.4 RunFlow 可视化组件

```
RunFlowGraph (32.8K)                 ← 流程图主组件
├── topologyViewModel (13.2K)        ← 拓扑数据模型
├── RunFlowNodeDetails (15.1K)       ← 节点详情弹窗
├── RunFlowSummaryBar (3.8K)         ← 进度概要条
└── RunFlowEventList (6.3K)          ← 事件日志列表
```

分析流程的可视化（数据采集→分析→通知），每一步可展开查看详情。

### 3.5 主题系统

```
ThemeToggle     — 主题切换按钮
ThemeProvider   — Context Provider
```

### 3.6 报告查看组件

```
ReportOverview              — 报告概览
ReportMarkdownPanel         — Markdown 渲染面板  
ReportMarkdownBody          — 正文区
ReportMarkdownDrawer        — 侧边抽屉
ReportDiagnostics           — 诊断信息
ReportNews                  — 相关新闻
ReportStrategy              — 策略分析
ReportDetails               — 详细参数
AnalysisContextSummary      — 分析上下文摘要
MarketReviewReportView      — 大盘分析报告
```

### 3.7 WebUI 启动流程

```python
# 启动时自动构建前端
if WEBUI_AUTO_BUILD != false:
    检查前端构建产物是否过时
    若源文件比产物新 → 自动运行 npm ci + npm build
```

### 借鉴点
- **组件库目录结构**（common / layout / dashboard / report / settings → 按功能分模块）
- **StockScreeningPage** → HermesAlpha 的策略筛选 UI
- **Checkbox + Collapsible + Drawer** 等通用组件实现细节
- 前端自动构建检测 → 省去手动 `npm run build` 的步骤

---

## 四、tickflow-stock-panel: 实时量化工作台

tickflow-stock-panel 的前端价值不在视觉复杂度，而在“同一套工作台承载多个运行态”：看板、自选、策略、回测、个股分析、监控、复盘、设置都接到同一个 FastAPI 后端和同一条行情事件流。

### 4.1 全局 SSE 事件流

前端的 `useQuoteStream` 监听 `/api/intraday/stream`，这条通道不只推行情：

| 事件类型 | 用途 |
|------|------|
| quote 更新 | 看板、自选、个股页实时刷新 |
| monitor alert | 监控规则触发后全局通知 |
| market review progress | 大盘复盘生成进度 |
| depth correction | 五档盘口旁路数据修正 |

这是一种适合小型自托管应用的实时架构：前端不需要为每个页面开一条 WebSocket，也不需要把轮询散落到各组件。

### 4.2 页面不是报告，而是操作台

与 UZI-Skill 的静态报告不同，tickflow 的 UI 面向反复操作：

| 页面 | 主要动作 |
|------|------|
| Dashboard / Watchlist | 查看行情、切换标的、进入分析 |
| Strategy | 运行内置/自定义策略，查看命中结果 |
| Backtest | 配置参数，启动回测，查看成交与收益 |
| Monitor | 创建 signal/price/market/strategy/ladder 规则 |
| Market Review | 触发盘后复盘，接收流式进度 |
| Ext Data | 管理扩展分析表并挂入工作台 |

借鉴点不是页面数量，而是让“数据、策略、监控、复盘”共享同一套导航、状态和事件通道。

### 4.3 AI 输出有边界地嵌入 UI

个股分析、财务分析、复盘和策略生成都在 UI 里，但 AI 不直接接管应用状态。策略生成还要经过后端校验才能进入策略目录。这个边界适合所有金融类前端：AI 可以生成解释、候选规则和报告，但最后必须走确定性保存/校验路径。

### 借鉴点

- HermesAlpha 若做 Web 前端，可以优先做“操作台”而不是营销式首页。
- ashare-audit 可用一条 SSE 推送审计进度、缺口修复、规则触发和报告生成状态。
- 实时事件类型应集中定义，组件只订阅自己关心的事件。

---

## 五、后两批新增：盯盘/桌面/工具型 UI 边界

第五、第六批项目的 UI 价值不都来自完整前端，有些来自“该如何把工具运行态显示给用户”。这些项目补上了桌面会议室、提醒规则、静态快照、认证状态和 token/scope 这几类金融工具 UI。

| 项目 | UI/交互启发 | 可迁移点 |
|------|------------|---------|
| JCP | Wails 桌面股票研究台 + 多 Agent 会议室 | 个股页中加入 Moderator 选人、专家发言队列、二轮复核和股票记忆入口 |
| PanWatch | 自托管盯盘/PWA + 提醒/建议池/模拟盘 | 把 AI 分析结果放入 suggestion pool，展示预算、缓存、冷却和触发来源 |
| QuantDinger | Agent Trading OS + Web/mobile 工作台 | Agent token scope、paper-only 状态、job timeline、策略沙箱校验和实盘 kill switch 必须可见 |
| magpie | CLI/HTTP daemon + watchlist/alert/digest | 最小控制面：自选股、规则、触发历史、`test-fire`、digest 预览 |
| hhxg-market | Markdown/JSON 输出 + OpenAPI | 快照型 UI 必须显示数据日期、schema 版本、是否缓存、最近交易日说明 |
| snowball-cli | JSON CLI + 登录状态 | 外部数据源设置页要区分 public 可用、需要登录、token 状态、最近 403/WAF |
| Privora Examples | Bearer Token + scope + DEK 边界 | API 设置页应显示 token scopes、response shape 验证、敏感数据是否可解密 |

### 新增 UI 原则

- 盯盘 UI 的核心不是“生成报告”，而是让用户看到规则、触发、冷却、历史和测试入口。
- 外部数据源 UI 必须把认证状态和公开/登录接口分开，不要只显示一个“连接成功”。
- Agent 会议室 UI 要显示每位专家为什么被选中、任务是什么、是否引用了前序发言和历史记忆。
- 静态快照 UI 必须把“这是哪天的数据”放在首屏，不可埋在附录。

---

## 六、跨项目 UI 模式对比

### 6.1 报告/结果输出风格

| 项目 | 格式 | 依赖 | 可分享性 |
|------|------|------|---------|
| UZI-Skill | 单文件 HTML (124KB) | Google Fonts + 内联 SVG | · 微信直接打开<br>· Cloudflare Tunnel 远程分享 |
| Vibe-Trading | React SPA + ECharts | React 19 + ECharts | 需部署 |
| daily_stock_analysis | React SPA + Web API | React + Tailwind | 需部署 + 登录 |
| tickflow-stock-panel | React 量化工作台 + FastAPI | React + ECharts/lightweight-charts + SSE | 自托管单容器 |
| QuantDinger | Web/mobile Trading OS + Agent Gateway | Vue 预构建镜像 + Flask + PostgreSQL + job/SSE | 自托管多容器 |
| ai-berkshire | Markdown 文件 | 无 | GitHub 直接看 |
| JCP | Wails 桌面 + React | 本地桌面运行态 | 本机研究台 |
| PanWatch | React/PWA + FastAPI | 自托管 Web/PWA | 盯盘和模拟盘 |
| magpie / hhxg-market / snowball-cli | CLI/HTTP/Markdown 输出 | 轻量工具面 | 可嵌入设置页和状态页 |

### 6.2 数据状态展示

| 项目 | 缺失数据 | 数据质量 | 加载中 |
|------|---------|---------|--------|
| UZI-Skill | `—` 占位符 + 橙色 Banner + chip 列表 | `_review_issues.json` 驱动 banner 颜色 | N/A (静态报告) |
| Vibe-Trading | ToolProgressIndicator | 每步状态图标  ✅/🔄/○ | SSE 实时推送 |
| daily_stock_analysis | EmptyState 组件 | 列名标准化后始终有值 | Loading 组件 + RunFlow 进度 |
| tickflow-stock-panel | 能力不足时功能降级/隐藏 | CapabilitySet + 数据更新时间 | SSE 行情/告警/复盘进度 |
| QuantDinger | scope/market/instrument 不足时阻断 | token 权限、paper_only、live kill switch、回测范围 policy | Agent job stream + result |

### 6.3 认证与权限

| 项目 | 方案 |
|------|------|
| daily_stock_analysis | FastAPI 认证 + LoginPage + AuthContext + JWT |
| UZI-Skill | 无认证（本地分析→可选 Cloudflare Tunnel 远程） |
| Vibe-Trading | API key 配置 |
| tickflow-stock-panel | 自托管访问密码 + 本地用户配置 |
| snowball-cli | public 命令免登录，cookie 命令需用户显式登录 |
| Privora Examples | Bearer Token + scope，持仓字段受 DEK 边界保护 |
| PanWatch | AI 调用预算、冷却和启停 gate 是权限/成本 UI 的一部分 |
| QuantDinger | Agent token 有 R/W/B/N/C/T scope、market/instrument allowlist、paper_only 和 rate limit |

---

## 当前项目行动清单

| 能力 | 参考来源 | 适用项目 | 优先级 |
|------|---------|---------|--------|
| SVG 图表原语层 (19 个函数) | UZI-Skill | HermesAlpha/ashare-audit 报告 | P1 |
| 数据质量 Banner 三级体系 | UZI-Skill | HermesAlpha 报告 | P1 |
| 颜色语义体系 (bull/bear 固定色值) | UZI-Skill | 所有项目 UI 统一 | P1 |
| RunFlow 流程可视化 | daily_stock_analysis | 分析/采集执行态 | P2 |
| SSE 实时流 Hook (重连+去重) | Vibe-Trading | 实时数据 | P2 |
| 单 SSE 通道承载行情/告警/复盘进度 | tickflow-stock-panel | 量化工作台 / 审计进度 | P1 |
| 操作台式页面组织（看板+策略+回测+监控） | tickflow-stock-panel | HermesAlpha Web 前端 | P1 |
| 通用组件库 (20+ 组件) | daily_stock_analysis | HermesAlpha Web 前端 | P2 |
| ScoreGauge 环形仪表盘 | daily_stock_analysis | HermesAlpha 看板 | P2 |
| Thinking Timeline 透明化 | Vibe-Trading | 分析过程 | P2 |
| 66 评委 Panel (头像+评分+气泡) | UZI-Skill | HermesAlpha 多视角分析 | P2 |
| 前端自动构建检测 | daily_stock_analysis | 所有项目 | P2 |
| CSS 变量双主题模板 | UZI-Skill + Vibe-Trading | 所有项目前端 | P3 |
| 多空辩论可视化 | UZI-Skill | HermesAlpha 策略推演 | P2 |
| i18n 多语言框架 | Vibe-Trading | 国际版 | P3 |
| Moderator 会议室：专家选择、发言队列、记忆引用 | JCP | HermesAlpha 个股研究 | P2 |
| 盯盘规则面板：触发条件、冷却、历史、test-fire | PanWatch / magpie | 监控告警 | P1 |
| 数据快照 Banner：日期、schema、cache、最近交易日 | hhxg-market | 日报/两融/日历页 | P1 |
| 外部数据源认证状态：public/auth/token/WAF 分层 | snowball-cli | Provider 设置页 | P1 |
| Token scope / response shape / DEK 状态面板 | Privora Examples | Agent API 设置页 | P1 |
| Agent token scope + paper-only/live gate 面板 | QuantDinger | 交易/通知/外部写入类 Agent 工具 | P1 |
| Agent job timeline：queued/running/progress/result/idempotent replay | QuantDinger | 回测/实验/审计长任务 | P1 |
