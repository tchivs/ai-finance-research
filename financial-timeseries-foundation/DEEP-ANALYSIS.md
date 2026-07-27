# Financial Time-Series Foundation Models 深度分析

> Kronos 与 FinCast 对比 · 离散 K 线语言建模 · Patch MoE 预测 · 量化系统接入边界
> 源码: `/root/source/tmp/Kronos/`, `/root/source/tmp/FinCast-fts/`
> 原始仓库: [Kronos](https://github.com/shiyu-coder/Kronos) · [FinCast-fts](https://github.com/vincent05r/FinCast-fts)

---

## 1. 为什么合并分析

Kronos 和 FinCast 都属于“金融时序基础模型”，但路线不同：

```text
Kronos: continuous OHLCV -> tokenizer -> hierarchical tokens -> autoregressive generation -> OHLCV forecast
FinCast: continuous time series -> patches -> decoder + MoE -> mean/quantile forecast
```

对当前项目来说，二者不是互斥选择，而是两类模型接口：Kronos 更像 K 线语言模型，FinCast 更像通用金融预测器。

---

## 2. Kronos 架构要点

### 2.1 Tokenizer

`KronosTokenizer` 用 encoder Transformer 将输入映射到 codebook 维度，再通过 `BSQuantizer` 做 Binary Spherical Quantization。它将 token 分成 `s1_bits` 和 `s2_bits` 两层。

这个设计的意义是：

1. 把连续、有噪声的金融序列转换为离散 token。
2. 用层级 token 表示粗粒度和细粒度市场状态。
3. 让后续 decoder-only Transformer 像语言模型一样生成金融序列。

### 2.2 Predictor

`Kronos` 模型包含：

| 模块 | 作用 |
|---|---|
| `HierarchicalEmbedding` | s1/s2 token 嵌入和融合 |
| `TemporalEmbedding` | minute/hour/weekday/day/month 时间特征 |
| Transformer blocks | 自回归上下文建模 |
| `DependencyAwareLayer` | s2 预测条件依赖 s1 |
| `DualHead` | 分别预测 s1 和 s2 token |

推理时先预测 s1，再用 s1 条件预测 s2。这个层级依赖比单一 token head 更适合金融序列的多尺度变化。

### 2.3 推理流程

`auto_regressive_inference()` 的核心流程：

```text
clip normalized input
repeat sample_count paths
tokenizer.encode(x, half=True)
for each future step:
  decode_s1(context)
  sample s1 with T/top_k/top_p
  decode_s2(context, sampled_s1)
  sample s2
  append into rolling context buffer
tokenizer.decode(full tokens)
average sample paths
```

`KronosPredictor.predict()` 再负责 DataFrame 校验、实例级归一化、时间特征生成和反归一化。

---

## 3. Kronos 微调与回测样板

Kronos 的 `finetune/` 给了一个从 A 股 Qlib 数据到 TopK 回测的样板：

| 步骤 | 文件 | 内容 |
|---|---|---|
| 配置 | `finetune/config.py` | Qlib 路径、instrument、时间切分、lookback、predict window、checkpoint |
| 数据准备 | `qlib_data_preprocess.py` | 生成 train/val/test pickle |
| tokenizer 微调 | `train_tokenizer.py` | 调整离散化到目标市场分布 |
| predictor 微调 | `train_predictor.py` | DDP 训练 token language model |
| 回测 | `qlib_test.py` | 生成 close 预测信号，用 Qlib TopkDropoutStrategy 回测 |

最值得迁移的是这个流程骨架，而不是默认参数。当前项目如果要接入任何 TSFM，都应先建立相同的 walk-forward 流程。

---

## 4. FinCast 架构要点

### 4.1 TimesFM 风格接口

`FFmBase` 借鉴 TimesFM，提供：

| 方法 | 作用 |
|---|---|
| `_preprocess()` | pad/truncate context，构造 padding 和 freq |
| `forecast()` | 输入序列，返回 mean 和 full quantile forecast |
| `forecast_with_covariates()` | 结合动态/静态协变量和 xreg 残差建模 |
| `forecast_on_df()` | `unique_id`, `ds`, `values` DataFrame 预测接口 |

它比 Kronos 更容易包装成业务服务，因为输入/输出接近通用 forecasting API。

### 4.2 Patch Decoder + MoE

`pytorch_patched_decoder_MOE.py` 中，FinCast 使用 patch length、horizon length、RMSNorm、attention 和 Sparse MoE。每个 decoder layer 的 MLP 被 MoE 替代：

```text
self attention
  -> residual
  -> SparseMoEBlock
  -> hidden states + auxiliary loss
```

MoE 的意义是让模型在不同金融域、频率或资产行为上路由到不同专家，而不是用一个统一 FFN 处理所有模式。

### 4.3 Quantile Forecast

FinCast 默认 quantiles 为 `0.1` 到 `0.9`。`forecast()` 可返回 mean 或 median 作为点预测，同时保留 full forecast。

这对交易系统的价值不是“更准”，而是能表达不确定性：

```text
wide interval -> lower confidence / reduce position / require confirmation
narrow interval + positive median -> candidate signal
quantile skew -> asymmetric risk clue
```

---

## 5. FinCast 推理工程

`FinCast_Inference` 封装了 CSV 推理流程：

1. 读取单 CSV 多列时间序列。
2. 按列构建 `TimeSeriesDataset_SingleCSV_Inference`。
3. 支持 last-window 或 sliding windows。
4. DataLoader 批量推理。
5. 收集 mean/full outputs 和 mapping metadata。
6. 可绘图、可导出 CSV。

这个 mapping metadata 很值得吸收，因为预测结果必须能追溯到输入列、窗口起止、context length 和频率。

---

## 6. PEFT/LoRA 领域适配

`peft_Fincast/peft_injector.py` 提供 LoRA/DoRA 注入：

| preset | target |
|---|---|
| `attn` | `qkv_proj`, `o_proj` |
| `attn_mlp` | attention + input/horizon FF layers |
| `attn_mlp_gating` | attention + MLP + MoE gate |
| `experts_heavy` | attention + MLP + gate + experts |
| `all_linear` | 所有 Linear |

这说明金融 TSFM 的微调可以分层：先低成本调 attention，再调 gating，最后才 heavy experts。当前项目可以用这个思想做消融实验，而不是一上来全参微调。

---

## 7. 接入当前项目的统一接口

建议不要让业务代码直接调用 Kronos 或 FinCast，而是封装为：

```text
ForecastRequest
  symbol
  frequency
  context_df
  horizon
  model_name
  sample_count / quantiles

ForecastResult
  point_forecast
  quantiles
  raw_paths optional
  model_name
  checkpoint
  context_len
  horizon
  generated_at
  data_quality
```

然后再把结果转成策略信号：

```text
forecast -> signal calibration -> cross-sectional rank -> risk constraints -> backtest/shadow
```

---

## 8. 验证要求

接入 foundation model 前至少要做：

1. Walk-forward split，不使用未来归一化统计。
2. 与简单 baseline 比较，如 last value、MA、ARIMA/LightGBM、传统因子。
3. 加入交易成本、滑点、涨跌停、停牌和成交约束。
4. 分市场状态评估：牛/熊/震荡、高波/低波。
5. 分股票池评估：沪深300、中证500、中证1000、小票、ST/新股排除。
6. 模型预测稳定性评估：不同 `T/top_p/sample_count` 或 quantile 区间。
7. 将输出作为 signal，而不是直接生成交易动作。

---

## 9. 值得直接吸收的原则

1. 金融时序基础模型必须先封装成预测服务，再进入策略层。
2. 原始预测不是 alpha，必须校准、排序、约束和回测。
3. 不确定性输出比单点预测更适合仓位和风险控制。
4. A 股微调必须处理复权、停牌、涨跌停、成交约束和交易日历。
5. 模型结果必须保留 checkpoint、context、horizon、频率和输入窗口元数据。
6. PEFT 比全参微调更适合早期领域适配和快速实验。
7. Foundation model 应作为证据源之一，不应覆盖公告、资金、基本面和风控规则。
