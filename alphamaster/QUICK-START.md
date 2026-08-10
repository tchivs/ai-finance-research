# AlphaMaster 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/rosemarycox5334-debug/AlphaMaster.git
> 分析基线：
> - `AlphaMaster`：commit `e45aa15a6a6c0bdc45c3cbb010c521470f3cabfd`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/AlphaMaster`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `AlphaMaster`：`3b8c86a1d13b` → `e45aa15a6a6c`

提交摘要：
- e45aa15 1.22
- 044ace0 Update tongdaxin_source.py
- ff861da 1.21
- 5d145b7 Update README.md
受影响路径：
- `M	README.md`
- `D	_launch_eurusd.bat`
- `D	_launch_index.bat`
- `D	_launch_jp225.bat`
- `D	_launch_precious.bat`
- `D	_launch_us100.bat`
- `D	_launch_us2000.bat`
- `D	_launch_us30.bat`
- `D	_launch_us500.bat`
- `D	_launch_web.bat`
- `D	_launch_xauusd.bat`
- `M	config.py`
- 其余 5 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> 强化学习公式搜索 · StackVM · Parquet 训练/回测 · Web 实时信号
> 源码: `src/AlphaMaster/`
> 原始仓库: <https://github.com/rosemarycox5334-debug/AlphaMaster>
> 研究基线: `3b8c86a`（2026-07-24，`1.2`）

## 1. 一句话定位

AlphaMaster 是一个把量化因子表示为 token 公式、由神经网络策略采样器搜索，并用成本调整回测筛选的研究工具。它可以从单个本地 Parquet K 线文件训练可解释公式，在 Web 控制台回测，并按已收盘 K 线输出实时多空信号。

它不是价格预测模型，也不是当前可用的自动下单系统。源码中的 `execution.trader` 已被移除；`MT5StrategyRunner` 在尝试连接或下单时会明确报错。研究、回测和信号监控是现有可用边界。

## 2. 核心链路

```text
{symbol}_{timeframe}.parquet / MT5 OHLCV
    -> ParquetDataManager / MT5DataManager
    -> causal feature registry
    -> AlphaGPT + ConstrainedSampler
    -> formula token sequence
    -> StackVM execute()
    -> factor [N, T]
    -> position = tanh(factor), small exposure -> flat
    -> cost-adjusted walk-forward evaluation
    -> strategies/best_{symbol}.json + checkpoint/history
    -> Web backtest or closed-bar real-time signal
```

训练、回测和实时信号都通过同一条核心计算链：特征 -> StackVM -> `tanh` 仓位。这是该项目最值得保留的设计，不应在上线阶段另写一套指标或信号实现。

## 3. 最小可用流程

### 3.1 准备数据

单文件训练要求：

- 文件名为 `{品种}_{周期}.parquet`，如 `BTCUSDT_H1.parquet`、`000001_D1.parquet`。
- 周期支持 `M1` 至 `MN1`，同时识别 `1h`、`60min`、`1d` 等别名。
- 必须包含 `time/open/high/low/close` 和 `tick_volume` 或 `volume`。
- 默认至少 3,000 根 K 线；加载时会按时间排序、去重，并检查列完整性。

```bash
cd src/AlphaMaster
python -m pip install -r requirements.txt
python train_file.py --data-file /absolute/path/BTCUSDT_H1.parquet
```

默认训练支持从 `checkpoints/ckpt_{symbol}_step_*.pt` 续训。`--from-scratch` 会删除该品种的既有检查点和训练历史，但会尝试把已有策略分数作为下限，避免弱候选覆盖磁盘上的更优策略。

### 3.2 使用 Web 控制台

```bash
cd src/AlphaMaster
python run_web.py --port 8765
```

默认地址为 `http://127.0.0.1:8765`。控制台围绕三个工作流组织：选择/训练 Parquet、选择策略进行带手续费和滑点的回测、配置数据源后的实时信号监控。

## 4. 关键研究资产

