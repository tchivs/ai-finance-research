# QuantaAlpha 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/QuantaAlpha/QuantaAlpha.git
> 分析基线：
> - `QuantaAlpha`：commit `b7ceb27b1001261d7a95b209a963664ae1f8ab23`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/QuantaAlpha`
<!-- source-sync:end -->


> parallel planning · AlphaAgentLoop · trajectory pool · mutation/crossover evolution · factor library
> 源码: `src/QuantaAlpha/`
> 原始仓库: <https://github.com/QuantaAlpha/QuantaAlpha>

## 1. 架构定位

QuantaAlpha 可以看成 AlphaAgent 的演化控制层：AlphaAgent 解决“一个方向下如何生成因子并回测”，QuantaAlpha 进一步解决“如何同时探索多个方向，并在结果基础上持续 mutation/crossover”。

核心对象：

```text
Planning
    generate_parallel_directions()

Research loop
    AlphaAgentLoop

Evolution
    EvolutionController
    StrategyTrajectory
    TrajectoryPool
    MutationOperator
    CrossoverOperator

Backtest
    BacktestRunner / FactorLoader

Asset store
    FactorLibraryManager
```

## 2. Planning: 从一个方向到多个方向

`planning.py` 的 `generate_parallel_directions()` 接收：

```text
initial_direction
n
prompt_file
max_attempts
use_llm
allow_fallback
```

它先读取 YAML prompt，让 LLM 输出：

```json
{"directions": ["...", "..."]}
```

然后用 `_parse_directions()` 从 fenced JSON 或混杂文本中抽取 JSON。如果多次失败，则用 `_fallback_directions()` 生成 deterministic 子方向，例如：

```text
base + short-term momentum signal with volume confirmation
base + volatility regime switch using rolling variance
base + liquidity/turnover adjustment for noise reduction
base + cross-sectional rank with sector-neutralization
```

这个 fallback 很实用：研究系统可以降级继续跑，不会因为 LLM 格式失败中断整批实验。

## 3. AlphaAgentLoop 五步链路

`loop.py` 的 `AlphaAgentLoop` 继承 `LoopBase`，主要步骤是：

| 步骤 | 方法 | 产物 |
|------|------|------|
| 假设生成 | `factor_propose()` | hypothesis / idea |
| 因子构造 | `factor_construct()` | factor sub_tasks |
| 因子计算 | `factor_calculate()` | generated workspace/code |
| 因子回测 | `factor_backtest()` | experiment/backtest result |
| 反馈总结 | `feedback()` | feedback + trace hist + factor library |

初始化时注入 evolution 元数据：

```text
strategy_suffix
trajectory_id
parent_trajectory_ids
round_idx
quality_gate_config
```

这保证每轮因子挖掘都能追溯到方向、阶段、父代和轮次。

## 4. FactorLibrary 写入

`feedback()` 中有一个非常重要的动作：自动把实验因子写到统一库。

写入字段包括：

```text
experiment
experiment_id
round_number
hypothesis
feedback
initial_direction
user_initial_direction
planning_direction
trajectory_id
parent_trajectory_ids
```

这比只保存 backtest CSV 更有价值。未来要做因子检索、复现、审计、去重、组合，都依赖这些 metadata。

## 5. Trajectory model

`StrategyTrajectory` 表示一次完整探索：

```text
trajectory_id
round_idx
phase: original / mutation / crossover
hypothesis
hypothesis_details
factors
backtest_result
backtest_metrics
feedback
feedback_details
parent_ids
created_at
extra_info
```

它的 `get_primary_metric()` 默认取 `RankIC`，`is_successful()` 要求 RankIC > 0。

`to_summary_text()` 会压缩 hypothesis、前 5 个 factor、metrics 和 feedback，用于 mutation/crossover prompt。

## 6. TrajectoryPool

`TrajectoryPool` 管理所有轨迹：

```text
_trajectories: id -> trajectory
_by_direction: direction -> ids
_by_phase: phase -> ids
```

支持：

| 方法 | 作用 |
|------|------|
| `add()` | 加入并持久化轨迹 |
| `get_by_direction()` | 找同一方向轨迹 |
| `get_by_phase()` | 找 original/mutation/crossover |
| `select_parents_for_mutation()` | 取同方向最新轨迹 |
| `select_parents_for_crossover()` | 按 best/weighted/random 选父代组合 |

这个池子是 evolution 的核心状态。

## 7. EvolutionController

`EvolutionController` 维护：

```text
current_round
current_phase
directions_completed
active_branch_count
mutation_targets
crossover_groups
```

配置项包括：

```text
num_directions
max_rounds
mutation_enabled
crossover_enabled
crossover_size
crossover_n
prefer_diverse_crossover
parent_selection_strategy
parallel_enabled
fresh_start
```

### 7.1 阶段流转

```text
ORIGINAL
    all directions completed
    -> MUTATION if enabled
    -> CROSSOVER if mutation disabled and crossover enabled

