# AlphaMaster 深度分析

> 强化学习公式搜索 · 注册式词表 · StackVM · walk-forward 多目标评分 · 实时信号
> 源码: `/root/source/tmp/AlphaMaster/`
> 原始仓库: <https://github.com/rosemarycox5334-debug/AlphaMaster>
> 研究基线: `3b8c86a`（2026-07-24，`1.2`）

## 1. 系统定位与真实边界

AlphaMaster 的主路径是“市场序列 -> 公式搜索 -> 因子 -> 连续仓位 -> 回测/信号”。其中 AlphaGPT 不是直接输出价格或交易动作，而是生成特征/算子 token；StackVM 将 token 解释成 `[N, T]` 因子张量；回测器据此筛选更好的公式。

```text
数据层
    Parquet / MT5 fetcher -> standard OHLCV tensors

公式层
    feature registry + operator registry -> deterministic vocabulary
    AlphaGPT -> constrained token sampler -> StackVM

评估层
    target return -> position -> costs -> walk-forward reward
    OOS / exposure / beta / correlation gates

产物层
    strategy JSON + checkpoint + history + backtest reports

服务层
    FastAPI training/backtest UI + closed-bar real-time watches
```

README 和历史文件会提到 MT5 下单，但当前 `strategy_manager/runner.py` 已明确说明 `execution.trader` 被移除。导入时的占位 `MT5Trader` 会在 `connect()`、`buy()`、`sell()` 等调用时抛出异常。因此本项目应被评估为研究、回测和信号监控工具，而不是自动执行引擎。

## 2. 数据契约与目标定义

### 2.1 单 Parquet 路径

`data_pipeline/parquet_manager.py` 是最容易复用的研究入口。

```text
{symbol}_{timeframe}.parquet
    -> parse_parquet_filename()
    -> inspect_parquet_file()
    -> ParquetDataManager.load()
    -> raw_dict: open/high/low/close/volume/time, each [1, T]
    -> MT5FeatureEngineer.compute_features()
    -> target_ret
```

加载器验证 `.parquet` 后缀、名称中的品种和周期、最小 bar 数及 OHLCV 列。它使用 `tick_volume` 时会规范化为 `volume`，排序并以最后一个值去除重复时间戳。对异常缩小的数值时间戳还提供乘以 1,000 的兼容分支。

目标并非 close-to-close 收益，而是：

```text
target_ret[n, t] = log(open[n, t + 2] / open[n, t + 1])
```

最后两个位置填零。这把每个 t 的因子与下一次可执行开盘后的收益关联起来。接入新数据源或改变执行时点时，必须先重新论证这一标签和实际成交时点是否一致。

### 2.2 多品种路径

`MT5DataManager` 加载多个品种后优先取时间戳交集，避免闭市时 forward-fill 制造重复 K 线；若交集少于 `Config.MIN_BARS`，才退化为并集加前向填充，并记录警告。

这条降级路径有明确的研究风险：前向填充可保持因果性，却仍可能把不同市场的休市和缺失报价变成零波动段。跨资产训练应把交集规模、各市场交易时段和填充比例作为实验元数据保存。

### 2.3 年化与成本

`estimate_periods_per_year()` 根据时间戳跨度与 bar 数估计年化周期数，而不是一律使用外汇 H1 的 6,240。训练侧默认成本率来自 `Config.COST_RATE=0.0003`；Web 回测的默认手续费 0.02% 与滑点 0.01% 也对应单边 0.0003。

成本口径已试图统一，但它仍只是模型化成本。点差、冲击、成交失败、隔夜利息、停牌/熔断和不同合约的成交量限制不在该核心公式中。

## 3. 公式资产：注册表、词表与 StackVM

### 3.1 确定性词表

`model_core/vocab.py` 从两个有序注册表派生词表：

```text
FEATURE_REGISTRY.feature_names
    + OPERATOR_REGISTRY.operator_names
    -> FormulaVocab.token_names
    -> VOCAB_VERSION = "v" + sha256(joined names)[:12]
```

feature token 位于 `[0, F-1]`，operator token 从 `F` 开始。项目在构建时检查段内和跨段名称唯一性；加载 checkpoint 或导入训练包时，`FORMULA_VOCAB.verify()` 会拒绝不一致版本。

