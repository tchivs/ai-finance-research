# 类似金融 AI 项目开发实施 TODO

本清单把 [落地路线图](17-落地路线图.md)、[模式决策矩阵](18-模式决策矩阵.md) 和 [首批源码落地验证](19-首批源码落地验证.md) 转换成可执行任务。默认目标是先完成一个本地优先、只读、可审计的数据垂直切片，再逐步加入长任务、策略和 Agent。

## 1. 使用规则

| 标记 | 含义 |
|------|------|
| `[ ]` | 尚未开始 |
| `[-]` | 进行中 |
| `[x]` | 已完成且有验收证据 |
| `[!]` | 阻塞，必须记录原因 |
| `[~]` | 取消或被其他方案替代 |

任务只有在验收标准通过后才能标记 `[x]`。代码已提交、页面已显示或接口能返回数据，都不能单独代替端到端验收。

## 2. 当前最先做的 10 项

- [ ] `NEXT-01` 确定第一个目标用户和高频工作流。
- [ ] `NEXT-02` 确定本地单用户或服务端多用户运行形态。
- [ ] `NEXT-03` 确定唯一主存储，不直接采用无事务的 `both` 双写。
- [ ] `NEXT-04` 定义 `ProviderResult` 四态返回契约。
- [ ] `NEXT-05` 定义首个数据集的 `DataContract`。
- [ ] `NEXT-06` 定义 `ToolCallEnvelope`。
- [ ] `NEXT-07` 接入一个公开、只读、不需要登录的数据 provider。
- [ ] `NEXT-08` 生成一份带日期、来源、缓存状态和 schema 版本的静态快照。
- [ ] `NEXT-09` 提供只读查询 API，并记录完整工具调用 envelope。
- [ ] `NEXT-10` 在最小 UI 中显示数据日期、来源、缓存和质量状态。

完成以上 10 项后，才进入第二 provider、长任务或 Agent 编排。

## 3. Phase 0：范围与架构基线

### 任务

- [ ] `BASE-01` 写明目标用户、首个工作流和明确非目标。
- [ ] `BASE-02` 确定部署形态：本地单用户、单实例服务或多实例服务。
- [ ] `BASE-03` 确定主真源：SQLite、PostgreSQL、Parquet 或其他存储只能有一个权威写入源。
- [ ] `BASE-04` 确定第一阶段只读边界，明确不包含自动实盘和代用户登录。
- [ ] `BASE-05` 建立 ADR 目录和首条架构决策记录。
- [ ] `BASE-06` 建立最小测试数据集，包含正常、空结果、过期缓存、字段缺失和 provider 失败样例。
- [ ] `BASE-07` 确定源码、数据源、模型和第三方 API 的许可及使用边界。

### 交付物

| 交付物 | 最小内容 |
|--------|----------|
| `PROJECT_SCOPE.md` | 用户、工作流、范围、非目标、成功标准 |
| `ADR-001-storage.md` | 主存储选择、候选方案、升级条件和回退条件 |
| `fixtures/` | 五类可重复测试样例 |

### 阶段门禁

- [ ] 能用一句话描述第一个用户工作流。
- [ ] 能回答数据真相最终落在哪里。
- [ ] 能列出第一阶段明确不做的功能。
- [ ] 所有后续任务都能映射到第一个工作流。

## 4. Phase 1：五个核心契约

### `ProviderResult`

- [ ] `CONTRACT-01` 定义 `ok/empty/unavailable/invalid` 四种状态。
- [ ] `CONTRACT-02` 增加 `provider/data_date/fetched_at/from_cache/empty_reason/error_code/raw_hash`。
- [ ] `CONTRACT-03` 明确每个状态是否允许 fallback。
- [ ] `CONTRACT-04` 测试空结果不会被误判为成功数据或普通异常。

### `DataContract`

- [ ] `CONTRACT-05` 定义 dataset、schema version、主键、时区和单位。
- [ ] `CONTRACT-06` 定义必填字段、可空字段、缺失值语义和质量规则。
- [ ] `CONTRACT-07` 定义字段级 source 和数据集级 provenance。
- [ ] `CONTRACT-08` 建立契约版本升级和兼容策略。

