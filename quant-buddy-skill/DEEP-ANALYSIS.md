# quant-buddy-skill 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/pseudo-longinus/quant-buddy-skills.git
> 分析基线：
> - `quant-buddy-skills`：commit `4a5501875027e8838d7d87cd69bc2363c22299d8`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/quant-buddy-skills`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `quant-buddy-skills`：`f0797f59eede` → `4a5501875027`

提交摘要：
- 4a55018 chore(qbs): 更新正式库资产、数据名与板块预设至 4.24.5
- 84bf180 chore(qbs): 更新正式库资产、数据名与板块预设至 4.24.5
- 4ca0f13 feat(quant-buddy-skill): 升级至 4.24.4，完善事实核验、Turn 追踪与预设数据
- 9230a14 fix(qbs): 增加时效性事实核验并升级至 4.24.2
- 185f72d fix(qbs): 增加时效性事实核验与资产目录冲突处理
- 83bac5b chore: 更新 quant-buddy-skill 至 4.24.1
- 17483c0 新增「维度指标库」能力：以前 skill 只能通过 `presets/dimensions.yaml` 看到**综合指标**（维度分）并拿去 `selectByComposition` 选股，看不到细分指标，也拿不到任何指标的口径公式。本次接入两个服务端只读接口，把整套指标库和公式定义打开。
受影响路径：
- `M	skills/quant-buddy-skill/CHANGELOG.md`
- `M	skills/quant-buddy-skill/SKILL.md`
- `M	skills/quant-buddy-skill/presets/assets_db/future.yaml`
- `M	skills/quant-buddy-skill/presets/assets_db/index.yaml`
- `M	skills/quant-buddy-skill/presets/assets_db/stock_a.yaml`
- `M	skills/quant-buddy-skill/presets/assets_db/stock_hk.yaml`
- `M	skills/quant-buddy-skill/presets/assets_db/stock_us.yaml`
- `M	skills/quant-buddy-skill/presets/data_catalog.yaml`
- `M	skills/quant-buddy-skill/presets/index_info_catalog/guanzhao.yaml`
- `M	skills/quant-buddy-skill/presets/index_info_catalog/manifest.yaml`
- `M	skills/quant-buddy-skill/presets/sectors.yaml`
- `M	skills/quant-buddy-skill/recipes/download-data.md`
- 其余 15 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> formula execution skill · fast_query · SSE/resume · session/version guard · TopN audit discipline
> 源码: `src/quant-buddy-skills/`
> 原始仓库: <https://github.com/pseudo-longinus/quant-buddy-skills>

## 1. 架构定位

quant-buddy-skill 是一个高度工程化的 Agent Skill。它的目标不是单个 API 调用，而是让 LLM 在复杂量化任务中遵守一套稳定的工具协议。

目录结构代表了它的分层：

```text
SKILL.md
    top-level rules and routing

workflows/
    leaf workflows by task type

tools/
    exact tool schemas and return contracts

recipes/
    reusable formula patterns

presets/
    local data catalog, functions, asset dictionaries, cases

scripts/
    executor, Python SDK, formula package client, helpers
```

## 2. SKILL.md 的硬规则体系

`SKILL.md` 前半部分不是介绍，而是执行契约。关键规则包括：

| 规则 | 价值 |
|------|------|
| unknown-tool 红线 | 工具名错了不能继续猜变体 |
| newSession 前置 | 新问题隔离 task_id 和中间变量 |
| 原生工具优先 | 禁止用 shell/Python 包装已有平台工具 |
| 失败熔断 | 同类错误不能无信息重试 |
| 受控失败答复 | 失败也必须给用户明确卡点 |
| 用户条件冻结 | 不得改写百分比、时间、资产宇宙、事件口径 |
| 模糊任务先澄清 | 防止“支撑位”这类概念被擅自定义 |
| SKILL_VERSION_MISMATCH 自愈 | 工具签名漂移时强制重建 session 并重读规则 |
| body code 判成败 | HTTP 200 不等于业务成功 |

这些规则是 Agentic data tooling 最值得借鉴的部分：很多错误不是工具能力不够，而是模型在调用协议上失控。

## 3. Fast Path: fast_query

`tools/fast_query.md` 定义一个合并接口，覆盖：

```text
snapshot: 最新行情/估值
window: 最近 N 日或固定区间序列
report: 最近报告期财务
```

它适合 ≤1000 资产、标准字段、最多 2500 交易日的数据。字段白名单覆盖行情、估值、财务、资金流向、南北向和商品期货部分字段。

返回结构分两种：

```text
value mode
    dates
    results: asset -> fields

series/window mode
    results: asset -> dates + arrays
