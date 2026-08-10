# Alpha Evolution Lab 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/hongha5192-bit/AlphaAgentEvo.git
> 分析基线：
> - `AlphaAgentEvo`：commit `4e69a98e5205af1657dd6782ca0af62994d73b78`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/AlphaAgentEvo`
<!-- source-sync:end -->


> 策略 YAML DSL · RunPipeline · EvolutionPipeline · ResearchCommittee · 因子 reward · multi-searcher controller
> 源码: `src/alphaevo/`, `src/AlphaAgentEvo/`, `src/EvoAlpha/`
> 原始仓库: [alphaevo](https://github.com/ZhuLinsen/alphaevo) · [AlphaAgentEvo](https://github.com/hongha5192-bit/AlphaAgentEvo) · [EvoAlpha](https://github.com/AAAAndrews/EvoAlpha)

## 1. 合并视角

三个项目分别覆盖 Alpha 进化系统的不同层次：

| 层次 | 项目 | 核心问题 |
|------|------|----------|
| 策略产品层 | alphaevo | 如何把一条策略持续诊断、突变、回测、筛选成 champion |
| Agent 训练层 | AlphaAgentEvo | 如何奖励 LLM 在工具交互中产生更好的因子 |
| 搜索控制层 | EvoAlpha | 如何组织多个 searcher agent 多轮产生、验证、入库因子 |

合并后的模式是：

```text
Research assets
    strategy YAML / factor DSL

Evaluation engine
    backtest / IC / robustness / data quality

Evolution operators
    mutate / crossover / param search / LLM proposal

Promotion gates
    score, signal count, overfit, data quality, complexity

Memory flywheel
    trajectory, failures, accepted candidates, lessons
```

## 2. alphaevo RunPipeline

`alphaevo/orchestrator/pipeline.py` 的 `RunPipeline` 负责单次策略研究流水线：

```text
load strategy
fetch stock universe
adaptive sampling
fetch historical data
build market/indicator contexts
backtest
evaluate
save evaluation
write report
```

### 2.1 Adaptive sampling

如果信号太少，pipeline 会自动扩大样本：

```text
attempt 1: requested max_symbols / method / date_range
if signal_count < target:
    expand max_symbols
    maybe change sampling method
    maybe expand date range