### `ToolCallEnvelope`

- [ ] `CONTRACT-09` 定义 `call_id/tool/route/command/params/session_id`。
- [ ] `CONTRACT-10` 定义 `auth_scope/idempotency_key/status/response_shape/raw_hash`。
- [ ] `CONTRACT-11` 定义开始、结束、耗时和错误结构。
- [ ] `CONTRACT-12` 定义敏感字段脱敏规则。

### `JobRecord`

- [ ] `CONTRACT-13` 定义 queued/running/succeeded/failed/cancelled/orphaned 状态。
- [ ] `CONTRACT-14` 定义 worker lease、progress sequence 和结果引用。
- [ ] `CONTRACT-15` 定义进程重启后的 orphan 检测与恢复规则。

### `ActionGuard`

- [ ] `CONTRACT-16` 定义 required scope 和资源 allowlist。
- [ ] `CONTRACT-17` 定义 `paper_only`、服务端确认和部署 kill switch。
- [ ] `CONTRACT-18` 定义数据库不可用时哪些动作必须 fail-closed。

### 阶段门禁

- [ ] 五个契约都有 schema、合法样例、非法样例和自动验证测试。
- [ ] 契约字段在文档与代码中使用同一命名。
- [ ] 不依赖 prompt 或 UI 文案传递关键安全语义。

## 5. Phase 2：第一个只读数据垂直切片

### 数据接入

- [ ] `SLICE-01` 选择一个公开、稳定、合法、无需登录的数据源。
- [ ] `SLICE-02` 实现 provider adapter，只返回 `ProviderResult`。
- [ ] `SLICE-03` 设置 timeout、有限重试和结构化错误。
- [ ] `SLICE-04` 保存 raw payload 或内容摘要，禁止只保留格式化文本。

### 快照与存储

- [ ] `SLICE-05` 生成带 `date/schema_version/generated_at/source/from_cache` 的静态快照。
- [ ] `SLICE-06` 用临时文件和原子替换写快照。
- [ ] `SLICE-07` 使用唯一主键去重，明确同 key 更新语义。
- [ ] `SLICE-08` 对主键、日期、单位、空值和范围运行 DataContract 校验。
- [ ] `SLICE-09` 失败时保留上一个有效快照，并明确标记 stale/cache 状态。

### API 与审计

- [ ] `SLICE-10` 提供一个只读查询 API。
- [ ] `SLICE-11` 每次调用写入 `ToolCallEnvelope`。
- [ ] `SLICE-12` API 响应包含 data、meta、quality 和 error 四个稳定区域。
- [ ] `SLICE-13` 增加健康检查，区分服务可达、provider 可达和数据新鲜度。

### 最小 UI

- [ ] `SLICE-14` 显示数据所属日期和生成时间。
- [ ] `SLICE-15` 显示 provider、缓存、降级和数据质量状态。
- [ ] `SLICE-16` 显示空数据、过期数据、provider 失败和 schema 不兼容状态。
- [ ] `SLICE-17` 提供原始证据或审计记录入口。

### 测试

- [ ] `SLICE-18` 正常数据端到端测试。
- [ ] `SLICE-19` 空结果测试。
- [ ] `SLICE-20` timeout 和 provider 失败测试。
- [ ] `SLICE-21` 过期缓存回退测试。
- [ ] `SLICE-22` schema 变化阻断测试。
- [ ] `SLICE-23` UI 信任状态测试。

### 阶段门禁

- [ ] 用户不用查看日志就能判断数据日期、来源和可信状态。
- [ ] 每个 API 结果都能回到 provider 调用和原始摘要。
- [ ] provider 失败不会生成看起来正常的新快照。
- [ ] 首个垂直切片可以在干净环境重复启动和验证。

## 6. Phase 3：第二数据源与数据韧性

