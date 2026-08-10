# Privora Python Examples 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/GuangfuWu/privora-python-examples.git
> 分析基线：
> - `privora-python-examples`：commit `a36f28c1f2b01f1912972b70ac5beea715f555d2`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/privora-python-examples`
<!-- source-sync:end -->


> agent skill gateway examples · bearer token scopes · dataasset access · encrypted portfolio path
> 源码: `src/privora-python-examples/`
> 原始仓库: <https://github.com/GuangfuWu/privora-python-examples>

## 1. 架构定位

privora-python-examples 是一个 API 使用样板仓库。它的目标不是展示复杂金融分析，而是告诉开发者和 Agent：如何安全、正确、最小权限地接入 Privora 的金融数据后端。

核心链路：

```text
Python script
    -> env LG_AGENT_BASE_URL
    -> env LG_AGENT_TOKEN
    -> POST /agent/skills/execute
    -> skillId selects capability
    -> params carries path/query/body
    -> response envelope with success/data/pagination
```

这是一种 “skill gateway as API surface” 的设计。

## 2. Bearer Token 验证示例

`01-bearer-token-setup.py` 做两步验证：

```text
Step 1
    GET /api/public/agent/skill-version
    no auth
    verify network + service version

Step 2
    POST /agent/skills/execute
    skillId = dataasset.list
    verify token + minimum scope
```

它的好处是把网络问题、服务版本问题、token 问题分开定位。

错误处理也很清楚：

- 公开 ping 非 200：网络或服务问题。
- 未设置 token：给出创建 token 和 export 示例。
- 401：token 无效或过期。
- 403：scope 不足。
- `success=false`：skill 层失败。
- 非 JSON：网关/代理异常。

## 3. stock_day 数据示例

`02-fetch-stock-day.py` 展示统一日线表访问方式：

```text
dataasset.list
    -> find assetName == stock_day
    -> get numeric assetId

dataasset.data.get
    pathParams: {id: asset_id}
    query:
        filter_column = stock_num
        filter_op = eq
        filter_value = 600519 / 00700.HK
        limit = 100
        order_by = day_id
        order_direction = asc
```

它强调 A 股和港股共用同一表、同一 schema：

- A 股：`600519`、`000001`
- 港股：`00700.HK`、`09988.HK`
- 指数：如 `1B0300`

这个模型适合 Agent，因为 Agent 不需要理解不同市场的物理表，只需要传 `stock_num`。

## 4. 持仓示例与字段级加密

`03-portfolio-snapshot.py` 展示敏感数据读取：

```text
investment.stock.portfolio.list
    query: {asset_class: stock, accountType: real}
    -> encrypted portfolio fields decrypted by API layer

dataasset.list
    -> find stock_day id

dataasset.data.get
    -> latest close price per stock_num

local calculation
    pnl = (current - cost) * qty
```

文件注释明确说明：持仓字段是 per-tenant DEK 字段级加密，DBA 读不到明文。只有持 token 的应用通过 API 得到解密结果。

如果 tenant 没有 DEK，后端可能返回：

```text
Wealth data integrity error
```

脚本把它视为预期隐私边界，而不是程序错误，并以 warning 后正常退出。

## 5. call_skill 统一封装

`02` 和 `03` 都实现了 `call_skill`：

```python
def call_skill(base, token, skill_id, params):
    url = f"{base}/agent/skills/execute"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {"skillId": skill_id, "params": params}
    resp = requests.post(url, headers=headers, json=body, timeout=15)
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(...)
    return payload
```

这段代码虽小，但体现了很好的 API contract：调用方只需要知道 `skillId` 和 params，不直接绑定具体 REST path。

## 6. Response Shape 的价值

README 和脚本多次强调 response shape 已验证：

```text
data 是 array
pagination 在 top level
不是 {rows: [...]} 结构
```

这是很实际的工程经验：Agent/API 示例最容易出错的不是请求发不出去，而是文档中的响应结构和实际服务不一致，导致下游解析失败。

对 ashare-audit 来说，response shape 本身应成为审计对象。

## 7. Scope 矩阵

README 给出最小权限矩阵：

| 示例 | scope |
|---|---|
| `01-bearer-token-setup.py` | `dataasset.list` |
| `02-fetch-stock-day.py` | `dataasset.list`, `dataasset.data.get` |
| `03-portfolio-snapshot.py` | `dataasset.list`, `dataasset.data.get`, `investment.stock.portfolio.list` |

这比“给一个全权限 token”更适合 Agent 接入，也更方便审计最小权限。

## 8. 对 HermesAlpha 的迁移方案

HermesAlpha 如果要对外暴露 Agent API，可借鉴：

```text
POST /agent/skills/execute
    Authorization: Bearer <token>
    body:
        skillId
        params.pathParams
        params.query
        params.body

response:
    success
    data
    totalElements
    totalPages
    pageSize
    currentPage
    message/error
```

优势：

- 权限可绑定到 `skillId`。
- 审计日志天然按 skill 聚合。
- Agent 只需要一种调用协议。
- response envelope 稳定，下游容易解析。

## 9. 对 ashare-audit 的审计模板

可按以下字段记录每次调用：

```json
{
  "skillId": "dataasset.data.get",
  "required_scopes": ["dataasset.data.get"],
  "pathParams": {"id": 123},
  "query": {
    "filter_column": "stock_num",
    "filter_op": "eq",
    "filter_value": "600519"
  },
  "response_shape": {
    "success": "boolean",
    "data": "array",
    "totalElements": "number"
  },
  "sensitive": false
}
```

持仓类调用额外审计：

- 是否使用 `investment.stock.portfolio.list` scope。
- 是否是 real account。
- 是否发生 DEK/data integrity error。
- 响应是否含明文字段，日志是否脱敏。

## 10. 工程质量观察

优点：

- 示例小，但边界清晰。
- 环境变量名统一。
- scope 最小化写进 README。
- 错误诊断具体，不只抛 stack trace。
- dev/prod 差异被显式说明。

不足：

- 目前只有 quickstart，README 中 backtest/paper-trading/alerts/ai-agent 仍是 coming soon。
- `02-fetch-stock-day.py` 定义了 start/end，但 query 中没有实际用日期过滤，只按 ticker 拉取 limit/order。
- 示例没有抽取公共模块，三个脚本存在重复 `call_skill` 逻辑；作为 quickstart 可接受，作为 SDK 还不够。
- 依赖线上服务和真实 token，CI 需要 mock 或 sandbox token。

## 11. 最关键结论

privora-python-examples 的价值不是算法，而是 Agent API 接入纪律：

```text
public ping first
Bearer token second
minimum scope per example
single skill gateway envelope
verified response shape
friendly diagnosis
sensitive data behind DEK boundary
```

HermesAlpha 可以借它设计对外 Agent API；ashare-audit 可以借它设计 API 调用审计和敏感持仓数据检查。
