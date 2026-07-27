# AlphaAgent 深度分析

> A 股 panel · 因子 DSL · memmap FactorZoo · IC/MLS 评估 · LLM tool-call mining
> 源码: `/root/source/tmp/AlphaAgent/`
> 原始仓库: <https://github.com/RndmVariableQ/AlphaAgent>

## 1. 系统定位

AlphaAgent 不是一个通用聊天 Agent，而是 A 股多因子研究系统。它把数据、表达式、评估、因子库和 LLM 挖掘分层：

```text
Data layer
    raw market/fundamental/industry/index caches
    panel builder

DSL layer
    parser
    operator registry
    evaluator

Factor layer
    evaluation metrics
    report generation
    FactorZoo storage

Mining layer
    prompts
    tools
    multi-turn loop
    trajectory logs
```

这种结构适合当前项目吸收，因为它把 LLM 从“直接写代码”限制为“提出 DSL 表达式并调用评估工具”。

## 2. 数据层

README 给出两种数据准备方式：

| 方式 | 特点 |
|------|------|
| Open data package | 下载 raw parquet cache，无需 Tushare token |
| Tushare fetch | 设置 `TUSHARE_TOKEN`，运行 market/fundamental fetch |

然后统一运行：

```text
build_panel.py --with-fundamentals --with-industry
init_factorlib.py
ingest_factors.py --expr-dir artifacts/factorzoo/stock_1d/expressions
eval_factor.py --expr-file ... --report
```

关键点是“raw cache”和“研究 panel”分离。采集可以不稳定，但研究评估必须读取固定的本地 panel。HermesAlpha 应该采用同样做法：数据获取层不应直接喂给因子评估或 LLM 分析。

## 3. DSL parser

`alphaagent/dsl/core/parser.py` 使用 pyparsing，开启 packrat 并提高递归深度。它把 DSL 解析成 Python 表达式字符串，由 evaluator 绑定变量和 operator。

### 3.1 变量与频率

变量支持：

```text
$close
$volume
$close@60m
$close@1d
```

这为多频因子预留了表达能力。当前项目如果要统一日线、分钟线、财务、事件，可以仿照 `field@freq` 或 `field@source` 语法。

### 3.2 中缀运算重写

对两个非数字操作数：

```text
A + B -> ADD(A, B)
A - B -> SUBTRACT(A, B)
A * B -> MULTIPLY(A, B)
A / B -> DIVIDE(A, B)
```

对双列比较：

```text
A > B  -> GT(A, B)
A < B  -> LT(A, B)
A >= B -> GE(A, B)
A <= B -> LE(A, B)
A == B -> EQ(A, B)
A != B -> NE(A, B)
```

这样做的好处是 operator 统一处理 index 对齐、缺失值和 panel 语义，而不是依赖 pandas 默认广播行为。

### 3.3 逻辑与条件表达式

```text
A || B -> OR(A, B)
A && B -> AND(A, B)
condition ? x : y -> pd.Series(np.where(...), index=($close).index)
```

这适合策略/因子 DSL：表达式可读，但执行仍受 operator registry 控制。

## 4. 因子评估

`alphaagent/factor/eval.py` 是评估入口。

`evaluate_factor()`：

```text
sort panel
check label_col
eval_factor(expr, panel_full)
align_series_to_panel
slice eval window
evaluate_on_panel
return metrics
```

`evaluate_factor_on_split()` 面向 mining session，支持 train/val split、多行 DSL、详细 timing 和 detail tables。

### 4.1 失败返回结构

它不是直接抛异常给 LLM，而是返回：

```text
ok: false
error
error_type
split
date_range
```

这对 LLM tool loop 很关键。模型需要读到错误类型后修正表达式，而不是整个进程失败。

### 4.2 成功返回结构

成功结果包含：

```text
ok
split
date_range
eval_wall_seconds
timing_ms: eval / align / metrics / total
summary
monthly_corr_robustness
label_quantile_buckets
label_col
bar_interval
```

这比只返回 IC 更适合审计，因为可以看到 evaluation 是否慢、覆盖是否低、是否只在某些月份有效。

## 5. FactorZoo 存储

`alphaagent/factor/zoo/zoo.py` 使用：

```text
manifest
row index
catalog parquet
factor values memmap per factor
sample summary memmap
sample summary meta
```

