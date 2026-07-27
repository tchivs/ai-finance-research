# Quant Autoresearch 深度分析

> OPENDEV terminal-agent architecture · long-horizon code evolution · truth engine · defense-in-depth
> 源码: `/root/source/tmp/Quant-Autoresearch/`
> 原始仓库: <https://github.com/yllvar/Quant-Autoresearch>

## 1. 架构总览

Quant Autoresearch 的核心类是 `QuantAutoresearchEngine`。它把策略演化拆成固定循环：

```text
QuantAutoresearchEngine
    -> ContextCompactor
    -> SafetyGuard
    -> ModelRouter
    -> LazyToolRegistry
    -> Playbook
    -> PromptComposer
    -> Backtester subprocess
    -> telemetry / iteration tracker
```

这是一种 terminal-agent 架构：模型不是直接返回一份研究报告，而是在工具、代码、回测和记忆之间长期迭代。

## 2. Engine 的 6 阶段循环

`engine.py` 中 `run()` 每轮执行：

```text
save baseline strategy code
_phase_context_mgmt()
_phase_thinking()
_phase_action_selection(thinking_trace)
_phase_doom_loop_detection(action_proposal)
_phase_execution(action_proposal)
_phase_observation(observations)
```

### 2.1 Phase 0: Context management

每轮开始调用 `ContextCompactor.adaptive_context_compaction()`。这让上下文管理成为 Agent 主循环的一部分，而不是等模型超窗后再补救。

### 2.2 Phase 1: Thinking

`ModelRouter.thinking_phase()` 要求模型“不使用工具，只生成 reasoning trace”。上下文包含当前分数、最近动作和目标。

这个分相值得迁移：金融研究系统可以先让模型形成假设和风险意识，再进入工具调用阶段。

### 2.3 Phase 2: Action selection

执行前会先通过 `LazyToolRegistry.search_tools("active", EXECUTOR)` 取工具，再由 `PromptComposer.compose_prompt("reasoning", ...)` 拼装 prompt，并把 system reminders 作为 user message 追加。

关键点：工具不是全部暴露给模型，而是按阶段搜索和裁剪。

### 2.4 Phase 3: Doom-loop detection

对每个动作生成 fingerprint：

```text
tool_name + sorted(parameters)
```

如果短窗口内重复次数过多，就提示 doom-loop。这类机制对金融 Agent 很实用，例如反复调整同一个阈值、反复下载同一数据源、反复运行无效回测时应自动暂停。

### 2.5 Phase 4: Execution

每个 action 先过 `SafetyGuard.defense_in_depth_check()`，再进入 `tool_registry.execute_tool()`。被阻止的工具调用会变成 observation，而不是直接丢失。

### 2.6 Phase 5: Observation

如果工具结果超过 8000 字符，会保留头尾并 mask 中间。若 `run_backtest` 返回分数提升，则写入 Playbook；否则恢复本轮开始前保存的策略代码。

## 3. Truth Engine: 回测即裁判

`src/core/backtester.py` 是这个项目最有价值的文件之一。

### 3.1 AST security_check

回测前先解析策略代码 AST，阻止：

```text
forbidden builtins: exec/eval/open/getattr/setattr/delattr
forbidden modules: socket/requests/urllib/os/sys/shutil/subprocess
look-ahead: shift(-N) 或 shift(periods=-N)
```

这说明防未来函数不能只靠 prompt，必须在执行层扫描。

### 3.2 RestrictedPython sandbox

策略文件会先移除 import 语句，再用 `compile_restricted()` 编译。沙箱只开放：

```text
safe_builtins
safer_getattr
guarded iterator/item
pd
np
```

策略必须定义 `TradingStrategy`，否则直接失败。

### 3.3 Forced lag

即便策略代码自己返回了全量信号，回测仍强制：

```text
signals = full_signals.shift(1).fillna(0)
```

这是金融系统里非常重要的设计：不要相信策略作者已经防未来函数，执行层必须统一处理。

### 3.4 Walk-forward validation

回测按最短数据长度切成 5 个窗口，每个窗口只统计 OOS 区间表现，最终输出：

```text
SCORE: avg_oos_sharpe
DRAWDOWN: avg_oos_drawdown
TRADES: total_oos_trades
P-VALUE: avg_monte_carlo_pval
```

### 3.5 Volatility-adjusted slippage

成本不是常数，而是：

```text
costs = trades * (base_cost + volatility * 0.1)
```

虽然简化，但方向正确：波动越大，策略越容易被滑点吞噬。

## 4. SafetyGuard 五层安全

`SafetyGuard` 的五层：

