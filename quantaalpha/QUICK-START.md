# QuantaAlpha 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/QuantaAlpha/QuantaAlpha.git
> 分析基线：
> - `QuantaAlpha`：commit `b7ceb27b1001261d7a95b209a963664ae1f8ab23`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/QuantaAlpha`
<!-- source-sync:end -->


> 多方向因子挖掘与演化 · parallel directions / AlphaAgentLoop / mutation / crossover / FactorLibrary
> 源码: `src/QuantaAlpha/`
> 原始仓库: <https://github.com/QuantaAlpha/QuantaAlpha>

## 1. 一句话定位

QuantaAlpha 是 AlphaAgent 思路的工程扩展版：先把一个研究方向拆成多条平行方向，再对每条方向跑“hypothesis -> factor construction -> code -> backtest -> feedback”，随后通过 mutation 和 crossover 继续演化优秀轨迹。

它最值得学的是“因子研究轨迹”的结构化管理：每轮 hypothesis、factor、backtest metrics、feedback、parent lineage 都被保存，可用于下一轮变异和交叉。

## 2. 核心工作流

```text
initial_direction
    -> generate_parallel_directions(n)
    -> original rounds per direction
        -> AlphaAgentLoop.factor_propose
        -> factor_construct
        -> factor_calculate
        -> factor_backtest
        -> feedback
        -> save factors to FactorLibrary
    -> EvolutionController
        -> mutation from latest trajectory
        -> crossover from selected parents
        -> repeat until max_rounds
```

## 3. 关键文件

| 文件 | 作用 |
|------|------|
| `quantaalpha/pipeline/planning.py` | LLM 生成平行研究方向，失败时 fallback |
| `quantaalpha/pipeline/loop.py` | AlphaAgentLoop 五步因子研究循环 |
| `quantaalpha/pipeline/evolution/controller.py` | original/mutation/crossover 调度器 |
| `quantaalpha/pipeline/evolution/trajectory.py` | StrategyTrajectory 与 TrajectoryPool |
| `quantaalpha/pipeline/evolution/mutation.py` | 从父轨迹生成正交探索提示 |
| `quantaalpha/pipeline/evolution/crossover.py` | 多父轨迹融合成 hybrid hypothesis |
| `quantaalpha/backtest/run_backtest.py` | 统一 backtest CLI，支持 alpha158/custom/combined |

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| Parallel directions | 初始方向拆成多个互补子方向 | 防止单一路径陷入局部最优 |
| Fallback planning | LLM JSON 失败时生成 deterministic directions | 研究系统不能因一次解析失败停摆 |
| AlphaAgentLoop | propose/construct/calculate/backtest/feedback 固定步骤 | 把因子发现变成可审计工作流 |
| Evolution metadata | phase、round、trajectory_id、parent_ids 注入 loop | 每个因子知道自己从哪里演化来 |
| FactorLibrary | 每轮 feedback 后自动写统一因子库 | 因子资产化，不丢在日志里 |
| TrajectoryPool | 按 direction/phase 索引轨迹 | 后续 mutation/crossover 可选父代 |
| MutationOperator | 生成 orthogonal new hypothesis | 不是微调阈值，而是探索不同信号维度 |
| CrossoverOperator | 融合多个 parent 的优势与弱点 | 因子研究可以做组合式创新 |
| Parent selection | best/random/weighted/top-percent-plus-random | evolution 的 exploration/exploitation 可配置 |

## 5. 对 HermesAlpha 的借鉴

1. **研究入口先做方向拆分**：把“新能源景气度”拆成资金、估值、供应链、波动 regime、业绩预期等平行方向。
2. **每个研究假设必须有轨迹 ID**：报告、因子、回测、反馈、父子关系统一入库。
3. **将 mutation 和 crossover 显式化**：mutation 用于探索正交信号，crossover 用于融合已验证的 thesis。
4. **统一 FactorLibrary**：所有候选因子写入同一库，带 experiment_id、round、phase、parent_ids。
5. **质量门控可开关**：consistency、complexity、redundancy 分开配置，方便不同阶段使用不同严苛度。

## 6. 对 ashare-audit 的借鉴

1. **审计因子血缘**：每个因子是否有 trajectory_id、parent_ids、hypothesis、feedback。
2. **审计 mutation 是否正交**：新假设是否真的换了数据维度，而不是复述父策略。
3. **审计 crossover 是否继承弱点**：融合策略是否同时继承了多个父代的过拟合风险。
4. **审计 FactorLibrary 写入**：是否记录了 initial_direction、planning_direction、round_number、evolution_phase。

## 7. 不该照搬的部分

- evolution controller 很强，但生产版要加资源预算，避免方向数和轮数指数级膨胀。
- LLM 生成 mutation/crossover prompt 仍需要审计，否则可能产生同质化探索。
- FactorLibrary 是核心资产，必须加 schema version、数据口径、回测窗口和去重规则。
- 并行执行要小心共享文件和环境变量，例如 `FACTOR_LIBRARY_SUFFIX` 这种全局开关在多租户下要隔离。

## 8. 结论

QuantaAlpha 的价值在于把“因子挖掘”升级成“可演化的研究轨迹系统”。它比单轮 AlphaAgent 多了方向规划、轨迹池、mutation/crossover 和因子库血缘，对构建 A 股 Alpha 工厂很有借鉴价值。
