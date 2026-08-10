# 多市场量化工作台设计 PRD

- 状态：草案
- 日期：2026-08-10
- 目标产品：HermesAlpha Multi-Market Quant Workbench
- 适用市场：A 股、港股、美股、加密货币、Polymarket
- 证据基础：本资料库全部项目文档、`10-SYNTHESIS.md`、`15-数据底座与采集底座篇.md`、`17-落地路线图.md`、`18-模式决策矩阵.md`、`20-开发实施TODO.md`、`21-项目价值评估与方法论.md`

## 1. 产品定位

建设一个本地优先、可审计、可回放、支持多市场的量化研究工作台。工作台通过独立的 `HermesData Unified Data Platform` 消费行情、基本面、新闻、因子原料和 Polymarket 事件数据，再把策略、回测、组合、盯盘、Agent 研究和纸面交易放到同一套运行状态中。数据源不属于工作台代码库的内部模块。

产品不是“聊天机器人加行情页面”，也不是第一阶段的自动实盘系统。核心顺序是：

```text
统一数据平台 -> SDK/API/MCP/WS -> 数据契约与工具审计 -> 策略资产化
-> 可回放研究 -> 工作台 -> 纸面交易 -> 受控实盘
```

## 2. 目标用户与核心工作流

### 目标用户

- 需要跨 A/H/美股、加密货币和预测市场比较机会的个人研究者。
- 需要把观点、因子、策略和交易记录长期沉淀的量化开发者。
- 需要使用 Agent 做资料收集、反方复核和盘中提醒，但不希望 Agent 直接越权交易的投资者。

### 首个高频工作流

```text
选择市场/标的 -> 获取带来源的数据快照 -> 运行筛选或策略
-> 查看信号、风险和数据质量 -> 回测/复盘 -> 生成报告或进入建议池
```

### 非目标

- 第一阶段不做自动实盘和自动策略晋级。
- 工作台不内置供应商采集、标准化和数据存储；这些能力归属独立的 `hermes-data` 项目。
- `hermes-data` 第一阶段不追求覆盖所有供应商，而是先稳定统一契约，再按市场和 provider 扩展。
- 不让 Agent 自由拼接 HTTP 请求、读取宿主凭证或直接触碰账户状态。
- 不复制 FinceptTerminal 等受许可证约束项目的完整代码和依赖。

## 3. 能力范围

### 多市场

统一资产目录支持 `EquityInstrument`、`CryptoInstrument` 和 `PredictionMarket` 三类模型。A 股、港股、美股共享证券研究能力，但交易规则通过市场适配器实现：交易日历、时区、币种、交易单位、T+1、涨跌停、停牌、盘前盘后、手续费和滑点均不得写死在通用回测代码中。

Polymarket 使用独立的事件市场模型：`Event`、`Market`、`OutcomeToken`、`OrderBook`、`Resolution`、`Settlement`。它可以复用信号、订单、任务和审计契约，但不能伪装成普通股票 K 线。源码研究后，接入顺序明确为：统一 `ts-sdk`/`py-sdk` 作为新应用入口，CLOB v2 客户端作为低层签名兼容层，实时客户端作为事件输入，subgraph/Go watcher 作为链上事实层，CTF/UMA/NegRisk 作为独立结算域。

### 功能模块

| 模块 | 主要能力 |
|---|---|
| 数据服务接入 | 通过 `hermes-data` SDK/API/MCP/WS 获取统一数据、质量状态和实时事件 |
| 研究中心 | 个股/事件研究、基本面、新闻、情绪、引用和研究记忆 |
| 因子策略 | Factor DSL、FactorZoo、StrategyDef、YAML 配置、四向信号 |
| 回测实验 | 事件重放、成本模型、组合约束、实验记录、样本外验证 |
| 盯盘监控 | 规则触发、AND/OR 条件、冷却、预算、触发历史、通知 |
| 组合风控 | TargetWeight、仓位上限、行业/市场约束、回撤、流动性和风险复算 |
| Agent 会议室 | Moderator、专家分工、多空辩论、反方复核、结构化结论 |
| 纸面执行 | paper broker、订单生命周期、成交模拟、持仓和 PnL |
| 报告审计 | claim-to-source、数据质量、工具调用、策略 lint、运行回放 |

## 4. 总体架构

