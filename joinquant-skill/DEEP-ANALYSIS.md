# joinquant-skill 深度分析

> JoinQuant API skill · strategy lint · factor registry · research importer · MCP server
> 源码: `/root/source/tmp/joinquant-skill/`
> 原始仓库: <https://github.com/gaaiyun/joinquant-skill>

## 1. 架构定位

joinquant-skill 是一个“平台型 Agent Skill”。它并不直接跑交易，而是帮助 AI 生成、审阅和解释可以粘贴到 JoinQuant 在线编辑器运行的策略代码。

整体结构：

```text
Knowledge layer
    references/01-14-*.md
    api文档/api.txt

Generation layer
    templates/01-05-*.py
    scripts/strategy_scaffold.py

Audit layer
    scripts/strategy_lint.py

Factor layer
    factors/*
    factor_lab/*

Research import layer
    research_importer/*

Tool service layer
    jqskill_mcp/server.py
```

## 2. SKILL.md: Agent 的路由器

`SKILL.md` 先把用户请求分为三类：

| Pattern | 行为 |
|------|------|
| Quick code | 选模板、修改、返回可粘贴代码 |
| API question | 只读取相关 reference category 回答 |
| Code review | 对用户代码应用 strategy_lint 规则 |

最重要的是渐进披露：14 个 API 类别分别放在 `references/01-14-*.md`，Agent 根据关键词只读相关文件。这样既省上下文，也减少不同 API 类别混淆。

## 3. strategy_lint.py: 聚宽代码的 AST 审计

`scripts/strategy_lint.py` 的核心是 `StrategyLinter(ast.NodeVisitor)`。

它维护：

```text
KNOWN_APIS
KNOWN_HALLUCINATIONS
DEPRECATED_APIS
_THIRD_PARTY_MODULES
_PYTHON_BUILTINS
```

并在 `visit_Call()` 中做多类检查：

| Code | 检查 | 例子 |
|------|------|------|
| JQ001 | 不存在 API | `get_stock_data`, `place_order`, `buy_stock` |
| JQ002 | 废弃 API | `update_universe`, `set_universe` |
| JQ003 | 未来函数风险 | `get_price` 用 `start_date` 但无 `count/end_date` |
| JQ004 | 非交易时段下单 | 在 `before_trading_start` 调 `order_target` |
| JQ005 | strict 白名单检查 | 疑似聚宽 API 但不在白名单 |

它还追踪必备设置：

```text
set_option('use_real_price', True)
set_order_cost(...)
set_slippage(...)
initialize() exists
```

这种 AST lint 是量化 Agent 代码生成的底线能力。正则可以抓一部分错误，但 AST 能区分函数调用、当前函数作用域和参数结构。

## 4. MCP server: 把 skill 能力服务化

`jqskill_mcp/server.py` 暴露 7 个只读工具：

```text
jq_list_factors
jq_get_factor
jq_resolve_factor_id
jq_lint_strategy
jq_scaffold_strategy
jq_search_api
jq_build_research_extract_prompt
```

设计原则很稳：

| 原则 | 实现 |
|------|------|
| 避免包名冲突 | 目录叫 `jqskill_mcp`，不叫 `mcp` |
| Pydantic schema | 每个 tool 有输入模型和约束 |
| 只读工具 | 不修改用户文件、仓库或远程服务 |
| 统一错误 | `_format_error()` 返回可操作修复建议 |
| 测试友好 | tool 内部走 `*_impl` 同步函数，不装 mcp 也能测 |
| 命名前缀 | 全部 `jq_`，避免多 MCP server 冲突 |

这是一种把 Skill 从“提示词文件”升级为“工具服务”的参考实现。

## 5. Factor registry: 因子作为可检索资产

`factors/_base.py` 定义：

```text
FactorMeta
    name
    chinese_name
    category
    description
    paper_refs
    direction
    jq_dependencies
    recommended_neutralization
    universe_hint
    known_issues

FactorEntry
    meta
    compute_jq
    compute_local
    module
```

全局注册表不允许重复注册 name，`search()` 会按 name、中文名、描述和论文引用模糊匹配。

这比把因子散落成函数更好：Agent 可以先看因子经济含义、方向、数据依赖和适用股票池，再决定是否生成代码。

## 6. Factor Lab: 单因子验证语义

`factor_lab/single_factor/ic.py` 给出 IC / Rank-IC 分析：

```text
compute_ic(factor_panel, returns_panel, method, forward_periods)
ic_decay(factor_panel, returns_by_horizon, method)
```

`ICReport` 包含：

```text
ic_mean
ic_std
ic_ir
ic_ir_annualized
ic_t_stat
ic_win_rate
positive_n
total_n
```

一个好点是它明确要求 `returns_panel` 已经是前向收益，不在函数里隐式 shift。这减少了未来函数和 horizon 歧义。

## 7. Research Importer: 研报先抽结构，再生成代码

`research_importer/parser/schema.py` 用 dataclass 定义抽取结果：

```text
ExtractedFactor
    name
    chinese_name
    category
    definition
    formula
    weight
    direction
    paper_excerpts
    jq_dependencies_guess

ExtractedStrategy
    title
    source
    rebalance_freq
    universe
    primary_factors
    secondary_factors
    benchmark
    fee_rate
    slippage
    risk_constraints
    confidence
```

`from_dict()` 会忽略未知字段，并为缺失必填字段补默认值。这是为了处理 LLM JSON 常见问题：多字段、少字段、格式漂移。

## 8. Strategy generator

`research_importer/generator/strategy_code.py` 将 `ExtractedStrategy` 转成聚宽策略模板。

关键策略：

| 设计 | 说明 |
|------|------|
| `_UNIVERSE_MAP` | 从“沪深300/中证800”等文本识别指数代码 |
| `_SCHEDULE_SNIPPETS` | daily/weekly/monthly 调度模板 |
| `_resolve_native_id()` | 查本地因子到聚宽官方 factor id 的映射 |
| duplicate slug handling | 多个因子同名时加 `_2/_3`，防止静默覆盖 |
| 权重归一化 | `sum(abs(w))` 归一 |
| non-native placeholder | 非 native 因子生成 TODO 手算块 |

生成模板内强制设置：

```text
set_benchmark
set_option('use_real_price', True)
set_order_cost
set_slippage
run_daily/run_weekly/run_monthly
end_date=context.previous_date
```

这说明代码生成器本身也承担风控职责。

## 9. 对当前项目的迁移模式

| 需求 | 可迁移模式 |
|------|------------|
| 生成 Qlib/Backtrader/聚宽策略 | template-first + platform-specific lint |
| 审计 AI 代码 | AST visitor + platform whitelist/blacklist |
| 管理因子 | FactorMeta + registry + native mapping |
| 研报转策略 | ExtractedStrategy schema + generator + lint |
| 跨客户端调用 | MCP server with readOnly tools |

## 10. 风险与改造建议

| 风险 | 建议 |
|------|------|
| 白名单不全导致误报 | 分 severity，strict 模式才报未知 API |
| 黑名单依赖经验积累 | 从实际失败案例持续补充 |
| 非 native 因子生成 TODO | 不允许直接标记为可运行策略 |
| 聚宽平台变更 | reference 和 lint 规则要版本化 |
| 研报抽取置信度虚高 | 要求 paper_excerpts 和人工 review |

## 11. 结论

joinquant-skill 是“AI 策略代码生成”走向可用的关键参考。它把平台知识、模板、lint、因子元数据和 MCP 工具面结合起来，核心理念是：LLM 可以生成策略，但平台约束、未来函数、交易成本和 API 真伪必须由工程规则兜底。
