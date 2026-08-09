# EvoAlpha 深度分析

> LLM 驱动的 Qlib 表达式因子进化器 · 变异/交叉搜索 · 外部回测验证 · MongoDB 溯源
> 源码: `/root/source/docs/aaa/src/EvoAlpha/`
> 原始仓库: <https://github.com/AAAAndrews/EvoAlpha>

## 1. 为什么 EvoAlpha 重要

EvoAlpha 解决的不是“再训练一个预测模型”，而是把因子研究中最耗人工的假设生成环节变成可迭代的搜索闭环：从一批可解释的 Qlib 表达式种子出发，让具有不同研究偏好的 LLM 生成候选，再用独立评估服务筛掉无效表达式，把通过者作为下一轮的高分种子。`README.md` 将其准确概括为 “Quant Factor Multi-Agent Search”。

量化因子搜索同时受三个约束：表达式必须能被计算引擎解析，经济或统计意义必须能由研究者复核，样本内指标也必须经过明确阈值。EvoAlpha 将这三层拆开：`SearcherAgent` 只负责提出 Qlib DSL 候选；`quality_check_fn` 负责轻量语法/需求门槛；`Validator` 通过外部因子评估 API 取得指标并做准入；`FactorRepository` 保存种子、结果和溯源。这样 LLM 的输出不是最终结论，而是可被计算和筛选的假设。

项目也刻意保持轻量：依赖只有 LangChain/OpenAI、PyMongo，实际回测或表达式执行并不在仓库内。`api/factor_eval_client.py` 假定本地已有 Factor Evaluation REST 服务（`/health`、`/check`、`/eval`、`/batch_eval`）。因此它适合作为因子发现的编排层，而不是完整的数据、回测与交易平台。

## 2. 高层组件

完整运行由两个 CLI 串起。先用 `apps/init_factors_from_json.py` 的 `load_factors_from_json()` 读取初始 JSON，将 `origin` 因子写入 MongoDB；再由 `apps/run_search.py` 读取种子、基线评估并调用 `Controller.run()`。

```text
origin_factors_sample.json
    -> init_factors_from_json.py / FactorRepository.insert_origin_factors()
    -> MongoDB factors(type=origin)
    -> run_search.py baseline_eval_and_update() / 按 IC 排序
    -> Controller.run() 多轮调度
        -> SearcherAgent（mutation 或 crossover；persona 驱动）
        -> default_quality_check() 或注入的质量服务
        -> Validator.validate() -> Factor Evaluation API
    -> MongoDB factors(type=search) + 下一轮高分 seed pool
    -> runs/.../raw、record 与 JSONL 审计日志
```

| 领域 | 实现 | 职责 |
|------|------|------|
| 任务与参数 | `factor_search/config.py` | `SearchTask` 描述市场、风格、期限、偏好/禁用算子；`ControllerConfig` 描述轮数、agent 数、配额、温度和 seed 上限。|
| 控制层 | `factor_search/controller.py` | 创建不同模式和人设的搜索器、切分每轮配额、去重、验证、更新演化池并持久化。|
| 生成层 | `factor_search/searcher_agent.py`、`prompts.py` | 以 `ChatOpenAI` 生成 Qlib 表达式，支持 mutation 与 crossover 两种操作。|
| 验证层 | `validator.py`、`api/factor_eval_client.py` | 批量请求外部评估，按 IC、Rank IC、ICIR 做硬阈值准入。|
| 存储与审计 | `db/mongo.py`、`run_logger.py`、`audit_log.py` | 保存因子文档、原始 prompt/回答、逐候选指标和轮次摘要。|

名称中的“multi-agent”表示有多个逻辑角色而非并发执行：`Controller.run()` 在 `for agent, quota in zip(...)` 中依次调用每个 `agent.search()`。这避免共享池的并发冲突，但一次 LLM 调用或评估失败会顺序拖慢本轮；不能把它误读成并行搜索器实现。

