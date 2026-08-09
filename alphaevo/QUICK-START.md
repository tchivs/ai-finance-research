# AlphaEvo 快速概览

> ZhuLinsen · 可追溯的量化策略与因子进化研究系统 · Python / Typer / Pydantic / pandas / SQLite / 可选 LiteLLM
> 源码: `/root/source/docs/aaa/src/alphaevo/`
> 原始仓库: <https://github.com/ZhuLinsen/alphaevo>

## 1. 一句话定位

AlphaEvo 把可读的 YAML 股票策略变成“抽样—回测—评估—反思—变异—复测”的研究循环：LLM 负责提出受限的策略或因子假设，历史数据和统计门槛负责决定哪些版本可以留下。它是策略研究资产的进化器，不是直接给出交易建议的预测服务。

## 2. AlphaEvo 覆盖的链路

```text
自然语言观点 / 内置 YAML 策略
    -> Strategy DSL（触发器、硬过滤、退出、可调参数）
    -> DataManager 多适配器 + AdaptiveSampler 市场/样本选择
    -> BacktestEngine 逐标的、逐日信号模拟
       （入场时机、滑点、手续费、止损/止盈冲突）
    -> Evaluator 收益/风险/分状态/过拟合诊断
    -> ReflectionAnalyzer：失败归因 + 多个候选实验
    -> SelfCritic + StrategyMutator：审核、有限变异、版本血缘
    -> 同批数据筛选/复测 -> champion、Markdown 报告、研究日志、trajectory

反思无可用修改
    -> AlphaFactory：LLM 因子假设 -> AST/子进程沙箱
       -> IC/IR/月度胜率/换手/相关性验证 -> 动态指标注册 -> 策略复测
```

项目安装入口为 `alphaevo = "alphaevo.cli.main:app"`。`alphaevo run` 跑单次研究，`optimize` 搜索 `params.tunable`，`evolve` 执行多轮进化；还提供 `evolve-islands` 和 `evolve-curriculum`。`showcase` 使用仓库内固定 yfinance 快照，适合作为无密钥的可重复演示；真实数据路径须安装相应数据适配器 extra。

## 3. 核心模块

| 模块 | 作用 | 对当前项目的价值 |
|------|------|------------------|
| `cli/main.py`、`cli/commands/` | Typer 命令入口，挂接运行、优化、进化、因子发现和策略子命令。 | 用 CLI 统一实验协议，避免研究过程散落在 notebook。 |
| `models/strategy.py`、`strategy/dsl/`、`strategy/store.py` | Pydantic `Strategy` 契约和 YAML 解析/序列化/存储；根目录 `strategies/builtin/` 有 7 个模板。 | 把观点、规则、版本和父子关系保存为可审计资产。 |
| `data/`、`sampler/`、`orchestrator/pipeline.py` | `DataManager` 组合适配器和缓存；`AdaptiveSampler` 选样；`RunPipeline.run()` 串起取数、回测、评估和报告，并在信号不足时扩样。 | 把数据健康与样本量放在进化前，而不是事后修饰收益。 |
| `backtest/engine.py` | `BacktestEngine` 逐日模拟，默认 0.1% 滑点、0.03% 手续费；处理入场、ATR/百分比/跟踪止损、止盈和同 K 线冲突。 | 建立最小可复跑的交易级验证层；实际市场规则仍需本地化。 |
| `evaluator/metrics.py`、`optimizer/` | `Evaluator` 计算胜率、收益、回撤、Sharpe、信号数、walk-forward、CPCV 等；`ParamOptimizer` 在同一数据上做有界调参。 | 用稳健性和复杂度惩罚约束参数搜索，避免只挑最高历史收益。 |
| `orchestrator/evolution.py`、`reflection/` | `EvolutionPipeline` 调用 `ReflectionAnalyzer`、`SelfCritic`、`StrategyMutator`，筛选候选变异、记录经验并选出 `champion_id`。 | 将 LLM 定位为可验证假设生成器；每次修改都有理由、结果和回退路径。 |
| `alpha_factory/` | `AlphaFactory` 生成因子、`FactorSandbox` 静态检查并子进程运行、`FactorValidator` 以 IC/IR/月胜率/换手/相关性筛选，再注册到 `IndicatorRegistry`。 | 新因子必须先安全执行、统计合格、再进入策略测试，不能把生成代码直接投入回测。 |
| `research_log/`、`scripts/`、`examples/`、`sources/` | 记录研究日志和 JSON/JSONL 轨迹；`scripts/experiments/` 提供基准、消融和进化实验；`examples/` 是 showcase 数据；`sources/` 为视觉素材。 | 形成可复现证据链；明确资源文件与运行逻辑的边界。 |

借鉴重点：把策略和因子作为带版本、数据切片、成交假设和统计检验的实验对象；事件类链路仍不完整。