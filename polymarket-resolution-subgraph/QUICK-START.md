# polymarket-resolution-subgraph

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/resolution-subgraph
> 分析基线：
> - `polymarket-resolution-subgraph`：commit `75d1818547862a5bd3477ed2e6b16f693d42dab6`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-resolution-subgraph`
<!-- source-sync:end -->


## 一句话定位

专门索引 Polymarket/UMA 市场解析生命周期的 The Graph 子图，覆盖旧版和多个 Optimistic Oracle、UMA CTF Adapter、Managed OO、Mod Registry 事件。

## 核心流程

监听 question initialized、reset、propose/dispute、resolved、settled 和 ancillary data 更新，写入 `MarketResolution`、`Moderator`、`Revision` 等 GraphQL entity。

## 最值得借鉴的设计

1. 将 resolution 与交易/盘口索引分开，避免把“市场价格”和“最终结果”混成一个状态。
2. 通过多 ABI data source 兼容旧版与新版权威合约。
3. 用 revision 和 ancillary-data hash 保存解析问题的变更轨迹。

## 限制

这是链上解析事实索引，不是结果裁决器；最终展示还需保留原始 transaction、block、oracle 版本和 dispute 状态。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
