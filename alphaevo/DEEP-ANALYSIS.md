# AlphaEvo 深度分析

> 可追溯的量化策略/因子进化研究系统 · YAML DSL、LLM 反思、统计验证与历史回测
> 源码: `/root/source/docs/aaa/src/alphaevo/`
> 原始仓库: <https://github.com/ZhuLinsen/alphaevo>

## 1. 为什么 AlphaEvo 重要

AlphaEvo 的定位不是预测下一根 K 线，而是把一个可读的交易假设持续变成可检验的研究资产。策略以 YAML 表达入场触发器、硬过滤、退出、止损止盈和可调参数；系统从真实或固定快照的 OHLCV 数据中抽样，生成交易级回测结果，按收益、风险、样本量与稳定性评分，再据失败案例提出有限、可执行的变异，最后只把通过复测的版本保留为候选冠军。README 概括该闭环为“backtest → diagnose → mutate → re-test → keep evidence”。

这填补了知识库中两类系统之间的空位。Qlib 更擅长数据—模型—预测—组合回测的通用基础设施；AlphaEvo 则把“策略规则本身也应被研究、评估和版本化”做成了研究循环。它适合承接自然语言投资观点、技术分析模板或已有 Alpha DSL：先固化成显式规则，再让每次改动都留下输入数据、评估、理由、版本血缘和输出报告。相较直接让 LLM 给出买卖结论，价值在于 LLM 的作用被约束为提出假设，而非替代验证。

项目当前最可信的范围仍是依赖 OHLCV 和基准上下文的趋势、反转类策略。`README.md` 明确将事件和轮动策略标为实验性：新闻、宏观和外部事件管线尚未完整接入，部分 L3 事件指标以价量代理替代。因此回测得分是研究筛选证据，不应被误读为可直接上线的收益承诺。

## 2. 高层组件

```text
Typer CLI / Python API
    -> RunPipeline: 载入策略 -> 抽样 -> 取数/上下文 -> 回测 -> 评估 -> 报告
    -> EvolutionPipeline: 反思 -> 审核 -> 变异/候选筛选 -> 下一轮/冠军
    -> ResearchLogger + TrajectoryCollector + SQLite stores

YAML Strategy DSL  <->  BacktestEngine / IndicatorRegistry  <->  Evaluator
                              ^                                      |
                              |                                      v
                         AlphaFactory <--- FactorSandbox <--- LLM 因子假设
```

| 领域 | 关键模块 |
|------|----------|
| 入口与配置 | `src/alphaevo/cli/main.py` 注册 `run`、`optimize`、`evolve`、`evolve-islands`、`evolve-curriculum`、`strategy` 与 `factor`；`core/config.py` 集中配置；`pyproject.toml` 的 `alphaevo = "alphaevo.cli.main:app"` 是安装后入口。 |
| 策略资产 | `models/strategy.py` 的 `Strategy`、`StrategyMeta`、`StrategyEntry`、`StrategyExit` 是 Pydantic 契约；`strategy/dsl/` 负责 YAML 解析/序列化，`strategy/store.py` 管理版本和评估。根目录 `strategies/builtin/` 有 7 个内置模板，`custom/` 供用户策略，`research/` 保存研究版本。 |
| 数据与抽样 | `data/adapter.py` 的 `DataManager` 组合数据适配器、缓存与健康状态；`sampler/adaptive.py` 和 `sampler/regime.py` 按代表性、市场状态或策略范围选样本。`RunPipeline` 可在信号不足时扩大样本、切换抽样方式并延长窗口。 |
| 回测与指标 | `backtest/engine.py` 的 `BacktestEngine` 按标的逐日模拟；`condition.py`、`rules.py`、`indicators.py` 分别解释条件、市场规则和指标；`portfolio.py` 提供组合级回测。 |
| 评估与优化 | `evaluator/metrics.py` 的 `Evaluator` 产生收益/风险、分市场状态和分行业指标、过拟合诊断、walk-forward、CPCV 与基准对比；`optimizer/params.py` 的 `ParamOptimizer` 对 YAML 中标记为 `tunable` 的参数做有界搜索。 |
| 反思与进化 | `orchestrator/evolution.py` 的 `EvolutionPipeline` 统筹循环；`reflection/analyzer.py` 的 `ReflectionAnalyzer` 诊断并设计实验，`SelfCritic` 审查改动，`StrategyMutator` 原子地应用 `StrategyChange`。经验库、模式库、playbook 和轨迹分别在 `reflection/`、`strategy/library/`、`research_log/`。 |
| 因子发现 | `alpha_factory/factory.py` 的 `AlphaFactory` 串起假设生成、沙箱、统计验证、SQLite 存储和动态 `IndicatorRegistry` 注册；它把新因子纳入策略 DSL 可调用的指标集合。 |
| 项目资产 | `sources/` 仅放 Logo/SVG 与宣传图片，不参与运行；`examples/` 当前是 showcase 固定数据快照；`scripts/validate_real_data.py` 与 `scripts/experiments/run_repro_benchmark.py`、`run_ablation.py`、`run_evolution_experiment.py` 用于真实数据验证、可复现基准、消融和实验。 |

