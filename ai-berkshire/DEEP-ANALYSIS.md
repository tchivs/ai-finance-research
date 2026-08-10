# ai-berkshire 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/xbtlin/ai-berkshire
> 分析基线：
> - `ai-berkshire`：commit `3de0ef252dc129532454d10750c5a46027b38b65`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/ai-berkshire`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `ai-berkshire`：`93aaec3229cb` → `3de0ef252dc1`

提交摘要：
- 3de0ef25 README：新增搭配 Claude Code 内置 /deep-research 的说明与两篇实战示例
- a7ed9332 添加泡泡玛特最新业绩深研报告（2025年报复核+2026H1前瞻），更新thesis追踪记录
- 4ddc638f 添加梁文锋CUDA护城河核查公众号文章（20260801）；gitignore新增公司品牌图目录忽略规则
- d3941421 添加《时代α筛选：中国AI产业链》202608：光模块与国产算力双主线筛选，五维度验证+估值锚点+拐点清单，数据截至2026-08-04/05
- 4d2355da 添加《看懂理想汽车》系列4篇（2026-08版）：认知重置与护城河/两场豪赌/财务拆解/管理层与决策终章，数据基准2026-07-31，经跨篇一致性核查与事实修订
- ac606f84 添加《看懂英伟达》20260801版系列：5篇正文+系列说明（数据基准2026-07-31，纳入7月云厂商财报季/AMD大会/OpenAI担保谈判增量）
- 06672ac3 新增浦发银行投资研究报告（20260805）：数据双源验证+抽检准出，结论=观望，8.4元以下转高股息配置
- cff8b603 修订第02篇：五组并行事实核查后更正数据与口径
受影响路径：
- `A .editorconfig`
- `A .github/ISSUE_TEMPLATE/bug_report.yml`
- `A .github/ISSUE_TEMPLATE/config.yml`
- `A .github/ISSUE_TEMPLATE/data_error.yml`
- `A .github/ISSUE_TEMPLATE/other.yml`
- `A .github/ISSUE_TEMPLATE/suggestion.yml`
- `M .gitignore`
- `M AGENTS.md`
- `M CLAUDE.md`
- `A CODE_OF_CONDUCT.md`
- `A CONTRIBUTING.md`
- `M README.md`
- 其余 468 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->

## 1. 系统边界与资产形态

项目的运行时不是一个常驻服务，而是“客户端读取 Skill、Skill 调工具、结果写报告”的文件型研究系统。入口主要是 `skills/*.md` 中的工作流说明；`tools/*.py` 提供确定性计算和数据适配；`reports/`、`data/`、`实盘记录/` 保存研究状态和证据。

源码树中有 20 个 Claude Code Skill、对应的 `codex-skills/` 生成物和可选的 `codex-prompts/` 兼容层。`AGENTS.md` 明确规定 `skills/*.md` 是 canonical source，不能直接把生成物当成手工维护的第二套实现。

## 2. 控制流与平台兼容

```text
用户问题
  -> Claude command / Codex skill
  -> 单 Skill 或 Team Lead
  -> 外部搜索、工具脚本、报告模板
  -> reports/<公司或主题>/...
```

团队型入口把任务拆成商业模式、财务估值、行业竞争、风险管理四个视角；`investment-research` 适合单公司完整研究，`investment-team` 适合并行协作。`earnings-team` 进一步增加编辑和读者评审，`thesis-tracker`/`thesis-drift` 将一次性研究变为持续核对。

同步链由 `scripts/sync-codex-skills.py` 实现：读取 `skills/*.md` 的 front matter 和正文，补充 Codex 元数据与适配说明，写入 `codex-skills/<name>/SKILL.md`。安装脚本再把 Claude commands、Codex skills 或 prompts 放到客户端目录。该链路的关键不是文件复制，而是把提示词规则、工具路径和数据截止日期约束一起传播到不同 Agent 平台。

## 3. 质量门与确定性工具

`tools/financial_rigor.py` 是无第三方依赖的 Python CLI，使用 `decimal.Decimal`，提供：

- `verify-market-cap`：股价 × 总股本与报告市值对比；
- `verify-valuation`：PE、PB、ROE、FCF yield 等派生指标；
- `cross-validate`：按容差比较多个来源；
- `benford`：对数字首位分布做异常提示；
- `calc` 与 `three-scenario`：精确表达式和三情景估值。

`tools/report_audit.py` 将 Markdown 表格和正文中的金额、百分比、倍数提取成数据点，再按比例抽样并输出准出/打回所需的核验结果。它处理全角负号、表格负数、GBK 终端和异常绝对值，这些边界由 `tests/test_report_audit.py` 与 `tests/test_financial_rigor.py` 锁定。

其他工具按数据域拆分：`ashare_data.py`、`twstock_data.py`、`xueqiu_scraper.py` 负责数据获取，`stock_screener.py` 与 `momentum_backtest*.py` 负责筛选/回测，`morningstar_fair_value.py` 和 `star_history_chart.py` 提供补充数据与素材。它们依赖外部网络或本地凭据，不能把脚本成功运行误认为数据已被独立验证。

## 4. 报告结构与状态

研究输出按公司目录、行业/主题根目录和组合文件分层。团队报告通常保留四个视角、综合报告和读者评审；长期跟踪使用 thesis 文件；财报、行业漏斗、公众号文章使用带日期的文件名。`CLAUDE.md` 要求事实、观点、估计和不确定项分开，关键财务数据至少两个独立来源交叉验证。

该设计形成一个轻量状态机：研究问题 -> 筛选 -> 深研 -> 验算/审计 -> 发布 -> thesis 复核。状态主要存在 Markdown 文件和 Git 历史中，没有中心数据库，因此可审计、可迁移，但也容易出现命名漂移、报告与代码脱节和重复结论。

## 5. 当前远端变更的结构影响

本次从旧本地基线切换到 `3de0ef252dc1` 后，结构变化不只是新增报告：

- README 已明确为 **20 个 Skill**，新增/补齐 `income-investment`、`thesis-drift` 等入口，并增加与 Claude Code `/deep-research` 的协作说明；
- `AGENTS.md`、`CONTRIBUTING.md`、`SECURITY.md` 和 Issue 模板补齐了双平台协作、质量门和项目治理；
- `codex-skills/` 与 `codex-prompts/` 的生成/兼容边界更清楚，安装脚本成为跨客户端的正式入口；
- 报告资产大量扩展到 AI 产业链、公司系列研究、财报复核和公众号发布，但这些报告属于证据资产，不能直接替代最新源码分析。

## 6. 可迁移模式与限制

适合迁移的是“canonical workflow + 生成适配层”“确定性工具负责算术、模型负责解释”“发布前抽样审计”和“事实/观点/置信度分离”。迁移时应保留工具的输入输出协议和报告模板，而不是照搬四大师角色或具体估值阈值。

不应照搬的部分包括：依赖特定 Claude/Codex 客户端能力、把外部数据服务视为稳定接口、用 Markdown 目录代替高并发状态存储，以及把历史报告中的价格和收益数字当成当前事实。下一次同步应重点复核 Skill 数量、生成物一致性、工具 CLI 参数、报告命名和外部数据源可用性。

## 7. 验证范围

- 已基于 `3de0ef252dc1` 建立 codebase-memory 索引；索引显示主要源码是 Markdown，Python 代码集中在工具和两组测试。
- 已核对 README、AGENTS/CLAUDE 指令、`skills/`、`codex-skills/`、`tools/`、`tests/`、`reports/` 和同步脚本。
- 未执行需要外部行情、FinMind、雪球或大模型凭据的在线研究命令；相关运行结果仍待实际环境验证。