MUTATION
    mutate each target
    -> CROSSOVER if enabled
    -> MUTATION again if crossover disabled

CROSSOVER
    run each crossover group
    -> MUTATION if enabled
    -> CROSSOVER again if mutation disabled
```

### 7.2 并行任务接口

`get_all_tasks_for_current_phase()` 会一次性返回当前阶段所有可并行任务。每个 task 包含：

```text
phase
parent_trajectories
strategy_suffix
round_idx
```

这很适合后续接 task queue 或 distributed runner。

## 8. MutationOperator

Mutation 的目标不是小修，而是“orthogonal exploration”。Prompt 输入包括：

```text
parent_hypothesis
parent_factors
parent_metrics
parent_feedback
```

输出字段：

```text
new_hypothesis
exploration_direction
orthogonality_reason
expected_characteristics
```

若 LLM 失败，会按父假设关键词 fallback：momentum -> mean reversion，mean reversion -> trend following，volume -> price patterns，volatility -> liquidity。

这个 fallback 虽简单，但提供了重要原则：mutation 应尽量换数据维度和市场机制。

## 9. CrossoverOperator

Crossover 输入多个 parent trajectory，格式化每个父代的：

```text
phase
hypothesis
factors
metrics
feedback
```

输出字段：

```text
hybrid_hypothesis
fusion_logic
innovation_points
expected_benefits
parent_ids
```

提示词强调：融合优势、避免共同弱点、寻找协同效应。

## 10. Backtest CLI

`backtest/run_backtest.py` 提供统一入口：

```text
--config
--factor-source alpha158 | alpha158_20 | alpha360 | custom | combined
--factor-json repeatable
--experiment
--dry-run
--skip-uncached
```

这说明 QuantaAlpha 把“LLM 生成因子”和“标准 Qlib 因子/自定义因子回测”放到同一 backtest runner 下，便于横向比较。

## 11. 当前项目迁移方案

### 11.1 Alpha 工厂

```text
User research theme
    -> planning directions
    -> original trajectories
    -> factor library
    -> mutation/crossover rounds
    -> trajectory pool
    -> promotion gate
```

每个候选因子必须带：

```text
factor_id
expression
hypothesis
direction_id
phase
round_idx
parent_ids
metrics
feedback
universe
```

### 11.2 审计规则

| 审计对象 | 问题 |
|----------|------|
| direction planning | 是否多样化，还是同义改写 |
| mutation | 是否真的正交 |
| crossover | 是否记录所有 parent |
| factor library | 是否有完整 metadata |
| backtest | 是否同口径比较 alpha158/custom/combined |
| trajectory pool | 是否可复现每一代 |

## 12. 风险和限制

- LLM 生成 JSON 仍然脆弱，生产版要用 schema retry 或 function calling。
- Mutation/crossover 可能生成漂亮但不可计算的研究方向，需要因子 DSL 或表达式校验层约束。
- `RankIC > 0` 作为成功判断太粗，A 股生产需要 ICIR、换手、容量、行业中性、稳定性等多门控。
- 并行 execution 要加 artifact 隔离，避免多个 task 同时写同一个 factor library。

## 13. 结论

QuantaAlpha 的核心贡献是把因子研究从单轮 Agent 任务提升为带血缘的演化系统。它给当前项目的启发是：Alpha 不是一次生成出来的，而是在方向规划、轨迹记录、正交突变、父代融合、统一回测和因子资产化中逐步形成的。
