# akshare 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/akfamily/akshare
> 分析基线：
> - `akshare`：commit `5cb11b4270ee5c4c97fdb6c4db040b51c82a46fd`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/akshare`
<!-- source-sync:end -->


## 系统边界

AKShare 是函数式金融数据采集库，不负责数据治理、回放、行情推送或订单执行。它通过多种公开网页/接口为 Python 用户返回 pandas DataFrame，适合作为 A/H/美股及宏观数据的原始 provider，而不是直接作为事实库。

## 关键模块

入口 `akshare/__init__.py` 汇总主题函数；`akshare/stock_feature/stock_hist_em.py` 提供 `stock_zh_a_spot_em`、`stock_zh_a_hist` 等东方财富路径，`stock/stock_zh_a_sina.py` 和 `stock/stock_zh_a_tx.py` 提供其他行情来源，`tool/trade_date_hist.py` 提供交易日历。模块内部使用 requests/curl_cffi、BeautifulSoup、lxml、jsonpath、pandas 等完成请求和解析。

## 执行流与数据流

函数参数 -> endpoint-specific URL/headers -> HTTP/HTML/JSON/CSV 响应 -> 解析和字段重命名 -> DataFrame。失败可能来自反爬、网络、接口下线、字段变化、空数据和时区/复权规则变化；大多数函数返回的是已经解析后的结果，raw response、provider request、available_time 和 schema 需要由上层采集 worker 另外保存。

## 契约、状态与持久化

每个函数的参数、列名、日期格式、复权选项和 symbol 规则构成隐式契约；库本身没有统一的 ProviderResult、schema registry、数据版本或持久化账本。采集层需要把函数名、参数、请求时间、原始响应 hash、解析版本和 DataFrame schema 写入 raw/normalized 层。

## 质量、安全、性能与运维

接口调用有网络、反爬、限速和字段漂移风险，且不同来源可能存在复权、时区、交易日和单位差异。应以小批量、缓存、重试退避和 source health 保护上游；不要在 API worker 中无限并发抓取，也不要把空 DataFrame 当成正常无数据。

## 可迁移模式与限制

可迁移：按主题拆分的 provider 函数、简单的参数到表格接口、交易日历和多来源 fallback。不应照搬：把函数结果直接写入交易信号、假设字段永久稳定、缺失时静默返回空表，或不保存来源和原始响应。仓库为 MIT，但 README 明确声明数据仅供研究参考、接口可能被移除，使用者仍需遵守各数据源条款。

本文基于 commit `5cb11b4270ee5c4c97fdb6c4db040b51c82a46fd`、核心数据函数和 README 进行静态研究，并建立 codebase-memory 索引；未执行测试、编译或构建。上线前应逐 provider 复核字段、复权、交易日历和可再分发权限。