```

当数据点超过 500，会自动切 CSV 模式，返回 `csv_url`，禁止在对话中逐行展开 CSV。

这个 fast path 对 HermesAlpha 很重要：简单数据问题应该一次完成，不要进入自由公式引擎。

## 4. Formula Path: runMultiFormulaBatchStream

`tools/run_multi_formula.md` 是核心执行协议。

关键契约：

```text
tool name: runMultiFormulaBatchStream only
formulas: string[]
same task_id for same formula chain
begin_date must be explicit
max formulas per batch: 10
data_id is for readData
expression_id is internal, never for readData
execution_profile=research_24h for long research tasks
```

公式语法硬规则：

| 规则 | 正确 |
|------|------|
| 引用数据/变量名 | `"全市场每日收盘价"` |
| 函数参数为板块名 | `板块(万得全A)` |
| AND | 乘法 `("A")*("B")` |
| 不等式参与运算 | 加括号 |
| 一维条件转二维 | 乘以 `板块(万得全A)` |
| 一维 0/1 相加 | 先 `缺失填零()` |

这些规则直接针对 LLM 最常见的公式错误。

## 5. quant-standard workflow

`workflows/quant-standard.md` 是选股/回测/因子/图表的完整流程。

它先问两个问题：

```text
最终输出是什么？净值曲线/走势图/选股列表/因子矩阵
每个输入数据从哪里来？单资产函数还是全市场数据集
```

然后定义不同微流程，尤其是 TopN 结果治理：

| 规则 | 说明 |
|------|------|
| 资产宇宙先收敛 | 用户说 A 股/股票时先加 `板块(万得全A)` |
| 排序前施加掩码 | 不能先取前 N 再事后过滤 |
| 字段预确认 | 每个数据集名来自 presets 或 confirmDataMulti |
| 隐含约束禁止 | 不得默认加 PE>0、非 ST、市值门槛 |
| description 优先 | 掩码 description 已含名单时不读全表 |
| 禁止读大布尔掩码 | `last_column_full` 会返回数千行无效数据 |
| readData 后重排 | 原始顺序不保证按排序字段有序 |
| 单调性校验 | 最终表格必须逐行满足排序方向 |

这是一套非常具体的“LLM 结果审计”规则，尤其适合 ashare-audit 借鉴。

## 6. executor.py: 工具路由和错误分类

`scripts/executor.py` 维护 `TOOL_ROUTES`：

```text
fast_query -> /fastQuery
searchFunctions -> /searchFunctions
searchSimilarCases -> /searchSimilarCases
getCardFormulas -> /getCardFormulas
confirmDataMulti -> /confirmDataMulti
runMultiFormulaBatchStream -> /runMultiFormulaBatch
readData -> /readData
renderChart -> /renderChart
renderKLine -> /renderKLine
stockProfile -> /stockProfile
selectByComposition -> /selectByComposition
scanDimensions -> /scanDimensions
resumeJob -> /runMultiFormulaBatch/stream
```

错误类别统一为：

```text
input_error
server_timeout
server_error
transport_recoverable
```

并且为客户端自产终态码补类别，例如 `STREAM_INTERRUPTED` 属于可恢复传输错误，应该用 `resumeJob`，不是改公式重跑。

它还有 presets 层：`confirmDataMulti` 和 `searchFunctions` 可以先查本地 YAML 子集，命中就零网络返回。

## 7. QuantAPI: Python SDK 的 session/version/配额治理

`scripts/quant_api.py` 是同步 Python 客户端。

核心状态：

```text
skill_root
timeout
session_file
_task_id
_session_ru_cost
_last_quota
```

`newSession` 不走 HTTP，直接本地生成 UUID，并写：

```json
{
  "task_id": "...",
  "skill_version_at_creation": "4.23.0",
  "user_query": "..."
}
```

后续调用会检查 session version。如果 session 创建时版本与当前 `SKILL.md` version 不一致，则抛 `SKILL_VERSION_MISMATCH`，要求新建 session 并重读规则。

这解决了一个真实问题：Agent 上下文里的旧工具签名可能和本地 skill 文件/服务端版本不一致。

## 8. SSE 和续传

`QuantAPI._call()` 对 `runMultiFormulaBatchStream` 优先走 SSE：

```text
call_run_multi_formula_batch_stream
    -> if StreamUnsupportedError
        fallback call_post old sync endpoint
```

`quant-standard.md` 要求 deferred、trace_id 或流中断后只能用 `resumeJob`，并且必须带 `task_id` 和 `trace_id`。

这类长任务协议很适合当前项目的回测、批量因子计算、报告生成等场景。

## 9. 对当前项目的迁移模式

### 9.1 Tool Contract Table

每个核心工具应有类似文档：

```text
exact tool name
endpoint
required params
business limits
return shape
failure categories
retry policy
fields that must not be confused
```

`data_id` vs `expression_id` 是典型例子。任何容易混淆的字段都要写成红线。

### 9.2 Session Isolation

HermesAlpha 的研究任务也应有：

```text
task_id
user_query
skill/tool version
created_at
intermediate variables
final artifacts
quota/cost
```

这样多轮追问和新问题不会共享错误状态。

### 9.3 Final Answer Audit

ashare-audit 可以把 quant-buddy 的输出纪律变成检查项：

```text
是否直接给结论
是否隐藏运行态字段
是否排序正确
是否展示中间草稿表
是否扩大用户条件
是否披露实际覆盖范围
```

## 10. 风险与改造建议

| 风险 | 建议 |
|------|------|
| 规则文件很长 | 按 leaf workflow 分块加载，避免每次全读 |
| 工具协议依赖服务端 | 抽象 provider contract，加入 mock server 测试 |
| 公式 DSL 容易被模型写错 | 提供 parser/linter，在执行前本地检查 |
| session 文件并发 | 用内存 task_id + 文件只给外部工具读，或改 SQLite |
| 重规则压制灵活性 | fast path、standard path、research path 分层，不同严格度 |

## 11. 结论

quant-buddy-skill 是当前批次中最强的工具治理样本。它不是展示某个数据源，而是展示“如何让 Agent 稳定调用复杂数据平台”：硬工具名、session 隔离、版本自愈、错误分类、续传、字段口径冻结、TopN 校验和最终答案纪律。这些都可以直接转化为 HermesAlpha 工具层和 ashare-audit 审计规则。
