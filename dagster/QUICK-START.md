# dagster

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/dagster-io/dagster
> 分析基线：
> - `dagster`：commit `6542eff83164cbb1b544225d0890a38c6aeb75c9`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/dagster`
<!-- source-sync:end -->


## 一句话定位

面向数据资产生命周期的声明式编排平台，以 assets、Definitions、jobs、sensors、schedules、event log 和 lineage 组织采集、质量和计算任务。

## 核心流程

用户用 `@asset` 声明数据资产和依赖，再由 `Definitions` 聚合 assets、resources、schedules 和 jobs；`define_asset_job`/`materialize` 生成运行计划，`DagsterInstance` 保存 run、event log、调度和持久化状态，daemon/sensor 驱动增量物化与告警。

## 最值得借鉴的设计

1. 数据资产优先：`definitions_class.py` 将资产图、资源和作业装配成可加载定义，适合描述 raw/normalized/quality/lakehouse 层。
2. 运行事实外置：`_core/instance/instance.py` 统一承载 run storage、event log、schedule 和持久化，不把任务状态塞进 worker 内存。
3. 声明式自动物化：自动物化规则根据依赖、缺失和 freshness 决定运行，比固定 cron 更适合增量市场数据。

## 限制

Dagster 解决数据资产编排，不解决订单撮合、交易回报或实时 tick 的低延迟路径。资产定义、资源凭证和 run storage 需要和执行网关隔离；高频数据应通过事件流/专用 worker 处理，不把每个 tick 建模成一次 Dagster run。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