## 3. 核心实现细节

### 3.1 因子数据模型：origin 是不可改的起点，search 是可追溯的产物

`FactorRepository` 默认连接 `factor_search.factors`，并在 `ensure_indexes()` 创建唯一 `name`、`metrics.ic` 降序和 `type` 索引。`insert_origin_factors()` 以 `$setOnInsert` 幂等写入原始因子，故同名初始化不会覆盖已有数据；`data/origin_factors_sample.json` 的 `KMID`、`ROC`、`CORR`、`VSUMD` 等均是价格/成交量的 Qlib 风格表达式。

核心文档字段包括 `name`、`expression`、`type`（`origin` 或 `search`）、`meta`、`metrics`、`tags`、`provenance`、`created_at` 和 `updated_at`。`FactorCandidate` 额外在内存中保存 `reason`；搜索器为每个候选附加 `agent_id`、`mode`、`persona`、`round`、`attempt` 到 `provenance`，mutation 的 `meta.from` 或 crossover 的 `meta.from_A`/`meta.from_B` 则保存父因子信息。

需要按真实代码理解一个细节：`mongo.py` 的类注释仍展示 `operations` 字段，初始化脚本也会读取 JSON 的 `operations`，但 `insert_origin_factors()` 与 `store_search_results()` 实际写入的是 `meta`，不会持久化 `operations`。因此当前可依赖的血缘字段是 `meta`/`provenance`，不能假定 collection 中存在 `operations`。

### 3.2 Controller 的进化循环

`apps/run_search.py` 先只取 `include_search=False` 的原始因子，`baseline_eval_and_update()` 通过 `batch_evaluate_factors_via_api()` 填充内存中的 `metrics`，然后 `rank_by_ic()` 排序。这里的基线指标不会调用 `update_metrics_bulk()` 回写 MongoDB；数据库里的 origin metrics 是否更新取决于其他流程。

`Controller._spawn_searchers()` 按 `mutation_share` 计算 mutation 数量，剩余为 crossover，随机打乱模式；每个 `SearcherAgent` 从 `PERSONA_LIBRARY` 领取一个人设，如 `Volatility Whisperer`、`Liquidity Normalizer` 或 `Mean-Reversion Surgeon`。从第二轮开始，`_maybe_refresh_personas()` 可按 `persona_refresh_prob` 更换人设。

每轮核心逻辑是：

```python
seeds = select_seed_pool(self.pool, top_k=ctrl_cfg.seeds_top_k)
cands, report = agent.search(..., seeds=seeds, n_factors=quota, ...)
unique_candidates = self._dedup_candidates(round_candidates)
validation = self.validator.validate(candidates=unique_candidates, thresholds=thresholds)
self.repo.store_search_results(validation.accepted)
self.pool = rank_by_ic(dedup_by_expression(self.pool + validation.accepted))
```

配额由 `factors_per_round` 整除 `num_searchers` 后将余数依次分配。候选与池的去重都只移除表达式中的空白再比较，名称不同但表达式相同的候选会被视为同一个；池则被裁剪到 `seed_pool_size`。这使已通过验证的 search 因子能够进入后续轮次的 top-k 种子，形成基于 IC 的选择压力。

### 3.3 Searcher：受约束的 DSL 生成，不是自由文本问答

`SearcherAgent.search()` 同时构造系统提示和用户提示。系统提示复用 `build_mutation_prompt()` 或 `build_crossover_prompt()` 的规则；用户提示由 `_build_user_prompt()` 注入真实任务、种子及已有 `metrics`，并要求 JSONL。它限制输入变量为 `$close`、`$open`、`$high`、`$low`、`$volume`，要求避开用户禁用算子、保持括号/参数个数正确、对可能为零的分母加 `1e-12`，且与种子不完全相同。

