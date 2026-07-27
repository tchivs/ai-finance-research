# quant-buddy-skill 快速概览

> 观照量化投研 Skill · A/H/US 行情财务查询 · 公式引擎 · 回测/选股/图表 · session/version/配额治理
> 源码: `/root/source/tmp/quant-buddy-skills/`
> 原始仓库: <https://github.com/pseudo-longinus/quant-buddy-skills>

## 1. 一句话定位

quant-buddy-skill 是一个面向 AI Agent 的量化数据与公式执行 skill。它把 A 股、港股、美股、指数、期货的行情/估值/财务快查，以及全市场公式计算、选股、因子、回测、图表、数据上传下载，组织成一套严格 workflow。

最值得学的是“Agent 工具调用纪律”：工具名、session、参数、字段口径、错误熔断、配额、版本自愈、TopN 结果校验都写成硬规则，防止模型乱读、乱试、乱扩大条件。

## 2. 核心能力

```text
Fast Path
    fast_query(snapshot/window/report)
    stockProfile
    renderKLine

Formula Path
    newSession
    confirmDataMulti
    runMultiFormulaBatchStream
    readData
    renderChart / downloadData

Research Path
    searchFunctions
    searchSimilarCases
    getCardFormulas
    scanDimensions
    formula package
```

## 3. 核心工作流

```text
User asks data / selection / backtest question
    -> route by SKILL.md scene table
    -> newSession for new task
    -> load global rules + leaf workflow
    -> choose fast_query for simple data
    -> choose formula chain for selection/backtest/factor
    -> run formulas in <=10 formula batches
    -> read only final data_id, not expression_id
    -> sort/validate final table before answer
```

## 4. 关键文件

| 文件 | 作用 |
|------|------|
| `skills/quant-buddy-skill/SKILL.md` | 顶层规则、场景路由、硬红线、目录说明 |
| `tools/fast_query.md` | 快速行情/估值/财务合并查询协议 |
| `tools/run_multi_formula.md` | 公式批次、SSE、data_id/expression_id、begin_date、拆批规则 |
| `workflows/quant-standard.md` | 选股/回测/因子/图表标准流程和 TopN 校验 |
| `scripts/executor.py` | 工具名到 HTTP endpoint 映射、SSE、presets、错误分类 |
| `scripts/quant_api.py` | Python SDK，session/version/配额/工具调用封装 |
| `presets/functions.yaml` | 常用公式函数 |
| `presets/data_catalog.yaml` | 高频数据字段目录 |
| `presets/assets_db/*.yaml` | A/H/US/指数/期货资产字典 |

## 5. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| Tool name redline | 公式执行唯一工具名 `runMultiFormulaBatchStream` | 防止模型 unknown-tool 后乱试变体 |
| Session first | 新问题必须 `newSession` | 中间变量和结果必须隔离 |
| Fast path | 简单查数用 `fast_query`，不进公式链 | 降低失败率和成本 |
| User condition freeze | 禁止百分比/区间/宇宙/事件口径静默改写 | Agent 不能替用户改题 |
| Formula batch cap | 单批最多 10 条公式 | 控制超时和失败损失 |
| data_id discipline | `readData` 只能传 data_id，不能传 expression_id | 工具协议里最容易踩的坑要写死 |
| SSE + resume | deferred/stream 中断后用 `resumeJob` | 长任务必须可续传 |
| Version guard | `SKILL_VERSION_MISMATCH` 时 newSession + 重读规则 | skill 和工具签名要自愈 |
| Presets layer | 本地 data/function catalog 命中时零网络 | 常见字段应本地解析 |
| TopN output audit | readData 后重新排序、单调性校验、禁止展示中间表 | 结果呈现也要被规则治理 |

## 6. 对 HermesAlpha 的借鉴

1. **为每个工具链写硬协议**：工具名、参数、错误、重试、续传、字段含义都要进文档和测试。
2. **简单问题走 fast path**：不要让所有查询都进入自由公式/Agent 链路。
3. **公式/因子执行必须 session 隔离**：每个研究问题一个 task_id，防止变量引用跨任务污染。
4. **TopN 结果要二次排序验证**：服务端返回顺序不可信，最终表格必须按用户排序字段重排。
5. **配额和版本信息进入工具响应**：Agent 要能从返回体判断成本、版本、是否需要升级。

## 7. 对 ashare-audit 的借鉴

1. **审计用户条件冻结**：是否把“股息率 > 3%”改成 `>0.03`，是否扩大资产宇宙或事件口径。
2. **审计工具名和重试**：unknown-tool 后是否尝试变体，是否违反熔断。
3. **审计 session 隔离**：是否复用旧 session 的变量或 data_id。
4. **审计 data_id/expression_id**：是否把 expression_id 传给 readData。
5. **审计最终排序**：TopN 表是否按排序字段单调，是否照搬 readData 原始顺序。

## 8. 不该照搬的部分

- 这套 skill 极重，适合高价值数据工具，不适合所有小工具都写成上千行协议。
- 平台 API 是闭源服务端，迁移时要抽象 endpoint，避免把业务绑定到单一供应商。
- 规则过多会增加 Agent 读取成本，应按 fast path / standard path 分层加载。
- 中文公式 DSL 很强，但需要稳定语法解析和可解释错误，否则 LLM 修复会反复试错。

## 9. 结论

quant-buddy-skill 的价值在于把 Agent 工具调用从“模型自己猜”变成“协议驱动执行”。它对当前项目最大的启发是工具治理：session、版本、配额、错误熔断、字段口径和最终答案排序都应该成为可审计规则，而不是靠模型临场自觉。