- [ ] `DATA-01` 接入第二 provider，继续使用同一 `ProviderResult`。
- [ ] `DATA-02` 为每个 provider 配置 `fallback_on_empty`。
- [ ] `DATA-03` 区分停牌、未上市、非交易日和 provider 空结果。
- [ ] `DATA-04` 建立字段级 source 和 provider 优先级。
- [ ] `DATA-05` 建立固定 repair window，补齐迟到或修订数据。
- [ ] `DATA-06` 建立跨 provider 数值差异阈值与告警。
- [ ] `DATA-07` 增加 source health、最近成功时间和连续失败次数。
- [ ] `DATA-08` 增加 Doctor 命令或诊断页。
- [ ] `DATA-09` 高并发文件写入增加进程锁，或迁移到事务存储。
- [ ] `DATA-10` 若需要分析副本，使用异步导出和对账，不做无状态顺序双写。

### 阶段门禁

- [ ] 空结果、异常和无效数据有不同状态。
- [ ] fallback 发生后仍能追溯字段来源。
- [ ] 主存储和分析副本存在可运行的对账流程。
- [ ] Doctor 能解释当前为什么可用、降级或不可用。

## 7. Phase 4：长任务、幂等与审计

- [ ] `JOB-01` 将所有长任务改为 submit + poll，返回稳定 `job_id`。
- [ ] `JOB-02` JobRecord 写入持久化存储后才能开始执行。
- [ ] `JOB-03` 实现 worker lease 和 heartbeat。
- [ ] `JOB-04` 实现 orphan 检测、超时和安全重试。
- [ ] `JOB-05` 实现按 sequence 恢复的 SSE 进度流。
- [ ] `JOB-06` 终态结果独立持久化，不只存在内存 ring buffer。
- [ ] `IDEM-01` 在副作用前事务预占 idempotency key。
- [ ] `IDEM-02` 同 key 并发请求只能有一个进入 processing。
- [ ] `IDEM-03` 使用稳定外部 `client_order_id` 或等价标识。
- [ ] `IDEM-04` 数据库不可用时写入和高风险动作 fail-closed。
- [ ] `AUDIT-01` 审计请求、响应、scope、耗时、状态和 idempotency 状态。
- [ ] `AUDIT-02` 对 password、token、secret、cookie、authorization 和持仓敏感字段脱敏。
- [ ] `AUDIT-03` 增加审计查询、保留期限和删除策略。

### 阶段门禁

- [ ] 进程在任务运行中退出后，任务会变成 orphaned 或被其他 worker 接管。
- [ ] 并发相同 idempotency key 不会重复产生外部副作用。
- [ ] SSE 断线重连不会丢失最终结果。
- [ ] 审计日志本身不包含真实凭证。

## 8. Phase 5：策略、监控与回测

- [ ] `STRAT-01` 定义自己的 `StrategyDef`，不直接复制上游字段。
- [ ] `STRAT-02` 分离候选过滤、入场信号、退出信号、评分和风险约束。
- [ ] `STRAT-03` 为选股、监控和回测实现独立 adapter。
- [ ] `STRAT-04` 建立跨 adapter 一致性测试，明确允许存在的差异。
- [ ] `STRAT-05` 回测加入 T+1、涨跌停、停牌、手续费、滑点和仓位限制。
- [ ] `STRAT-06` 防止 basic filter 删除持仓后续行情，避免卖出和估值失真。
- [ ] `STRAT-07` 监控规则包含条件、冷却、历史和 synthetic test-fire。
- [ ] `STRAT-08` AI 生成策略必须经过 schema、AST 和未来函数检查。
- [ ] `STRAT-09` AI 建议先进入 suggestion pool，不直接产生交易动作。

### 阶段门禁

- [ ] 同一策略在三个 adapter 中的共有语义有自动测试。
- [ ] 回测结果可以重现，并保存数据版本和全部参数。
- [ ] 监控触发可解释、可冷却、可回放。

## 9. Phase 6：Agent Gateway 与高风险能力

