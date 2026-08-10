# Awesome Finance Skills 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/RKiding/Awesome-finance-skills.git
> 分析基线：
> - `Awesome-finance-skills`：commit `853f09b4d0baae747759ed31e21ed5c5b2316a5f`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Awesome-finance-skills`
<!-- source-sync:end -->


> AlphaEar 金融技能集合 · 新闻/股票/情绪/预测/搜索/研报/可视化 · Agent 可插拔能力包
> 源码: `src/Awesome-finance-skills/`
> 原始仓库: <https://github.com/RKiding/Awesome-finance-skills>

## 1. 一句话定位

Awesome Finance Skills 不是一个单体应用，而是一组可安装到 OpenCode / OpenClaw / Claude / Codex / Antigravity 的金融 Agent skills。

它最值得学的是“能力拆包”：把金融研究拆成新闻搜索、股票数据、情绪分析、Kronos 预测、逻辑链可视化、结构化研报、DeepEar Lite 信号读取等多个独立 skill，让 Agent 按任务只加载需要的能力。

## 2. Skill 清单

| Skill | 作用 | 可借鉴点 |
|---|---|---|
| `alphaear-stock` | A 股/港股/美股行情和基本面 | akshare/yfinance/东方财富直连 fallback、本地 SQLite 缓存 |
| `alphaear-search` | Web 搜索 + 本地 RAG | Jina/DDG/Baidu/local 多引擎，BM25+向量 RRF 融合 |
| `alphaear-sentiment` | 情绪分析 | BERT 快速批处理 + Agent 手动分析落库 |
| `alphaear-predictor` | Kronos 时序预测 | 技术预测先行，新闻语义由 Agent 二次调整 |
| `alphaear-logic-visualizer` | 逻辑链/行情图可视化 | pyecharts 生成 K 线、预测线、情绪趋势、图谱 |
| `alphaear-reporter` | 专业研报生成 | 信号聚类、章节写作、参考文献、结构化报告 |
| `alphaear-deepear-lite` | DeepEar Lite 信号读取 | 远端 `latest.json` 转 Markdown 信号简报 |
| `skill-creator` | skill 打包/校验 | skill 模板化分发和验证 |

## 3. 核心模式

```text
Agent question
    -> choose focused skill by description
    -> skill exposes small Python utility or prompt workflow
    -> utility returns structured data / Markdown / chart config
    -> Agent performs higher-level reasoning
    -> optional SQLite persistence for cache, signals, references
```

它的设计不是让脚本替代 Agent，而是把高确定性工作交给脚本：拉数、缓存、检索、图表、格式化、模型预测。判断、解释、调权、成文仍交给 Agent。

## 4. 最值得吸收的 6 点

1. **金融能力拆成小 skill**：每个 skill 有独立 `SKILL.md`、scripts、tests、references，不需要一个巨大金融 Agent。
2. **工具做可验证事实层**：股票数据、搜索、BERT、Kronos、可视化都可单测；Agent 负责主观分析。
3. **SQLite 作为轻量研究记忆**：`daily_news`、`search_cache`、`search_detail`、`stock_prices`、`signals` 构成最小本地研究库。
4. **搜索缓存和 RAG 分层**：先用详细缓存，再 fallback 到旧 JSON 缓存；本地新闻用 BM25+向量 RRF。
5. **预测分两段**：Kronos 输出 base forecast，Agent 根据新闻/逻辑做 qualitative adjustment，避免模型和解释混在一起。
6. **报告引用稳定化**：参考文献用 URL/title/source 的 sha1 短 key，报告可以追溯来源。

## 5. 对 HermesAlpha 的启发

- 可把 HermesAlpha 的能力按 `data / search / sentiment / forecast / report / visualization` 拆成可安装 skill，而不是只做内部服务。
- 可复用 `DatabaseManager` 的轻量 schema 思路，先建本地研究缓存，再接更重的数据湖。
- 可把“模型预测”和“新闻调整”拆成两个可审计步骤，保留 base forecast 与 adjusted forecast。
- 可把报告生成变成 `cluster -> write sections -> assemble -> references` 的流水线。

## 6. 对 ashare-audit 的启发

- 审计点可以围绕 skill 边界建立：每个 skill 的输入、输出、缓存、外部 API、模型权重、环境变量都可独立检查。
- 对预测类输出，必须同时保存 base model 结果、Agent 调整理由、使用的新闻证据。
- 对搜索/新闻类输出，必须审计缓存命中、TTL、URL 引用、重复引用、来源缺失。
- 对模型权重加载，必须限制 checkpoint 路径和文件名模式。

## 7. 风险与局限

- 仓库中多个 skill 的实现深浅不一，部分能力是 prompt workflow，部分是完整工具。
- `alphaear-predictor` 依赖 Kronos/torch/transformers/本地权重，部署成本高于普通 skill。
- `alphaear-stock` 使用 akshare/yfinance/东方财富直连，需处理源站限流、字段变化和代理问题。
- BERT 情绪模型是通用中文新闻模型，不等于金融专用情绪模型。

## 8. 可直接借鉴的最小实现

```text
skills/
  market-data/
    SKILL.md
    scripts/stock_tools.py
    scripts/database_manager.py
  finance-search/
    SKILL.md
    scripts/search_tools.py
    scripts/hybrid_search.py
  report-writer/
    SKILL.md
    references/PROMPTS.md
    scripts/report_utils.py
```

先拆能力，再做编排。这样 HermesAlpha 的 Agent 可以按任务加载工具，ashare-audit 也能按 skill 做独立审计。