```text
消费者项目：HermesAlpha / Agent / Backtest / Dashboard / 其他项目
      | Python SDK / TypeScript SDK / REST API / MCP / WebSocket
      v
HermesData Unified Data Platform（独立仓库 hermes-data）
      |
      +-- 控制面：数据目录、资产模型、provider、权限、配额、schema、质量规则
      +-- 采集面：Provider Adapter -> Raw -> Normalize -> Quality -> Repair
      +-- 存储面：Object Storage/Parquet + DuckDB；可选 TimescaleDB 热层，规模增长后再引入 Iceberg/ClickHouse
      +-- 服务面：SDK / REST API / MCP Server / WebSocket / CLI
      +-- 事件面：market.normalized / orderbook / fundamental / news / settlement
      +-- 实时计算面（可选）：RisingWave 物化视图、窗口聚合、实时 Join 和告警

HermesAlpha Workbench
      |
      +-- Strategy / Feature / Backtest / Portfolio / Risk / Paper Execution
      +-- Agent / Report / Audit / UI
```

第一阶段两个项目都采用模块化单体加独立 worker；`hermes-data` 先作为本地可运行服务，工作台通过 SDK 或 localhost API 消费。第二阶段按数据采集、查询服务、回测、Agent 和执行的负载及权限边界拆分服务。分布式契约从第一天建立，但不从第一天部署复杂微服务。

## 4.1 独立项目：HermesData Unified Data Platform

### 项目目标

`hermes-data` 是类似 Tushare 的统一数据源项目，但同时提供程序库和服务协议。所有下游项目只依赖它的稳定契约，不直接依赖 AKShare、OpenBB、CCXT、Polymarket SDK 或某个交易所的原始接口。

### 对外产品面

| 接口 | 使用者 | 约束 |
|---|---|---|
| Python SDK | Qlib、vectorbt、Notebook、回测 worker、数据分析 | 支持 pandas/Polars，返回统一 `DataResponse` |
| TypeScript SDK | Web、Electron、Node worker、其他服务 | 与 REST schema 同源，不在前端保存 provider 凭证 |
| REST API | 外部项目、桌面端、跨语言服务 | OpenAPI、分页、字段版本、scope 和 rate limit |
| WebSocket | 实时 bars、quotes、trades、order book、news、settlement | topic、订阅过滤、序列号、心跳、断线重连和 replay cursor |
| MCP Server | Agent、研究技能和自动化工具 | 只暴露 allowlist 查询和受控订阅，不暴露原始凭证或任意 URL |
| CLI | 运维、回填、快照和诊断 | JSON 输出优先，可被任务系统和 CI 调用 |

### 统一数据域

```text
Instrument / Venue / Calendar
EquityBar / Quote / Trade / OrderBook
Fundamental / CorporateAction / News / MacroSeries
CryptoFunding / OpenInterest / Liquidation
PredictionEvent / PredictionMarket / OutcomeToken / Resolution
ProviderStatus / DataQuality / Snapshot / Correction
```

股票、加密货币和 Polymarket 共享 `Instrument`、时间、来源和质量字段，但不共享错误的业务语义。预测市场保留 `Event`、`OutcomeToken`、`Resolution` 和 `Settlement`；股票保留复权、交易日、停牌和公司行动；加密市场保留 funding、OI、perpetual 和 24/7 calendar。

所有数据集使用统一的数据包络，但使用独立的领域模型。统一包络至少包含 `dataset`、`instrument_id`、`venue`、`event_time`、`available_time`、`ingested_at`、`timezone`、`currency`、`unit`、`provider`、`schema_version`、`quality_status` 和 `raw_hash`；领域模型负责表达股票、加密货币和预测市场不能互相替代的语义。

### 内部层次

```text
provider adapters
      -> raw response/object storage
      -> canonical normalizer
      -> quality/freshness/schema checks
      -> snapshot + hot cache + query index
      -> REST/SDK/MCP/WS serving
```

Provider Adapter 只能负责来源协议和字段解析，不能把上游字段直接泄漏给消费者。每个 provider 需要声明 `capabilities`、覆盖市场、认证方式、限频、字段映射、更新时间、fallback 和许可限制。原始数据、标准化数据、修复任务和质量结果必须可追溯。

### 清洗、归一化与差异抹平

```text
raw immutable
  -> parse/provider schema
  -> entity resolution
  -> canonical field mapping
  -> unit/currency/timezone/calendar normalization
  -> duplicate/order/correction handling
  -> quality checks and quarantine
  -> normalized serving tables and streams
```