repeat until accepted or max expansions
```

这解决了策略研究中的常见问题：一个策略可能不是坏，只是在当前样本没有足够信号。系统先扩大样本，再决定是否拒绝。

### 2.2 DataManager 与 adapter chain

RunPipeline 通过 `get_adapter_chain()` 创建数据源链，并可插入 Adanos sentiment adapter。README 还说明支持 yfinance、akshare、daily_stock_analysis plugin。

这与当前项目的数据层设计一致：策略引擎不应直接依赖某一个数据 API，而应通过 adapter chain 获取标准 market/context 数据。

## 3. alphaevo Evaluator

`Evaluator` 计算：

```text
OverallMetrics
RegimeMetrics
SectorMetrics
AntiFitMetrics
WalkForwardFoldMetrics
RegimeHoldoutMetrics
CPCVMetrics
Benchmark comparison
Stress windows
Event context metrics
```

### 3.1 Confidence score

公式：

```text
0.25 * win_rate
+ 0.15 * avg_return
+ 0.15 * profit_loss_ratio
+ 0.15 * drawdown_score
+ 0.10 * sharpe_score
+ 0.10 * consistency
+ 0.10 * sensitivity
- overfit_penalty
- complexity_penalty
```

再乘以 signal_count reliability：

| signal_count | 处理 |
|--------------|------|
| < 10 | reliability = 0.3，score hard cap 0.15 |
| 10-30 | reliability 至少 0.5，随数量提升 |
| >= 30 | full reliability |

这个机制非常实用：防止一个只出现 3 次、碰巧全赢的策略排到榜首。

### 3.2 Anti-overfit

Evaluator 检查 train_val_gap、val_test_gap、walk_forward_gap、walk_forward_pass_rate、yearly consistency、parameter sensitivity。README 中也明确把“诚实失败”作为产品故事：候选 in-sample 改善但泛化差时应被阻止。

## 4. ResearchCommittee

`ResearchCommittee.review()` 运行五类确定性 verdict：

```text
technical_verdict
risk_verdict
overfit_verdict
mutation_planner_verdict
```

如果任一 verdict fail，则 overall fail；任一 watch，则 overall watch；否则 pass。

它的 thesis 很直接：

```text
Promote only evidence-backed mutations;
reject prettier output if the retest does not improve the measured strategy.
```

这句话适合作为当前项目 Alpha 工厂的原则：LLM 生成的解释再漂亮，也必须服从 retest 和门控。

## 5. StrategyMutator

`StrategyMutator` 是 LLM mutation 的安全边界。

### 5.1 Guardrails

```text
max_changes: 每轮最多修改数量
complexity_limit: entry 条件最多数量
atomic: 是否要求整组修改全部成功
```

如果超过 max_changes，非 atomic 模式会截断；如果复杂度超限，会 trim entry rules；如果没有任何修改成功，抛 `MutationError`。

### 5.2 Mutation targets

支持的 change handlers：

| Handler | 行为 |
|---------|------|
| tighten_filter / loosen_filter | 调整条件阈值 |
| add_condition | 添加 entry condition，先检查 IndicatorRegistry |
| remove_condition | 按 indicator 删除条件 |
| adjust_exit | 修改 stop_loss、take_profit、max_holding_days |
| change_universe | 修改 universe |
| change_logic | entry logic 在 and/or 间切换 |
| discover_factor | 添加已注册的新因子 |

LLM 常见输出问题也被处理：`_sanitize_condition_value()` 会把 `"< 65.0"`、`">= 1.5"`、`"true"` 转成干净的数值/布尔。

## 6. EvolutionPipeline

`EvolutionPipeline` 组织多轮演化：

```text
for round in rounds:
    run current strategy
    compute score and gates
    assess market hypothesis
    data quality gate
    record pending experience outcome
    reflect / choose method
    generate mutation candidates
    screen candidates
    save improved strategy
    update champion
    collect trajectory
```

它维护：

```text
ExperienceStore
MetaLearner
PatternLibrary
SelfCritic
PlaybookStore
ResearchLogger
ContextBuilder
TrajectoryCollector
```

这说明 alphaevo 不只是一个 optimizer，而是一个能沉淀经验的研究系统。

## 7. Trajectory data flywheel

README 明确说每次真实 evolution run 可导出：

```text
trajectory.jsonl: state -> diagnosis -> hypothesis -> change -> outcome
sharegpt.jsonl: SFT-style conversations
preference.jsonl: improved vs non-improved steps
```

这对当前项目很重要。真实金融研究过程本身就是训练数据：哪些诊断有效、哪些 mutation 被拒绝、哪些指标导致过拟合，都可以训练下一代研究 Agent。

## 8. AlphaAgentEvo reward

`AlphaAgentEvo/training/factor_tool.py` 实现论文式层级 reward：

```text
R(τ) = [min(R_cons, C_cons) + min(R_expl, C_expl)] / min(R_tool, C_tool)
       + min(R_perf, C_perf) * min(R_streak, C_streak)
