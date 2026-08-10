# joinquant-skill 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/gaaiyun/joinquant-skill.git
> 分析基线：
> - `joinquant-skill`：commit `2a0b794ef85c55cdb646dc84bfd7ce58f8b64434`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/joinquant-skill`
<!-- source-sync:end -->


> 聚宽策略生成与审计 Skill · API 知识库 · 模板 · AST lint · 因子库 · 研报抽取 · MCP server
> 源码: `src/joinquant-skill/`
> 原始仓库: <https://github.com/gaaiyun/joinquant-skill>

## 1. 一句话定位

joinquant-skill 是一个面向 AI Agent 的聚宽策略开发工具箱。它把 14 类聚宽 API 文档、5 个生产模板、静态 lint、因子注册表、单因子分析、研报抽取到策略代码，以及 MCP tools 都打包成可被 Agent 渐进读取和调用的能力。

最值得学的是“平台型代码生成的防幻觉工程”：先用模板生成，再用聚宽 API 白名单/黑名单和未来函数规则做 lint，最后才交给用户粘贴到聚宽编辑器。

## 2. 核心工作流

```text
User asks for JoinQuant strategy
    -> identify pattern: quick code / API question / code review
    -> load only relevant reference category
    -> start from template, modify, do not write from scratch
    -> run or mentally apply strategy_lint.py
    -> return ready-to-paste code
```

研报转策略路径：

```text
brokerage report text/PDF
    -> LLM extraction prompt
    -> ExtractedStrategy schema
    -> build_strategy_code()
    -> native jqfactor mapping or TODO manual compute block
    -> generated JoinQuant strategy.py
    -> lint
```

## 3. 关键文件

| 文件 | 作用 |
|------|------|
| `SKILL.md` | Agent 使用入口，14 类 API 渐进读取、模板和 lint 规则 |
| `references/01-14-*.md` | 聚宽 API 分门别类知识库 |
| `templates/01-05-*.py` | 单股、多因子、ETF 轮动、动量、均值回归模板 |
| `scripts/strategy_lint.py` | AST lint，抓不存在 API、未来函数、缺交易成本/滑点、禁用时段下单 |
| `scripts/api_search.py` | 在原始 API 文档中按关键词/正则搜索 |
| `factors/_base.py` | 因子元数据和注册表基础设施 |
| `factor_lab/single_factor/ic.py` | IC / Rank-IC / IC decay 分析 |
| `research_importer/parser/schema.py` | 研报抽取结果 dataclass schema |
| `research_importer/generator/strategy_code.py` | ExtractedStrategy 到聚宽策略代码 |
| `jqskill_mcp/server.py` | MCP server，暴露 lint、scaffold、factor、API search、research prompt 等工具 |

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| Progressive disclosure | 14 类 API 文档按触发词加载 | Agent 不应一次吞完整平台文档 |
| Template-first generation | 明确要求从模板改，不从零写 | 平台代码生成要复用已验证骨架 |
| Lint whitelist/blacklist | KNOWN_APIS + KNOWN_HALLUCINATIONS | 防止 LLM 编造平台 API |
| Future function checks | `get_price(start_date)` 无 count 警告 | 量化代码审计要懂平台级未来函数 |
| Mandatory settings | use_real_price、order_cost、slippage | 回测真实度门槛前置 |
| FactorMeta | name/category/direction/dependencies/issues | 因子不是代码片段，而是带元数据资产 |
| Native factor resolver | 本地因子名映射到聚宽 factor id | 优先用平台原生因子，降级手算 |
| Research schema | ExtractedStrategy 容错反序列化 | LLM 抽取结果要结构化且可降级 |
| MCP wrappers | 7 个 `jq_` 前缀只读工具 | Skill 能力可以变成跨客户端工具服务 |

## 5. 对 HermesAlpha 的借鉴

1. **平台适配要有知识库分层**：把聚宽、Qlib、Backtrader、内部 DSL 的 API 文档按场景切分，而不是全塞 prompt。
2. **策略生成必须模板优先**：模板里预埋交易成本、滑点、调度、回测口径，LLM 只改策略逻辑。
3. **引入平台 lint**：对每个平台建立 hallucinated API 黑名单、必要设置、未来函数规则。
4. **因子注册表资产化**：每个因子带经济解释、方向、数据依赖、已知问题和 native mapping。
5. **研报抽取要落 schema**：不能直接让 LLM 从 PDF 生成代码，要先抽取结构化策略。

## 6. 对 ashare-audit 的借鉴

1. **审计不存在 API**：识别 AI 从其他平台搬来的 `place_order`、`get_stock_data` 等幻觉调用。
2. **审计回测必备设置**：`use_real_price=True`、`set_order_cost`、`set_slippage` 是否存在。
3. **审计未来函数**：日期切片、`context.previous_date`、`count` 参数是否正确。
4. **审计下单时段**：`before_trading_start` / `after_trading_end` 中是否下单。
5. **审计研报转代码 trace**：生成的因子是否能追溯到 paper_excerpts 和 jq_dependencies_guess。

## 7. 不该照搬的部分

- 该项目专注 JoinQuant，迁移到其他平台要重建 API 白名单和未来函数语义，不能复用规则名。
- MCP tools 是只读安全面，若未来加入写文件/提交策略，需要更严格权限分层。
- 研报生成中的非 native 因子目前会生成 TODO placeholder，不能当成可直接生产策略。
- `standardlize` 这类聚宽拼写必须按平台原样保留，不要“修正”为通用写法。

## 8. 结论

joinquant-skill 的核心价值是把“AI 生成策略代码”变成可约束流程：按场景加载文档、从模板改、用 AST lint 抓平台错误、用因子元数据管理研究资产，再通过 MCP 暴露给任意 Agent 客户端。
