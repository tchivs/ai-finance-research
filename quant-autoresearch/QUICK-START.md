# Quant Autoresearch 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/yllvar/Quant-Autoresearch.git
> 分析基线：
> - `Quant-Autoresearch`：commit `16636a87596c32600fdd088bb9ee5dacd491e1b2`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Quant-Autoresearch`
<!-- source-sync:end -->


> OPENDEV 风格量化策略自进化 · ReAct loop / RestrictedPython / ACC / Playbook
> 源码: `src/Quant-Autoresearch/`
> 原始仓库: <https://github.com/yllvar/Quant-Autoresearch>

## 1. 一句话定位

Quant Autoresearch 把 alpha 发现当成“长周期代码演化问题”：Agent 先思考、再选择工具、修改策略代码、运行安全回测、根据 OOS Sharpe 决定保留或回滚，并把成功模式写入 SQLite playbook。

它最值得学的不是具体策略，而是如何给“会写代码的金融 Agent”加上上下文管理、安全边界、回测真值引擎和失败回滚。

## 2. 核心循环

```text
baseline backtest
    -> Phase 0: Adaptive Context Compaction
    -> Phase 1: thinking model 生成推理轨迹
    -> Phase 2: reasoning model 选择工具调用
    -> Phase 3: doom-loop fingerprint 检查
    -> Phase 4: SafetyGuard + ToolRegistry 执行
    -> Phase 5: observation / playbook / keep-or-revert
```

核心文件：

| 文件 | 作用 |
|------|------|
| `src/core/engine.py` | 6 阶段 autonomous loop |
| `src/core/backtester.py` | RestrictedPython 沙箱回测和 walk-forward 验证 |
| `src/safety/guard.py` | 五层 defense-in-depth 安全系统 |
| `src/tools/registry.py` | lazy tool discovery + schema gating |
| `src/context/compactor.py` | 4 阶段 Adaptive Context Compaction |
| `src/memory/playbook.py` | SQLite 策略模式记忆 |
| `src/models/router.py` | thinking/reasoning/summarization 模型路由 |
| `src/context/composer.py` | 模块化 prompt + system reminders |

## 3. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| Program Constitution | 不变的投资任务、风控和代码约束注入每轮 | 金融 Agent 需要“宪法”而不是每轮临时 prompt |
| Phase split | thinking model 与 reasoning model 分离 | 便宜模型做思考，强模型做执行决策 |
| LazyToolRegistry | Agent 先搜索工具，再加载可用 schema | 避免一次性暴露过多工具导致乱调用 |
| Schema gating | planner/analyzer/executor 看到不同工具 | 用权限边界控制 Agent 行为 |
| SafetyGuard | prompt guardrails、schema、approval、validator、hook 五层 | 不把安全寄托在单个正则或系统提示词上 |
| Restricted backtester | 禁 import、禁 os/sys、只开放 pd/np | AI 写的策略必须在受限环境里跑 |
| Forced signal lag | 回测里强制 `signals.shift(1)` | 从执行层防止未来函数，而不是只靠提示词 |
| ACC | 70/80/90/99% 四阶段压缩 | 长周期 Agent 必须有上下文压力管理 |
| Playbook | 成功策略 hash、metrics、tags、embedding 入 SQLite | 把实验成功经验做成可检索记忆 |
| Keep/Revert | 分数没有改善就恢复 baseline code | 自动研发必须有失败回滚，不应只累积修改 |

## 4. 对 HermesAlpha 的借鉴

1. **建立 Quant Constitution**：固定最大回撤、最大杠杆、数据口径、禁止未来函数、禁止自动实盘下单等硬规则。
2. **把“研究”和“执行”分相**：先让研究 Agent 生成 hypothesis，再由执行 Agent 调工具生成或修改策略。
3. **回测层强制防作弊**：信号延迟、walk-forward、滑点、交易成本、Monte Carlo p-value 应在 backtester 里硬编码。
4. **失败回滚**：每次策略修改前保存 baseline，只有通过门控才推广为 active strategy。
5. **把好策略沉淀为 playbook**：保存假设、代码、指标、适用市场、失败条件，供下一轮检索。

## 5. 对 ashare-audit 的借鉴

1. **审计 AI 生成代码**：扫描 `shift(-1)`、危险 import、文件/网络访问、position size 越界。
2. **审计回测真值引擎**：确认策略信号是否被强制 lag，交易成本是否真实扣除，OOS 是否独立。
3. **审计工具权限**：Planner 不应能写文件，Analyzer 不应能运行系统命令。
4. **审计失败回滚**：策略分数下降时是否真的恢复 baseline，而不是继续污染 active strategy。

## 6. 不该照搬的部分

- 当前实现仍有 prototype 味道，例如用 stdout regex 解析回测指标、策略文件直接覆盖、部分 prompt 路径假设较硬。
- 安全系统有方向，但生产环境仍需要 OS 级沙箱、资源限制、审计日志不可篡改和更严格的审批流。
- 数据默认是 SPY/QQQ/BTC/ETH 类缓存，A 股系统需要换成本地 A 股数据底座与交易日历。
- Playbook 的 embedding 是 TF-IDF 关键词级，足够示范但不应作为最终语义检索方案。

## 7. 最小可迁移方案

```text
Phase 1: Constitution
    写死金融 Agent 的不可违反规则

Phase 2: Truth Engine
    walk-forward + forced lag + costs + p-value

Phase 3: Tool Registry
    按 planner/executor/analyzer 裁剪工具

Phase 4: Keep/Revert Loop
    只推广通过门控的策略

Phase 5: Playbook Memory
    成功模式、失败模式、指标上下文入库
```

## 8. 结论

Quant Autoresearch 是“AI 自动写策略”方向里很适合借鉴工程边界的项目。它说明自动研发系统的核心不是让模型多写几行代码，而是把代码修改、回测真值、安全扫描、上下文压缩、失败回滚和经验记忆串成闭环。
