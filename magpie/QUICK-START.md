# magpie 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/SymbolStar/magpie.git
> 分析基线：
> - `magpie`：commit `177d8bb089c88448760afee69d8d64db8eb8d436`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/magpie`
<!-- source-sync:end -->


> 轻量 A 股监控 daemon · Node HTTP/CLI + Python 数据 worker · SQLite watchlist/alerts/cache · Feishu 通知 · OpenClaw skill
> 源码: `src/magpie/`
> 原始仓库: <https://github.com/SymbolStar/magpie>

## 1. 一句话定位

magpie 是一个本地 A 股盯盘小 daemon。它不做复杂投研，只做一件事：维护自选股和价格提醒，盘中轮询公共行情源，触发规则时推送通知，并提供 Agent 友好的 HTTP API 和 SKILL.md。

它最值得学的是“小而稳的监控工具边界”：本地 SQLite 保存状态，Node 负责 CLI/HTTP/poller/scheduler/rule engine，Python worker 负责抓 Sina/Tencent/Eastmoney 数据。

## 2. 核心工作流

```text
magpie start
    -> start Poller
    -> start Scheduler
    -> serve HTTP API on 127.0.0.1:17891

Poller tick
    -> listWatches()
    -> python fetch.py quote codes
    -> cacheQuote()
    -> if market open: evaluateQuote()
    -> notify fired rules
```

## 3. 关键文件

| 文件 | 作用 |
|------|------|
| `src/cli.ts` | Commander CLI，start/quote/watch/alert/status/flow/kline/lhb/digest |
| `src/server.ts` | 本地 HTTP API，quote/flow/kline/lhb/digest/watchlist/alerts |
| `src/db.ts` | better-sqlite3 schema 和 watchlist/rule/history/cache 操作 |
| `src/poller.ts` | 盘中 5s、闲时 5min、闭市 30min 的轮询循环 |
| `src/engine.ts` | alert rule engine，gte/lte/breakout/breakdown + cooldown |
| `src/scheduler.ts` | 09:25、15:30、周五 15:35 digest 调度 |
| `src/digest.ts` | morning/evening/weekly markdown digest |
| `src/notify.ts` | Feishu webhook / stdout 通知 |
| `python/fetch.py` | Sina/Tencent/Eastmoney quote/flow/kline/lhb worker |
| `skill/SKILL.md` | OpenClaw/Agent 调用本地 daemon 的使用规则 |

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| 本地 SQLite | watchlist、alert_rules、alert_history、quote_cache | 小工具不必上复杂数据库 |
| Poll cadence | 盘中 5s，午休/盘前/盘后 5min，闭市 30min | 轮询频率应跟市场状态绑定 |
| Rule types | `gte/lte/breakout/breakdown` | 简单阈值和突破/跌破语义分开 |
| Cooldown | 每条规则 `cooldown_s`，默认 30min | 防止同一提醒刷屏 |
| Quote fallback | Sina primary，Tencent fallback | 公共行情源必须主备 |
| Digest | 早盘、收盘、周报，输出 markdown | 通知内容可作为 Agent digest artifact |
| Local HTTP | `127.0.0.1:17891` 无 auth | 本机 agent 工具可用极简接口 |
| Skill docs | 明确何时 activate、何时不要 activate | 工具边界要写给 Agent 看 |

## 5. 对 HermesAlpha 的借鉴

1. **做轻量监控 daemon**：不是所有功能都进入主系统，quote/alert/digest 可拆成本地小服务。
2. **把市场状态用于调度频率**：盘中密集，休市稀疏，节省资源并减少封禁风险。
3. **提醒规则保持可解释**：gte/lte/breakout/breakdown 四类足够覆盖大多数价格提醒。
4. **digest 直接输出 markdown**：报告生成可以先做结构化对象，再附 markdown view。
5. **Agent skill 明确边界**：magpie 不做买卖建议、不做美港股、不做技术分析，避免工具滥用。

## 6. 对 ashare-audit 的借鉴

1. **审计提醒去重**：同一 rule 是否遵守 cooldown。
2. **审计突破语义**：breakout/breakdown 是否同时检查 prevClose。
3. **审计行情延迟**：quote 5s、flow 60s，应在回答中披露。
4. **审计数据源 fallback**：Sina 失败后是否尝试 Tencent，错误是否明确。
5. **审计本地 API 边界**：无 auth 只适合 127.0.0.1，不应直接公网暴露。

## 7. 不该照搬的部分

- magpie 的 HTTP API 本地无认证，公网部署必须加认证或只绑定 localhost。
- 公共行情源 best-effort，不能作为严肃回测或交易执行数据源。
- 它不支持 HK/US、不做技术指标、不做组合 PnL，迁移时不要夸大范围。
- 通知渠道目前主要 Feishu/stdout，生产系统要抽象多渠道配置和重试。

## 8. 结论

magpie 的价值是小而清晰：本地 watchlist、规则、轮询、通知和 Agent HTTP API。它适合当前项目学习“轻量监控边车”的设计，把高频盯盘和提醒从主研究系统中解耦出来。