这解决了公式 token 序列最危险的兼容性问题：只要特征或算子顺序改变，旧数字 token 就不能再静默解释为另一种公式。

### 3.2 StackVM 执行模型

`StackVM.execute()` 以逆波兰式栈语义处理 token：

```text
feature token -> push feat_tensor[:, feature_id, :]
operator token -> pop arity operands -> execute registered operator -> push result
end -> stack size must equal 1 -> normalize output
```

所有已注册算子都遵循 `[N, T] -> [N, T]` 契约，二元和三元算子还校验形状一致。执行过程中 NaN/Inf 会被规范化；未知 token、栈深不足、异常或结束时栈不为一都会使候选失效。

最终标准化的优先级是：多品种时按每个时间点做横截面 z-score；单品种时做 expanding 时序 z-score；然后截断到 `[-3, 3]`。单品种和多品种的统计语义不同，不能将两类策略评分直接比较。

### 3.3 因果性和结构约束

算子库对移动窗口、EMA、rank、correlation 等尽量采用历史窗口或递推实现。StackVM 还定义“恒正感染”检查：`TS_RANK`、`ABS` 等操作可能消灭符号，若随后持续使用保符号的平滑/汇总操作，因子可能退化为长期单边 beta 暴露。采样掩码会限制过长感染链，验证函数会报告末尾仍处于感染状态的公式。

该设计值得借鉴，但应理解其范围：它只能识别有限的结构性退化，不能证明因子中性、没有风格暴露或没有隐含未来信息。

## 4. 搜索与训练循环

`AlphaEngine.train()` 是核心搜索控制器。

### 4.1 受限公式生成

每一步由 `AlphaGPT` 为 token 位置生成 logits，`ConstrainedSampler` 根据当前栈深、剩余 token 数和感染状态生成合法掩码。采样最大长度由 `ModelConfig.MAX_FORMULA_LEN` 控制，默认 8。这样模型不会把大部分预算花在无法在 StackVM 上完成的序列上。

项目默认使用 CPU。配置文件中记录了其基准结论：当前公式评估由大量小张量与 Python 调度构成，GPU kernel 启动和线程并行反而更慢。这个结论依赖具体的公式长度、batch、CPU/GPU 和特征规模，迁移前应重新测量，不应当成通用规律。

### 4.2 候选评估

每条公式的评估顺序为：

```text
StackVM.execute(formula, features)
    -> reject None / near-constant output
    -> evaluate each rolling walk-forward fold
    -> apply IC direction gate
    -> repetition and factor-correlation penalties
    -> train reward + validation score
```

默认构建 5 折 rolling window，`WF_GAP=20`。滚动而非 expanding 的训练切片避免早期验证段重新出现在后续训练段中。候选成为冠军前还会经过：训练/验证差距检查、最小暴露检查和验证分数比较。

### 4.3 REINFORCE、精英池与重启

训练使用 REINFORCE 更新 token 生成概率，并维护：

| 机制 | 作用 |
|------|------|
| EMA reward baseline | 避免全负 batch 中仅凭相对值把坏公式当作“较好”样本 |
| entropy floor | 低熵时继续施加探索压力，减少模式坍塌 |
| elite replay pool | 保留历史高验证分公式并按衰减权重重放 |
| factor pool | 保存高分因子输出，对高相关候选惩罚 |
| adaptive restart | 长期无改进或熵坍塌后增加扰动，周期性全量重置 |

这是一套搜索启发式，而非统计保证。精英重放、奖励权重和重启次数都可能把研究者偏好编码进搜索结果，必须记录每次实验配置、随机种子、数据版本和候选分布。

## 5. 回测目标与模型选择

`MT5Backtest` 将因子映射为连续目标仓位：

```text
position = tanh(factor)
position = 0 when abs(position) < MIN_TRADE_EXPOSURE
pnl = position * target_ret - abs(position - previous_position) * cost_rate
```

评分不只看收益，还综合年化收益、Sortino、Calmar、时序 IC、换手质量、暴露度、前后半段一致性和 beta 中性。多品种时还衡量品种间表现一致性与两倍成本下的压力表现；单品种还依据 `REWARD_MODE` 使用 standard、FTMO 或外汇均值回归权重。