Mutation 通过改窗口、算子或归一化方式保留已有信号核心；crossover 则组合两个因子的核心、归一化或门控子表达式。虽然 `prompts.py` 原始 builder 的示例写的是 JSON 数组，实际 `_build_user_prompt()` 明确要求 JSONL，`_parse_jsonl_or_array()` 先按行解析，失败后退回 `extract_json_array()`，因而能兼容两种模型输出。

每次模型调用后，候选要先经过注入的 `quality_check_fn`。默认的 `default_quality_check()` 只验证表达式非空、含 `$`、长度至少 10 且不含 `NaN`/`Inf`，其 docstring 明确说这是待替换的占位实现；它不校验完整 Qlib 语法、算子白名单或 look-ahead。若要生产使用，应将该函数替换为真正的 `/check` 调用或 DSL parser，而不是把 prompt 约束当作验证。

搜索器在达到 quota 前最多尝试 `max_retries` 次，并以 `1 / (1 + attempts / accepted)` 记录 `reliability_score`。`SearcherReport` 同时保存 accepted、retries、耗时和 calls-per-factor，便于评估某个人设/模式的生成成本。

### 3.4 Validator 与外部评估边界

`Validator.validate()` 将 `FactorCandidate` 转为 `{name, expression}` 的有序列表，调用注入的 `evaluate_fn`。评估异常、短返回或无 `metrics` 时填零指标，保持候选和结果按位置一一对齐。其准入条件为：

```text
abs(ic) >= ic_min
abs(rank_ic) >= rank_ic_min
abs(icir) >= icir_min
```

因此负 IC、负 Rank IC、负 ICIR 只要绝对值达标也会被接受；这是源代码的绝对阈值语义，而非“只接受正向 alpha”。`winrate_min` 和 `stability_min` 虽在 `MetricThresholds` 中定义，相关判断在 `validator.py` 被注释，当前不参与淘汰。

`FactorEvalClient._request()` 对 HTTP 200 以外、连接失败和超时最多重试五次，等待时间线性增加。它提供 `check_factor()`、`evaluate_factor()`、`batch_evaluate_factors()`；后一方法的实现逐个 POST `/eval`，并没有调用 README 所列的 `/batch_eval`，所以“批量”仅表示返回列表和顺序保持。默认评估窗口为 CSI300、2023-01-01 至 2024-01-01、`close_return` 标签，CLI 可以改写这些参数。

### 3.5 可复现记录

`RunLogger` 为每个 round/searcher 写入两类 JSON：`raw/round_<r>/searcher_<id>.json` 保留 system prompt、user prompt、原始回答和调用耗时；`record/round_<r>/searcher_<id>.json` 保留带 metrics、accepted 标记的候选。`AuditLogger` 还以线程锁追加 JSONL 轮次摘要到 `FACTOR_SEARCH_LOG_DIR` 或 `./logs`。这三处记录把“为何生成、谁生成、是否通过、依据何种指标”连起来，足以支持一次实验的事后审计。

## 4. 对当前项目的价值

EvoAlpha 最值得吸收的是“受控生成—独立评估—反馈入池”的 contract。当前项目若已有 Qlib 数据和回测服务，可以将研究需求映射为 `SearchTask`，把可行表达式库作为 origin，把评估 API 接成 `evaluate_fn`，并把 `meta`/`provenance` 作为因子谱系的最小记录。`RunLogger` 的 prompt、原始输出、逐候选指标结构也可直接成为 LLM 量化研究的审计 artifact。

集成时必须补齐三项生产边界：第一，用真正的 DSL 编译/数据可用性检查替换 `default_quality_check()`；第二，明确指标方向、样本外切分、换手和稳定性规则，避免当前绝对 IC 阈值将反向信号无标记地混入；第三，为外部评估服务记录数据版本、股票池、标签定义和成本假设。EvoAlpha 的搜索逻辑能高效提出假设，但因子是否可交易仍由这些外部验证合同决定。
