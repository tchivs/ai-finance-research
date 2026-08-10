# polymarket-agent-skills

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/agent-skills
> 分析基线：
> - `polymarket-agent-skills`：commit `91ee44ae113e958affd20cd505c6e9d9d6100e0b`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-agent-skills`
<!-- source-sync:end -->


## 一句话定位

面向 Agent 的 Polymarket 集成知识包，以渐进式披露组织认证、订单、行情、WebSocket、CTF、桥接、gasless 和 NegRisk 操作说明。

## 核心流程

Agent 先读取 `SKILL.md` 的端点、凭证和核心模式，再按任务加载 `authentication.md`、`order-patterns.md`、`market-data.md`、`websocket.md` 等专题文件。

## 最值得借鉴的设计

1. progressive disclosure 控制上下文成本。
2. 把“何时使用、使用什么 API、有哪些边界”写进 Skill，而不是只依赖 prompt。
3. 以 endpoint、contract address、订单类型和错误模式为可检索知识单元。

## 限制

这是文档型 skill，不是执行沙箱；README 中仍有旧 SDK 名称和示例，实施前必须与当前统一 SDK 和实际端点交叉验证。密钥和签名只能由受限服务处理。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
