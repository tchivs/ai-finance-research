# DojoAgents 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Alpha-Dojo/DojoAgents.git
> 分析基线：
> - `DojoAgents`：commit `0d3389e6f3739c0b0abc24869fa55a2e7acd19ef`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/DojoAgents`
<!-- source-sync:end -->


> 原始仓库: <https://github.com/Alpha-Dojo/DojoAgents>

## 1. 架构结论

DojoAgents 的中心不是多 Agent，而是一个配置驱动的 `Runtime`。`Runtime.from_config_store()` 装配 Extension、Skills、工具、MCP、LLM provider、Memory、Session、任务 harness；只有显式开启配置时，才挂入多 Agent、规划工具和自动化 hook。

```text
AgentsConfig
  -> Runtime
      -> ToolRegistry
      -> ToolExecutor + SandboxPolicy
      -> AgentLoop
          -> Strands bridge
          -> LLM provider
          -> DojoBridgedTool
      -> SessionManager / MemoryManager / JobStore
      -> Dashboard / Gateway / CLI
```

这是合理的渐进式结构：核心对话、工具和会话先可用，复杂编排成为配置能力而非启动前提。值得迁移的是装配边界，不是直接移植模块。

## 2. Agent Loop 与工具闭环

`AgentLoop.run()` 先组装系统上下文：时间信息、Skill prompt、Memory 检索、量化上下文、Dashboard 协议、任务 harness 和 turn intent。之后它用 `DojoStrandsModelBridge` 将内部 provider 转为 Strands `Model`，再把每个 `ToolSpec` 转为 `DojoBridgedTool`。

关键路径：

```text
LLM tool call
  -> Strands BeforeToolCall hook
  -> 可选 Agent guardrail / task harness / plugin hook
  -> DojoBridgedTool.stream()
  -> ToolExecutor.execute_one()
  -> ToolSpec.handler()
  -> ToolResult -> SSE event / tool trace / 下一轮模型上下文
