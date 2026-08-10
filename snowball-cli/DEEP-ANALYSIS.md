# snowball-cli 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/baixianger/snowball-cli.git
> 分析基线：
> - `snowball-cli`：commit `f3c0a641c835c5f7425afa61e1f5fc1a11b463b4`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/snowball-cli`
<!-- source-sync:end -->


> Xueqiu/Danjuan API wrapper · JSON CLI · cookie auth · finance/social/fund data for agents
> 源码: `src/snowball-cli/`
> 原始仓库: <https://github.com/baixianger/snowball-cli>

## 1. 架构定位

snowball-cli 是一个面向 AI Agent 的雪球数据命令行工具。它没有做复杂缓存、调度或 UI，而是专注于一个边界：把雪球/蛋卷的 HTTP API 转成稳定、可脚本解析的 JSON 命令。

```text
Agent / user
    -> snowball <command> <args>
    -> command registry in index.ts
    -> lib/api.ts HTTP function
    -> JSON output
```

这种形态很适合接入不稳定但价值高的第三方数据源：Agent 不直接拼 HTTP 请求，而是调用一个受约束的 CLI。

## 2. 命令注册表

`index.ts` 维护一个分组命令表：

```ts
const commands: Record<string, Record<string, Command>> = {
  Auth: {...},
  Market: {...},
  Financials: {...},
  Company: {...},
  Capital: {...},
  Social: {...},
  Discovery: {...},
  Funds: {...},
}
```

每个命令包含：

- `usage`
- `desc`
- `run`

dispatch 逻辑遍历所有 group，如果 `MODE` 命中命令名就执行，否则输出帮助。

这比散落的 if/else 更适合 Agent CLI：帮助文档、命令发现、技能文档可以从同一个结构推导。

## 3. HTTP client 分层

`lib/api.ts` 有两个请求函数：

```text
requestPublic(path, params, base)
    -> no Cookie
    -> quote / market / Danjuan fund endpoints

request(path, params, base)
    -> Cookie from getCookie()
    -> most Xueqiu endpoints
    -> check HTTP status and error_code
```

统一 headers 包含：

- `User-Agent`
- `Accept: application/json`
- `Origin: https://xueqiu.com`
- `Referer: https://xueqiu.com/`
- `X-Requested-With: XMLHttpRequest`

这说明该工具在模拟 Web 前端请求，不是官方稳定 SDK。

## 4. 认证设计

认证由 `lib/auth.ts` 管理：

```text
~/.snowball-cli/token.json
    cookie
    extractedAt
    source: chrome | chrome-qr | manual
```

认证入口：

1. `login`：启动 Chrome/Chromium，打开 CDP，尝试二维码登录。
2. `login --manual`：打开雪球页面，用户自行登录，回车后从 Chrome cookies 提取。
3. `token <cookie>`：用户手动提供 `xq_a_token`。
4. `export/import`：base64 转移 token 到服务器或容器。
5. `status`：调用 `quotec` 轻量接口验证 token。

关键产品约束写在 `SKILL.md`：Agent 不应主动替用户登录，只在需要登录的命令失败后提示用户自己执行认证。

## 5. 数据覆盖面

### Market

- `quote`：`/v5/stock/realtime/quotec.json`，公开可用。
- `quoteDetail`：`/v5/stock/quote.json`，含 PE/PB/股息率/52 周高低。
- `pankou`：买卖五档。
- `minute`：当日分时。
- `kline`：K 线，支持 `1m/5m/15m/30m/60m/120m/day/week/month/quarter/year`。
- `indices`：上证、深成、创业板、沪深300、上证50、中证500。

### Financials

通过 `detectRegion` 按代码判断 `cn/hk/us`，路由到：

- income
- balance
- cash_flow
- indicator
- business

### F10

- company profile
- top holders
- holder count
- bonus/dividend
- industry/concepts
- institutional holding changes

### Capital

- intraday capital flow
- historical daily capital flow
- order-size assortment
- margin trading
- block transactions

### Social

- category feed
- search posts
- hot posts
- live news
- important live news
- stock KOLs
- user posts/profile
- post detail

### Discovery/Funds

- stock search
- user search
- screener
- Danjuan fund detail/NAV/growth，公开可用。

## 6. Agent 工作流设计

`SKILL.md` 不只是命令列表，它给 Agent 设定了几套工作流：

早盘简报：

```bash
snowball market
snowball live --important --count 10
snowball trending --count 5
```

个股研究：

```bash
snowball quote SH600519 --detail
snowball income SH600519 --count 8
snowball indicator SH600519 --count 8
snowball holders SH600519 --top
snowball flow SH600519 --history
snowball forecast SH600519
```

大 V 舆情：

```bash
snowball kol SH600519 --count 10
snowball user <ID> --count 10
snowball profile <ID>
```

这类 workflow 比只列 API 更有价值：它让 Agent 知道怎样组合数据，而不是只知道可以调用什么。

## 7. 对 HermesAlpha 的迁移价值

可以迁移三件事：

1. **CLI-first external provider**：先用 CLI 包住外部站点，后续再升级为服务。
2. **认证边界声明**：公开接口优先，登录接口按需，Agent 不代用户认证。
3. **社交信号分层**：KOL/热帖/快讯进入 sentiment/context 层，不进入事实层。

建议在 HermesAlpha 中形成：

```text
Provider CLI
    snowball quote
    snowball finance
    snowball social

Ingestion adapter
    normalize JSON
    attach source metadata
    write raw payload

Agent context builder
    pick evidence
    label social/opinion/fact
```

## 8. 对 ashare-audit 的审计价值

snowball-cli 给审计系统提供了“命令级 provenance”：

```json
{
  "provider": "xueqiu",
  "command": "snowball flow SH600519 --history",
  "requires_login": true,
  "token_source": "chrome-qr",
  "endpoint_family": "capital",
  "raw_payload_hash": "...",
  "fetched_at": "..."
}
```

审计规则可包括：

- 公开命令不应强制要求登录。
- 登录命令不应由 Agent 自动执行。
- cookie 不得进入日志或报告。
- 社交/KOL 数据必须标注为 opinion/social source。
- 财务/F10 结果应保留 `symbol`、`region`、`count`、`endpoint_family`。

## 9. 风险评估

技术风险：

- 反向接口可能变动。
- WAF/403 可能导致不稳定。
- cookie 失效需要用户重新认证。
- CLI 没有内建缓存，重复调用会增加外部依赖风险。

合规/安全风险：

- cookie token 存储在用户目录，需确保权限。
- export/import 会把 token 以 base64 明文形态传播，不能进日志。
- 社交帖子可能包含不可靠或误导性内容。

## 10. 最关键结论

snowball-cli 的精华是“第三方金融网站数据的 Agent 安全包装”：

```text
JSON-only CLI
public-first usage
explicit login boundary
command workflows
social data as opinion source
auth token never hidden behind Agent automation
```

这对 HermesAlpha 的外部数据接入和 ashare-audit 的数据来源审计都很实用。
