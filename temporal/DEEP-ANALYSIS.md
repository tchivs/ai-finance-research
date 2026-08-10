# temporal 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/temporalio/temporal
> 分析基线：
> - `temporal`：commit `d562008739b606e7477fb28a8973ae0acf913448`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/temporal`
<!-- source-sync:end -->


## 系统边界

Temporal 仓库是 durable execution server，核心是通过 gRPC API、task queue、workflow event history、history/matching/frontend 服务和 persistence/visibility 保存并推进工作流。业务 Workflow、Activity、Worker 通常由外部 SDK 项目实现，不能把本仓库当作应用层任务库直接嵌入。

## 关键模块

`service/frontend` 暴露 WorkflowService API；`service/history` 负责 workflow execution、事件历史、timer、signal、update、重试和状态迁移；`service/matching` 管理 workflow/activity task queue 与 worker poll；`service/worker` 执行系统内部 workflow/activities；`common/persistence`、SQL/Cassandra/Elasticsearch/S3 等配置承载历史和可见性。`service/history/api/startworkflow/api.go` 的 prepare/lock/conflict 逻辑体现 workflow id 冲突、历史和启动状态的处理。

## 执行流与数据流

客户端 StartWorkflow -> frontend 校验 namespace、workflow id 和启动请求 -> history 创建或恢复 execution 并追加事件 -> matching 把 workflow/activity task 分发到 worker -> worker 回报 completion/failure/heartbeat -> history 追加事件并决定 retry、timer、继续任务或 close -> persistence/visibility 提供恢复和查询。事件历史是重放依据，task queue 是执行和扩展边界。

## 契约、状态与持久化

Workflow ID、namespace、task queue、event history、Activity retry/timeout/heartbeat、Search Attributes 和 visibility 是主要契约。History 是 durable state，persistence 负责重启恢复，visibility 负责查询和运营视图；Workflow 代码必须确定性，外部 IO 应放入 Activity。

## 质量、安全、性能与运维

服务端部署需要 namespace、持久化、可见性、worker 版本治理和容量规划；升级、历史兼容、跨区域复制和数据保留都属于平台运维问题。Workflow 的重试可能重复执行 Activity，订单 Activity 必须自己实现 client order id、幂等提交、状态查询、对账和 kill switch。

## 可迁移模式与限制

可迁移：长任务状态机、幂等 workflow id、activity retry/timeout/heartbeat、任务队列分片、事件历史和可见性索引。适合本项目的回测、数据回填、报告生成和人工审批流程；不适合 tick 级 market stream、撮合或订单回报热路径。仓库声明 MIT。

本文基于 commit `d562008739b606e7477fb28a8973ae0acf913448`、server/history/worker 目录和 README 进行静态研究，并建立 codebase-memory 索引；未执行测试、编译或构建。后续需验证 Temporal SDK 版本、生产数据库、worker 部署和 workflow determinism 约束。
