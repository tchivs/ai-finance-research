# ai-berkshire 快速概览

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

## 一句话定位

`ai-berkshire` 是一个以 Markdown Skill 为核心的价值投资研究工作台。它把巴菲特、芒格、段永平、李录四种视角固化为可复用的研究流程，再用精确计算、数据交叉验证和报告抽检约束 AI 输出。它不是行情交易系统，也不是独立运行的服务端应用。

## 当前结构

```text
skills/*.md                 Claude Code 的 canonical workflow（20 个）
codex-skills/*/SKILL.md     从 skills 生成的 Codex 包
codex-prompts/*.md          可选的 Codex slash prompt 兼容层
tools/*.py                  财务验算、数据获取、筛选、回测、报告审计
tests/*.py                  financial_rigor 与 report_audit 的回归测试
scripts/                    跨客户端同步和安装脚本
reports/                    按公司、行业、主题落档的研究结果
data/                       基础面、观察列表和回测输入
docs/                       路线图和方法文档
assets/                     架构图、收益图和发布素材
```

## 核心工作流

```text
研究问题
  -> quality-screen / industry-funnel 初筛
  -> investment-research 或 investment-team 深研
  -> financial-data 取数与 financial_rigor.py 验算
  -> report_audit.py 抽检报告数据点
  -> reports/ 归档，并由 thesis-tracker 持续复核
```

复杂任务由 Team Lead 拆成四个视角并行研究；轻量任务直接调用单个 Skill 和工具。`/deep-research` 是 Claude Code 客户端的外部能力，不属于本仓库 20 个 Skill。

## 20 个 Skill 的分组

- 深度研究：`investment-research`、`investment-team`、`management-deep-dive`、`private-company-research`、`deep-company-series`
- 财报与发布：`earnings-review`、`earnings-team`、`wechat-article`
- 行业与筛选：`industry-research`、`industry-funnel`、`quality-screen`、`bottleneck-hunter`、`investment-checklist`
- 组合与追踪：`income-investment`、`portfolio-review`、`thesis-tracker`、`thesis-drift`、`news-pulse`
- 思维与数据：`dyp-ask`、`financial-data`

## 最值得借鉴的设计

1. **canonical workflow**：`skills/*.md` 是唯一真源，脚本生成 Codex 兼容层，避免双平台版本漂移。
2. **研究质量门**：信息充分度 A/B/C 分级、双源核验、Decimal 精确算术、报告随机抽检组成闭环。
3. **事实与观点分离**：报告要求写清数据来源、估计值、置信度和反面论据，适合迁移到其他研究 Agent。

## 限制

- 主要资产是提示词、Markdown 和本地脚本，结论质量仍依赖模型、数据源和人工复核。
- `tools/` 的行情/财务脚本需要外部数据服务和相应凭据；仓库本身不提供数据授权。
- 报告目录是研究结果，不等同于当前源码行为；变更后必须重新阅读代码和调用路径。

## 常用命令

```bash
python3 scripts/sync-codex-skills.py
python3 scripts/sync-codex-skills.py --check
python3 -m unittest discover -s tests
python3 tools/financial_rigor.py --help
python3 tools/report_audit.py --help
```

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
