# TDX Market Data Clients 深度分析

> TDX MAC/7709 protocol · host probing · heartbeat/reconnect · VIPDOC offline files · business APIs · MCP
> 源码: `/root/source/tmp/easy_tdx/`, `/root/source/tmp/eltdx/`
> 原始仓库: [easy_tdx](https://github.com/handsomejustin/easy_tdx) · [eltdx](https://github.com/electkismet/eltdx)

## 1. 合并视角

TDX 这组项目覆盖 A 股行情底座的多个层次：

```text
Protocol layer
    frame / command / codec / bitmap

Transport layer
    socket / heartbeat / reconnect / pool / host probing

Data layer
    quote / kline / minute / trade / finance / F10 / VIPDOC

Research layer
    factor engine / forward returns / local adjustment

Agent layer
    MCP tools / CLI / web routers
```

easy_tdx 更像功能完整的工具箱，eltdx 更像重新整理过的现代客户端。

## 2. easy_tdx MacClient

`easy_tdx/src/easy_tdx/mac/client.py` 提供同步和异步 MAC 协议高层 API。

### 2.1 Host selection

`MacClient.from_best_host()`：

```text
get_mac_hosts()
ping_mac_all(hosts, port, ping_timeout)
ranked[0]
save_best_host(best)
return MacClient(best)
```

行情服务端延迟和可用性变化大，自动选路比硬编码 host 更可靠。

### 2.2 Connection lifecycle

```text
connect()
    -> TdxConnection.connect()
    -> start_heartbeat(interval)

ensure_connected()
    -> execute KlineOffsetCmd probe
    -> on TdxConnectionError: close/recreate/connect/start heartbeat

_execute(cmd)
    -> execute
    -> on connection error: retry with _RETRY_DELAYS
```

这说明行情客户端应假设连接会断，而不是把异常抛给业务层处理。

### 2.3 Pagination

常量：

```text
_KLINE_PAGE_SIZE = 700
_BOARD_MEMBERS_PAGE_SIZE = 80
_TRANSACTION_PAGE_SIZE = 1000
```

`get_stock_quotes_list()` 自动分页拉板块成员报价，业务调用方只传 count。

## 3. easy_tdx 字段位图报价

`mac/commands/symbol_quotes.py` 实现 MAC 批量报价命令 `0x122B`。

请求体：

```text
20-byte field bitmap
stock count
repeat market + gbk code padded to 22 bytes
```

响应解析：

```text
field_bitmap
total_stocks,row_count
active fields from bitmap
row_len = 68 + 4 * field_count
market/code/name
field values with fmt
FIELD_POSTPROCESS
MacQuoteField
```

字段位图是非常值得学的设计：Agent 查询“只要价格/涨跌幅/成交额”时，不必拉全字段。

## 4. easy_tdx Frame parser

`codec/frame.py` 描述 16 字节响应帧：

```text
magic: 7654321
ZipFlag
SeqID
Method
zipsize
unzipsize
body
```

`decompress_body()` 严格检查：

```text
len(raw_body) == zipsize
if zipsize != unzipsize: zlib.decompress
len(body) == unzipsize
```

二进制行情协议必须做这些长度校验，否则数据错位会悄悄污染上层指标。

## 5. easy_tdx 离线 VIPDOC

`offline/daily_bar.py` 解析通达信 `.day` 文件。

### 5.1 记录结构

```text
<IIIIIfII
date YYYYMMDD
open/high/low/close
amount
volume
reserved
32 bytes per row
```

### 5.2 证券类型识别

根据文件名 `sh600000.day` / `sz000001.day` 的代码段判断：

```text
A股/B股/指数/基金/债券/UNKNOWN
```

不同类型使用不同价格系数和量系数，避免把 ETF/债券/指数误按股票处理。

### 5.3 可迁移价值

本地 VIPDOC 可以作为：

```text
online API fallback
historical data cross-check
用户本机数据导入通道
TDX 口径复现
```

## 6. easy_tdx FactorEngine

`factor/engine.py` 提供轻量因子计算：

```text
compute_single(df, factors)
compute_cross_section(data, factors, date)
compute_forward_returns(data, period)
```

`compute_cross_section()` 支持：

```text
date omitted: all dates
date is None: latest row
date int: exact date
```

这套接口适合把行情客户端和轻量选股/验证连接起来，但不应替代完整回测平台。

## 7. eltdx TdxClient

`eltdx/src/eltdx/client.py` 是业务 API facade。

### 7.1 API composition

`__post_init__()` 初始化：

```text
SessionApi
CodeApi
QuoteApi
BarApi
MinuteApi
TradeApi
AuctionApi
CorporateApi
LimitApi
WorkdayService
F10Client
HelperApi
caches
```

调用方使用 `client.quotes.get_snapshots()`、`client.bars.all()` 等业务方法，不关心底层命令号。

### 7.2 Transport selection

若未注入 transport，则创建 `PooledSocketTransport`：

```text
hosts
pool_size
probe_hosts
probe_timeout
probe_workers
heartbeat_interval
```

也支持 `TdxClient.in_memory()`，方便测试。

### 7.3 Backward-compatible helpers

`get_quote()` 自动按 80 只批量拆分，并且补一个关键细节：

```text
0x054c 当前只稳定包含一档盘口
用 0x0547 首次刷新补齐买一到买五
不返回伪造深度档位
```

这体现了非常重要的审计原则：如果协议不稳定，就不要伪造看似完整的数据。

### 7.4 Local adjustment and equity

`TdxClient` 提供：

```text
get_gbbq()
get_xdxr()
get_equity_changes()
get_equity()
get_turnover()
get_factors()
```

其中 `get_factors()` 基于不复权日 K 和除权除息记录计算本地复权因子。

## 8. eltdx PooledSocketTransport

`transport/pool.py` 是小型连接池：

```text
unique_hosts(DEFAULT_HOSTS)
optional latency sort
create N SocketTransport with rotated hosts
round-robin execute
poll/drain push messages across transports
```

关键属性：

```text
connected_hosts
connected_host
pending_push_count
pool_size
heartbeat_interval
```

这比单连接客户端更适合高并发 Agent 查询场景。

## 9. eltdx MCP

`mcp.py` 用 FastMCP 暴露：

```text
eltdx_quote
eltdx_kline
eltdx_stock_profile
eltdx_stock_topics
eltdx_topic_stocks
eltdx_company_profile
eltdx_hot_topics
eltdx_auction_0925
eltdx_docs_index
```

每个工具内部创建 `TdxClient(timeout, host, heartbeat_interval=None)`，查询后转成 JSON-able 对象。

这说明底层行情客户端可以直接成为 Agent 工具，不必再通过 Web API 中转。

## 10. 当前项目迁移方案

### 10.1 Provider abstraction

```text
TdxProvider
    health()
    quote(codes, fields)
    kline(code, period, adjust)
    minute(code, date)
    depth(codes)
    f10(code)
    source_meta()
```

### 10.2 数据质量字段

每次返回附加：

```text
provider: tdx
host
protocol: mac|7709|vipdoc
adjust
field_set
latency_ms
cache_hit
fallback_used
decode_warnings
```

### 10.3 审计门

```text
frame length ok
zlib ok
row count ok
field bitmap matches
market/code normalized
adjustment source recorded
depth source recorded
```

## 11. 与其他项目组合

| 组合 | 价值 |
|------|------|
| TDX + Financial-API MarketDB | TDX 做实时/分时，MarketDB 做稳定日线和复权 |
| TDX + stock-sdk-mcp | TDX provider 包进 MCP 复合工具 |
| TDX + Vibe-Research | 本地投研看板增加实时盘口和 F10 |
| TDX + QuantaAlpha | 因子挖掘使用 TDX 离线/实时数据补充 |
| TDX + ashare-audit | 审计行情源口径、复权和深度档位真实性 |

## 12. 风险和限制

- TDX 主站协议没有强稳定性承诺，字段解析需要持续维护。
- 在线行情可能受网络、地区、主站负载影响，必须有重试、备用源和降级文案。
- VIPDOC 本地文件依赖用户安装和数据更新，必须检查新鲜度。
- 二进制协议错误容易产生“看似合理但错位”的数据，解析层必须宁可失败也不要静默修复。

## 13. 结论

TDX 客户端组给当前项目的最大价值是 provider 工程纪律：连接要自愈，字段要最小化，协议要严解析，复权要可解释，实时深度不能伪造，离线数据要能作为备用。它们适合作为 A 股数据底座中“实时行情和通达信口径”的一层。
