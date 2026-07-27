# a-share-watch-butler 快速概览

> A 股 AI 盯盘管家 · 多 Agent 定时链路 · 数据诚实性 · 命中率反馈再校准
> 源码: `/root/source/tmp/a-share-watch-butler/`
> 原始仓库: <https://github.com/nexaforgelab/a-share-watch-butler>

---

## 一句话定位

`a-share-watch-butler` 把 A 股盯盘拆成盘前、盘中、盘后、周末备战和单股查询五类可审计 Agent 链路。它的主控 `Orchestrator` 调度 MacroScout、CapitalFlow、TechAnalyst、AnomalyHunter、PoolScorer、ReviewAttributor、StockPicker、EventCalendar、Notifier 等子 Agent，默认生成本地 Markdown/JSON 报告，也可扩展飞书、企微、个人微信和邮件推送。

最值得学习的是它的“数据诚实性纪律”：所有输出都拆成 `objective`、`ai_interpretation`、`data_quality` 三层；LLM 不参与算数，失败数据标注待确认，不补造数值。

---

## 最高价值借鉴点

| 借鉴点 | 位置 | 可复用价值 |
|---|---|---|
| 三层输出模型 | `src/models.py` | 物理隔离客观数据、AI 解读、数据质量问题 |
| 多链路 Orchestrator | `src/orchestrator.py` | 盘前并行、盘中监控、盘后复盘、周末备战、单股查询 |
| SQLite 状态表 | `src/data/store.py` | 预测、异动、命中率、权重版本、周报、运行报告全部可追溯 |
| 盘后反馈闭环 | `ReviewAttributor` | 用命中率和因子有效性生成新权重版本，可回滚 |
| 配置驱动调度 | `config.yaml`, `src/scheduler.py` | cron、监控池、阈值、权重、数据源、推送渠道统一配置 |
| 轻量回测 | `src/backtest/backtest.py` | 胜率、平均收益、回撤和缺源 notes 的最小闭环 |
| 降级不崩溃 | `Orchestrator._safe_run()` | 子 Agent 异常写入数据质量，链路继续执行 |

---

## 工作流地图

```text
premarket
  MacroScout + CapitalFlow + TechAnalyst 并行
  -> PoolScorer 保存候选池预测
  -> Notifier 输出盘前情报

intraday
  AnomalyHunter 扫描 watch_pool
  -> Notifier 输出异动或平稳摘要

postmarket
  ReviewAttributor 验证盘前预测
  + CapitalFlow + PoolScorer
  -> 命中率/因子有效性/权重再校准

weekend
  EventCalendar + StockPicker
  -> 下周观察池和事件日历归档

query stock
  TechAnalyst + AnomalyHunter
  -> 单股技术/异动卡片
```

---

## 数据诚实性模型

| 字段 | 含义 | 规则 |
|---|---|---|
| `objective` | 数据源或代码计算结果 | 行情、均线、得分、命中率、收益等 |
| `ai_interpretation` | LLM 或模板解释 | 只能解释客观数据，不能补算 |
| `data_quality` | 失败、冲突、待确认、替代源 | 失败必须记录，不允许杜撰 |

这个模型应直接迁移到当前项目的报告、推送和 Agent 工具返回值中。

---

## 最适合迁移的模块

1. **LayeredCard**: 把所有报告统一为客观数据层、AI 解读层、数据质量层。
2. **Run Report**: 每次运行记录 run_id、task、card、agents、notifier、status。
3. **Weight Version Table**: 因子权重版本化，自动调整必须保留 parent 和 reason。
4. **Safe Agent Runner**: 单个 Agent 失败时降级继续，并写入 `data_quality`。
5. **Scheduler CLI**: 所有定时任务也能 `--once --dry-run` 手动验收。
6. **Data Source Fallback**: 东财失败后腾讯/Yahoo/AkShare/Tushare 分层兜底，并说明字段缺失。

---

## 注意事项

- 当前回测是轻量模式，历史资金、事件、估值缺源时按中性值处理，不能当生产级策略评测。
- `PoolScorer` 是解释型多因子排序，不是严格 alpha 模型。
- 公开数据接口易变，生产环境应加强 provider 限流、缓存和字段契约验证。
- 推送渠道默认关闭，远端凭证只通过环境变量读取。
