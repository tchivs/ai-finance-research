# FinceptTerminal 快速概览

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Fincept-Corporation/FinceptTerminal.git
> 分析基线：
> - `FinceptTerminal`：commit `823f63848084f3869e4c9a487663f41f44d55989`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/FinceptTerminal`
<!-- source-sync:end -->


> Fincept-Corporation · 原生桌面金融工作站 · C++20 / Qt6 / Python / SQLite / HTTP-WebSocket
> 源码: `src/FinceptTerminal/`
> 原始仓库: <https://github.com/Fincept-Corporation/FinceptTerminal>

## 1. 一句话定位

Fincept Terminal 是一个以 C++20 和 Qt6 构建的 Bloomberg-style 原生多窗口金融终端：在单个桌面二进制中组合跨资产行情、新闻与宏观、投研/量化计算、AI 智能体、纸面或经纪商交易及本地工作区。其 Python 能力实际由 `src/python/PythonRunner` 以受控 `QProcess` 子进程提供，而非浏览器或 Electron 前端。README 已声明公开版从 2026-06 起改为每月更新，并以 AGPL-3.0 加商业许可发布。

## 2. FinceptTerminal 覆盖的链路

```text
行情 / RSS 新闻 / 宏观数据 / 经纪商与交易所 / Python 数据脚本
    -> services/* 领域服务与 PythonRunner
    -> DataHub topic：缓存、TTL、节流、订阅和错误状态
    -> Qt Screens：仪表盘、投研、新闻、交易、组合、智能体
    -> SQLite 主库 / 缓存库 / SecureStorage / 工作区状态
    -> 人工决策、纸面撮合或 UnifiedTrading 实盘路由
```

`src/app/main.cpp` 在首屏前注册市场、新闻、宏观等生产者，并预热 `market:quote:*`、`news:general` 等主题；期权、预测市场、智能体等在首个事件循环后延迟启动。`DockScreenRouter::register_factory()` 与 `navigate()` 让屏幕首次使用才实例化，支持停靠、浮动、标签和多窗口工作流。

## 3. 核心模块

| 模块 | 作用 | 对当前项目的价值 |
|---|---|---|
| `src/datahub/DataHub`、`Producer`、`TopicPolicy` | 主题化 pub/sub；`subscribe()` 有 QObject 生命周期保护，`publish()` 保存最新值，`request()` 按 TTL 和频率刷新。 | 作为数据层共享合约，避免多个视图重复取数；把新鲜度与错误显式交给 UI。 |
| `src/services/markets/MarketDataService` | 通过 Python/yfinance 获取报价、基本面、OHLCV；100ms 批处理去重，30 秒报价缓存。 | 行情服务应同时有批量、缓存和按标的主题，不能仅暴露逐代码 HTTP 调用。 |
| `src/services/news/NewsService` | 聚合 RSS、按股票/分类分发，支持 `analyze_article()`、AI 标题摘要及实时 WebSocket。 | 新闻数据、来源质量、摘要缓存和事件流可拆成清晰职责。 |
| `src/python/PythonRunner` 与 `fincept-qt/scripts/` | 异步运行数据、分析、策略和智能体脚本；返回 `PythonResult` 与 JSON；默认至多 3 个并发。 | 为 Python 数值与数据生态建立可观测的进程边界、限流和统一返回格式。 |
| `src/services/agents/AgentService`、`src/mcp/` | 调度 `finagent_core` 智能体、流式事件、结构化输出及内部/外部 MCP 工具。 | 把 Agent 输出作为可关联请求、可订阅主题和可持久化证据，而非 UI 内黑箱。 |
| `src/trading/UnifiedTrading`、`BrokerRegistry`、`PaperTrading` | 将订单路由到纸面引擎或账户化经纪商；支持撤单、改单、篮子和拆单。 | 研究信号、模拟执行和实盘账户必须经统一 DTO 分层，保留审计边界。 |
| `src/storage/`、`src/auth/` | SQLite 主库/缓存库、迁移、`CacheManager`、`SecureStorage`、会话和工作区状态。 | 将短期缓存、长期研究资产与敏感凭据分开管理，支持恢复和清理。 |

FinceptTerminal 最值得借鉴的是“终端外壳 + 主题数据平面 + Python 计算适配器”的组合，而非照搬它所接入的任一第三方源。面对实时交易和 AI 研究，应额外验证数据授权、更新时间、输出证据与实盘风险。
