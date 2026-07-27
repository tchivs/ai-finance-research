# DojoAgents 快速概览

> 原始仓库: <https://github.com/Alpha-Dojo/DojoAgents>
> 分析基线：`Alpha-Dojo/DojoAgents` 本地浅克隆，commit `d69d469c6b7511a269f1e57909ffa54540724616`（2026-07-10）。上游许可证为 Apache-2.0；Python 要求 >= 3.11。

## 一句话定位

DojoAgents 是一个本地优先的个人投资 AI Copilot：以 Python Agent Loop 为核心，将金融工作台、工具执行、技能与插件、会话记忆、可选多 Agent/计划、定时任务和 Slack/微信等 Gateway 组合进同一运行时。

它更适合作为“金融 Agent 操作系统”的架构参考，而不是可直接复制的数据底座、交易执行服务或生产级沙箱。

## 值得先看的部分

| 目标 | 入口 | 可借鉴内容 |
|------|------|------------|
| 组合运行时 | `dojoagents/agent/runtime.py` | 配置驱动装配工具、Skills、MCP、会话和可选能力 |
| Agent 推理闭环 | `dojoagents/agent/loop.py` | Strands 适配、流式事件、工具桥接、上下文压缩、可选 guardrail |
| 工具结果治理 | `dojoagents/tools/executor.py` | 超长结果截断、会话归属、大结果 artifact 指针 |
| 会话可审计性 | `dojoagents/agent/session_manager.py` | sidecar、JSONL turn、tool trace、OpenAI 格式导出 |
| 本地金融工作台 | `dojoagents/dashboard/server.py` | FastAPI 路由、OpenAI 兼容 `/api/chat`、SSE、领域数据预加载 |
| 跨渠道消息 | `dojoagents/gateway/` | Slack、微信、企业微信、飞书、Discord、Telegram 的归一化 adapter |

## 已验证的调用路径

```text
CLI / Dashboard / Gateway
  -> Runtime.from_config_store()
  -> ToolRegistry + SkillManager + SessionManager + AgentLoop
  -> DojoStrandsModelBridge -> LLM provider
  -> DojoBridgedTool -> ToolExecutor -> ToolSpec.handler
  -> Agent events / tool trace / session export / SSE
```

Dashboard 在启动时预加载 DojoSDK 离线数据和金融领域 store；聊天 API 支持 OpenAI `messages` 格式、旧格式兼容以及 SSE。多 Agent 和 Planning 默认关闭，开启后才注册 `delegate_task`、`create_plan`、`execute_plan`、`revise_plan` 等工具。

## 可直接吸收的模式

1. 用单一 Runtime 负责装配，让可选能力通过配置注册工具，而不是把每个模块写入主循环。
2. 将大工具结果保存在会话 artifact 中，传给模型的是稳定指针或摘要，避免上下文被原始表格淹没。
3. 对每个运行保存 session status、事件、tool trace、token usage 与可导出的标准消息格式。
4. 外部聊天平台先归一化为 `ChatRequest`，再进入同一个 Agent 入口；渠道适配器不应复制业务逻辑。
5. Dashboard 协议同时兼容 OpenAI SSE 与自己的扩展事件，是渐进迁移而不是一次性替换的可行路径。

## 不应直接照搬

- `SandboxPolicy.check_tool()` 在当前基线是空实现；`allowed_roots`、`allowed_commands` 和 `allow_network` 不能视为统一强制隔离。
- `execute_code` 以当前 Python 解释器启动子进程，并通过 Unix socket 将整个工具注册表暴露给代码；它不是容器或 VM 沙箱。
- 插件可从 `~/.dojo/plugins` 加载 Python 模块，也可通过 `subprocess.run(..., shell=True)` 执行声明式 hook。仅安装受信任插件。
- 自动规划会让 LLM 生成 Plan 后立即执行；PlanStateStore 是 YAML 文件且无事务、租约、幂等键或人工审批。金融高风险动作必须移到独立 Gateway。
- 默认配置更偏向本地单用户，CORS 允许任意 origin；多用户部署需要另建认证、授权、审计脱敏和速率限制边界。

## 与当前路线的关系

适合作为 `20-开发实施TODO.md` 中 Phase 4、Phase 6、Phase 7 的参考：运行记录、工具 artifact、跨渠道归一化、工作台流式状态和插件生命周期。数据契约、provider fallback、交易门禁和强隔离仍应按 `19-首批源码落地验证.md` 的原则自行实现。

## 推荐阅读顺序

1. [DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
2. [Agent 协作专题](../09-Agent-协作与设计哲学篇.md)
3. [工程治理专题](../06-工程治理篇.md)
4. [UI/UX 交互专题](../11-UI-UX交互设计.md)