归一化不是简单改列名，而是把 provider 差异转成稳定的领域契约：

| 差异 | 统一策略 |
|---|---|
| symbol、代码、token id 不同 | 通过 `InstrumentMaster` 映射到稳定 `instrument_id`，保留所有 source symbol |
| 时间戳、时区、交易日不同 | 统一 UTC `event_time`，同时保留 venue timezone、session 和原始时间 |
| 货币、数量、价格精度不同 | 保存 `currency`、`unit`、scale、tick_size 和 precision，禁止隐式浮点转换 |
| A/H/美股复权和公司行动不同 | 同时提供 raw/unadjusted/adjusted 版本，记录 adjustment policy 和 corporate action |
| 加密货币 24/7、funding、OI、perpetual 不同 | 使用 crypto 专属模型和 calendar，不强行映射为股票交易日 |
| Polymarket event/outcome/resolution 不同 | 使用 `Event`、`Market`、`OutcomeToken`、`Resolution`、`Settlement` 专属模型 |
| 同一数据多源冲突 | 按 provider policy、优先级、时间和质量评分选择，并保留冲突记录 |

清洗规则分为 `reject`、`quarantine`、`repair` 和 `accept_with_warning`。重复记录、非法主键、时间倒退、单位缺失和无法解析的关键字段进入隔离区；迟到事件、供应商修订和历史纠错通过 `correction_id`、watermark 和版本化快照处理。任何被修复的数据都不能覆盖 immutable raw。

### 复用规则

1. `HermesAlpha`、`ashare-audit`、Agent、回测 worker 和 UI 只能通过 `hermes-data` 的 SDK/API/MCP/WS 获取数据。
2. Provider 凭证只存在 `hermes-data` 的服务端边界，不能进入消费者配置、前端、策略代码或 Agent prompt。
3. 查询结果、实时消息和 MCP 工具必须引用同一份 JSON Schema/Protobuf 契约。
4. `hermes-data` 不负责策略、组合、订单执行和投资建议；它只提供带来源、时间和质量状态的数据。
5. 工作台可以本地嵌入只读 SDK 和 DuckDB 快照，但快照格式必须与远端 API schema 兼容。

### 读写路径约束

当前数据访问实现存在以下边界，不能把 Parquet、Arrow、Polars 和 DuckDB 视为等价路径：

- `start/end` 过滤在当前 kernel 路径中是在 Arrow 读入后由 Polars 执行，不能默认认为存在日期 predicate pushdown；需要范围扫描时优先按 `dataset/venue/date` 选择文件，再由 DuckDB 负责跨文件过滤。
- `generic_upsert` 会读取旧表、合并去重、排序并整表重写，适合低频表和修复任务，不适合高频增量写入；行情写入应采用分区追加、临时批文件、manifest 提交和后台 compaction。
- 分钟聚合会先读取完整时间窗口，再执行 resample；不要对每条 tick 触发全窗口重算，应按完整窗口或微批执行，并记录窗口 watermark。
- 单文件或少量标的的转换可以走 Polars kernel；跨大量标的、跨目录和宽时间范围分析统一走 DuckDB，避免逐文件调用 kernel 产生重复 I/O 和调度开销。

因此，查询服务需要按范围、标的数量和目录数量做路由；写入服务需要区分 append、upsert、repair 和 compaction，不能用一个通用写入函数覆盖所有数据频率。

### 采集编排选择

`hermes-data` 默认采用 Dagster 作为批处理和数据资产控制面：用 `Definitions`/`Assets` 描述 raw、canonical、quality、snapshot 的依赖图，用 partitions 按 `dataset/venue/date` 切分，用 schedules/sensors 处理新鲜度、回填和修复，用 asset checks 执行 schema、完整性、唯一性和 freshness 门禁，并保留 run/event log 作为 lineage 与审计证据。实时 quote、trade、order book 不为每个 tick 创建 Dagster run，而由独立 collector 写入 Redpanda/Kafka，再由标准化和服务层消费。

| 编排工具 | 本项目定位 | 适用边界 |
|---|---|---|
| Dagster | `hermes-data` 默认控制面 | 批量采集、分区回填、清洗归一化、质量检查、快照发布和 lineage |
| Prefect | 暂不与 Dagster 并行部署；作为独立脚本或小型 flow 的对比参考 | 临时数据任务、轻量编排和团队已有 Prefect 资产 |
| Temporal | 可选业务工作流引擎 | 报表、审批、对账、修复等需要长时间等待和强恢复语义的任务 |