## 3. 核心实现细节

### 3.1 从 YAML 规则到交易信号

策略的 `entry.triggers` 是买点，`entry.guards` 是始终以 AND 组合的硬过滤；`exit.triggers` 是持仓期的显式卖出条件。`BacktestEngine.run()` 先检查 `IndicatorRegistry` 中是否存在策略所需指标，并为每个样本标的调用 `_run_symbol()`。该方法根据最长指标窗口计算 warm-up，空仓时检查市场规则、偏好市场状态和 `ConditionEvaluator.evaluate_entry()`；持仓时只检查退出，不会在同一时刻重复开仓。

成交假设不是被忽略的细节。构造器默认滑点 `0.001`、双边手续费 `0.0003`，`_open_position()` 支持 `next_open`、`close`、`breakout_high` 三种入场时机；`_close_position()` 对买卖分别计入滑点和佣金：

```python
net_entry = position.entry_price * (1 + self.commission)
net_exit = exit_price * (1 - self.commission)
return_pct = (net_exit - net_entry) / net_entry
```

`_check_exit()` 的优先级是最长持仓、止损、止盈、显式卖出触发器。百分比、ATR、从高点回撤、价格位和组合条件均可止损；止盈支持收益风险比、百分比、目标均线与移动止盈。若同一根 K 线同时命中止损与止盈，`_resolve_intrabar_conflict()` 按 `conservative`（默认先止损）、`optimistic` 或 `close_first` 处理，避免把不可观测的盘中路径默认为最优成交。

### 3.2 评估不是只看胜率

`RunPipeline.run()` 的实际顺序是：从 `StrategyStore` 读取策略，向 `DataManager` 获取股票池，令 `AdaptiveSampler.sample()` 生成 `SampleBatch`，拉取历史数据和指标上下文，调用回测和 `Evaluator`，保存 `EvaluationReport`，可选写 Markdown 报告。若信号数低于 `config.evolution.min_signal_count`，它会记录 `SamplingAttempt` 并扩样本后重跑；仍不足则让后续进化停止，而不是用偶然的小样本晋级。

`Evaluator.compute_metrics()` 从已平仓的 `TradeSignal` 计算胜率、平均/中位收益、盈亏比、最大回撤、Sharpe、连续亏损、总收益和平均持仓天数。`compute_confidence_score()` 将胜率、平均收益、盈亏比、回撤、Sharpe、一致性和参数敏感度归一化加权，扣除训练—验证/验证—测试差距和策略复杂度；少于 10 个信号时总分硬封顶 0.15，10—29 个信号降低可靠度。完整 `evaluate()` 还按时间切分、walk-forward、市场状态留出、CPCV、压力窗口与基准比较，向反思器暴露最差十笔交易而非只呈现赢家。

`ParamOptimizer.optimize()` 在一次取数/抽样结果上生成有限的参数候选，候选版本设置 `parent_id`、下一版本号和 `DRAFT` 状态；可用 `ThreadPoolExecutor` 并行回测。快速模式跳过重型诊断，排名靠前者可再全量评估；配置了稳健性门槛时，只有完成全量指标的候选能够通过相关门控。

