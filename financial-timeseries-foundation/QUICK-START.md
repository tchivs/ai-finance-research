# Financial Time-Series Foundation Models 快速概览

> Kronos + FinCast · 金融时序基础模型 · K 线 tokenization / Patch MoE / probabilistic forecast
> 源码: `/root/source/tmp/Kronos/`, `/root/source/tmp/FinCast-fts/`
> 原始仓库: [Kronos](https://github.com/shiyu-coder/Kronos) · [FinCast-fts](https://github.com/vincent05r/FinCast-fts)

---

## 一句话定位

这一条目合并吸收两个金融时序基础模型项目：`Kronos` 和 `FinCast`。

`Kronos` 把 OHLCV K 线序列量化成层级离散 token，再用 decoder-only Transformer 自回归生成未来 K 线；它强调“金融市场语言”的 tokenization，并提供 A 股 Qlib 微调和回测示例。

`FinCast` 更接近 TimesFM 路线，是面向金融时序预测的 decoder-only / patch decoder 模型，训练在超过 20B 金融时间点上，使用 MoE 和 quantile-aware/PQ-Loss，支持零样本、监督和少样本预测。

---

## 两者差异

| 维度 | Kronos | FinCast |
|---|---|---|
| 核心表示 | OHLCV -> Binary Spherical Quantization -> 层级 token | 连续时间序列 patch 输入 |
| 模型形态 | decoder-only Transformer，s1/s2 双 token head | TimesFM 风格 patched decoder + Sparse MoE |
| 输出 | open/high/low/close/volume/amount 预测路径 | mean + quantile probabilistic forecast |
| 重点场景 | K 线语言建模、A 股 Qlib 微调、TopK 回测 | 多资产多频率预测、不确定性、MoE 专家化 |
| 输入要求 | `open/high/low/close` 必需，`volume/amount` 可补 | 单变量或 dataframe 时序，freq 映射 |
| 风险 | 生成的是 raw signal，不是纯 alpha | 预测不等于交易策略，需要校准和风险控制 |

---

## 最高价值借鉴点

| 借鉴点 | 来源 | 可复用价值 |
|---|---|---|
| 金融专用 tokenizer | Kronos `KronosTokenizer` | 连续 K 线先离散化，再做语言建模 |
| 自回归采样参数 | Kronos `T/top_k/top_p/sample_count` | 多路径生成，平均得到概率性预测 |
| 实例级归一化 | Kronos `KronosPredictor.predict()` | 每条序列单独标准化和反标准化 |
| Qlib 微调闭环 | Kronos `finetune/` | 数据准备、tokenizer 微调、predictor 微调、TopK 回测 |
| Patch decoder + MoE | FinCast `pytorch_patched_decoder_MOE.py` | 用专家路由适配不同金融域 |
| Quantile 输出 | FinCast `ffm_base.py` | mean + q0.1~q0.9，天然支持风险区间 |
| PEFT 适配 | FinCast `peft_injector.py` | LoRA/DoRA 针对 attention、MLP、gating、experts |

---

## 最适合迁移的模块

1. **Forecast Adapter**: 把模型预测包装为统一接口，输出 `mean`, `quantiles`, `source_model`, `context_len`, `horizon`。
2. **Signal Calibration**: 原始预测只作为 signal，必须经过横截面排序、交易成本、风险暴露和回测。
3. **Uncertainty Band**: FinCast quantile 输出可用于“预测分歧/风险区间”，而非只看点预测。
4. **A 股 Fine-tune Pipeline**: Kronos 的 Qlib 数据切分、微调、TopK 回测适合做模型接入样板。
5. **PEFT Experiments**: FinCast 的 LoRA target preset 可用于低成本领域适配实验。

---

## 当前项目使用建议

| 用途 | 推荐模型 | 原因 |
|---|---|---|
| K 线形态生成/短周期 OHLCV 预测 | Kronos | 原生面向 K 线 token 和 OHLCV 输出 |
| 多资产单变量预测和风险区间 | FinCast | quantile 输出和多频率接口更直接 |
| A 股 Qlib 回测样板 | Kronos | 官方 finetune demo 已含 Qlib TopK 回测 |
| 低成本领域微调实验 | FinCast | PEFT/LoRA/DoRA 脚本已具备雏形 |

---

## 注意事项

- 两个模型输出都不能直接视为交易建议，必须进入策略、组合优化和交易成本评估。
- Kronos README 明确 demo backtest 是简化示例，生产需要风险因子中性化、组合优化、滑点和冲击成本。
- FinCast 支持 flexible context/horizon，但具体 checkpoint 的训练 horizon、patch 长度和模型配置仍有限制。
- Foundation model 容易过拟合热门 benchmark，接入前必须做本地 walk-forward 和 out-of-sample 验证。