- [ ] `AGENT-01` 分离 Human API 和 Agent API 的认证方式。
- [ ] `AGENT-02` 定义最小 scope 分类，避免无意义复制 R/W/B/N/C/T。
- [ ] `AGENT-03` token 只保存 hash，明文只显示一次。
- [ ] `AGENT-04` 加入 market、instrument、portfolio 或资源 allowlist。
- [ ] `AGENT-05` rate limit 使用共享存储，不能只依赖单进程内存。
- [ ] `AGENT-06` 所有 Agent route 通过统一审计中间件。
- [ ] `GUARD-01` 高风险动作默认 `paper_only=true`。
- [ ] `GUARD-02` 服务端 Gateway 强制确认或一次性审批令牌。
- [ ] `GUARD-03` MCP、CLI 和 UI 的确认只作为额外门禁。
- [ ] `GUARD-04` 增加部署级 kill switch。
- [ ] `GUARD-05` 提供真正能停止外部动作的 kill switch，不把“取消本地记录”误写成撤单。
- [ ] `SANDBOX-01` 不可信代码在独立进程或容器中执行。
- [ ] `SANDBOX-02` 限制 CPU、内存、时间、文件、网络和子进程。
- [ ] `SANDBOX-03` validator 与 runtime 隔离同时生效，并有逃逸回归测试。

### 阶段门禁

- [ ] 直接绕过 MCP 调用 HTTP Gateway 仍无法跳过服务端确认。
- [ ] 数据库、审计或权限服务故障时，高风险动作 fail-closed。
- [ ] 默认配置无法触发真实资金动作。
- [ ] 不可信代码无法访问宿主凭证、文件和网络。

## 10. Phase 7：工作台与可信交互

- [ ] `UI-01` 首页显示市场状态、数据日期、待处理信号和运行任务。
- [ ] `UI-02` 运行页显示阶段、进度、工具调用、失败原因和重试入口。
- [ ] `UI-03` 数据质量页显示字段来源、缓存、降级和 schema 状态。
- [ ] `UI-04` 工具调用页显示参数、scope、版本、响应形态和 raw hash。
- [ ] `UI-05` 策略页区分候选、信号、回测和监控语义。
- [ ] `UI-06` 高风险动作显示 paper/live、scope、确认和 kill switch 状态。
- [ ] `UI-07` 所有空状态和错误状态提供明确下一步操作。
- [ ] `UI-08` 完成桌面和移动端响应式验证。
- [ ] `UI-09` 完成键盘、屏幕阅读器、颜色对比和焦点管理检查。

## 11. 暂缓清单

- [ ] `DEFER-01` 完整多市场实盘交易。
- [ ] `DEFER-02` 大规模实时行情分发。
- [ ] `DEFER-03` 完整 LangGraph 多 Agent 状态机。
- [ ] `DEFER-04` 自动策略演化和自动晋级。
- [ ] `DEFER-05` 多租户计费和复杂套餐系统。
- [ ] `DEFER-06` 一次性接入大量 provider。
- [ ] `DEFER-07` 大而全导航和营销首页。

暂缓项只有在前置门禁通过、出现真实需求和有对应 ADR 时才能转入实施。

## 12. 每周更新模板

```markdown
## YYYY-MM-DD 周进展

- 本周完成：<任务 ID + 验收证据>
- 当前进行：<任务 ID>
- 阻塞事项：<任务 ID + 原因 + 所需决策>
- 新发现风险：<风险及影响>
- 下周目标：<最多 3 项>
- 变更的 ADR：<链接>
```

## 13. 完成定义

整个第一轮项目不以功能数量判定完成，而以以下问题全部可回答为准：

- [ ] 数据来自哪里，属于哪个日期，是否缓存或降级？
- [ ] 空结果、异常、无效数据和非交易日是否被正确区分？
- [ ] 每次工具调用能否重放和审计？
- [ ] 长任务在进程重启后是否有明确状态？
- [ ] 相同幂等 key 是否能阻止重复副作用？
- [ ] 策略在选股、监控和回测中的差异是否明确？
- [ ] 高风险动作是否由服务端门禁保护？
- [ ] 用户是否能从 UI 看懂数据质量、失败原因和下一步？