### 3.3 受约束的策略进化

`EvolutionPipeline.evolve_async()` 每轮以 `RunPipeline.run()` 得到基线，然后读取数据质量、信号数、参数敏感度和 `Strategy.assess_market_hypothesis()`。满足继续条件时，`ContextBuilder` 汇集同家族经验、playbook、模式库和已有研究日志，`ReflectionAnalyzer` 按“两步”工作：先诊断根因和最弱市场状态，再产生多个彼此不同的 `CandidateExperiment`。其 prompt 规定每个实验最多 `max_changes` 个具体变更，且指标必须来自注册表。

候选并不直接落库。`SelfCritic.rank_candidates()` 排序，`SelfCritic.critique()` 删除不合规改动，`_filter_failed_repeated_changes()` 避免重试已失败的方向。`StrategyMutator.mutate(..., atomic=True)` 才会应用 `tighten_filter`、`loosen_filter`、`add_condition`、`remove_condition`、`adjust_exit`、`change_logic`、`discover_factor` 等 `ChangeType`；构造时的 `max_changes_per_round` 和 `complexity_limit` 限制单轮改动和规则复杂度。随后代码可在相同批次上预筛多个突变候选，仅把经过晋级护栏的更优版本作为下一轮输入。连续停滞、过拟合、数据质量阻断、样本不足或所有变异无效都会提前停止，并把最优 `champion_id`、分数、研究日志与 JSON/JSONL 轨迹保留下来。

### 3.4 从策略参数进化到新 Alpha

当常规反思没有可用改动时，`EvolutionPipeline._try_factor_discovery()` 才尝试 `AlphaFactory`。`FactorSynthesizer` 要求 LLM 只基于 OHLCV 写出 `def compute(df: pd.DataFrame, idx: int) -> float`，只允许向后看，不得使用文件、进程、动态导入或 `eval`。`FactorSandbox` 先做 AST 名称/dunder/未来数据访问检查，再以子进程和超时执行，限制的导入集合仅为 NumPy、pandas、math 及其别名。

`AlphaFactory.discover()` 的代码路径是 `generate()` → `_execute_factor_series()` → `FactorValidator.validate()` → `FactorStore.save()` → `register_factor_record()`。验证默认要求方向一致的 rank IC 至少 0.02、IR 至少 0.3、月度胜率至少 50%、换手不超过 0.8、与已有因子 rank 相关绝对值不超过 0.7；不合格因子记录原因，不进入动态指标注册表。通过者才可作为 `DISCOVER_FACTOR` 变异注入后续策略回测。这是“LLM 写代码”被安全性、统计显著性、冗余度和再次回测四重约束的关键。

## 4. 对当前项目的价值

1. **将观点变为可反驳的 DSL。** 借鉴 `Strategy`/YAML 契约，把 AI 研究结论拆成股票池、触发器、过滤条件、退出与成交假设；每个字段必须能被回测解释，而不是把自然语言直接当策略。
2. **把进化做成受控实验。** 采用 `EvaluationReport` + `StrategyChange` + `CandidateExperiment`：一次只改少量可定位字段，在同一数据切片上比较，并记录父版本、假设、批准/否决原因和失败经验。
3. **把过拟合与数据质量设为硬门。** 复用最小信号数、时间切分、walk-forward、复杂度惩罚、参数敏感度和数据质量阻断；排行榜与策略库应保存 canonical 数据快照、费用/滑点和评估协议，不能横向比较不同输入条件下的裸收益。
4. **因子发现须分层上线。** 可采用 `AlphaFactory` 的“LLM 提案—静态/运行沙箱—IC/IR/换手/相关性—注册—策略复测”链路。候选因子先是研究工件，只有跨样本、跨时期和组合回测仍稳健时才进入生产因子库。
5. **保留边界。** AlphaEvo 的回测以交易信号为中心，虽有 `PortfolioBacktester`，并非完整交易执行平台；事件类输入仍有代理指标。对 A 股或实盘系统还必须补齐复权、停牌、涨跌停、T+1、容量、行业成分与独立样本外验证。