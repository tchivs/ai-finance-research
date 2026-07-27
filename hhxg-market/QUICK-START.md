# hhxg-market 快速概览

> 恢恢量化 A 股数据助手 · 零依赖 Python skill · 日报快照/日历/两融/快讯 · OpenAPI 公开接口
> 源码: `/root/source/tmp/hhxg-top-hhxg-python/`
> 原始仓库: <https://github.com/Niceck/hhxg-top-hhxg-python>

## 1. 一句话定位

hhxg-market 是一个零依赖 A 股量化数据 skill。它不要求安装第三方 Python 包，只用标准库从 `hhxg.top/static/data` 拉 JSON，再格式化成 Agent 易读的 Markdown 报告。

它最值得学的是“公开静态数据 + skill 脚本”的低摩擦形态：数据由网站每日生成，Agent 只负责读取、缓存、分板块展示和回答组织。

## 2. 能力范围

| 脚本 | 数据 | 用途 |
|---|---|---|
| `fetch_snapshot.py` | 盘后日报快照 | 赚钱效应、热门题材、连板天梯、游资龙虎榜、行业资金、焦点新闻 |
| `calendar.py` | A 股日历 | 交易日、限售解禁、业绩预告、期货/期权交割日 |
| `margin.py` | 近 7 日融资融券 | 融资余额、融券余额、净买入/净卖出 TOP |
| `news.py` | 实时财经快讯 | 最新新闻流，按时间倒序 |
| `_common.py` | 共用工具 | HTTP、缓存、schema 检查、参数解析 |

所有脚本支持 `--json` 输出原始 JSON。

## 3. 核心工作流

```text
Agent asks about A-share market
    -> choose script by intent
    -> fetch static JSON from hhxg.top/static/data
    -> retry once on network error
    -> save ~/.cache/hhxg-market cache
    -> fallback to cache if network unavailable
    -> format section-specific Markdown
```

## 4. 数据端点

脚本实际读取静态 JSON：

- `assistant/skill_snapshot.json`
- `calendar/trading_days_<year>.json`
- `calendar/delivery_<year>.json`
- `calendar/unlock_<yyyymm>.json`
- `calendar/earnings_<yyyymm>.json`
- `assistant/recent_margin_7d.json`
- `news/n0.json`

仓库还提供 `openapi.yaml`，定义公开 API：

- `GET /api/snapshot`
- `GET /api/margin`
- `GET /api/news?limit=20`
- `GET /api/calendar?type=trading|delivery|earnings|unlock&month=YYYY-MM`

所有接口标注 `x-openai-isConsequential: false`，适合只读 Agent 调用。

## 5. 最值得吸收的 5 点

1. **零依赖脚本**：只依赖 Python 标准库，适合分发给各种 Agent 环境。
2. **静态 JSON 数据层**：高频计算在服务端完成，skill 只读结果，降低 Agent 执行不确定性。
3. **缓存兜底**：网络失败后自动读取 `~/.cache/hhxg-market`，并向 stderr 标注缓存日期。
4. **schema 版本检查**：服务端 schema 比客户端新时提示升级 skill。
5. **回答范式写进 SKILL.md**：先结论、再展开、标注日期、非交易日提示、引导图表趋势。

## 6. 对 HermesAlpha 的启发

- 可把每日盘后聚合结果发布为静态 JSON，让 Agent/skill/前端都读同一份数据。
- 可先实现“最近交易日快照”，再做实时服务，降低系统复杂度。
- 可把复杂选股/回测留在网站或服务端，把当日完整数据慷慨暴露给 Agent。
- 可对 A 股市场情绪建立固定字段：赚钱效应、涨停、炸板、连板、游资、题材、行业资金。

## 7. 对 ashare-audit 的启发

- 审计每日快照时必须检查 `date` 是否是今天，非交易日要明确说明最近交易日。
- 静态数据 skill 要审计 schema_version 和缓存命中状态。
- 对“较昨日变化”的字段要审计比较基准是否来自同一数据源和同一口径。
- 对引流链接/趋势图链接要区分数据事实和产品引导。

## 8. 风险与局限

- 数据粒度是盘后/快照型，不适合做实时交易决策。
- 静态 JSON 依赖网站生成任务，若源站未更新，skill 只能返回最近交易日。
- 具体字段含义依赖 `references/data-schema.md` 和服务端 schema。
- 部分回答范式带产品引导，需要在严肃投研系统中明确标注。

## 9. 最小可迁移模式

```text
daily-market-snapshot
    static JSON publish
    openapi.yaml readonly endpoints
    zero-dependency Python skill
    ~/.cache fallback
    schema_version warning
    Markdown formatter per section
```

这是一种很适合 Agent 的 A 股“日报数据供应”模式：服务端算好，Agent 读好，审计系统查好。
