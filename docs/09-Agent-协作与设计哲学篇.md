# 补充四：Agent 协作模式与设计哲学

## 来源项目
- ai-berkshire (4角色并行团队、AI偏见评估、跨平台技能同步)
- Vibe-Trading (LangGraph 状态机、RunStateStore、MCP 三层暴露)
- UZI-Skill (多平台适配、AGENTS.md 治理、HARD-GATE)
- daily_stock_analysis (AGENTS.md 作为真源、技能目录)
- JCP / PanWatch / Awesome Finance Skills (Moderator 会议室、BaseAgent 生命周期、金融能力拆包)
- snowball-cli / quant-buddy-skill / joinquant-skill / hhxg-market / Privora Examples (工具型 Skill 契约)
- QuantDinger (Agent Gateway、MCP薄封装、scope/audit/idempotency、paper-only交易闸门)
- DojoAgents (配置化 Runtime、Strands Agent Loop、Skills/Plugins、MCP、Gateway 与计划编排)

---

## 0. DojoAgents：配置化 Agent Runtime，而非默认多 Agent

### 运行时装配模式

DojoAgents 的 `Runtime.from_config_store()` 先装配 ToolRegistry、SkillManager、MemoryManager、SessionManager 和 AgentLoop；多 Agent、Planning 和 MCP 是由配置决定是否注册的附加能力。这个顺序比“先引入复杂编排再补工具和会话”更适合首版金融系统。

```text
Runtime -> ToolRegistry -> AgentLoop -> LLM / ToolExecutor
                       -> Session / Memory / Skills
                       -> optional: Planning / Multi-Agent / Gateway
```

### 可迁移结论

- Agent 的核心接口应稳定在 `ChatRequest -> AgentResponse`，CLI、Web、定时任务和聊天渠道只负责适配。
- 通过配置注册能力，默认关闭复杂多 Agent 与自动计划，避免首版把异常处理、审批和审计推迟到以后。
- Tool result 应有截断、artifact 和 trace；不能只把原始输出塞回模型上下文。
- Plugin/MCP/Skill 是受信任扩展点。DojoAgents 支持用户目录 Python 插件与 shell hook，生产系统必须增加签名、allowlist、权限和隔离，不能把兼容性当作安全边界。

### 不可照搬边界

其 `SandboxPolicy.check_tool()` 在当前源码基线是空实现，`execute_code` 直接使用宿主 Python 子进程。因此“有 guardrail”和“具备强隔离”是两件不同的事；涉及账户、交易或不可信代码时，仍要采用独立 ActionGuard 与容器/VM 隔离。

---

## 1. ai-berkshire: 四角色并行研究团队

### 团队架构
```
Team Lead（你自己）— 统筹协调、汇总研判、输出最终报告
├── business-analyst   — 段永平视角：商业模式 & 护城河
├── financial-analyst  — 巴菲特视角：财报 & 估值
├── industry-researcher— 芒格视角：行业格局 & 竞争态势
└── risk-assessor      — 李录视角：风险 & 管理层
```

### 前置：AI 研究偏见评估
在启动研究前，先评估「AI 可研究性」：

| 等级 | 特征 | AI 陷阱 | 应对策略 |
|------|------|--------|---------|
| A级 | 信息充裕 | 共识过强，输出趋同于市场 | 反面检验：聪明人为什么不买？ |
| B级 | 信息适中 | 用"合理推测"填补空白 | 标注置信度，区分有据推算和凭空填充 |
| C级 | 信息稀缺 | 因资料不足而过度保守 | 第一性原理：聚焦商业本质核心问题 |

### 第一性原理（C 级公司）
1. 客户是谁？为什么付钱？有没有替代选择？
2. 复购靠什么驱动？
3. 竞争对手拿 100 亿能复制这门生意吗？
4. 管理层做过什么关键决策？

### 投资研究质量约束
- 客观客观客观 — 所有分析基于事实和数据
- 严格区分「事实」与「观点」
- 不预设立场 — 先摆数据、再推逻辑、最后得结论
- 呈现正反两面 — 每个核心判断附带反面论据
- 不确定就诚实说「不确定」
- 数据必须标注来源，关键数据至少 2 个来源交叉验证

---

## 2. Vibe-Trading: LangGraph 状态机 + RunStateStore

