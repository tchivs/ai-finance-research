# Privora Python Examples 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/GuangfuWu/privora-python-examples.git
> 分析基线：
> - `privora-python-examples`：commit `a36f28c1f2b01f1912972b70ac5beea715f555d2`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/privora-python-examples`
<!-- source-sync:end -->


> Privora API quickstart · Bearer Token · skill gateway · A股/港股统一 stock_day · 持仓字段级加密
> 源码: `src/privora-python-examples/`
> 原始仓库: <https://github.com/GuangfuWu/privora-python-examples>

## 1. 一句话定位

privora-python-examples 是 Privora 金融数据后端的最小 Python 示例仓库。它不实现完整策略，而是演示 Agent/脚本如何用 Bearer Token 调用 Privora 的 skill gateway：验证 token、查 `stock_day` 数据、读取持仓并计算盈亏。

它最值得学的是“API 接入样板”：scope 最小化、统一 gateway envelope、响应 shape 验证、错误路径诊断、字段级加密失败的 graceful handling。

## 2. 示例清单

| 文件 | 作用 | 关键点 |
|---|---|---|
| `01-bearer-token-setup.py` | public ping + token verify | 公开版本端点、`dataasset.list` 验证 token/scope |
| `02-fetch-stock-day.py` | 拉 A 股/港股日线 | `dataasset.list` 找 assetId，`dataasset.data.get` 统一查询 |
| `03-portfolio-snapshot.py` | 查持仓并算盈亏 | `investment.stock.portfolio.list` + 最新价 + DEK 错误处理 |

## 3. 环境变量

```bash
export LG_AGENT_BASE_URL=https://privora.cn
export LG_AGENT_TOKEN=lgatk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

最小 scope：

- 跑 `01`：`dataasset.list`
- 跑 `02`：`dataasset.list + dataasset.data.get`
- 跑 `03`：再加 `investment.stock.portfolio.list`

## 4. Gateway 调用形态

所有鉴权调用走同一个入口：

```text
POST {base}/agent/skills/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "skillId": "dataasset.data.get",
  "params": {
    "pathParams": {"id": 123},
    "query": {...},
    "body": {...}
  }
}
```

响应 shape 明确验证过：

```json
{
  "success": true,
  "data": [],
  "totalElements": 6,
  "totalPages": 1,
  "pageSize": 20,
  "currentPage": 1
}
```

重点：`data` 是数组，不是 `{rows: [...]}`。

## 5. 最值得吸收的 5 点

1. **先 ping public endpoint**：先验证网络和服务版本，再验证 token。
2. **最小权限 scope**：不同示例只要求对应的最小 scope。
3. **统一 skill gateway**：所有能力通过 `skillId + params` 调用，Agent 接入面一致。
4. **资产名转 numeric id**：先 `dataasset.list` 找 `stock_day` 的 `assetId`，再用 id 拉数据。
5. **错误诊断友好**：403/scope、DataSource not found、DEK 缺失都给明确原因。

## 6. 对 HermesAlpha 的启发

- 如果做金融数据 API 给 Agent，用 gateway envelope 比散落 REST path 更适合权限和审计。
- A 股/港股可统一成一张 `stock_day` 表，用 `stock_num` 路由。
- API 示例要验证真实 response shape，避免文档和实际不一致。
- 持仓等敏感数据必须通过 token 和字段级加密边界，而不是直接暴露数据库。

## 7. 对 ashare-audit 的启发

- 审计 Agent API 调用时应记录 `skillId`、scope、pathParams、query、response shape。
- `success=false` 和 HTTP 非 2xx 都要保留原始 message，不能只报“失败”。
- 对持仓数据，DEK 缺失不能被误判为脚本 bug；它是隐私边界的信号。
- 文档中明确“dev gap/prod complete”这类环境差异，可减少错误归因。

## 8. 风险与局限

- 仓库目前只有 quickstart，backtest/paper-trading/alerts/ai-agent 还未实现。
- 示例依赖真实 Privora 服务和 token，无法离线运行。
- dev 环境可能缺数据源或 DEK，示例代码必须容忍。
- `stock_day` 示例里 `start/end` 变量暂未真正传入 query，只演示按 ticker 拉取最近记录的模式。

## 9. 最小可迁移模式

```text
agent-api-examples
    01-token-verify
    02-dataasset-query
    03-sensitive-portfolio-query
    common call_skill(base, token, skillId, params)
    clear scope matrix
    response-shape assertions
    friendly diagnostics
```

这对 HermesAlpha 建 API 示例和 ashare-audit 建调用审计模板都很直接。
