# Kronos 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/shiyu-coder/Kronos.git
> 分析基线：
> - `Kronos`：commit `67b630e67f6a18c9e9be918d9b4337c960db1e9a`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Kronos`
<!-- source-sync:end -->


> shiyu-coder · 将金融 K 线离散成 token 并自回归生成的时间序列基础模型 · Python / PyTorch / Hugging Face Hub / Flask
> 源码: `src/Kronos/`
> 原始仓库: <https://github.com/shiyu-coder/Kronos>

## 1. 一句话定位

Kronos 是面向金融 K 线“语言”的 decoder-only 基础模型：先由 `KronosTokenizer` 把连续 OHLCV（以及 amount）序列量化为层级离散 token，再由 `Kronos` 预测下一个 token，最后反量化为未来多期的价格、成交量和成交额路径。它是市场数值序列模型，不是阅读新闻、研报或财报的财经 LLM。

公开调用入口是 `model/kronos.py::KronosPredictor`。`predict()` 要求 `open/high/low/close` 和历史、未来时间戳；`volume` 可缺省为零，`amount` 可由成交量和均价补齐。它按输入窗口标准化并 clip，提取 minute/hour/weekday/day/month，生成后反标准化，返回以未来时间戳为索引的六列 DataFrame。`predict_batch()` 可并行多个资产，但所有序列必须有相同历史和预测长度。

## 2. Kronos 覆盖的链路

```text
K 线 CSV / Qlib 数据
    -> OHLCV(A) + 五类时间特征，按历史窗口标准化
    -> KronosTokenizer.encode(..., half=True)
    -> s1/s2 两级离散 token
    -> Kronos 因果 Transformer：先 s1、后条件化 s2
    -> top-k / top-p / temperature 自回归采样，多路径取均值
    -> tokenizer.decode() + 反标准化
    -> 未来 OHLCVA 路径 / close 变化 score
    -> 可选 Qlib TopkDropoutStrategy 示例回测
```

训练提供两条真实路径。`finetune/` 用 `QlibDataPreprocessor` 生成 train/val/test pickle，先执行 `train_tokenizer.py` 的重建与 BSQ 损失训练，再执行 `train_predictor.py` 的双级 token next-token 交叉熵训练；`qlib_test.py` 把 close 预测转成 `last/mean/max/min` score 并进行示例回测。`finetune_csv/` 则用 `CustomKlineDataset` 读取自定义 CSV，`SequentialTrainer` 先微调 tokenizer、再微调基础预测器，支持单卡或 DDP。

## 3. 核心模块

| 模块 | 作用 | 对当前项目的价值 |
|------|------|------------------|
| `model/kronos.py::KronosTokenizer` | 编码连续 K 线，调用 `BSQuantizer` 生成层级 token，并可解码重建 | 提供跨资产、跨价格尺度的离散市场表示接口 |
| `model/module.py::BinarySphericalQuantizer` / `BSQuantizer` | 将归一化连续码按二元球面量化；计算 commitment 与熵正则 | 避免直接将高噪声连续值作为“词表”，可研究 token 覆盖和码本退化 |
| `model/kronos.py::Kronos` | `HierarchicalEmbedding`、`TemporalEmbedding`、因果 `TransformerBlock`、`DependencyAwareLayer` 与 `DualHead` | 将多变量市场状态建模成 $p(s1_t|history)$、$p(s2_t|history,s1_t)$ |
| `KronosPredictor` / `auto_regressive_inference()` | 输入校验、窗口标准化、自回归生成、top-k/top-p 采样、反标准化 | 可封装为统一预测服务；记录采样参数和模型版本以保证复现 |
| `finetune/qlib_data_preprocess.py` / `dataset.py` | Qlib 数据加载、时间切分、滑窗与仅用历史窗口的归一化 | 可复用其防未来泄漏的窗口统计原则，不应直接复用示例数据范围 |
| `finetune/train_tokenizer.py` / `train_predictor.py` | 两阶段 DDP 微调、AdamW、OneCycleLR、验证最优 checkpoint | 为本地市场和频率适配提供最小训练闭环 |
| `finetune/qlib_test.py::QlibBacktest` | 将预测 close 路径转换为 score，用 `TopkDropoutStrategy` 做含成本示例回测 | 可作为信号接入 Qlib 的原型；生产需补充中性化、流动性、涨跌停与组合约束 |
| `webui/app.py` | Flask 接口加载 Hub 权重、预测本地 CSV/Feather、展示 Plotly K 线和实际值对照 | 适合人工验数与演示，不是实时行情、训练或下单系统 |

Kronos 与 LLM 的共同点是离散 token、自回归 Transformer 和概率采样；区别是 token 表示市场数值状态而非文字，输出是 OHLCVA 预测路径而非自然语言结论。最稳妥的集成方式是让 Kronos 只负责数值预测或 score，LLM 负责文本研究解释，独立的组合与回测层负责把 score 转成受交易规则和风险约束检验的决策。