注意两个限制：

1. 项目中的“交易次数”通过连续仓位变化近似，未模拟订单、限价/市价队列或部分成交。
2. OOS 分数仍在同一个数据文件上的 walk-forward 切片产生，不等于真正的最终盲测。策略推广前应保留未参与任何搜索、特征选择和阈值调节的时间段。

## 6. 产物与运行时一致性

单文件训练的产物 `strategies/best_{symbol}.json` 通常包括：

```text
vocab_version
symbol / timeframe / data_file / mode
formula / formula_decoded
best_score / train_steps
```

重新训练会保护已有更高 `best_score`，避免用较弱结果覆盖；检查点和训练历史则用于恢复搜索。策略加载端会跳过词表版本不一致或分数非正的策略。

`strategy_manager/live_signal.py` 在运行时再次调用相同的特征工程和 StackVM，并以最后一根已收盘 bar 的因子值产生方向与强度。实时计算要求至少 `max(Config.MIN_BARS, 500)` 根历史 K 线，以减少指标 warm-up 导致的 train-serve skew。

这条共享路径是优点，但策略 JSON 没有完整记录原始数据文件 hash、特征注册表完整快照、训练随机种子、代码 commit 和回测报告 hash。若作为可审计研究系统，这些来源信息应追加为不可变 manifest。

## 7. Web 与实时监控

`web/app.py` 提供 FastAPI 端点以启动训练/回测子进程、检查策略、保存设置、管理实时监控项，并支持 AI 对训练日志的辅助分析。回测必须收到本地 Parquet 文件，子进程日志写入 `logs/backtest_*.log`。

`RealtimeManager` 使用后台线程和最多四个 worker：

```text
watch = source + symbol + timeframe + strategy
    -> source fetch with short TTL cache
    -> remove obviously future bars
    -> use closed bar only
    -> evaluate_signal()
    -> persist watch definition in web_settings
```

源码会在词表不匹配、策略品种不匹配时提示，但仍允许执行。它还在 FastAPI 中配置 `allow_origins=["*"]`。默认只监听 `127.0.0.1`，风险较低；一旦通过反向代理或 `--host` 对外暴露，就必须增加认证、来源限制、密钥保护和对 API 错误详情的脱敏。

## 8. 适合吸收的模式

### 8.1 面向 HermesAlpha

```text
Factor definition
    expression / token AST + immutable vocabulary version

Evaluation run
    data snapshot + feature snapshot + cost model + folds + metrics

Promotion gate
    parser validity + OOS + exposure + turnover + correlation + capacity

Serving
    one feature/VM/signal implementation shared by backtest and online scoring
```

建议保留 AlphaMaster 的受限执行、确定性 token 版本和共享信号链；以显式实验对象替代当前分散的 JSON、checkpoint 和本地设置文件。

### 8.2 面向 ashare-audit

审计应至少检查：

| 检查项 | 证据 |
|------|------|
| 公式兼容性 | token registry 版本、策略 JSON 与运行时版本是否一致 |
| 数据可重现性 | 原始文件 hash、时间范围、缺失/填充统计、复权/合约规则 |
| 时间因果性 | target 定义、特征窗口、归一化、信号时点与成交时点 |
| 选择偏差 | 搜索次数、候选总数、精英池、未入选候选和最终筛选阈值 |
| 回测真实性 | 成本、点差、滑点、容量、停牌、交易时段与订单模型 |
| 服务安全 | 监听范围、CORS、密钥存储、策略文件访问控制、错误输出 |
| 执行边界 | 信号服务与任何未来交易网关是否以审批和账户级限额隔离 |

## 9. 结论

AlphaMaster 体现了一个务实的因子搜索闭环：受限 token 公式、因果特征、walk-forward 评分、版本兼容检查和实时复用。其最强的工程贡献是减少“训练公式、回测公式、线上公式各不相同”的问题。

它的研究结论仍受数据、成本、搜索多重比较和资产特定参数制约。将其用于生产级量化系统时，应把策略来源、独立验证、执行模拟和运行安全提升为与模型搜索同等重要的交付物。
