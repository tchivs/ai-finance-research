# wudao-mcp 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/jcdreamjc/wudao-mcp.git
> 分析基线：
> - `wudao-mcp`：commit `6874ef9b2f0be95ec6db1e26b1fefc28615ea0cd`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/wudao-mcp`
<!-- source-sync:end -->


> A 股只读 MCP 数据层 · 67 个结构化工具 · Agent 市场复盘/题材/资金/公告入口
> 源码: `src/wudao-mcp/`
> 原始仓库: <https://github.com/jcdreamjc/wudao-mcp>

---

## 一句话定位

`wudao-mcp` 是一个面向 AI Agent 的 A 股结构化数据 MCP Server。它不在本地实现采集代码，而是把行情、K 线、指数/ETF/可转债、涨停生态、板块轮动、资金流、龙虎榜、研报、事件日历、公告、估值、财务摘要、自选股和复盘 workflow 暴露为只读 MCP 工具。

对当前项目最有价值的不是具体 API，而是产品化的数据入口设计：Agent 先通过 `tools/list` 发现工具，再优先调用 workflow 级工具做复盘，必要时下钻到原子工具。它把“数据服务”包装成 Agent 能理解、能安全使用、能按 profile 裁剪的能力面。

---

## 最高价值借鉴点

| 借鉴点 | 位置 | 可复用价值 |
|---|---|---|
| 只读 MCP 边界 | `README.md`, `skills/wudao-stock-data/SKILL.md` | 明确“不交易、不投资建议”，让 Agent 接入数据而不越权 |
| 67 工具按领域组织 | `README.md` Available Tool Areas | 给 A 股数据能力做可发现目录，而不是散落函数 |
| workflow 优先 | `SKILL.md` Agent Behavior | 大问题先用 market replay/stock research，再下钻 atomic tools |
| profile 裁剪 | `?profile=short_term` 等 | 降低 Agent 工具面，减少误用和 token 噪音 |
| 市场化 Skill 文档 | `skills/wudao-stock-data/SKILL.md` | 告诉 Agent 何时使用、如何验证、如何保持安全边界 |
| 多客户端接入说明 | README 安装片段 | 同一 MCP 服务适配 Codex、Claude、Cursor、OpenClaw、Hermes、Coze 等 |

---

## 工具能力地图

```text
市场数据      stock search / K线 / 分钟线 / 市场概览 / 交易日历
指数品种      指数 / ETF / 可转债
涨停生态      涨停梯队 / 炸板 / 跌停 / 临近涨停 / 涨停统计 / 热点板块
资金与板块    资金流 / 板块分析 / 概念排行 / 概念成分 / 异动检测
市场情报      热榜 / 财联社新闻 / 研报 / 集合竞价 / 简报 / 龙虎榜
基本面        估值快照 / 财务摘要 / 股东结构
事件公告      公司事件 / 宏观日历 / 短线催化 / 官方公告 / 互动问答
自选股        分组 / 标签 / 备注 / 观察池
Workflow      market replay / stock research / limit-up review / theme research
```

---

## 推荐迁移方式

1. **MCP Tool Catalog**: 为当前项目的数据工具建立 `tools/list` 风格的能力目录，包含领域、输入、输出、边界。
2. **Workflow First**: 盘后复盘、个股研究、题材研究先走组合工具，减少 Agent 自己拼多次查询的错误率。
3. **Profile 参数**: 给短线、主题、个股、复盘、自选股等场景做工具面裁剪。
4. **Read-only Data Contract**: 数据工具只能返回事实和来源，不下单、不生成承诺式收益建议。
5. **Agent Discovery Page**: 把“什么时候该连这个数据源”写成机器可读推荐页，便于外部 Agent 发现。

---

## 和现有项目的互补

| 项目 | 已有强项 | wudao-mcp 补的空白 |
|---|---|---|
| `a-stock-data` | 单文件端点实现和数据源踩坑 | MCP 化、profile 化、Agent 工具发现 |
| `OpenAshare` | 本地研究台 UI 与 SSE 进度 | 外部 Agent 可直接接入的数据服务边界 |
| `a-share-watch-butler` | 定时盯盘闭环 | 可替换/补充其底层数据工具层 |
| `daily_stock_analysis` | 多端应用和推送 | 标准化 MCP 数据入口和 workflow 工具 |

---

## 注意事项

- 该仓库主要是文档、Skill 与远端 MCP 服务入口，不是可本地审计的数据采集实现。
- 使用前必须配置 API Key，并通过 `tools/list` 验证实际工具 schema。
- 对当前项目来说，优先学习 MCP 能力设计、profile 裁剪和只读边界，不应把它当作可完全替代本地数据底座的源码库。
