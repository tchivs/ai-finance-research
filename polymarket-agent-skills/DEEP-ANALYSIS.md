# polymarket-agent-skills 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/agent-skills
> 分析基线：
> - `polymarket-agent-skills`：commit `91ee44ae113e958affd20cd505c6e9d9d6100e0b`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-agent-skills`
<!-- source-sync:end -->


## 系统边界

仓库几乎全部是 Markdown：`SKILL.md` 为入口，其他文件按领域拆分。它不提供可执行 client、token 管理、订单数据库或风险引擎。

## 关键模块

- `authentication.md`：L1/L2、builder headers、credential lifecycle。
- `order-patterns.md`：GTC/GTD/FOK/FAK、tick size、cancel、heartbeat 和错误。
- `market-data.md`：Gamma、Data API、CLOB order book、subgraph 和价格历史。
- `websocket.md`：market/user/sports channel 和心跳。
- `ctf-operations.md`：split、merge、redeem、token id 和 NegRisk。
- `bridge.md` / `gasless.md`：资产桥接、relayer、wallet deployment 和 builder setup。

## 执行流与数据流

```text
任务触发 -> SKILL.md -> 专题参考 -> 工具/SDK 调用 -> 结构化结果 -> 审计记录
```

Skill 负责解释和路由，不应该直接让模型执行私钥签名。工作台应把 skillId、版本、读取的参考文件、工具参数和响应摘要写入调用 envelope。

## 契约、状态与持久化

文档定义了 CLOB、Gamma、Data、Bridge、Relayer、WebSocket 等端点和 Polygon 合约地址，但这些内容可能随上游部署变化；应保存 source commit、校验日期和 provider version。

## 质量、安全、性能与运维

仓库没有代码测试；质量依赖链接、端点、地址、SDK 版本和示例的定期校验。应把真实交易、bridge、gasless 和 redeem 作为高风险工具，默认只读或 `paper_only`。

## 可迁移模式与限制

最值得吸收的是技能拆包、渐进式披露和任务边界；不要把 Skill 文档当成权限系统、API schema 或最新事实源，必须由 provider health 和 contract tests 兜底。
