# temporal

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/temporalio/temporal
> 分析基线：
> - `temporal`：commit `d562008739b606e7477fb28a8973ae0acf913448`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/temporal`
<!-- source-sync:end -->


## 一句话定位

提供 durable execution 的工作流服务：通过事件历史、任务队列、重试、超时和持久化状态，让长任务在进程崩溃或网络失败后继续运行。

## 核心流程

客户端 SDK 启动 Workflow 并把任务放入 task queue；Temporal server 的 frontend/gRPC API 接收请求，history service 维护 workflow execution history，matching service 分发 workflow/activity task，worker 执行业务代码并回报结果，persistence/visibility 保存状态和查询索引。

## 最值得借鉴的设计

1. 事件历史即恢复依据：`service/history` 的 workflow execution 状态和事件序列允许重放、重试和故障恢复。
2. Workflow/Activity 分离：确定性编排只描述状态转换，外部 IO 放在 Activity，并由 worker 通过 task queue 执行。
3. 服务与 worker 解耦：server 只负责调度和持久化，适合把回测、数据修复和报告生成作为可恢复长任务。

## 限制

本仓库是 Temporal server，而不是业务 SDK；部署需要数据库、可见性存储、namespace 和 worker 治理。Workflow 必须遵守确定性约束，不适合承载每笔行情 tick 或低延迟订单路径；执行网关仍需自己的幂等键、回报对账和 kill switch。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