```

`ToolExecutor` 的可迁移设计较好：并发 `execute_many()`、`asyncio.wait_for()` 超时、统一 `ToolResult`、30,000 字符截断、较大内容的 artifact 落盘及会话关联。它还将非零 exit code 规范成失败结果，避免 shell 工具把 stderr 当作普通答案。

但 `execute_many()` 只是 `asyncio.gather()`，没有队列、优先级、资源限额、持久化 job 或并发幂等。这适合短期只读工具，不足以承担可靠长任务。

## 3. 会话、记忆与产物

`DojoAgentSessionManager` 将 Strands 会话投影为可检索的 domain model，并在每次运行写入：

- `dojo_session.json`：标题、用户、模型、状态、token 状态和错误；
- `dojo_turns.jsonl`：事件、tool trace、usage；
- Strands repository 消息；
- 可选 memory 同步标记；
- 导出后的 Markdown transcript、`messages.jsonl` 和 `openai_dataset.jsonl`。

这个模式比只保留聊天文本更有价值：工具调用、消耗和事件能支持复盘。但它是文件系统存储，状态写入不带跨进程锁、事务或保留策略。多实例、共享文件系统或长期审计场景应迁移到带事务的 Job/Run/Audit 表，并将大 artifact 交给对象存储。

`MemoryManager` 支持 provider 生命周期和 turn 同步，但只允许一个非 `skill_summary` 外部 provider。该约束适用于简化本地产品，复杂企业部署通常需区分用户记忆、策略知识、数据检索和审计记录，不能共用一份 prompt memory。

## 4. 规划、多 Agent 与定时任务

多 Agent 默认关闭；开启后注册 `delegate_task`，角色为 analyst、implementer、reviewer。Planning 同样默认关闭，注册创建、执行、修订 Plan 工具并接入 `TaskComplexityHigh` 事件。

`AutoPlanManager` 的路径是：LLM 生成 JSON Plan -> YAML 存储 -> `PlanExecutionEngine` 按依赖执行 -> LLM 汇总结果。引擎有 `len(steps) * 2 + 1` 的死锁上限，失败时将 Step/Plan 标记失败并保存。

这提供了一个容易理解的最小 DAG 例子，但存在明确边界：

- LLM JSON 解析失败时降级为单步“分析”计划，可能掩盖生成质量问题；
- Plan YAML 写入不是原子或事务化的；
- 没有 worker lease、orphan 状态、恢复、取消语义或 idempotency；
- 自动生成后立即执行，未按工具风险、用户权限或资源预算进行服务端审批；
- `ScheduledJob` 仅保存 job 配置与 Markdown 输出，不等价于持久化 job state machine。

因此应只复用“Plan 状态和依赖显式化”的思想。生产金融任务要采用 `JobRecord`、lease、事件序号、幂等键、审批与 kill switch。

## 5. Dashboard 与 Gateway

Dashboard 是 FastAPI 应用。`create_app()` 注册金融域 router 与 dashboard tool，在 lifespan 中预加载 DojoSDK 离线数据及内存 store，启动后台刷新循环。`/api/chat` 同时接受 OpenAI 风格 `messages` 与旧 payload；流式响应使用 SSE，并可附带 Dojo v2 事件扩展。

Gateway adapter 将 Slack、WeChat、WeCom、Feishu、Discord、Telegram 消息归一化，再经 `GatewayRunner` 送入统一 `runtime.agent.run()`。现有测试覆盖 adapter 的规范化、平台发送 shape、allowlist、pairing、群组策略、会话持久化和敏感 token 脱敏。

可借鉴的边界是：渠道只处理身份、会话和消息形状，Agent 与工具运行时保持单一入口。不可直接继承的是认证模型：Dashboard CORS 为 `allow_origins=["*"]`，本地默认与跨渠道接入不能直接等同为多租户 API。

## 6. 安全边界

### 已实现的防护

- Agent config 默认开启 guardrails、think scrubbing 和上下文压缩。
- Agent Loop 可在工具调用前拦截、重写或停止；插件 hook 也可以返回 block 决策。
- 图片输入轮次会禁止部分 shell/code 工具。
- ToolExecutor 有超时、结果截断和 artifact 机制。
- Gateway 有 allowlist、pairing、群组策略和部分响应脱敏测试。

### 必须补强的风险

1. `SandboxPolicy.check_tool()` 是 no-op，不能承担工具许可、路径、命令或网络控制。
2. `execute_code` 用宿主 Python 创建进程，未将 CPU、内存、文件系统、网络或子进程隔离；其 RPC 还能调用注册工具。
3. 插件发现会执行用户目录中的 Python 模块；声明式 hooks 通过 `shell=True` 执行命令。插件是可信代码扩展，不是沙箱扩展。
4. Plan、Job 和 Session 主要为文件存储；并发写入、崩溃恢复、审批和幂等缺少统一契约。
5. 金融操作没有独立于 Agent Loop 的服务端 ActionGuard。任何未来交易或账户写入都必须经过独立 Gateway，默认 paper-only 且 fail-closed。

## 7. 测试证据与测试缺口

当前仓库有覆盖运行时开关、Agent hooks、工具截断、计划工具、会话导出、Dashboard OpenAI/SSE、Gateway adapter/allowlist 的 pytest 测试。文档核对了这些测试文件，但未在本轮执行：资料库环境没有项目依赖安装，也不应修改上游工作树。

缺口集中在真正的隔离与生产可靠性：没有看到针对容器逃逸、资源限额、插件不可信输入、并发 Plan/Job 写入、重启恢复、跨实例幂等或真实资金动作门禁的端到端验证。

## 8. 对当前项目的落地建议

| 复用优先级 | 应迁移的思想 | 适配要求 |
|------------|--------------|----------|
| P0 | Run/Session 记录、tool trace、artifact 指针 | 先落到自己的 `ToolCallEnvelope` 与 `JobRecord` |
| P0 | 单一 Runtime + 配置化 tool registry | 工具 schema 必须绑定 scope、数据契约和审计 |
| P1 | OpenAI 兼容聊天 + SSE 扩展事件 | 固定事件 schema 与重连 sequence |
| P1 | Gateway 消息归一化和 allowlist/pairing | 服务端认证、速率限制与 tenant 边界另建 |
| P2 | Skills/Plugins/MCP 生命周期 | 只启用签名或受信任扩展，禁止任意 shell hook |
| P2 | Plan DAG 和多 Agent 委派 | 改为持久化 job、审批和恢复后再启用 |

结论：DojoAgents 是当前资料库中“Agent 运行时加工作台”的强参考，尤其补齐了 QuantDinger 的 Gateway/审计取向与 Vibe-Trading 的运行编排之间的空白。它不改变已有默认决策：数据先行、只读先行、主存储唯一、强隔离和高风险服务端门禁仍是首版前置条件。