| 层 | 机制 | 例子 |
|----|------|------|
| Prompt Guardrails | 检查危险内容和交易规则 | 禁 eval、禁未来函数、仓位不超过 1.0 |
| Schema Gating | 按 subagent 限制工具 | planner 只读，executor 可执行 |
| Runtime Approval | 按风险和审批模式决定是否需要人审 | write_file/run_command 高风险 |
| Tool Validation | 工具参数级校验 | position size、leverage、危险字符串 |
| Lifecycle Hooks | 执行前后 hook | 预留审计/监控/拦截 |

它的实现不是最终生产级，但结构很值得借鉴：安全不是一个 if，而是一组可解释的层级。

## 5. LazyToolRegistry

工具定义包含：

```text
name
parameters
category
subagent_access
risk_level
handler
```

`search_tools()` 先按查询、subagent 权限和 relevance 返回工具摘要。模型看到的是搜索结果，而不是完整工具宇宙。

这个模式适合 A 股数据工具很多的场景：先找“估值/公告/资金流/回测”相关工具，再加载 schema。

## 6. Adaptive Context Compaction

`ContextCompactor` 用四个阈值控制上下文压力：

| 阈值 | 阶段 | 动作 |
|------|------|------|
| 70% | WARNING | 记录警告 |
| 80% | WARNING_MASKING | mask 旧的大工具输出 |
| 90% | CRITICAL_PRUNING | 只保留最近 5 个操作 |
| 99% | CRITICAL_SUMMARIZATION | 用模型摘要关键上下文 |

此外 `optimize_tool_result()` 对超过 8000 字符的工具结果做结构化压缩，保留 `stdout/stderr/score/error/status` 等关键字段。

这对金融 Agent 尤其重要，因为行情、研报、回测日志、因子列表都容易超长。

## 7. PromptComposer

Prompt 被拆成：

```text
base_constitution
identity
safety_policy
quant_rules
schema gating
system reminders
phase-specific instructions
```

System reminders 由触发器生成，例如 incomplete todos、high risk operations、context pressure、iteration milestone、performance decline。

可迁移点：金融 Agent 的 prompt 不应是一块大文本，而应由稳定宪法、动态上下文、工具权限和即时提醒组合。

## 8. ModelRouter

模型分三类：

| Phase | 默认模型意图 | 参数 |
|-------|--------------|------|
| thinking | 低温、短输出、便宜模型 | temperature 0.1 |
| reasoning | 更大上下文、更强模型 | temperature 0.3 |
| summarization | 低成本摘要 | temperature 0.1 |

同时记录 token 估算和成本，并在主模型失败时 fallback 到 Groq 模型。

这说明多模型架构不只是“换供应商”，而是按任务类型路由。

## 9. Playbook 双记忆

`Playbook` 使用 SQLite 表：

```text
strategy_patterns
pattern_relationships
performance_contexts
memory_usage_stats
```

每个成功 pattern 包含：

```text
pattern_hash
hypothesis
strategy_code
performance_metrics
usage_count
success_rate
embedding
```

Embedding 是基于量化词表的 TF-IDF。虽然简单，但它提供了一个可落地的形态：成功经验必须结构化可检索，而不是只留在聊天历史里。

## 10. 当前项目迁移方案

### HermesAlpha

```text
Financial Research Constitution
    -> Thinking phase: 形成投资假设和需验证问题
    -> Tool discovery: 只加载相关数据工具
    -> Execution phase: 拉数据/生成模型/回测
    -> Truth engine: walk-forward + forced lag + 成本 + p-value
    -> Keep/Revert: 只推广通过门控的 signal
    -> Playbook: 保存成功和失败模式
```

### ashare-audit

```text
Audit target: AI-generated strategy or report
    -> AST/data-leak scanner
    -> tool-permission scanner
    -> backtest-integrity scanner
    -> context-pressure/output-masking scanner
    -> keep/revert trace verification
```

## 11. 风险和限制

- `engine.py` 当前用文件覆盖实现回滚，生产应使用 versioned artifact 或 git-like object store。
- `run_backtest_with_output()` 用 regex 解析 stdout，生产应让 backtester 输出 JSON schema。
- RestrictedPython 是一层防护，不等于完整沙箱；仍要加进程隔离、CPU/内存限制、文件系统白名单。
- Tool registry 的 schema 还不够严格，真实系统需要 JSON Schema/Pydantic 强校验和审计日志。
- Playbook 当前 semantic matching 粗糙，适合原型，不适合复杂策略知识检索。

## 12. 结论

Quant Autoresearch 的核心价值是“自动研发纪律”：分相推理、懒加载工具、五层安全、真值回测、上下文压缩、失败回滚、经验记忆。它给 HermesAlpha/ashare-audit 的启发是：任何能修改策略或给出投资判断的 Agent，都必须被一个确定性的工程壳包住。
