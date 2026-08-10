# Kronos 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/shiyu-coder/Kronos.git
> 分析基线：
> - `Kronos`：commit `67b630e67f6a18c9e9be918d9b4337c960db1e9a`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Kronos`
<!-- source-sync:end -->


> 金融 K 线序列的离散 token 基础模型 · 两阶段量化器 + 自回归 Decoder-only Transformer
> 源码: `src/Kronos/`
> 原始仓库: <https://github.com/shiyu-coder/Kronos>

## 1. 为什么 Kronos 重要

Kronos 不是面向财经文本、公告或研报的 LLM，也不是把连续数值直接回归到未来价格的普通时间序列模型。它将金融市场的“语言”严格定义为 K 线序列：把连续的多维 OHLCV 数据先转换为离散 token，再把未来预测转化为类似语言建模的下一个 token 生成。README 将其定位为面向金融蜡烛图的 decoder-only 基础模型，并说明预训练数据覆盖 45 个以上全球交易所；公开模型有 `Kronos-mini`（4.1M）、`Kronos-small`（24.7M）和 `Kronos-base`（102.3M）。

这条路线处理的是高噪声、异方差且跨市场尺度差异很大的数值序列。`model/kronos.py` 的 `KronosPredictor` 会对每一个输入窗口独立标准化、截断极端值，预测后再用原窗口均值与标准差还原量纲。因此同一模型可以在不同价格绝对水平、不同成交量数量级的资产上工作；但它并不理解公司基本面、新闻语义、交易制度或投资者观点。

把它称为“基础模型”的核心不在参数量，而在可迁移的预训练表示：连续 K 线被共享的 tokenizer 离散化，后续模型只学习 token 序列与时间戳条件下的联合分布。与 LLM 的联系是训练目标和解码方式：都在离散词表上做因果 next-token prediction，并可用 temperature、top-k、top-p 采样生成多条轨迹。区别是 Kronos 的 token 不对应自然语言词片，而是六维市场状态的量化码；输出也不是文字或工具调用，而是反量化后的 `open/high/low/close/volume/amount` 路径。它适合作为量化系统的数值预测层，而不能替代文本研究、因子中性化、组合优化和交易执行。

## 2. 高层组件

源码对应的运行链路如下：

```text
原始 K 线 DataFrame（OHLC 必需；volume/amount 可选）+ 历史/未来时间戳
    -> KronosPredictor：实例标准化、clip、minute/hour/weekday/day/month 特征
    -> KronosTokenizer：编码器 -> Binary Spherical Quantization -> 两级离散 token
    -> Kronos：层级嵌入 + 时间嵌入 + 因果 Transformer
    -> 先生成 s1、再条件生成 s2 的自回归循环
    -> tokenizer.decode() 还原连续特征 -> 反标准化 DataFrame
    -> 可选：将 close 路径转成横截面 signal，交给 Qlib TopkDropoutStrategy 回测
