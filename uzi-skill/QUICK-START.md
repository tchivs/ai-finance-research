# UZI-Skill — 设计分析与借鉴

> 原始仓库: <https://github.com/wbh604/UZI-Skill>
**定位**: AI 驱动的 A/H/US 三地股票深度分析框架，66 位投资大佬评委对抗分析  
**版本分析**: v3.5.0

---

## 1. 核心架构：Pipeline 模式

```
collect.py → score.py → synthesize.py → renderer/*.py
```

四个阶段职责清晰分离，每阶段输出纯数据（无副作用），下游只管消费上游产物。

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  collect.py │ →  │  score.py   │ →  │ synthesize   │ →  │  renderer/   │
│ 22 个 fetcher│    │ pure funcs │    │ stage2 wrapper│    │ 20+ 渲染器  │
│ 并发采集    │    │ 1228行 score│    │ 报告组装     │    │ SVG/HTML输出 │
└─────────────┘    └─────────────┘    └──────────────┘    └──────────────┘
```

### 借鉴点
- **当前项目** 的分析流程可参照 `collect → score → synthesize → render` 模式拆分
- 每个阶段输出 JSON cache，可独立重跑、调试、mock
- HermesAlpha 的 report_daily 等分析流程可照此重构

---

## 2. 多评委对抗分析系统

核心创新：66 位不同流派的投资大佬，每人独立对同一只股票评分。

| 流派 | 代表 | 关注维度 |
|------|------|---------|
| 价值派 (A) | 巴菲特、格雷厄姆、芒格 | ROE、护城河、安全边际 |
| 成长派 (B) | 林奇、木头姐、欧奈尔 | 增速、赛道、PEG |
| 宏观派 (C) | 索罗斯、达里奥 | 利率周期、行业位置 |
| 技术派 (D) | 利弗莫尔、米内尔维尼 | 均线排列、成交量 |
| 中国价投 (E) | 段永平、张坤、冯柳 | 好生意、管理层、认知差 |
| 游资 (F) | 赵老哥、章盟主 | 龙虎榜、板块热度 |
| 量化 (G) | 西蒙斯 | 动量/价值/质量因子 |

### 关键机制
- **School Lock (`--school F`)**：可锁定单一流派视角，只分析该流派关心的维度
- **规则引擎骨架分** → **AI 覆盖**：先用脚本打分，AI 再根据角色认知覆盖分数
- **Great Divide 辩论**：bull vs bear 各找证据，产出冲突金句
- `agent_analysis.json` 是闭环关键：记录 AI 的推理过程、覆盖理由、评委洞察

### 借鉴点
- 当前项目的「多角度分析」可借鉴流派分类法
- **裁判+辩论**模式可用于 HermesAlpha 交易信号评审
- School Lock 设计 → 用户可指定"只用趋势策略"或"只用价值策略"

---

## 3. 数据采集策略

### Playwright 兜底
```
Step 1: API 采集（akshare/tushare/东财）
Step 2: 检查数据完整性 → 生成 _review_issues.json
Step 3: 低质量维度 → 自动触发 Playwright 从百度/东财F10/雪球补数据
```
- `network_profile.json` 记录网络环境（国内通/境外受限），影响数据源选择
- 22 个独立 fetcher，每个可单独 `python fetch_xxx.py <ticker>` 执行
- `data_source_registry.py` 管理所有数据源的路由

### 借鉴点
- 数据质量自检 + 自动降级/兜底机制 → ashare-audit 的 LLM provider 验证逻辑
- Fetcher 独立 CLI 入口 → 方便调试和单元测试
- 网络 profile 预检 → 避免无意义的超时等待

---

## 4. 报告渲染系统

### 分层渲染架构
```
lib/report/
├── svg_primitives.py      # 19 个 SVG 绘图原语 + 颜色常量
├── dim_viz.py             # 19 个维度可视化函数
├── institutional.py       # DCF/LBO/IC memo/catalyst/competitive
├── panel_cards.py         # 66 评委 panel 渲染
├── special_cards.py       # fund/insights/school_scores/debate
└── segmental.py           # 分部估值
```

### 关键特色
- SVG 原生渲染（无依赖 Chart.js/Highcharts）
- Bloomberg 风格配色
- 可远程分享（内置 HTTP Server + Cloudflare Tunnel）
- Panel cards 展示所有评委评分分布

### 借鉴点
- HermesAlpha 的报告模块可参考这种组件化渲染方式
- SVG 原语层 → 可复用到 ashare-audit 的图表输出
- Cloudflare Tunnel 模式 → 远程分享分析结果

---

## 5. 代码架构特点

### 瘦身演进
```
v3.0: pipeline 架构引入
v3.1: run_real_test 瘦身 65%，纯函数搬至 score_fns.py
v3.2: assemble_report 瘦身 80%，拆 5 个 lib/report/* 模块
v3.5: School Lock 机制引入
```
- 保持向后兼容（对外 re-export）
- 每阶段有明确版本分水岭

### AI Agent 治理
- `AGENTS.md` + `CLAUDE.md` + `GEMINI.md` + `CODEX.md` 多平台适配
- `SKILL.md` 作为技能描述入口
- HARD-GATE 约束：AI 必须完成角色分析才能继续
- 多 `.plugin/` → Claude/Cursor/OpenCode 插件化接入

---

## 当前项目可借鉴点总结

| 维度 | UZI-Skill 做法 | 适用项目 |
|------|---------------|---------|
| 分析流程 | Pipeline collect→score→synthesize→render | HermesAlpha, ashare-audit |
| 多视角 | 66 评委流派分类+School Lock | HermesAlpha 信号评审 |
| 数据采集 | 22 fetcher + Playwright 兜底 + 自检 | ashare-audit 数据验证 |
| 报告渲染 | SVG 原语 + 组件化 renderer | HermesAlpha 报告 |
| Agent 治理 | AGENTS.md + SKILL.md + HARD-GATE | 所有项目 |
| 版本演进 | 瘦身不破坏兼容 | 通用工程原则 |