### RunStateStore — 运行状态持久化
```python
class RunStateStore:
    def create_run_dir(self, workspace: Path) -> Path:
        # timestamp + uuid 生成唯一目录
        # 自动创建 code/ logs/ artifacts/ 子目录

    def save_request(self, run_dir, prompt, context)  # 保存请求
    def mark_success(self, run_dir)                   # 标记成功
    def mark_failure(self, run_dir, reason)           # 标记失败
```

每次运行生成独立目录：
```
runs/
├── 20260115_143052_abc123/
│   ├── req.json      # 原始请求
│   ├── state.json    # 运行状态
│   ├── code/         # 生成的代码
│   ├── logs/         # 执行日志
│   └── artifacts/    # 产物（图表、报告）
```

### 借鉴点
- HermesAlpha 的每次分析可生成独立 run 目录

---

## 3. Vibe-Trading: MCP 三层暴露

```
vibe-trading (CLI/TUI)
├── vibe-trading serve    # FastAPI 服务器
└── vibe-trading-mcp      # MCP Server
    └── 暴露为 Claude/Cursor/OpenClaw 的工具
```

MCP 配置：
```yaml
mcp:
  command: vibe-trading-mcp
  args: []
```

### 借鉴点
- 当前项目可 MCP 化暴露：
  - HermesAlpha → 数据查询工具
  - ashare-audit → 审计工具
- Hermes 已有 `native-mcp` 和 `hermes-mcp-server` skill

---

## 4. UZI-Skill: 多平台 Agent 适配

```
UZI-Skill/
├── AGENTS.md                  # 通用 Agent 指令
├── CLAUDE.md                  # Claude Code 适配
├── CODEX.md                   # Codex 适配
├── GEMINI.md                  # Gemini 适配
├── .claude-plugin/plugin.json # Claude Code 插件
├── .cursor-plugin/plugin.json # Cursor 插件
├── .opencode/                 # OpenCode 适配
├── gemini-extension.json      # Gemini 扩展
└── package.json               # OpenClaw/npm
```

### 版本分水岭文档化
```
v3.0.0: pipeline 默认 · UZI_LEGACY=1 回老路径
v3.1.0: rrt 瘦身 65% · 纯函数搬至 score_fns
v3.2.0: assemble_report 瘦身 80% · 拆 5 个 lib/report/*
v3.5.0: School Lock 机制引入
```

每阶段保持向后兼容（对外 re-export）。

### HARD-GATE 约束
```
Step 3 是硬 gate：
1. READ panel.json 骨架分数
2. ANALYZE 每组评委
3. UPDATE panel.json
4. WRITE agent_analysis.json
5. SET agent_reviewed: true
```

违反 gate → 拒绝继续（不是警告，是阻断）。

---

## 5. daily_stock_analysis: AGENTS.md 治理体系

### 真源治理
```
AGENTS.md         — 仓库内 AI 协作规则唯一真源
CLAUDE.md         — 软链接 → AGENTS.md
copilot-instructions.md — GitHub Copilot 镜像/分层补充
.claude/skills/   — 仓库内 skill 目录
```

修改后执行：
```bash
python scripts/check_ai_assets.py
```

### 验证矩阵（前文详述）
- 6 类 CI 检查项，3 个阻断项
- 按改动面执行对应验证
- 稳定性护栏 7 条

### 贡献质量底线
- 不接受堆叠代码量替代设计收敛
- AI 辅助本身不是问题；问题是提交未经人工审查的代码
- 不接受只在被指出的位置追加局部 patch
- 多轮 review 后仍同类问题 → 要求关闭重做

---

## 6. 跨项目：技能同步模式

### ai-berkshire 的同步系统
```
skills/*.md (Claude Code 真源)
    ↓ sync-codex-skills.py
codex-skills/*/SKILL.md (Codex 生成)
codex-prompts/*.md (Codex 斜杠命令)
    ↓ install scripts
本地 ~/.claude/commands/
```