```

| 领域 | 真实入口与职责 |
|------|----------------|
| 模型导出 | `model/__init__.py` 导出 `KronosTokenizer`、`Kronos`、`KronosPredictor`，并以 `get_model_class()` 按名称获取。 |
| 连续值离散化 | `model/kronos.py::KronosTokenizer` 编码、量化、重建；`encode()` 返回 token id，`decode()` 将 token id 复原为 K 线特征。 |
| 生成模型 | `model/kronos.py::Kronos` 接收两级 token 与时间特征，输出两套词表 logits。 |
| 推理 API | `KronosPredictor.predict()` / `predict_batch()` 接收 pandas 数据和时间序列，封装预处理、生成与反标准化。 |
| Qlib 微调 | `finetune/qlib_data_preprocess.py`、`dataset.py`、`train_tokenizer.py`、`train_predictor.py`、`qlib_test.py` 形成 A 股示例链路。 |
| CSV 微调 | `finetune_csv/` 的 `CustomKlineDataset`、`finetune_tokenizer.py`、`finetune_base_model.py` 与 `SequentialTrainer` 面向单个自定义 CSV。 |
| 可视化 | `webui/app.py` 是 Flask API，加载 Hub 权重、读取数据、调用 predictor、生成 Plotly K 线和预测对照图。 |

公开推理的输入合同明确：`KronosPredictor.predict()` 要求 DataFrame 至少有 `open/high/low/close`；缺 `volume` 时补零，缺 `amount` 时以 volume 乘四价均值估计；价格或量相关列有 NaN 则报错。时间戳经过 `calc_time_stamps()` 展开为五个日历字段。输出是以给定 `y_timestamp` 为索引、含六个特征列的 DataFrame。小型与基础版公开模型的 `max_context` 为 512，超长历史在 `auto_regressive_inference()` 中只保留末尾窗口。

## 3. 核心实现细节

### 3.1 两阶段 tokenizer：先建市场“词表”，再做语言建模

`KronosTokenizer` 不把原始价格值直接喂给 Transformer。它先用线性层 `embed` 与若干 `TransformerBlock` 编码，再经 `quant_embed` 投到 `s1_bits + s2_bits` 维码空间。`BSQuantizer` 内部调用 `BinarySphericalQuantizer`：先 `F.normalize`，把每一维按符号量化到 $\{-1,1\}$，并用 `bits_to_indices()` 组合成整数 token。`BinarySphericalQuantizer.forward()` 同时计算 commitment loss 和熵正则，后者通过码本/样本熵防止离散码退化。

这里的“层级”是实际实现而非营销名词。`KronosTokenizer.forward()` 一次重建两条路径：前 `s1_bits` 的 `z_pre`，以及完整码的 `z`；`train_tokenizer.py::train_model()` 对两者分别算 MSE，令 `recon_loss = recon_loss_pre + recon_loss_all`，最终训练损失为 `(recon_loss + bsq_loss) / 2`。预测时使用 `half=True`，tokenizer 返回 `token_seq_0` 与 `token_seq_1` 两个整数序列，为后续分层生成准备条件。

### 3.2 Decoder-only 预测器：联合建模两级 token 与日历

`Kronos` 用 `HierarchicalEmbedding` 分别嵌入高位 `s1` 和低位 `s2`，拼接后投影；`TemporalEmbedding` 将 minute、hour、weekday、day、month 的 embedding 相加。主干是由 `TransformerBlock` 组成的因果网络：`MultiHeadAttentionWithRoPE.forward()` 调用 `scaled_dot_product_attention(..., is_causal=True)`，因此每个位置只能看到历史 token；层内采用 `RMSNorm`、SwiGLU 风格的 `FeedForward`（`silu(w1(x)) * w3(x)`）和残差连接。

分层 token 的依赖显式编码在 `DependencyAwareLayer`。`DualHead` 先产生 `s1_logits`；训练时 `Kronos.forward(..., use_teacher_forcing=True, s1_targets=...)` 可用真实 s1 作为条件，默认路径则从 s1 分布采样。随后 `DependencyAwareLayer` 对 s1 embedding 与 Transformer context 做交叉注意力，`cond_forward()` 输出条件化的 `s2_logits`。`DualHead.compute_loss()` 对两级分类交叉熵取平均。因此模型学习的是 $p(s1_t\mid history)$ 与 $p(s2_t\mid history,s1_t)$，不是六个特征各自独立回归。

### 3.3 从 token 到多路径价格预测

`auto_regressive_inference()` 是完整生成循环。它先把每条输入复制 `sample_count` 份，编码历史，随后逐步调用 `model.decode_s1()`、`sample_from_logits()`、`model.decode_s2()` 和 `sample_from_logits()`。该函数维护固定长度的 `pre_buffer`/`post_buffer`，上下文满后以 `torch.roll` 左移，保证生成成本受 `max_context` 限制。`top_k_top_p_filtering()` 支持 top-k 或核采样；最后把多条采样路径经 tokenizer 解码，并沿 sample 维求均值得到预测。

`KronosPredictor.predict_batch()` 为多资产并行准备张量，但强制所有序列具有相同历史长度和预测长度。此限制来自 `np.stack` 与同一批次的自回归解码，而非业务层面的资产约束。输出路径代表模型分布下的数值预测；工程上应保留采样路径或不确定性统计，不能把均值路径误写为确定价格。

### 3.4 训练、微调与验证边界

Qlib 示例的 `QlibDataPreprocessor` 读取 `$open/$close/$high/$low/$volume/$vwap`，构造 `vol` 与 `amt`，按配置保存 `train_data.pkl`、`val_data.pkl`、`test_data.pkl`。`QlibDataset.__getitem__()` 的窗口长度为 `lookback_window + predict_window + 1`，只用 lookback 段计算均值和标准差后再标准化整窗，明确避免未来数据进入归一化统计量。

微调分两阶段：`train_tokenizer.py` 优化重建和 BSQ 损失，保存验证 MSE 最优 tokenizer；`train_predictor.py` 在 `torch.no_grad()` 下调用 tokenizer 生成 token，以错一位的 `token_in`/`token_out` 训练 `Kronos` 的两个交叉熵头，保存最佳验证 loss 权重。两者使用 DDP、`DistributedSampler`、AdamW、OneCycleLR 和梯度裁剪。`finetune_csv/` 以 `CustomKlineDataset` 读取含 `timestamps, open, high, low, close, volume, amount` 的 CSV；`SequentialTrainer.run_training()` 先运行 `train_tokenizer_phase()`，再用已微调 tokenizer 运行 `train_basemodel_phase()`。这不是端到端联合训练。

评估脚本 `finetune/qlib_test.py` 将生成的 close 路径构造成 `last`、`mean`、`max`、`min` 四种分数，例如 `mean` 为预测期平均 close 减最后一个历史 close。`QlibBacktest.run_single_backtest()` 使用 Qlib `TopkDropoutStrategy` 和 `SimulatorExecutor` 做日频、开盘价成交的示例回测，并报告含/不含成本的相对基准收益。README 已明确提示这只是演示：原始信号尚未做风险因子中性化、组合优化、精细冲击成本或生产级风控。

### 3.5 WebUI 的定位与边界

`webui/app.py` 的 `/api/load-model` 从 `AVAILABLE_MODELS` 选择 Hub tokenizer/model，调用各自的 `from_pretrained()`，再构造 `KronosPredictor`。`/api/predict` 验证数据量与列，接收 `lookback`、`pred_len`、`temperature`、`top_p`、`sample_count`，调用真实 predictor；结果由 `create_prediction_chart()` 交给 Plotly，`save_prediction_results()` 落盘。它是单文件预测与结果对照界面，不是模型训练服务、实时行情接入、策略执行器或交易终端。`webui/run.py` 只是依赖检查后启动 Flask，默认监听 7070。

## 4. 对当前项目的价值

Kronos 最有价值的可复用点是“把数值市场行为 token 化，再使用自回归生成统一处理预测任务”的接口，而不是直接照搬一段回测脚本。当前项目可以把 `KronosPredictor` 置于模型层：输入有版本记录的 OHLCV 窗口和交易日历，输出多期 OHLCVA 预测、采样参数、模型/Tokenizer 版本、归一化范围及采样数；再由独立的信号层将路径转换为预先定义的收益分数或风险特征。

建议采用清晰的责任边界：Kronos 只产出价格/量预测或派生 score；研究 Agent/LLM 处理文本、事件与假设；Qlib 或等价回测层统一处理时点对齐、横截面选股、交易规则、成本和风险归因。这样既能让语言模型解释“为什么”，又能让时间序列基础模型给出“市场路径可能如何演化”，并在同一个可回放的实验记录中比较二者。

接入前必须补齐四项控制：第一，按市场、频率、复权、停牌和时区验证输入数据；第二，严格按预测时点切分训练、验证、测试，沿用仅用历史窗口统计量的规范；第三，将 `sample_count`、`T`、`top_p` 和 context 截断写入 artifact，避免不可复现的采样结论；第四，独立测试 score 到持仓的映射，并在有交易成本、涨跌停、流动性限制与因子中性的回测中检验。Kronos 提供的是预测能力，不构成收益承诺；其 README 的生产提示也明确要求把原始信号送入更完整的组合优化和风险管理流程。