| 资产 | 内容 | 作用 |
|------|------|------|
| Parquet 数据 | 时间、OHLCV、品种和周期 | 固定实验输入，避免训练依赖实时接口 |
| 公式 token | 特征 token 与算子 token 的序列 | 可序列化、可解释执行的因子定义 |
| `vocab_version` | 由有序 feature/operator 名称 SHA-256 派生 | 拒绝不兼容的旧策略和检查点 |
| 策略 JSON | formula、symbol、timeframe、data_file、best_score | 连接训练、回测和监控的交付物 |
| checkpoint/history | 模型状态、精英池、训练曲线 | 支持续训和问题追踪 |

公式不是 Python 代码。`StackVM` 只消费已注册的特征和算子，并要求最终栈恰好剩一个结果；非法栈深、未知 token、NaN/Inf 或异常公式会被拒绝或转换为无效候选。

## 5. 评估与防退化措施

| 机制 | 做法 | 解决的问题 |
|------|------|----------|
| 约束采样 | 采样时维持 StackVM 栈深可达性 | 减少语法非法公式 |
| 因果算子 | rolling/expanding 统计只使用当前及历史 bar | 降低未来数据泄漏风险 |
| Walk-forward | 默认 5 折、20 bar gap 的滚动训练/验证切片 | 不以单一 in-sample 分数选冠军 |
| OOS 门控 | 验证段 Sortino 影响候选分数 | 抑制样本内偶然高分 |
| 成本压力 | 回测扣除换手成本，并检查 2 倍成本表现 | 抑制高换手幻觉 |
| 因子池 | 对高度相关候选施加惩罚 | 提高已接受公式的多样性 |
| 结构检查 | 防恒正算子链使输出长期单边 | 防止 beta 暴露伪装成 alpha |

这些是工程护栏，不是策略有效性的证明。真实采用前仍须使用独立样本、市场制度变化区间、成交约束和交易所/经纪商成本进行复验。

## 6. 实时信号边界

实时模块会：

1. 为每个 `(source, symbol, timeframe, strategy)` 维护一个监控项。
2. 拉取约 3,500 根历史 K 线，使用最后一根已收盘 bar 计算因子。
3. 输出 `LONG`、`SHORT` 或 `FLAT`，并给出 `tanh(factor)` 得到的强度/仓位。
4. 发现策略词表版本不符或跨品种使用时显示警告。

它不会阻止跨品种策略运行，只会给出提示；也不会自动下单。将监控输出接入执行系统前，必须加独立的审批、账户级风险上限、订单幂等、断线恢复和完整审计日志。

## 7. 对 HermesAlpha 的借鉴

1. 因子应保存为受限 DSL/token，而非任意 Python 片段。
2. 训练产物必须携带数据集、周期、特征/算子版本和评分，版本不兼容要默认拒绝。
3. 训练、回测和实时服务共享同一份特征与信号函数，优先消除 train-serve skew。
4. 搜索过程要将非法、常数、低暴露、过拟合和高相关候选作为一等结果记录下来。
5. 自动执行必须与研究系统隔离，不能由“已能给信号”自然推导为“可自动下单”。

## 8. 不该照搬的部分

- 默认奖励模式、成本率、品种清单和 MT5 参数带有作者的市场与账户假设，不能直接用于 A 股或其他经纪商。
- 单品种训练会让横截面标准化退化为时序标准化；多品种模式又要求严谨处理交易时段交集，不能混用结论。
- 默认 Web 服务本地绑定，但应用设置了允许所有来源的 CORS；若改为非本机访问，先收紧网络边界和认证。
- 源码包含旧 MT5 runner、风险和组合管理代码，但当前下单实现已移除，不能把这些模块当作可验证的实盘能力。

## 9. 结论

AlphaMaster 的价值不在于“用 AI 找到赚钱公式”，而在于把因子搜索压缩为可版本化 token 资产，并让训练、回测、实时信号共用受限执行链。适合作为因子研究工具链的实现参考；不应未经独立验证和执行治理直接用于交易自动化。