原则：
- skills/*.md 是真源
- 修改后必须跑 sync 脚本
- 禁止手动编辑生成的 codex-skills/

### 借鉴点
- 当前项目的 prompt seed（HermesAlpha）可参照此同步模式
- LLM prompt 作为真源 → Alembic migration 自动注册（已在做）
- 技能/模板/配置作为真源 → 脚本生成 → 部署

---

## 7. 后两批新增：Agent 协作从“角色团队”扩展到“工具契约 + 产品运行态”

前几批强调多 Agent 团队、LangGraph 状态机和 AGENTS.md 治理；第五、第六批补上了更贴近产品落地的两类形态：桌面/盯盘运行态 Agent，以及工具型 Skill 契约。

### JCP: Moderator 会议室

```text
User question
    -> Moderator.Analyze 判断意图和专家列表
    -> selected ExpertAgents 串行发言
    -> later experts read previous opinions + stock memory
    -> optional second review
    -> Moderator.Summarize
```

这个模式介于“多角色并行”和“单 Agent 工具调用”之间。它更像一个股票会议室：先选人，再讨论，再总结。关键价值是 Moderator 不是只做最终总结，而是在入口处决定谁该参与、每个人任务是什么。

### PanWatch: BaseAgent 产品化

PanWatch 把 Agent 生命周期标准化为：

```text
collect -> analyze -> notify
```

TradingAgents 不是孤立脚本，而是被包装成可被预算、缓存、冷却、持仓上下文和 Web API 调度的产品功能。这说明 Agent 产品化的重点不是多会调用模型，而是能否进入调度、状态、通知和用户持仓上下文。

### Awesome Finance Skills: 能力拆包

Awesome Finance Skills 把金融能力拆成 stock/search/sentiment/predictor/reporter/visualizer 等 skill。它的设计哲学是：

```text
deterministic scripts handle data/search/model/chart
Agent handles judgment/synthesis/writing
SQLite keeps memory/citations/signals
SKILL.md defines trigger and usage boundary
```

这比把所有能力塞进一个巨型金融 Agent 更容易复用和审计。

### 工具型 Skill 契约

| 项目 | Agent 契约 |
|------|-----------|
| snowball-cli | 先用无需登录命令，只有失败才提示用户自行登录 |
| quant-buddy-skill | 新任务 fresh session，检查 skill version，保留 data_id，不信任原始 TopN 顺序 |
| joinquant-skill | 先查 API reference 和模板，再生成策略，生成后必须 lint |
| hhxg-market | 按问题选择脚本，回答必须标注日期/非交易日/缓存状态 |
| Privora Examples | 先 public ping，再 Bearer Token 验证，按 scope 调 skill gateway |
| QuantDinger | Agent Gateway 使用 R/W/B/N/C/T scope、job idempotency、调用审计；MCP 只做 Gateway 薄封装 |

### 借鉴点

- Agent 协作不只包括“几个角色讨论”，还包括工具触发边界、认证边界、输出范式和运行状态。
- `SKILL.md` 应被当成接口契约，而不是 README。
- 产品化 Agent 必须接入预算、缓存、冷却、通知和用户上下文。
- Moderator/Router 的职责要前置：先判断问题和选择能力，再开始分析。
- 接入交易/资金动作的 Agent 必须默认 paper-only，实动作需要 scope、服务端开关和显式确认。

---

## 当前项目行动清单

| 能力 | 参考来源 | 适用项目 | 优先级 |
|------|---------|---------|--------|
| 4角色并行团队模式 | ai-berkshire | HermesAlpha 分析 | P2 |
| AI 研究偏见评估 | ai-berkshire | 所有分析流程 | P2 |
| RunStateStore 运行目录 | Vibe-Trading | HermesAlpha | P2 |
| MCP 三层暴露 | Vibe-Trading | 所有项目 | P2 |
| Agent Gateway：scope、audit、idempotency、paper-only | QuantDinger | 对外 Agent API / MCP 后端 | P1 |
| 多平台 Agent 适配 | UZI-Skill | 所有项目 | P3 |
| HARD-GATE 约束 | UZI-Skill | 所有分析流程 | P2 |
| AGENTS.md 真源治理 | daily_stock_analysis | 所有项目 | P1 |
| 技能同步脚本 | ai-berkshire | HermesAlpha prompt seed | P2 |
| 贡献质量底线 | daily_stock_analysis | 所有项目 | P1 |
| Moderator 选专家 + 串行会议室 | JCP | HermesAlpha 个股研究 | P2 |
| BaseAgent 生命周期 `collect/analyze/notify` | PanWatch | 盯盘 Agent 产品化 | P1 |
| 金融能力拆包为 stock/search/sentiment/forecast/report skills | Awesome Finance Skills | HermesAlpha / OpenClaw 集成 | P1 |
| 工具型 `SKILL.md` 写清触发、认证、版本和回答边界 | snowball-cli / quant-buddy-skill / hhxg-market | 所有 Agent 工具 | P1 |
| 平台策略生成先 reference/template，再 lint | joinquant-skill | 策略 Agent | P1 |
| Agent API 先 public ping，再 token/scope 验证 | Privora Examples | 对外 Agent gateway | P1 |
