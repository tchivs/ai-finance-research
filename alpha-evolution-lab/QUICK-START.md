# Alpha Evolution Lab 快速概览

> alphaevo + AlphaAgentEvo + EvoAlpha · 自进化策略/因子研究工厂 · mutation / reward / controller
> 源码: `/root/source/tmp/alphaevo/`, `/root/source/tmp/AlphaAgentEvo/`, `/root/source/tmp/EvoAlpha/`
> 原始仓库: [alphaevo](https://github.com/ZhuLinsen/alphaevo) · [AlphaAgentEvo](https://github.com/hongha5192-bit/AlphaAgentEvo) · [EvoAlpha](https://github.com/AAAAndrews/EvoAlpha)

## 1. 一句话定位

这一条目合并三个“Alpha 自进化”项目：

| 项目 | 定位 |
|------|------|
| `alphaevo` | 把可读 YAML 策略变成 backtest -> diagnose -> mutate -> retest -> champion 的研究循环 |
| `AlphaAgentEvo` | 面向因子进化训练的 GRPO/奖励函数样板，强调 multi-turn tool calling 和层级 reward |
| `EvoAlpha` | 多 searcher agent 的因子搜索控制器，MongoDB 因子库，round 级日志和验证 |

它们共同提供一个模式：Alpha 不是一次生成出来的，而是在受控评估、失败诊断、突变、筛选和轨迹沉淀中演化出来的。

## 2. 三类进化循环

### alphaevo: 策略进化

```text
YAML strategy
    -> sample stocks
    -> fetch data
    -> backtest
    -> evaluate confidence + anti-overfit
    -> research committee review
    -> LLM/param/hybrid mutation
    -> save new version
    -> repeat
```

### AlphaAgentEvo: 因子训练奖励

```text
seed factor
    -> LLM multi-turn tool calls
    -> evaluate factors
    -> trajectory_results
    -> hierarchical reward
    -> GRPO training
```

### EvoAlpha: 多搜索器因子搜索

```text
seed pool
    -> spawn mutation/crossover searchers with personas
    -> generate candidates
    -> deduplicate
    -> validate by metrics threshold
    -> accepted factors upsert to DB
    -> update seed pool
    -> next round
```

## 3. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| Strategy YAML DSL | 策略可读、可 diff、可被 LLM 修改 | 策略研究资产化，不藏在代码里 |
| RunPipeline | strategy -> sample -> fetch -> context -> backtest -> evaluate -> report | 每次研究都有固定流水线 |
| Evaluator | win rate、avg return、drawdown、Sharpe、consistency、sensitivity、signal count | 评价不只看收益，还看稳健性 |
| ResearchCommittee | technical/risk/overfit/data-quality/mutation-planning verdicts | 用确定性委员会先挡住坏候选 |
| StrategyMutator | mutation 有 max_changes 和 complexity_limit | LLM 改策略必须受控 |
| Trajectory flywheel | 导出 state -> diagnosis -> hypothesis -> change -> outcome | 进化过程本身可用于训练下一代 Agent |
| Reward Eq.5 | tool success、consistency、exploration、performance、streak 分层组合 | 训练 Agent 时奖励不只看最终收益 |
| Multi-searcher controller | 多 persona、多轮、mutation/crossover、验证入库 | 因子搜索可以像进化算法一样组织 |

## 4. 对 HermesAlpha 的借鉴

1. **把策略/信号变成资产**：每个策略有 YAML、版本、parent_id、evaluation、research log。
2. **LLM 只提出受控 mutation**：修改 entry/exit/stop/take-profit/threshold，不允许任意改代码。
3. **每轮必须 retest**：没有回测提升或稳健性失败就不能 promoted。
4. **保存失败**：被拒绝的 mutation 和原因同样重要，可形成经验库。
5. **构建 trajectory dataset**：把真实研究过程导出为 SFT/preference 数据。

## 5. 对 ashare-audit 的借鉴

1. 审计 mutation 是否超出 max_changes 和 complexity_limit。
2. 审计候选是否只 in-sample 变好，train-val/test gap 是否过大。
3. 审计 data-quality verdict 是否阻断了策略迭代。
4. 审计 LLM 提出的指标是否存在 registry，是否被 sandbox 验证。
5. 审计 reward 是否鼓励刷工具调用或重复相似因子。

## 6. 不该照搬的部分

- alphaevo 示例多以 yfinance/akshare 为默认数据，生产 A 股需要统一数据底座和交易约束。
- LLM mutation 不能替代严谨实验设计，必须有 walk-forward、CPCV、成本和流动性约束。
- AlphaAgentEvo 的 reward 依赖 backtest API，训练前要确保 API 结果稳定且无未来函数。
- EvoAlpha 的 MongoDB 因子库是实现选择，不一定要照搬；关键是 accepted/rejected/round logs。

## 7. 最小迁移方案

```text
1. Strategy/Factor asset model
   id, version, parent_id, DSL/YAML, metadata

2. Evaluation pipeline
   sample -> data -> backtest/eval -> report

3. Mutation contract
   allowed targets, max_changes, complexity_limit

4. Promotion gate
   score_delta, signal_count, train_val_gap, val_test_gap, data_quality

5. Trajectory store
   before state, diagnosis, proposed change, result, accepted/rejected reason
```

## 8. 结论

Alpha Evolution Lab 的关键价值是把“AI 生成策略/因子”升级为“AI 迭代研究资产”。它强调受控突变、真实回测、稳健性门控、失败沉淀和训练数据飞轮，适合作为当前项目的 Alpha 工厂蓝图。