```

组件：

| Reward | 含义 |
|--------|------|
| R_tool | 成功工具调用奖励，失败工具调用惩罚 |
| R_cons | 与 seed factor 有一定结构相似，保持方向一致 |
| R_expl | 与前序候选不太相似，鼓励探索 |
| R_perf | best factor IR 相对 seed IR 的 softplus 提升 |
| R_streak | 多次刷新 best_so_far 的突破次数 |

关键细节：

- AST similarity 使用最大公共子树大小除以最大 AST 节点数。
- `R_TOOL_FLOOR = 0.01` 防止 denominator 为 0。
- 没有成功评估时直接 reward 0。

这比“只看最终 IR”更合理，因为它同时惩罚乱调用工具、奖励适度继承 seed 思路、鼓励探索和连续改进。

## 9. EvoAlpha Controller

`EvoAlpha/factor_search/controller.py` 是多 searcher 控制器。

### 9.1 Searcher spawn

```text
num_searchers
mutation_share -> mutation vs crossover modes
random_persona
SearcherAgent(mode, persona, model, temperature, quality_check_fn)
```

### 9.2 Round loop

每轮：

```text
maybe refresh personas
select seed pool by top_k
allocate factor quota per searcher
run each searcher
deduplicate candidates
validate candidates by thresholds
store accepted to MongoDB
extend and rerank seed pool
write per-agent factor records
write round summary audit event
```

这个结构适合做 Alpha 工厂的“搜索平面”：多个 Agent 不同 persona/mode 并行探索，然后由统一 validator 决定谁能入库。

## 10. 当前项目架构建议

### 10.1 ResearchAsset

```text
id
type: strategy / factor / signal_model
version
parent_id
source: llm / human / mutation / crossover / imported
body: YAML or DSL
metadata
created_at
```

### 10.2 EvaluationReport

```text
asset_id
data_version
sample_protocol
metrics
anti_overfit
data_quality
benchmark
cost_model
failure_cases
verdicts
```

### 10.3 MutationProposal

```text
target
change_type
from_value
to_value
rationale
expected_effect
risk
```

### 10.4 Promotion Gate

```text
parse_ok
backtest_ok
score_delta > threshold
signal_count >= min
train_val_gap <= max
val_test_gap <= max
data_quality not block
complexity <= limit
cost-adjusted positive
```

## 11. 审计规则

| 审计项 | 检查 |
|--------|------|
| Mutation scope | 每轮修改是否超过 max_changes |
| Indicator registry | 新指标/因子是否已注册并验证 |
| Complexity | entry 条件是否过多 |
| Data quality gate | 数据问题是否阻断了策略进化 |
| Overfit gate | 是否只 in-sample 提升 |
| Promotion trace | champion 是否真来自最高合格 score |
| Reward hacking | Agent 是否通过大量相似/失败工具调用刷 reward |
| Seed pool | accepted/rejected 因子是否完整记录 |

## 12. 与其他项目组合

| 组合 | 用法 |
|------|------|
| AlphaAgent + alphaevo | AlphaAgent 发现因子，alphaevo 把因子放进策略条件回测 |
| Qlib + alphaevo | Qlib 提供更成熟的 backtest/record，alphaevo 提供 mutation loop |
| RD-Agent + AlphaAgentEvo | RD-Agent 的 experiment loop 可替换为 multi-turn factor tools 和 reward |
| TradingAgents + alphaevo | TradingAgents 负责研究诊断，alphaevo 负责策略改动和验证 |
| a-share-watch-butler + alphaevo | 定期盯盘发现失败策略，触发离线演化任务 |

## 13. 风险和限制

- 回测得分很容易被过拟合，必须默认启用 walk-forward、CPCV、成本、滑点和样本外测试。
- LLM mutation 需要严格 registry，否则会发明不存在的指标。
- 进化系统会产生大量失败候选，需要存储和检索策略，否则会重复犯错。
- Reward 函数本身也要审计，避免鼓励“和 seed 足够像但没有真实增益”的候选。
- A 股策略还要加入涨跌停、停牌、ST、T+1、流动性约束。

## 14. 结论

Alpha Evolution Lab 是“AI 研究循环”的第三种形态：不是一次生成报告，也不是一次生成因子，而是持续演化研究资产。它把策略/因子表达、评估、突变、门控、日志和训练数据飞轮串起来。当前项目若要做长期自进化投研系统，应优先吸收它的 ResearchAsset、EvaluationReport、MutationProposal、PromotionGate 和 TrajectoryStore 这五个 contract。
