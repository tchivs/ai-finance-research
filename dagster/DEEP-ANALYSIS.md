# dagster 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/dagster-io/dagster
> 分析基线：
> - `dagster`：commit `6542eff83164cbb1b544225d0890a38c6aeb75c9`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/dagster`
<!-- source-sync:end -->


## 系统边界

Dagster 是数据资产和工作流控制面，负责定义依赖、调度、运行记录、事件日志、lineage、资源和自动物化。它不负责市场数据协议、订单执行或低延迟事件总线；这些应由 provider、streaming 和 execution 服务承载。

## 关键模块

`python_modules/dagster/dagster/_core/definitions/definitions_class.py` 的 `Definitions` 聚合 assets、jobs、resources、sensors 和 schedules；assets/asset_graph 表达数据依赖；`job_definition.py` 和 `unresolved_asset_job_definition.py` 将资产选择转成 job；`definitions/materialize.py` 执行物化；`_core/instance/instance.py` 统一管理 run storage、event log、schedule、daemon 和资源配置。

## 执行流与数据流

代码加载 Definitions -> 解析 asset graph 和资源 -> sensor/schedule/automation 产生 run request -> instance 创建 run -> executor 按依赖执行 asset/op -> 记录 materialization、metadata、失败和重试事件 -> UI/API/asset catalog 展示 lineage 与状态。资产的 partition、freshness、父级更新和缺失规则可驱动增量计算。

## 契约、状态与持久化

Definitions、AssetKey、resource、JobDefinition、Run、EventLogEntry 和 materialization metadata 构成核心契约。DagsterInstance 把运行状态和事件落入可替换存储，支持 UI、重试、回填和审计；业务数据本身仍由资产 IO manager、对象存储、数据库或 lakehouse 保存。

## 质量、安全、性能与运维

Dagster 需要控制面、run storage、event log、daemon、executor 和部署配置，生产要明确多租户、资源隔离、run 幂等和 backfill 策略。资产定义、资源凭证和 run storage 需要和执行网关隔离；高并发采集应由事件流和专用 worker 执行，Dagster 只编排批次、修复和回填。

## 可迁移模式与限制

可迁移：把 raw/normalized/quality/features/snapshots 建模为资产图，把 ProviderResult、DataContract 和质量报告写入 materialization metadata，并让 run/event log 成为审计入口。不要把每个行情 tick 变成 Dagster run，也不要让 Dagster worker 直接拥有实盘私钥。

本文基于 commit `6542eff83164cbb1b544225d0890a38c6aeb75c9`、Definitions/Instance/materialize/JobDefinition 源码和 README 进行静态研究，并建立 codebase-memory 索引；未执行测试、编译或构建。具体 executor、资产分区和部署拓扑仍需按数据量验证。
