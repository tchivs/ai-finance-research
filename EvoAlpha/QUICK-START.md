# EvoAlpha 快速概览

> AAAAndrews · Qlib 因子表达式的多角色 LLM 搜索与验证闭环 · Python / LangChain / MongoDB / REST API
> 源码: `/root/source/docs/aaa/src/EvoAlpha/`
> 原始仓库: <https://github.com/AAAAndrews/EvoAlpha>

## 1. 一句话定位

EvoAlpha 是一个以现有 Qlib 因子为种子、由不同角色的 LLM 做 mutation/crossover、经外部回测指标筛选并沉淀到 MongoDB 的因子发现编排器。它不实现行情处理、表达式执行或回测引擎；这些能力通过 `api/factor_eval_client.py` 对接外部 Factor Evaluation API。

## 2. EvoAlpha 覆盖的链路

```text
origin_factors_sample.json
    -> init_factors_from_json.py 写入 MongoDB
    -> run_search.py 读取 origin、调用 /eval 做基线 IC
    -> Controller 按轮选择 top-k seed factors
    -> SearcherAgent：人设 + mutation/crossover + Qlib DSL 候选
    -> quality_check_fn 轻量可行性检查
    -> Validator：外部评估 -> IC / Rank IC / ICIR 阈值
    -> accepted search factors 写回 MongoDB、进入下一轮 pool
    -> raw prompt/response、逐候选记录、round summary 落盘
```

CLI 默认搜索 CSI300 的中期动量风格：3 轮、4 个搜索器、每轮 24 个候选、前 12 个高 IC 种子。参数来自 `apps/run_search.py`，不是固定策略。虽然有多个 searcher，`Controller.run()` 逐个调用它们，并非并行执行。

## 3. 核心模块

| 模块 | 作用 | 对当前项目的价值 |
|------|------|------------------|
| `apps/init_factors_from_json.py` | `load_factors_from_json()` 校验 `name`/`expression`，`insert_origin_factors()` 幂等导入种子。 | 建立可版本化的因子起始库。 |
| `factor_search/db/mongo.py` | `FactorRepository` 保存 `origin` 与 `search` 因子；按 `metrics.ic` 排序，记录 `meta`、`tags`、`provenance`。 | 让因子、指标和生成血缘能查询、复用。 |
| `factor_search/controller.py` | `Controller` 分配 mutation/crossover 配额、选择高分种子、去重、验证、更新/裁剪演化池。 | 提供“生成—选择—再生成”的最小搜索闭环。 |
| `factor_search/searcher_agent.py` | `SearcherAgent.search()` 调用 `ChatOpenAI`；JSONL 优先、JSON array 回退解析；记录搜索成本。 | 将自然语言研究要求约束为结构化 Qlib 表达式。 |
| `factor_search/prompts.py`、`personas.py` | 定义允许变量、Qlib 算子和安全分母要求，并提供波动率、流动性、均值回归等人设。 | 把搜索多样性和 DSL 边界显式化。 |
| `factor_search/validator.py` | `Validator.validate()` 对齐评估结果，按 `abs(ic)`、`abs(rank_ic)`、`abs(icir)` 过滤。 | 将模型提案与可测量的准入标准分离。 |
| `api/factor_eval_client.py` | `FactorEvalClient` 访问 `/check`、`/eval`，提供重试和零指标失败回退。 | 作为现有 Qlib/回测服务的适配边界。 |
| `run_logger.py`、`audit_log.py` | 落盘原始 prompt/回复、候选指标/通过状态和 JSONL 轮次事件。 | 为 LLM 因子研究提供可追溯实验记录。 |

实际采用时有三条边界：`default_quality_check()` 只是占位的字符串检查，必须替换为真实 DSL/数据校验；`winrate` 与 `stability` 阈值尚未启用；绝对值阈值会接纳负向指标，方向应由下游信号定义或改为显式规则。EvoAlpha 的价值在于发现和治理假设，而不是替代样本外验证、交易成本建模或组合回测。