Prefect 中文站可作为阅读入口，包版本、源码和规范以 [Prefect GitHub](https://github.com/PrefectHQ/prefect) 与[官方文档](https://docs.prefect.io/)为准；它不进入第一阶段的核心数据采集链路。

## 5. 技术栈

| 层 | 默认选择 | 选择理由 |
|---|---|---|
| Web/桌面 | React + TypeScript + Vite；Electron 复用前端 | 延续 `tickflow`、`OpenAshare`、`trade-skills` 工作台模式 |
| API | 现有 TypeScript/Hono；复杂计算使用 Python FastAPI | 控制面与量化计算面解耦 |
| 统一数据平台 | Python SDK + TypeScript SDK；FastAPI/OpenAPI；MCP；WebSocket；CLI | 独立复用，统一连接 A/H/美股、加密货币和 Polymarket provider |
| 研究计算 | Python、Polars、NumPy、PyArrow、DuckDB、Qlib | 复用 `Qlib`、`AlphaAgent`、`tickflow` 的研究模式 |
| 任务编排 | Dagster Definitions/Assets/Partitions/Schedules；Temporal 仅用于业务长流程 | 数据资产可追踪，批量任务可回填，避免把实时流伪装成普通 job |
| 并行实验 | Ray，限于回测和研究实验 | 不进入实时订单路径 |
| 数据湖 | S3/MinIO + Parquet；规模增长后引入 Iceberg | 本地可运行、可迁移、支持 schema 演进 |
| 查询 | Parquet + DuckDB 默认；PostgreSQL 管元数据；TimescaleDB 仅作可选热数据层 | 保持轻量部署，历史事实不依赖在线数据库 |
| 查询路由 | 少量文件用 Polars；跨标的、跨目录和宽时间范围用 DuckDB | 避免逐文件 kernel 调用和误判日期 predicate pushdown |
| 大规模分析 | ClickHouse 作为后续可选扩展 | 只有全量 Tick、盘口历史和高并发聚合成为瓶颈时引入 |
| 运行态 | SQLite 本地；PostgreSQL 服务化 | 策略、任务、订单、持仓、审计需要事务 |
| 事件流 | Redpanda/Kafka 协议 | 支持分区、消费组、重放和横向扩展 |
| 流式计算 | 第一阶段不引入；需要实时 Join/窗口聚合时评估 RisingWave | 只做消息转发、最新行情缓存时不增加流计算平台 |
| 缓存 | Redis/Valkey | 热数据、限流、短期状态，不作为数据真相 |
| 接口契约 | JSON Schema + Protobuf/Buf | 保证 CLI、MCP、API、worker 的结构一致 |
| 观测 | OpenTelemetry、Prometheus、Grafana、Loki、Tempo | 统一指标、日志、链路和任务诊断 |
| 部署 | Docker Compose 本地；Kubernetes + Helm 生产 | 同一套服务可从单机演进到集群 |

Polymarket 的 Solidity/Go 仓库不应被编译进前端或普通 API：`ctf-exchange-v2`、`uma-ctf-adapter` 和 `neg-risk-ctf-adapter` 只作为 ABI、事件和结算契约的证据；真实执行必须通过独立的 `execution-gateway` 和链上 reconciliation。

本批新增源码研究的落位如下：`nautilus-trader` 作为 Rust/Python 事件驱动内核候选，`vectorbt` 作为批量参数研究 worker，`ccxt`/`hummingbot` 作为加密连接器与执行生命周期参考，`openbb`/`akshare` 作为 provider adapter 参考，`dagster` 作为 `hermes-data` 的数据资产编排与回填控制面，`temporal` 仅作为可恢复业务长任务候选。它们不应被整体堆叠：实时行情走事件流，订单走独立执行网关，批量研究和数据编排通过 job contract 连接。

## 6. 服务边界

### `hermes-data` 独立项目

```text
data-catalog-service
provider-registry-service
market-ingest-worker
normalizer-quality-worker
snapshot-lakehouse-service
data-query-service
data-stream-service
data-api-gateway
data-mcp-server
data-cli
```

这些服务拥有 provider 凭证、原始响应、标准化数据、质量规则、数据目录和实时数据出口。`data-api-gateway` 同时服务 SDK、REST 和 MCP；WebSocket 独立处理订阅、序列号、背压和 replay cursor。

### `HermesAlpha` 工作台项目

```text
api-gateway
workspace-service
instrument-calendar-service
hermes-data-client
feature-service
strategy-registry-service
backtest-worker
portfolio-risk-service
paper-execution-service
live-execution-gateway
agent-gateway
research-orchestrator
audit-policy-service
notification-service
```

工作台不再拥有 provider registry、采集 worker、标准化 worker 和数据湖服务。它通过 `hermes-data-client` 访问统一数据，通过 `data_stream` 消费实时事件。服务拆分规则：无状态查询服务优先水平扩展；`hermes-data` 采集按 provider/venue 分片；回测按 `job_id` 并行；实时事件按 `instrument_id` 或 `market_id` 分区；实盘执行和凭证服务与研究 worker 隔离。

## 7. 数据与事件契约

### 核心契约

- `DataQuery`：dataset、instrument/market、时间窗口、频率、字段、调整方式、provider policy、分页和 replay cursor。
- `DataResponse<T>`：`ok/empty/unavailable/invalid`、数据、来源、日期、缓存、schema、raw hash、quality、request_id。
- `ProviderResult`：`hermes-data` 内部 provider 的原始/标准化结果，不向消费者暴露 provider 私有字段。
- `DataContract`：dataset、规范主键、时区、单位、必填字段、缺失值、版本、质量规则和 `normalization_policy`。
- `NormalizationPolicy`：实体解析、时区/交易日历、单位/货币/精度、复权、重复记录、迟到数据、冲突选择和修订策略；策略变更必须提升版本并重建受影响快照。
- `StreamEnvelope`：topic、event_id、sequence、event_time、available_time、instrument_id/market_id、schema_version、payload、cursor。
- `MCPToolContract`：tool、input schema、scope、数据范围、分页、缓存策略和审计字段。
- `ToolCallEnvelope`：tool、route、params、session、scope、版本、响应形态、耗时、raw hash。
- `JobRecord`：queued、running、succeeded、failed、cancelled、orphaned、progress sequence。
- `ActionGuard`：required scope、资源 allowlist、`paper_only`、审批票据、kill switch。
- `StrategyDef`：候选过滤、入场、退出、评分、风险约束、版本和适配器。

### 时间和血缘

所有数据至少保存 `event_time`、`available_time`、`ingested_at`、`provider`、`data_date` 和 `raw_hash`，避免未来函数、供应商修订不可追踪和回测穿越。

`hermes-data` 还必须保存 `schema_version`、`quality_status`、`source_revision`、`request_id` 和 `correction_id`。SDK、REST、MCP 和 WebSocket 的同一数据集必须使用同一主键、时区、单位和版本语义。

### 事件主题

```text
market.raw
market.normalized
market.bars
market.orderbook
fundamental.updated
news.updated
data.quality.updated
data.snapshot.created
signal.generated
backtest.requested
backtest.completed
order.created
order.filled
settlement.resolved
```

采用至少一次投递、事件 ID 去重、分区内有序和可重放设计；不以全局 exactly-once 作为前提。

## 8. Agent 与风控

Agent 负责收集、解释、比较、辩论和生成候选策略；确定性规则负责数据校验、策略 lint、仓位、权限、交易成本、冷却和订单边界。

默认链路：

```text
Agent 结果 -> 质量门 -> suggestion pool -> 人工确认
-> paper order -> 风控复算 -> 执行适配器
```

所有高风险动作默认 `paper_only=true`。数据库、审计、权限或风控服务不可用时必须 fail-closed。凭证只允许从 Vault/KMS 或服务端安全边界读取，不能进入浏览器、Agent prompt、日志或回测代码。

## 9. 工作台页面

第一版只做高频工作流，不做营销首页：

1. 总览：市场状态、数据日期、质量告警、任务和待确认建议。
2. 市场/标的页：行情、基本面、新闻、因子、信号、来源和研究记忆。
3. 策略页：StrategyDef、版本、lint、回测、监控和适用市场。
4. 回测页：参数、数据版本、成交假设、进度、成交明细和结果。
5. 盯盘页：规则、冷却、触发历史、通知和 test-fire。
6. Agent 运行页：Moderator、工具调用、阶段、证据、失败原因和重试。
7. 审计页：Provider health、ToolCallEnvelope、权限、引用链和质量报告。

实时行情、告警和长任务统一使用 SSE；只有订单簿等确需双向低延迟的通道才使用 WebSocket。

## 10. 分阶段交付

### Phase 0：两个项目的契约和范围

建立 `hermes-data` 独立仓库，完成 `PROJECT_SCOPE.md`、`DATA_CONTRACTS.md`、OpenAPI/Protobuf、MCP tool schema、provider 许可清单和五类静态 fixture；同时建立 Dagster asset graph、分区策略、asset checks 和 raw-to-canonical lineage。工作台只保留 client contract，不再复制 provider 代码。

### Phase 1：统一数据平台只读切片

`hermes-data` 先接入一个 A 股 provider，提供 Python/TypeScript SDK、REST、MCP 和最小 WebSocket；由 Dagster 编排采集、实体映射、清洗、质量检查和快照发布，生成带日期、来源、缓存、schema、quality 和 raw hash 的快照。HermesAlpha 通过 SDK 消费，不直接安装 provider。

### Phase 2：多市场数据服务与研究闭环

`hermes-data` 增加港股、美股、加密货币和 Polymarket provider，完成 fallback、实时 topic、snapshot/replay 和数据质量 API；HermesAlpha 接入 StrategyDef、因子、回测、实验记录、报告引用和质量 Banner。

### Phase 3：工作台运行态

增加 SSE、JobRecord、worker lease、任务恢复、盯盘规则、建议池、组合优化和 paper broker。

### Phase 4：数据平台与工作台分布式演进

启用 `hermes-data` 的 Dagster、Redpanda、对象存储、Kubernetes 和水平扩展；按近期行情查询压力可选增加 TimescaleDB，按实时 Join、窗口聚合、物化视图和告警需求评估 RisingWave，只有全量 Tick、盘口历史和高并发分析成为瓶颈时再引入 ClickHouse。Temporal 仅在业务长流程确有需要时引入。工作台只扩展查询、回测、Agent 和执行服务，不复制采集链路。

### Phase 5：受控实盘

只在数据、审计、权限、风控和 paper 结果满足门禁后接入券商、交易所或 Polymarket 执行接口，并建立独立的实盘执行服务。

## 11. 验收标准

- 能回答每个结果来自哪个 provider、哪个日期、是否缓存或降级。
- Python SDK、TypeScript SDK、REST、MCP 和 WebSocket 对同一数据集保持契约一致。
- 新项目无需安装 provider 私有依赖，只通过 `hermes-data` 即可复用数据。
- 不同 provider 的同一实体使用稳定 `instrument_id`，并统一时间、时区、交易日历、单位、货币、精度和复权语义；原始字段仍可追溯。
- raw 数据不可变，清洗失败进入 quarantine，修复和供应商修订通过 `correction_id`、watermark 和版本化快照追踪，不能静默覆盖历史事实。
- SDK、API、MCP 和 WS 对同一查询返回相同的字段语义、质量状态、版本和可用时间。
- 同一策略可以用于筛选、监控和回测，并能解释三者差异。
- 回测可以用固定数据版本和参数重放。
- provider 失败不会生成看起来正常的新数据。
- 长任务重启后不会丢失终态或重复副作用。
- Agent 无法绕过服务端 scope、审批和 `paper_only`。
- Polymarket 的事件、概率、结算和股票行情不会互相污染。
- UI 能显示数据质量、任务进度、引用、权限和失败原因。
- 研究服务、回测 worker、数据采集和查询服务可以独立水平扩展。

## 12. 主要参考项目

- 数据平台与采集：`hermes-data`、`OpenBB`、`AKShare`、`CCXT`、`daily-stock-data`、`a-stock-data`、`agentic-china-data-tooling`、`tdx-market-data-clients`、`tickflow-stock-panel`
- 量化与回测：`Qlib`、`AlphaAgent`、`Lean`、`vn.py`、`PyPortfolioOpt`、`Quant Autoresearch`
- Agent 与研究：`ai-berkshire`、`JCP`、`TradingAgents Family`、`DeepFund`、`PanWatch`、`Vibe-Trading`
- 工作台与交互：`OpenAshare`、`tickflow-stock-panel`、`trade-skills`、`Vibe-Research`
- 治理与审计：`UZI-Skill`、`QuantDinger`、`PA-Agent`、`Privora Python Examples`、`joinquant-skill`、`quant-buddy-skill`
