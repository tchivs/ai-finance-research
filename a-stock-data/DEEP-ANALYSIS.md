# a-stock-data 深度分析

> A 股公开数据端点目录 · 数据源优先级 · 东财防封 · Agent Skill 化数据底座
> 源码: `/root/source/tmp/a-stock-data/`
> 原始仓库: <https://github.com/simonlin1212/a-stock-data>

---

## 1. 项目形态

`a-stock-data` 的核心不是 Python package，而是 `SKILL.md`。这个文件同时承担四个角色：

| 角色 | 内容 |
|---|---|
| Agent 触发器 | frontmatter 的 `name`, `description`, `version` 描述何时激活 |
| 数据源文档 | 十层数据架构、端点用途、字段说明、风险提示 |
| 可执行代码库 | 每个端点内嵌 Python 代码块，可直接复制执行 |
| 运维手册 | 更新日志记录失效接口、风控阈值、字段误判、兼容 bug |

这种形态非常适合 Agent 项目：LLM 不需要安装一个抽象库再猜 API，而是直接读到端点说明、调用代码、字段语义和已知坑。

---

## 2. 数据源治理: 不只是“能取到数据”

### 2.1 优先级按封禁风险和独有能力排序

项目最重要的工程判断是：行情、K 线、实时价、市值、基础财务等高频字段优先用 mootdx/腾讯，东财只做独有数据。

这解决了 A 股采集中常见的错误：把东财当万能源，批量任务并发一开就被封，最后把“风控问题”误判为“代码不稳定”。

建议当前项目把每个字段写成如下契约：

```text
field: pe_ttm
primary: tencent
fallback: eastmoney_push2
rate_limit: none for tencent, em_get for eastmoney
unit: ratio
known_pitfall: Tencent index 39 is PE_TTM; index 46 is PB
```

### 2.2 东财统一入口

`SKILL.md` 的 `em_get()` 是最值得迁移的代码模式。它集中处理：

| 能力 | 目的 |
|---|---|
| 全局 `requests.Session()` | Keep-Alive 复用连接 |
| 最小间隔 + 随机抖动 | 避免固定频率触发风控 |
| `HTTPAdapter + Retry` | 429/5xx/连接错误重试 |
| 403 不重试 | 403 是风控信号，继续打只会恶化 |
| 所有东财端点强制走 helper | 避免某个业务函数绕过限流 |

迁移时不要只复制函数，还要复制“禁止裸调东财”的代码规范。可以通过 lint/grep 检查 `eastmoney.com` 是否只出现在 provider 层。

---

## 3. 十层数据的真实价值

### 3.1 行情层

行情层拆成 mootdx、腾讯、百度 K 线三类。mootdx 负责交易级数据，腾讯负责估值字段，百度 K 线的特色是直接带 MA5/MA10/MA20。

关键点不是多源越多越好，而是每个源有明确职责：

| 字段类型 | 首选源 | 理由 |
|---|---|---|
| K 线/盘口/逐笔 | mootdx | TCP 行情协议，字段接近行情终端 |
| PE/PB/市值/涨跌停 | 腾讯 | 字段丰富且不封 IP |
| 带均线 K 线 | 百度 | 可减少本地指标计算，但稳定性需观察 |

### 3.2 研报层

东财 `reportapi` 提供个股/行业研报和 PDF，iwencai 提供自然语言主题检索，同花顺提供一致预期 EPS。

组合价值：

```text
主题发现: iwencai NL 搜索
    ↓
报告落地: 东财 reportapi + PDF
    ↓
估值量化: 同花顺一致预期 EPS
```

这比只搜网页更可审计，因为 PDF、评级、EPS 预测、机构名和发布日期都能落档。

### 3.3 信号与资金层

信号层聚焦短线和资金解释：同花顺热点给题材归因，东财 slist 给板块/概念归属，push2 给分钟资金流，datacenter 给龙虎榜/解禁。

建议迁移为四个标准上下文块：

