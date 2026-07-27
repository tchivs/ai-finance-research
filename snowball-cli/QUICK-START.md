# snowball-cli 快速概览

> 雪球数据 CLI · JSON 输出 · A股/港股/美股/基金/财务/F10/社交/KOL · Agent 友好命令层
> 源码: `/root/source/tmp/snowball-cli/`
> 原始仓库: <https://github.com/baixianger/snowball-cli>

## 1. 一句话定位

snowball-cli 是一个 TypeScript/Bun/Node CLI，把雪球和蛋卷的行情、财务、F10、资金流、社交帖子、KOL、基金接口封装成统一 JSON 命令。

它最值得学的是“Agent 友好 CLI 数据层”：每个命令输出 JSON，公开接口优先免登录，登录只在需要时触发，并通过 `SKILL.md` 明确告诉 Agent 不要一上来要求用户认证。

## 2. 主要能力

| 类别 | 命令 | 数据 |
|---|---|---|
| 行情 | `quote` `market` `pankou` `kline` `minute` | 实时行情、大盘指数、盘口、K 线、分时 |
| 财务 | `income` `balance` `cashflow` `indicator` `business` `forecast` | 三表、关键指标、营收构成、盈利预测 |
| F10 | `company` `holders` `bonus` `industry` `org` | 公司简介、股东、分红、行业概念、机构持仓 |
| 资金 | `flow` `assort` `margin` `block` | 资金流、大小单、融资融券、大宗交易 |
| 社交 | `trending` `live` `feed` `hot` `kol` `user` `profile` `post` | 热帖、快讯、信息流、热门股、大 V |
| 发现 | `search` `search-user` `screen` | 股票搜索、用户搜索、选股器 |
| 基金 | `fund --nav --growth` | 蛋卷基金详情、净值、收益 |

## 3. 认证策略

最重要的产品规则：**先用公开接口，失败再登录**。

无需登录：

```bash
snowball quote SH600519
snowball market
snowball fund 110011
snowball fund 110011 --nav
snowball fund 110011 --growth
```

需要登录：财务、F10、资金流、社交、K 线、盘口、详细行情等。

认证方式：

- `snowball login`：Chrome/Chromium CDP + 雪球 App 扫码。
- `snowball login --manual`：打开浏览器手动登录后提取 cookie。
- `snowball token <cookie>`：手动粘贴 cookie。
- `snowball export/import`：跨机器传 token。
- `snowball status`：调用轻量 API 验证 token 是否有效。

## 4. 核心实现

```text
index.ts command registry
    -> parse args/flags
    -> call lib/api.ts function
    -> JSON.stringify output

lib/api.ts
    -> requestPublic for no-token endpoints
    -> request for cookie endpoints
    -> normalize selected response fields

lib/auth.ts
    -> ~/.snowball-cli/token.json
    -> Chrome CDP cookie extraction
    -> verify token by quotec endpoint
```

接口 base：

- `https://stock.xueqiu.com`
- `https://xueqiu.com`
- `https://danjuanapp.com`

## 5. 对 HermesAlpha 的启发

- 可把第三方网站/API 先封成 JSON CLI，再由 Agent 组合，而不是一开始做重服务。
- 对公开接口和登录接口做明确分级，降低用户使用门槛。
- 用 `SKILL.md` 写清触发词、代码格式、认证边界和推荐工作流。
- 社交/KOL 数据可以作为市场情绪和观点战绩的输入源。

## 6. 对 ashare-audit 的启发

- 审计雪/社交类数据源时要保留：命令、symbol、时间、token 状态、HTTP 状态、原始 JSON。
- 对需要 cookie 的接口必须做认证边界审计，不应由 Agent 自动代用户执行登录。
- 对帖子/KOL 输出要区分事实字段和平台互动指标，不应把大 V 观点当成基本面事实。
- 对 `screen`、`hot`、`trending` 类榜单要记录排序依据和平台偏置。

## 7. 风险与局限

- 雪球接口是反向封装，端点、字段、WAF 策略可能变化。
- cookie 保存在本机 `~/.snowball-cli/token.json`，需要注意权限和泄漏风险。
- 部分接口需要登录，不适合作为完全无状态后端服务。
- 社交数据噪声很高，适合作为信号来源，不适合作为结论来源。

## 8. 最小可迁移模式

```text
external-data-cli
    command registry
    public request client
    authenticated request client
    token status/export/import
    JSON-only output
    SKILL.md with do-not-login-first rule
```

这套模式很适合 HermesAlpha 接入高频变化的外部数据源，也方便 ashare-audit 对每次调用做命令级追踪。