`append_factor()` 的步骤：

1. 检查 values 长度等于 manifest.n_rows。
2. 检查 factor_id 不重复。
3. 写 full values 到 factor-specific memmap。
4. 把 sample rows 写入 sample_summary_memmap。
5. 更新 factor_id_to_col 和 next_col_idx。
6. 在 catalog append factor_id/name/expr/status/finite_count/extra。

这套设计可支持大规模因子库。完整 values 只在需要时读取，检索/相似度/摘要可以先看 sample summary。

## 6. LLM mining loop

`alphaagent/factor/mining/loop.py` 是很有价值的 LLM 工程样板。

### 6.1 多轮 tool calls

`run_trajectory()` 构建 messages，然后每轮：

```text
client.chat.completions.create(tools=schemas, tool_choice=auto)
log assistant content/reasoning/tool_calls
if no tool_calls and tool rounds too少 -> nudge
dispatch tool calls in parallel
append tool result messages
write JSONL events
```

### 6.2 并行工具执行

`_dispatch_parallel()` 用 ThreadPoolExecutor 并行执行多个 eval/submit tool call，并保持返回顺序。这对因子挖掘很重要，因为一次 LLM 可能提出多个候选因子。

### 6.3 轨迹文件

每次 session 会写：

```text
log_jsonl
messages.json
summary.json
```

summary 中包含 tool call 数、成功数、总耗时、submitted_factors、submit_failures。

这正是 ashare-audit 需要的审计材料：LLM 不是黑盒，它每一轮提出了什么、工具怎么反馈、哪些因子入库都可查。

## 7. 当前项目如何吸收

### 7.1 Factor DSL 安全边界

不要让 LLM 直接生成 Python 因子函数。推荐路径：

```text
LLM natural-language idea
    -> DSL expression
    -> parser whitelist
    -> sandbox evaluator
    -> metrics
    -> factor store
```

### 7.2 因子入库门槛

每个 candidate 至少需要：

```text
parse_ok
eval_ok
coverage >= threshold
train IC / RankIC
val IC / RankIC
monthly robustness
complexity score
similarity to existing factors
no label leakage
```

### 7.3 与 Qlib 联动

AlphaAgent 可以负责表达式和 A 股 panel 评估，Qlib 负责更完整的回测和实验记录：

```text
AlphaAgent DSL -> factor values -> Qlib pred.pkl -> SigAnaRecord -> BacktestRecord
```

### 7.4 与 RD-Agent 联动

RD-Agent 的 hypothesis/experiment/coding/feedback 可用 AlphaAgent 的 DSL 和 eval tool 替代“自由写代码”，降低出错和安全风险。

## 8. 审计关注点

| 风险 | 审计方式 |
|------|----------|
| 未来函数 | DSL operator 标记 lookback/lookahead，禁止未来 label 字段 |
| 表达式注入 | parser/operator whitelist，不允许任意 import/exec |
| 覆盖率虚高或虚低 | 保存 coverage、finite_count、missing pattern |
| 单月偶然有效 | monthly_ic_robustness 强制检查 |
| 因子重复 | AST similarity + sample summary similarity |
| 工具调用不透明 | mining JSONL 轨迹必须保留 |
| 数据版本漂移 | panel manifest/hash 保存到 metrics |

## 9. 与 AlphaEvo 的区别

| 维度 | AlphaAgent | AlphaEvo |
|------|------------|----------|
| 研究对象 | 因子表达式 | 策略 YAML |
| 数据 | A 股 panel | yfinance/akshare/daily_stock_analysis adapters |
| 核心验证 | IC/RankIC/MLS | backtest/confidence/anti-overfit |
| 存储 | FactorZoo memmap/catalog | StrategyStore/evolution tree/research logs |
| LLM 角色 | 提出/迭代 DSL 因子 | 诊断策略失败并提出 mutation |

两者可以组合：AlphaAgent 发现因子，AlphaEvo 把因子作为策略条件进行回测和演化。

## 10. 结论

AlphaAgent 的核心价值是“受限表达 + 标准评估 + 可追踪挖掘”。它是 LLM 因子研究从想法到资产的中间层。当前项目如果要做 AI 驱动的 A 股因子/信号挖掘，应该优先吸收它的 DSL、FactorEval、FactorZoo 和 mining trajectory，而不是直接复制某个因子公式。
