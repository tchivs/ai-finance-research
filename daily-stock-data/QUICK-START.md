# daily_stock_data 快速概览

> 源码：`/root/source/tmp/daily_stock_data/`
> 原始仓库: <https://github.com/bzcsk2/daily_stock_data>
> 分析基线：`e0efc471e5350e08c58018cb49ba0e215cf1fb92`（2026-06-25）
> 源码复核：2026-07-10，详见 [首批源码落地验证](../19-首批源码落地验证.md#3-daily_stock_data)

## 一句话定位

`daily_stock_data` 不是投研 Agent，也不是分析看板，而是一个面向 A 股的轻量数据采集底座：用 shell wrapper + Python 脚本 + CSV/PostgreSQL 双后端，把日线、5 分钟线、腾讯快照、Tushare/TickFlow 基础资料、pytdx 参考数据稳定落盘。

它的最大价值不是“功能多”，而是把个人采集流程开源化时该有的边界做清楚：无数据库也能跑，长期运行可切 PostgreSQL，数据契约独立成文档，CI 检查脚本语法、Python 编译、CSV 存储语义和私有路径泄漏。

## 核心模块

| 模块 | 作用 | 可借鉴点 |
|------|------|----------|
| `bin/run_*.sh` | cron/手工运行入口 | 每个采集任务一个包装器，统一回项目根目录、读 `.env`、建 `logs/`、设 `PYTHONPATH` |
| `scripts/storage_common.py` | CSV/PostgreSQL 存储开关 | `STORAGE_BACKEND=csv/postgres/both`，CSV 原子写、append-upsert、区间替换 |
| `scripts/kline_common.py` | K 线公共层 | A 股 universe、指数清单、交易日、代码转换、日志和 DB 连接 |
| `scripts/get_new_daily.py` | 日线增量同步 | Tushare -> TickFlow -> baostock 异常 fallback，repair-days 回补；空结果当前不会继续降级 |
| `scripts/get_new_5min.py` | 5 分钟线同步 | 分钟线区间修复、交易时段外异常 bar 过滤 |
| `scripts/download_quotes_tencent.py` | 腾讯行情快照 | 统一快照表、盘口五档、涨跌停派生字段、`latest_tick` 当前态 |
| `scripts/sync_tdx_*.py` | pytdx 参考数据 | 除权除息、财务快照、板块、逐笔、F10 章节分频同步 |
| `docs/SCHEMAS.md` | 数据契约 | 表字段、主键、时间语义、CSV 规模边界写清楚 |
| `.github/workflows/ci.yml` | 质量门 | ruff、py_compile、pytest、shell syntax、私有路径泄漏检查 |

## 最值得吸收的设计

1. **双后端不是 ORM 化，而是运行模式化**

   CSV 是默认体验，PostgreSQL 是长期运行模式，`both` 是迁移/对账模式。这个设计比一开始强推数据库更适合个人和 Agent 场景。

2. **CSV 也有工程纪律**

   `write_csv_table()` 使用临时文件 + `os.replace()` 原子替换；`append_upsert_csv()` 以主键列去重保留最新；`replace_csv_slice()` 只替换某个 symbol 的日期窗口，不误删其他标的。

3. **脚本入口与业务脚本分离**

   cron 调 `bin/run_*.sh`，采集逻辑在 `scripts/`。包装器负责环境、日志、目录，Python 只管业务。这一点非常适合复制到数据采集类项目。

4. **数据契约先于分析**

   `docs/SCHEMAS.md` 明确 `daily_ohlcv`、`index_daily`、`min5_ohlcv`、`quote_snapshots_unified`、`latest_tick`、`stock_basic_tushare` 的字段和主键，降低下游分析对上游脚本的隐式依赖。

5. **开源边界写得干净**

   仓库明确不包含个人数据库、dump、密钥、日志、运行数据和完整 F10 正文；CI 还检查私有路径泄漏。这是从个人脚本走向开源项目时很容易漏掉的一环。

## 适合当前项目的落地点

| 当前项目 | 可落地能力 | 优先级 |
|----------|------------|--------|
| ashare-audit | 把审计输入数据落成 `DATA_DIR` CSV + 可选 PostgreSQL，先复用 append-upsert/区间替换语义 | P1 |
| HermesAlpha | 给行情和基本面缓存加 `csv/postgres/both` 模式，报告分析只读契约表 | P1 |
| 所有项目 | CI 增加“私有路径/密钥/本地目录泄漏”检查 | P1 |

## 不建议直接照搬的地方

- 过程式脚本较多，复杂度继续上升时需要注册表/任务编排层。
- CSV 模式读全表再写，长期高频任务会有 IO 压力，适合日线和试用，不适合逐笔/F10 大规模沉淀。
- 日线表当前缺少每行 `source/fetched_at/adjust_flag`，跨 provider 降级后主要靠日志追溯，建议下游实现时补上。
- `both` 是 CSV 后写 PostgreSQL 的顺序双写，不具备跨后端事务；PG 失败时可能只留下 CSV 结果。
- provider 只有抛异常才 fallback；返回空 DataFrame 会结束调用链，自己的实现应显式定义空结果是否降级。
