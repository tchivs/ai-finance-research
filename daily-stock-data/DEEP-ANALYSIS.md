# daily_stock_data 深度分析

> 源码：`/root/source/tmp/daily_stock_data/`
> 原始仓库: <https://github.com/bzcsk2/daily_stock_data>
> 分析基线：`e0efc471e5350e08c58018cb49ba0e215cf1fb92`（2026-06-25）
> 源码复核：2026-07-10，详见 [首批源码落地验证](../19-首批源码落地验证.md#3-daily_stock_data)

## 1. 项目定位：数据采集底座，而不是分析系统

其他项目大多围绕“研究、分析、Agent、交易执行”展开，`daily_stock_data` 的位置更底层：它负责把 A 股市场数据稳定采集、标准化并落盘。它不试图做 AI 结论、不做 Web UI、不做通知推送，反而因此有很强的可移植性。

它解决的是三个基础问题：

1. 没有数据库时，用户能不能直接开始采集；
2. 长期运行时，能不能切换到 PostgreSQL；
3. 下游分析系统能不能依赖稳定的数据契约，而不是反向读取采集脚本细节。

## 2. 分层架构

```
daily_stock_data
├── bin/                 # cron/手工运行包装器
├── scripts/             # 实际采集脚本与共享模块
│   ├── storage_common.py
│   ├── kline_common.py
│   ├── snapshot_unified_common.py
│   ├── tdx_common.py
│   └── sync/get/download 脚本
├── docs/                # 架构、脚本、数据源、数据契约、运维
└── tests/               # 当前重点覆盖 CSV 存储语义
```

这个结构很适合“先从个人脚本变成项目”的阶段：不引入任务平台，不强制数据库，不引入框架，但把运行入口、共享逻辑、文档契约拆开。

## 3. 存储层：`csv/postgres/both` 三模式

`scripts/storage_common.py` 是最值得借鉴的模块。

### 3.1 配置入口

```python
STORAGE_BACKEND=csv       # 默认，本地 CSV
STORAGE_BACKEND=postgres  # 只写 PostgreSQL
STORAGE_BACKEND=both      # CSV + PostgreSQL 双写
DATA_DIR=./data
```

代码层暴露三个基础判断：

```python
storage_backend()
use_csv()
use_postgres()
```

这种写法的好处是：采集脚本不需要关心部署形态，只在写入点判断当前 backend。

### 3.2 CSV 原子写

`write_csv_table()` 不是直接覆盖目标文件，而是先写临时文件，再 `os.replace()` 替换目标文件。这避免了脚本中断时留下半截 CSV。

可复用原则：

```
临时文件写完 -> 原子替换 -> finally 清理临时文件
```

### 3.3 append-upsert

`append_upsert_csv(df, table, key_columns)` 的语义：

1. 读旧 CSV；
2. 拼接旧数据和新数据；
3. 按主键列 `drop_duplicates(keep="last")`；
4. 按主键排序；
5. 原子写回。

这非常适合日线、基础资料这类中低频数据。

### 3.4 区间替换

`replace_csv_slice()` 用于 5 分钟线等需要“修复某个标的某段时间”的场景：

1. 读旧表；
2. 删除目标 symbol 在 `[start_date, end_date]` 窗口内的数据；
3. 拼入新数据；
4. 主键去重排序；
5. 写回。

关键点是只删目标 symbol 的窗口，不影响同一表其他标的。

## 4. K 线公共层：`kline_common.py`

`kline_common.py` 集中了 A 股采集的公共语义：

- A 股前缀白名单：`sh.600/601/603/605/688`、`sz.000/001/002/003/300/301` 等；
- 常用指数清单：上证综指、上证 50、沪深 300、科创 50、中证 500/1000、深成指、创业板等；
- `SymbolInfo` 数据类：`baostock_code/db_symbol/name/is_index`；
- Tushare code 与 baostock code 互转；
- 优先从本地 CSV 表加载 universe，再在 PostgreSQL 可用时从本地库加载；
- 统一日志与 PostgreSQL 连接配置。

这一层把“采集脚本应该处理哪些标的”从每个脚本里抽出来，避免日线、5 分钟线、回填脚本各自维护一份代码列表。

## 5. 日线增量同步

`scripts/get_new_daily.py` 的设计亮点：

| 设计 | 说明 |
|------|------|
| provider 顺序 | 股票日线优先 Tushare，其次 TickFlow，最后 baostock；指数走 baostock；当前只有异常会 fallback，空结果会直接返回 |
| `--repair-days` | 每次额外回补最近 N 个交易日，修复迟到数据和上游更正 |
| 连接池 | PostgreSQL 模式使用 `ThreadedConnectionPool` |
| 唯一索引自修复 | 如果补唯一索引遇到重复键，先按 `(time, symbol)` 去重再建索引 |
| CSV/PG 双路径 | `get_existing_dates()` 同时支持 CSV 和 PostgreSQL |
| 分批参数 | `--limit/--offset` 方便 cron 分批或测试 |

最值得学的是“增量同步 + 小窗口修复”的组合。只追加会错过上游修订；全量刷新又太重。`repair-days` 是实用折中。

## 6. 实时快照统一表

`scripts/download_quotes_tencent.py` 把腾讯/easyquotation 返回的字段映射成统一快照表：

- 当前价、开高低收、成交量/额；
- 涨跌额、涨跌幅、振幅；
- 总市值、流通市值、PE/PB；
- 涨跌停价与是否涨跌停；
- 五档 bid/ask；
- 原始字段留痕：`raw_volume/raw_turnover/raw_amount_wan`。

同时维护两个概念：

| 表 | 语义 |
|----|------|
| `quote_snapshots_unified` | 时间序列快照，主键 `snapshot_time, source, symbol` |
| `latest_tick` | 每个 symbol 的最新状态，CSV 模式每轮重写，PG 模式 upsert |

这对交易/风控系统很实用：历史回放和当前态查询分开建模。

## 7. pytdx 参考数据

pytdx 相关脚本覆盖：

- 除权除息/股本变化；
- 财务快照；
- 通达信板块与成分股；
- 逐笔成交；
- F10 章节与全文导出。

F10 同步按 daily/weekly/biweekly 分组，是一个很实际的“数据波动频率分层”设计：高频变化内容每天跑，低频章节不必每天抓。

## 8. 数据契约文档

`docs/SCHEMAS.md` 是这个项目最值得复制的文档：

| 表 | 主键/去重键 | 关键语义 |
|----|-------------|----------|
| `daily_ohlcv` | `time, symbol` | 股票日线，含估值字段和 ST 标记 |
| `index_daily` | `time, symbol` | 指数日线 |
| `min5_ohlcv` / `index_min5` | `time, symbol` | 5 分钟 bar，过滤交易时段外异常 |
| `quote_snapshots_unified` | `snapshot_time, source, symbol` | 快照时间序列 |
| `latest_tick` | `symbol` | 当前最新快照 |
| `stock_basic_tushare` | `ts_code` | Tushare 股票基础资料 |

对当前项目的启发：数据契约不应该埋在 ORM 或 DataFrame 列名里，应该独立成文档，并写明时间语义、主键、规模边界。

## 9. CI 与开源卫生

CI 做了五件具体的事：

1. `ruff check scripts tests`
2. `python -m py_compile scripts/*.py`
3. `pytest`
4. `for script in bin/run_*.sh; do bash -n "$script"; done`
5. grep 私有路径和本地敏感痕迹，防止 `/home/`、私有盘符、个人下载目录等泄漏。

第 5 条非常值得加到所有从个人脚本开源出来的项目里。很多项目代码能跑，但一开源就泄漏本地路径、手机号、账号目录或私有数据习惯。

## 10. 与 daily_stock_analysis 的区别

| 维度 | daily_stock_data | daily_stock_analysis |
|------|------------------|----------------------|
| 定位 | 数据采集底座 | AI 分析系统 |
| 用户入口 | cron/shell/Python 脚本 | Web/Desktop/Bot/GitHub Actions/Docker |
| 输出 | CSV/PostgreSQL 表 | 报告、看板、通知、聊天 |
| 架构复杂度 | 轻量脚本集 | 多端应用 + API + Agent |
| 最适合借鉴 | 数据契约、采集运行、存储模式 | 分析流程、数据源联邦、Bot、多端交互 |

二者不是替代关系，而是上下游关系：`daily_stock_data` 更像可以喂给 `daily_stock_analysis` 或 HermesAlpha 的数据底座。

## 11. 当前项目可吸收清单

| 能力 | 具体做法 | 适用项目 |
|------|----------|----------|
| `STORAGE_BACKEND` 三模式 | CSV 开箱、PostgreSQL 长期、both 迁移对账；双写需另做一致性检查 | ashare-audit / HermesAlpha |
| CSV 原子写 | 临时文件 + `os.replace()` | 所有有本地缓存的项目 |
| append-upsert | 主键去重保留最新 | 行情、基础资料、报告索引 |
| 区间替换 | symbol + 日期窗口局部修复 | 5 分钟线、快照、回测数据 |
| shell wrapper | 每任务一个 `bin/run_*.sh`，统一环境和日志 | 数据采集任务 |
| 数据契约文档 | 表字段、主键、时间语义、规模边界 | 所有下游分析 |
| repair-days | 增量同步时固定回补最近 N 天 | 行情和新闻采集 |
| 私有泄漏 CI | grep 本地路径、token 习惯、dump 目录 | 所有开源项目 |

## 12. 改进建议

如果把这个项目的设计吸收到当前体系里，建议顺手补三点：

1. 在所有行情表增加 `source`、`fetched_at`、`adjust_flag`，让跨 provider 降级可追溯。
2. CSV 后端后续可扩展 Parquet/DuckDB，用于分钟线和大规模快照。
3. 把采集任务注册成声明式 manifest，后续可以由 Doctor/调度器统一发现、检查和运行。
4. 将 provider 返回值改成 `ok/empty/unavailable/invalid` 四态，避免空结果提前终止 fallback。
5. 不把 `both` 当事务双写；确定主真源，并记录两端写入状态与对账结果。
