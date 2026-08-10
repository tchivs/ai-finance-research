# RD-Agent 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/microsoft/RD-Agent.git
> 分析基线：
> - `RD-Agent`：commit `6762f84f9bc0f5c6486c50a00e128a57ac6c3683`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/RD-Agent`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `RD-Agent`：`4f9ecb005881` → `6762f84f9bc0`

提交摘要：
- 6762f84 docs: add Agent² RL-Bench preprint and project page (#1447)
- 1deb2e0 fix(ci): upgrade Node.js to 22 for commitlint compatibility (#1444)
- 400abb0 ci: stabilize CI toolchain (#1445)
受影响路径：
- `M	.github/workflows/ci.yml`
- `M	.github/workflows/pr.yml`
- `M	README.md`
- `M	pyproject.toml`
- `M	rdagent/scenarios/rl/autorl_bench/README.md`
- `M	requirements.txt`
- `M	requirements/lint.txt`
<!-- source-sync:changes:end -->


> 自动化研发系统 · 演化框架 · Qlib 金融因子/模型循环 · Trace 驱动反馈学习
> 源码: `src/RD-Agent/`
> 原始仓库: <https://github.com/microsoft/RD-Agent>

---

## 1. 项目形态

RD-Agent 是一个完整的研发自动化平台，而不是单一金融项目。它的结构大致分为：

| 目录 | 作用 |
|---|---|
| `rdagent/core/` | 场景、实验、演化、评估、开发者、知识库等基础抽象 |
| `rdagent/components/` | workflow、coder、runner、agent、benchmark、knowledge management |
| `rdagent/scenarios/qlib/` | 金融量化场景的 proposal、developer、experiment |
| `rdagent/app/qlib_rd_loop/` | 因子、模型、因子+模型、报告提因子的 CLI 入口 |
| `rdagent/log/` | 对象级日志、trace 存储、Streamlit UI |
| `web/` | 新前端 UI |

它最值得学习的是抽象边界：研发 Agent 不直接“写最终答案”，而是通过场景、假设、实验、开发者、运行器、反馈器协同完成多轮迭代。

---

## 2. Evolving Framework

`rdagent/core/evolving_framework.py` 定义了通用演化组件：

| 抽象 | 含义 |
|---|---|
| `EvolvableSubjects` | 可被改进的目标对象，比如一组任务、代码、模型配置 |
| `EvoStep` | 一轮演化结果，包含对象、查询到的知识、反馈 |
| `EvolvingStrategy` | 如何从旧对象产生新对象 |
| `IterEvaluator` | 分阶段评估局部实现，并返回整体反馈 |
| `RAGStrategy` | 查询知识、生成知识、持久化知识库 |

这个抽象可以迁移到当前项目的策略研发：

```text
StrategyCandidate as EvolvableSubjects
FactorExperiment as EvoStep.evolvable_subjects
BacktestFeedback as Feedback
ProviderNotes/ResearchMemory as RAG knowledge
```

---

## 3. RAGEvoAgent 的多轮控制

`RAGEvoAgent.multistep_evolve()` 体现了成熟 Agent 循环需要的控制点：

1. 可选从 RAG 查询历史知识。
2. `evolving_strategy.evolve_iter()` 分步改进对象。
3. `eva.evaluate_iter()` 对每个局部实现做评估。
4. 汇总整体反馈。
5. 将 `EvoStep` 写入 trace。
6. 可选根据 trace 生成新知识并持久化。
7. 如果 feedback 标记完成则停止。

关键价值在于“反馈不是最后的总结，而是下一轮输入”。这正是量化策略、因子库和审计规则能够持续进化的必要结构。

---

## 4. RDLoop 的工程闭环

`rdagent/components/workflow/rd_loop.py` 是金融场景最值得读的文件。它把研发过程拆成五个步骤：

| 方法 | 作用 |
|---|---|
| `_propose()` | 基于 trace 和 plan 生成 hypothesis |
| `_exp_gen()` | 把 hypothesis 转成 experiment |
| `coding()` | coder 实现实验 |
| `running()` | runner 运行实验 |
| `feedback()` | summarizer 生成结构化反馈 |
| `record()` | 将实验和反馈写入 trace |

它还提供 `_interact_init_params()`、`_interact_hypo()`、`_interact_feedback()`，允许人在关键节点修正基础特征、假设和反馈。

当前项目可以借鉴这种分层，把“AI 自动改策略”拆成：

```text
idea proposal
experiment plan
code patch in sandbox
backtest/eval
review feedback
promotion decision
```

---

## 5. Qlib 因子生成机制

`QlibFactorHypothesisGen` 会基于历史 hypothesis/feedback 准备上下文。早期提示“先尝试简单快速因子”，超过一定轮数后再提示尝试高 IC 的复杂因子。

这个细节很实用：自动研发不应该一开始就追求复杂模型。合理的演化节奏是：

```text
simple factors -> diverse variants -> feedback accumulation -> complex ML factors
```

`QlibFactorHypothesis2Experiment` 还会检查历史实验，避免生成重复 factor_name。这可以迁移为当前项目的因子去重和 idea novelty 检查。

---

## 6. Workspace 与可恢复性

`FBWorkspace` 提供了文件级 workspace：

| 能力 | 价值 |
|---|---|
| `inject_files()` | 将 Agent 生成代码注入隔离目录 |
| `all_codes` / `get_codes()` | 汇总代码供评估和反馈使用 |
| `create_ws_ckp()` / `recover_ws_ckp()` | 支持 checkpoint 和回滚 |
| `workspace_path` | 每个实验独立目录，避免污染主项目 |

当前项目如果让 Agent 自动生成策略或审计规则，必须采用类似沙箱。直接让 Agent 改主分支策略代码再回测，风险太高。

---

## 7. 日志和 Trace

`RDAgentLog` 支持 tag 嵌套和对象存储。`RDLoop` 在每一步都 `logger.log_object()`，例如 scenario、settings、hypothesis、experiment、coder result、runner result、feedback。

这对长期研发很关键：文本日志只能看发生了什么，对象日志能重建每轮输入输出。当前项目可简化为 JSONL：

```text
run_id
loop_id
stage
object_type
payload_json
created_at
parent_run_id
```

---

## 8. 对当前项目的落地方案

### 8.1 最小 R&D Loop

不用引入 RD-Agent，也可以实现轻量版：

```text
propose_idea(context, history) -> Hypothesis
plan_experiment(hypothesis) -> ExperimentSpec
implement_experiment(spec) -> WorkspacePatch
run_experiment(workspace) -> Metrics
summarize_feedback(metrics, hypothesis) -> Feedback
record_trace(all)
```

### 8.2 Promotion Gate

每个实验输出分三档：

| Verdict | 含义 |
|---|---|
| `reject` | 不进入候选库，但保留失败经验 |
| `keep_research` | 有局部信号，需要更多样本 |
| `promote_shadow` | 进入影子组合或审计规则候选 |

### 8.3 知识沉淀

每轮反馈自动生成两类知识：

1. 哪些因子/规则在什么市场状态下失败。
2. 哪些实现 bug 或数据口径问题需要避免。

---

## 9. 值得直接吸收的原则

1. Agent 研发必须是循环，不是一次性代码生成。
2. 每轮必须有 hypothesis、experiment、code、result、feedback。
3. 反馈必须结构化，能驱动下一轮。
4. 自动生成代码必须在 workspace 中运行和评估。
5. 历史失败同样是知识，应进入 RAG/trace。
6. 人类应能在初始参数、假设和反馈三个节点介入。
7. 复杂因子应在简单因子和反馈积累后再引入。