| 上下文块 | 字段 |
|---|---|
| `theme_context` | 热点题材、概念板块、行业板块、龙头股 |
| `flow_context` | 主力/大单/中单/小单/超大单资金流 |
| `event_context` | 解禁、大宗、分红、公告、互动易问答 |
| `short_term_context` | 涨停池、炸板率、连板梯队、龙虎榜席位 |

### 3.4 打板层和舆情互动层

V3.3 新增的打板层和舆情互动层很适合补当前项目的市场情绪维度。

打板层提供的是“短线资金在做什么”：涨停数量、最高连板、炸板率、昨日涨停赚钱效应、涨停原因。互动易和热榜提供的是“市场在问什么/炒什么”：投资者问题、公司回应、人气排名、概念命中。

这两类数据不应用来直接给买卖建议，但适合做：

1. 盘后市场温度计。
2. 个股催化剂核验。
3. 题材生命周期跟踪。
4. Agent 报告里的“市场是否已经开始交易这个逻辑”。

---

## 4. 更新日志体现的工程经验

这个项目的 README 更新日志比很多源码更有价值，因为它记录了真实 A 股数据接口的漂移。

| 问题 | 经验 |
|---|---|
| 财联社旧 API 404 | 新闻源必须有替代源，不能写死一家 |
| 百度 PAE 板块接口失效 | 概念归属要能换源，并保留旧源失败说明 |
| 巨潮公告 orgId 硬编码错误 | 标识符映射不能靠代码拼接，应查官方映射表 |
| mootdx BESTIP 空串崩溃 | 依赖 bug 不一定靠锁版本解决，可能需要兼容 helper |
| EPS 取错列 | 关键财务字段必须按列名取，不按 `iloc` 取 |
| 分钟 K 参数静默退化 | 第三方库的 `**kwargs` 静默吞错参数很危险，需要 smoke 示例 |

迁移建议：为当前项目建立 `DATA_SOURCE_ISSUES.md` 或 `PROVIDER_NOTES.md`，记录每个端点的验证日期、失败表现和替代路径。

---

## 5. 对当前项目的落地方案

### 5.1 Provider Registry

```text
ProviderRegistry
  field -> ordered providers
  provider -> rate limiter
  provider -> auth requirements
  provider -> known pitfalls
```

示例：

```text
quote.pe_ttm: Tencent -> Eastmoney
report.stock: Eastmoney reportapi
report.theme: iwencai -> Eastmoney industry reports
event.investor_qa: cninfo irm
short.limit_pool: Eastmoney push2ex -> THS reveal
```

### 5.2 Rate Limit Boundary

所有东财请求放到单独模块，外部只能调用领域函数，不能拿到底层 URL。对批量任务暴露参数：

```text
EM_MIN_INTERVAL=1.0
EM_BATCH_INTERVAL=1.5
EM_MAX_RETRIES=3
EM_CONCURRENCY=1
```

### 5.3 Data Contract

每个端点输出必须声明：

| 字段 | 必填 |
|---|---|
| source | 是 |
| fetched_at | 是 |
| unit | 金额/比例/股数必须写 |
| symbol_format | 统一内部格式 |
| raw_payload_ref | 可选，便于审计 |
| quality_note | 可选，记录风控/空值/替代源 |

### 5.4 Agent 使用边界

`a-stock-data` 是数据工具，不是分析结论。Agent 层应该把它输出作为证据，并通过质量 gate 检查：

1. 是否有来源和时间。
2. 是否有单位。
3. 是否存在风控空值。
4. 是否和其他来源冲突。
5. 是否属于舆情/短线情绪而非基本面事实。

---

## 6. 值得直接写进项目规范的原则

1. 能用不封 IP 的源，就不要用高风控源。
2. 东财只拿独有数据，所有请求走统一限流入口。
3. 不按列序取关键财务字段。
4. 采集代码必须写字段单位和源验证日期。
5. 上游接口失效要记录替代源和失败表现。
6. Agent 调数据时必须保留 source、fetched_at、quality_note。
7. 舆情和热榜只能作为市场关注度证据，不能直接等同于投资逻辑。
