# magpie 深度分析

> local daemon · Node HTTP API · Python data worker · SQLite state · alert rule engine · digest scheduler
> 源码: `/root/source/tmp/magpie/`
> 原始仓库: <https://github.com/SymbolStar/magpie>

## 1. 架构定位

magpie 是一个轻量本地服务。它的目标不是完整投研，而是作为 Agent 或用户的盯盘边车：查行情、查资金流、看 K 线、设提醒、推 digest。

架构很清楚：

```text
CLI / HTTP API
    src/cli.ts
    src/server.ts

State
    src/db.ts -> ~/.magpie/magpie.db

Runtime loops
    src/poller.ts
    src/scheduler.ts

Rule engine
    src/engine.ts

Notification
    src/notify.ts

Data worker
    python/fetch.py

Agent instruction
    skill/SKILL.md
```

## 2. SQLite schema

`src/db.ts` 使用 better-sqlite3，并设置：

```text
journal_mode = WAL
foreign_keys = ON
```

表结构：

```text
watchlist
    code primary key
    name
    group
    note
    created_at

alert_rules
    id
    code
    type in gte/lte/breakout/breakdown
    threshold
    channel
    note
    enabled
    cooldown_s
    created_at
    last_fired_at

alert_history
    rule_id
    code
    type
    threshold
    price
    message
    delivered
    fired_at

quote_cache
    code
    payload
    updated_at
```

这是本地工具很合理的状态最小集：自选、规则、触发历史和短期行情缓存。

## 3. Rule engine

`src/engine.ts` 的 `shouldFire()` 覆盖四类规则：

```text
gte        price >= threshold
lte        price <= threshold
breakout   price >= threshold AND prevClose < threshold
breakdown  price <= threshold AND prevClose > threshold
```

它还先检查：

```text
rule.enabled
q.price != null
cooldown_s not active
```

`evaluateQuote()` 对当前 code 的 enabled rules 逐条评估，触发后：

```text
formatMessage
notify(channel)
recordAlert(delivered)
markRuleFired(now)
return fired/matched counts
```

breakout/breakdown 与 gte/lte 的分离很重要：前者要求从昨日收盘跨过阈值，后者只是当前价格满足条件。

## 4. Poller: 市场状态驱动的轮询频率

`src/poller.ts` 的频率：

```text
morning/afternoon: 5s
pre/lunch/post: 5min
closed: 30min
```

`tick()` 做：

```text
listWatches
pyQuote(codes)
cacheQuote for each quote
if isMarketOpen and price exists:
    evaluateQuote
```

即使非交易时段也会 tick，因为 digest 需要 stale snapshot。规则触发只在实际开市时做，避免休市重复触发。

## 5. Scheduler: 简易固定时间任务

`src/scheduler.ts` 不依赖 cron，而是每分钟 tick 一次，按 Asia/Shanghai 计算：

```text
morning digest: 09:25
evening digest: 15:30
weekly digest: Friday 15:35
```

`lastRun` 用日期 key 防止同一天同一任务重复跑。调度前检查 `isTradingDay()`。

这种轻量调度适合本地 daemon，不需要 APScheduler/Celery 之类重依赖。

## 6. HTTP API

`src/server.ts` 暴露本地 API：

```text
GET  /api/v1/health
GET  /api/v1/quote/:code
GET  /api/v1/quotes?codes=A,B
GET  /api/v1/flow/:code
GET  /api/v1/kline/:code?period=daily&days=30
GET  /api/v1/lhb?date=YYYY-MM-DD
GET  /api/v1/digest?type=morning|evening|weekly
GET  /api/v1/watchlist
POST /api/v1/watchlist
DELETE /api/v1/watchlist/:code
GET  /api/v1/alerts
POST /api/v1/alerts
DELETE /api/v1/alerts/:id
GET  /api/v1/alerts/history?days=7
```

`GET /quote/:code` 先查 4 秒内缓存，命中直接返回，未命中才调用 Python worker。这个短缓存让 Web/Agent 高频查询不会每次打上游。

## 7. CLI surface

`src/cli.ts` 通过 commander 提供同等能力：

```text
magpie start
magpie quote <code>
magpie watch add/rm/ls
magpie alert add/ls/rm/history
magpie poll-once
magpie test-fire <code> <price>
magpie status
magpie flow <code>
magpie kline <code>
magpie lhb
magpie digest <type> [--push]
```

`test-fire` 是一个好设计：它允许注入 synthetic quote 来 smoke test 规则触发，不需要等真实行情。

## 8. Data worker

`python/fetch.py` 把数据抓取放到 Python worker：

| 数据 | 来源 | 说明 |
|------|------|------|
| quote | Sina primary | GBK、5s 延迟、A 股字段齐全 |
| quote fallback | Tencent | Sina 失败时回退 |
| flow | Eastmoney push2 fflow | 主力/超大/大/中/小单，约 60s 延迟 |
| kline | Eastmoney push2his | daily/weekly/monthly，最多 1000 rows |
| lhb | Eastmoney datacenter | 龙虎榜，18:00 后稳定 |

代码规范化 6 位代码到 `sh/sz/bj` 前缀，支持 ETF 和北交所前缀识别。

输出字段包括 `source`、`delaySec`、`fetchMs`、`timestamp`，这对 Agent 回答是否需要披露延迟非常有用。

## 9. Digest generator

`src/digest.ts` 生成结构化 digest：

```text
type
generatedAt
watchCount
quotes
topGainer
topLoser
fundFlow for evening
weeklyChange for weekly
markdown
```

它在全红或全绿时有细节处理：全跌时不说“涨幅最大”，而说“抗跌最强”；全涨时说“涨幅最小”。这类文案细节适合迁移到报告生成器。

## 10. Agent skill boundary

`skill/SKILL.md` 明确：

```text
Use for A-share quote, flow, kline, watchlist, alerts, digest, lhb
Do not use for US/HK/crypto, technical analysis, order execution, news/sentiment
```

它要求先 `/health`，并给出股票名称映射、歧义处理、资金流单位转换、提醒类型选择和失败话术。

这说明 Agent 工具不仅需要 API，还需要“何时用、何时不用、怎么回答”的行为规范。

## 11. 对当前项目的迁移模式

| 需求 | magpie 模式 |
|------|-------------|
| 轻量行情边车 | 本地 HTTP + Python worker + short cache |
| 提醒系统 MVP | watchlist + alert_rules + cooldown + history |
| 本地 Agent 工具 | localhost API + SKILL.md |
| 调度 digest | minute tick + Shanghai market calendar |
| 数据源主备 | Sina primary + Tencent fallback |
| 规则测试 | synthetic `test-fire` |

## 12. 风险与改造建议

| 风险 | 建议 |
|------|------|
| API 无认证 | 只绑定 localhost，公网必须加 token |
| 公共数据 best-effort | 在回答和日志中保留 source/delaySec |
| Python worker subprocess 成本 | 批量调用或长期 worker 化 |
| 单通道通知 | 抽象 channel config 和重试策略 |
| 市场日历简化 | 接入交易日服务或本地 calendar |

## 13. 结论

magpie 是“做少但做稳”的样本。它没有复杂 Agent 推理，却把监控最小闭环做完整：自选股、行情、规则、冷却、通知、digest、HTTP API 和 skill 边界。对当前项目而言，它适合作为盯盘边车、提醒 MVP 和 Agent 本地工具的参考。
