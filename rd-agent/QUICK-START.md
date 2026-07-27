# RD-Agent 快速概览

> Microsoft R&D-Agent · 自动化研发循环 · Quant 因子/模型演化 · Hypothesis -> Experiment -> Code -> Run -> Feedback
> 源码: `/root/source/tmp/RD-Agent/`
> 原始仓库: <https://github.com/microsoft/RD-Agent>

---

## 一句话定位

`RD-Agent` 是微软开源的自动化研发框架，面向机器学习、量化、Kaggle、LLM fine-tuning 等场景，把研发过程抽象为“提出假设、生成实验、编码实现、运行评估、反馈沉淀”的循环。金融场景下，它提供 Qlib 驱动的因子、模型和量化策略自演化流程。

对当前项目最有价值的是研发闭环本身：不要只让 Agent 写一次策略，而是把每次想法、代码、运行结果、反馈和历史 trace 结构化保存，让系统能连续改进。

---

## 最高价值借鉴点

| 借鉴点 | 位置 | 可复用价值 |
|---|---|---|
| R&D 循环抽象 | `rdagent/components/workflow/rd_loop.py` | hypothesis -> experiment -> coding -> running -> feedback -> record |
| Evolving Framework | `rdagent/core/evolving_framework.py` | 可演化对象、策略、评估器、RAG 知识库的通用接口 |
| RAGEvoAgent | `rdagent/core/evolving_agent.py` | 多轮演化 trace、反馈、知识自生成、文件锁 |
| Workspace 抽象 | `rdagent/core/experiment.py` | 代码注入、执行、checkpoint、恢复、任务隔离 |
| Quant 因子闭环 | `rdagent/app/qlib_rd_loop/factor.py` | Qlib 因子生成、实现、运行、反馈 |
| Trace + Logger | `rdagent/log/logger.py` | 按 tag/PID 保存对象，方便复盘每轮实验 |
| 人机交互点 | `RDLoop._interact_*` | 用户可修改初始参数、假设和反馈 |

---

## 核心循环

```text
Scenario
  -> HypothesisGen.gen(trace, plan)
  -> Hypothesis2Experiment.convert(hypothesis, trace)
  -> Coder.develop(experiment)
  -> Runner.develop(coded_experiment)
  -> Summarizer.generate_feedback(result, trace)
  -> Trace.sync_dag_parent_and_hist(experiment, feedback)
  -> next loop
```

这个循环比“让 Agent 写一个因子”高一个层级。它要求每个实验都能被追溯、复用、反思和下一轮利用。

---

## Quant 场景适合学什么

RD-Agent(Q) 的金融路径围绕 Qlib：

| 场景 | 命令/入口 | 学习点 |
|---|---|---|
| 因子演化 | `rdagent fin_factor` / `app/qlib_rd_loop/factor.py` | 自动提出和实现新因子 |
| 模型演化 | `rdagent fin_model` | 自动尝试模型结构 |
| 因子+模型联合 | `rdagent fin_quant` | 因子和模型交替优化 |
| 报告提因子 | `rdagent fin_factor_report` | 从财报/研报抽取可实现因子 |

当前项目可以先吸收流程，不必完整迁移 RD-Agent 的庞大框架。

---

## 最适合迁移的模块

1. **Experiment Trace**: 每次策略/因子实验记录 hypothesis、code diff、result、feedback。
2. **Workspace Sandbox**: Agent 生成代码放入隔离 workspace 执行，不直接污染主代码。
3. **Feedback Object**: 评估结果不是文本日志，而是结构化反馈，决定是否继续演化。
4. **Base Features Guard**: 用户提供基础因子后，Agent 不重复生成同名或等价因子。
5. **Session Resume**: 可以从某个 log/session 路径继续跑，不丢历史上下文。

---

## 注意事项

- RD-Agent 是大型通用框架，直接引入会带来 Docker、Qlib、LLM、日志、UI、依赖和运行成本。
- 当前项目更适合借鉴“研发循环和 trace 结构”，而不是整体依赖它。
- 金融结果宣称需要谨慎，README 的 benchmark 和论文结果不能直接代表本地数据和策略表现。
- 自动研发必须有沙箱和评估门控，否则容易产生不可执行或过拟合代码。
