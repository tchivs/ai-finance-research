# TDX Market Data Clients 快速概览

> easy_tdx + eltdx · 通达信行情协议客户端、离线 VIPDOC、F10/MCP、因子引擎
> 源码: `/root/source/tmp/easy_tdx/`, `/root/source/tmp/eltdx/`
> 原始仓库: [easy_tdx](https://github.com/handsomejustin/easy_tdx) · [eltdx](https://github.com/electkismet/eltdx)

## 1. 一句话定位

easy_tdx 和 eltdx 都围绕通达信行情数据构建，但侧重点不同：easy_tdx 是“在线 MAC 协议 + 离线 VIPDOC + 因子/前端工具箱”，eltdx 是“现代化 7709 协议客户端 + 连接池 + 业务 API + MCP”。

它们最值得学的是 A 股行情底座的工程细节：主机探测、连接心跳、自动重连、批量分页、字段位图、帧解压、离线文件解析、本地复权和上层 API/MCP 包装。

## 2. 两个项目各自贡献

| 项目 | 定位 | 最值得学 |
|------|------|----------|
| easy_tdx | TDX MAC 协议高层 API + 离线数据 + 因子引擎 | 自定义字段位图、QFQ 兜底、VIPDOC `.day` 解析、因子截面计算 |
| eltdx | 现代 TDX 7709 客户端 | PooledSocketTransport、业务 API 分层、quote depth merge、F10/MCP |

## 3. 核心工作流

```text
host list
    -> latency probe / best host
    -> socket connection / heartbeat
    -> protocol command build_request
    -> frame header parse / zlib decompress
    -> binary row decode / postprocess fields
    -> business API DataFrame/dataclass
    -> optional MCP/tool wrapper
```

## 4. 最值得学的设计

| 模块 | 做法 | 可迁移点 |
|------|------|----------|
| Best host | ping 多台服务器，保存最低延迟 host | A 股实时源需要自动选路 |
| Auto reconnect | 指数退避重建连接并恢复 heartbeat | 行情长连接必须默认不稳定 |
| Batch page size | 报价 80、K 线 700/800、交易明细 1000/2000 | 协议限制要在客户端封装 |
| Field bitmap | 请求自定义字段，响应按 active fields 解码 | 减少带宽和无用字段 |
| Frame parser | 16 字节 header + zlib body 检查 | 二进制协议要严校验长度 |
| Offline `.day` | 32 字节记录、按证券类型价格/量系数 | 本地通达信数据可作为备用源 |
| FactorEngine | 单股/截面因子计算、forward returns | 数据客户端可带轻量研究能力 |
| Pool transport | 多 Socket round-robin + heartbeat | 并发查询用连接池而不是单连接排队 |
| API facade | `client.quotes/bars/minutes/trades/...` | 上层不应关心命令号 |
| MCP tools | quote/kline/profile/topics/F10/auction | TDX 可以直接成为 Agent 数据源 |

## 5. 对 HermesAlpha 的借鉴

1. **把 TDX 作为实时/准实时行情 provider**：用于 quote、K 线、分时、五档盘口、F10 辅助信息。
2. **做 provider 级健康和选路**：主机延迟、连接失败、pending push、重连次数都应可观测。
3. **使用离线 VIPDOC 做备用/校验源**：通达信本地 `.day` 可在网络失败时提供历史日线。
4. **字段请求最小化**：Agent 查询行情时按任务选择字段，不每次拉全量。
5. **复权本地重算**：服务端 QFQ 异常时用除权除息记录本地重算，避免负价污染研究。

## 6. 对 ashare-audit 的借鉴

1. **审计字段口径**：价格/成交量系数、复权类型、市场代码是否正确。
2. **审计实时深度**：eltdx 明确用 0x0547 补五档，不伪造深度档位。
3. **审计协议失败**：帧长度、zlib 解压、row decode 错误是否显式抛出。
4. **审计缓存**：代码表、股本变迁、财务信息的缓存是否可刷新。
5. **审计数据源 fallback**：在线 TDX、离线 VIPDOC、其他 provider 的优先级是否记录。

## 7. 不该照搬的部分

- 通达信协议和主站可用性不保证长期稳定，生产不能只依赖单一 TDX 源。
- 二进制协议字段需要持续实盘验证，不能把未解析字段当确定口径。
- MCP 入口适合本地 stdio，如果远程部署要加鉴权和限流。
- 因子引擎适合作轻量计算，完整研究回测仍应进入 Qlib/MarketDB 等统一底座。

## 8. 结论

TDX Market Data Clients 的价值在于行情底座的细节。对当前项目来说，它们不是多一个行情 API，而是提供了如何把不稳定二进制行情源包装成可恢复、可分页、可校验、可给 Agent 使用的数据 provider 的样板。
