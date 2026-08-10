# Vibe-Trading — 设计分析与借鉴

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/HKUDS/Vibe-Trading
> 分析基线：
> - `Vibe-Trading`：commit `d8d22a70f702da85aa55a6e920c2db89ae58dfa8`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/Vibe-Trading`
<!-- source-sync:end -->


> 原始仓库: <https://github.com/HKUDS/Vibe-Trading>
**定位**: 自然语言驱动的个人交易 AI Agent，直接关联券商账户  
**版本分析**: v0.1.10

---

## 1. MCP 服务化架构

核心设计：**CLI + API + MCP 三层** 暴露能力。

```
vibe-trading (CLI/TUI)        # 交互式命令行
    ├── vibe-trading serve    # FastAPI 服务器
    └── vibe-trading-mcp      # MCP Server（Claude/Cursor/OpenClaw 接入）
```

MCP Server 设计：

```python
mcp:
  command: vibe-trading-mcp
  args: []
```

> 通过 MCP 对外暴露工具，任何支持 MCP 的 Agent（Claude Desktop、Cursor、OpenClaw）都可直接调用。

### 借鉴点
- 当前项目（HermesAlpha 等）可以 **MCP 化暴露关键功能**（查询、分析、交易信号）
- MCP 是插件与 Agent 之间的标准接口，避免绑定特定平台
- Hermes 有 `hermes-mcp-server` skill 和 `native-mcp` skill，可直接用

---

## 2. LangGraph Agent 编排

### 状态管理
```python
agent/src/core/state.py       # Agent 状态定义
agent/src/core/runner.py      # Agent 执行器
```

LangGraph 提供有向图状态管理，节点间通过状态对象传递数据。

### 借鉴点
- HermesAlpha 的交易决策流程可借鉴 LangGraph 的状态机模式（不同阶段：数据收集→分析→决策→执行→反馈）
- 有向图拓扑比硬编码 if-else 更灵活、可扩展

---

## 3. Alpha Zoo — 量化信号库

核心数据资产：**452 个预构建量化 Alpha 信号**。

| 来源 | 数量 | 说明 |
|------|------|------|
| qlib158 | 158 | 微软 Qlib 标准 Alpha |
| alpha101 | 101 | WorldQuant 101 Alpha |
| gtja191 | 191 | 国泰君安 191 Alpha |
| academic | 2+ | 学术文献因子 |

### Signal Engine 模式
每个策略以 `example_signal_engine.py` 为模板：
```
agent/src/skills/ichimoku/example_signal_engine.py
agent/src/skills/multi-factor/zoo_signal_engine.py
agent/src/skills/event-driven/example_signal_engine.py
...
```

### 借鉴点
- HermesAlpha 的策略库也可用「引擎模板」组织

---

## 4. Backtesting 引擎

7 个回测引擎 + 基准对比面板：
```
backtest/
├── engine_*.py       # 7 种回测引擎
├── benchmark.py      # 基准对比（买入持有等）
└── results.py        # 结果聚合与可视化
```

### Shadow Account 闭环
```
交易日志/笔记 → 提取隐含规则 → 回测验证 → 效果可视化 → 改进规则
```

- 从自然语言记录的交易日志中提取交易规则
- 规则跨市场回测（A股/港股/美股/加密）
- 输出优化后的交易策略

### 借鉴点
- Shadow Account 模式 → 用户交易日志自动分析 → 策略优化
- HermesAlpha 的策略验证可接入回测引擎

---

## 5. Data Federation — 多数据源联邦

### 覆盖数据源（18个）
```
tushare, yfinance, okx, akshare, baostock, tencent, mootdx,
ccxt, futu, local, eastmoney, sina, stooq, yahoo,
finnhub(opt), alphavantage(opt), tiingo(opt), fmp(opt)
```

### 市场覆盖
A股 + 港股 + 美股 + Crypto + 期货 + 期权

### 借鉴点
- 当前项目的数据源接入可参照此范围
- 可选数据源的模式（opt-key）→ 有 key 增强，无 key 可用，降低配置门槛

---

## 6. 前端 Dashboard

```
frontend/
├── src/              # React + TypeScript
├── tailwind.config.ts
├── vite.config.ts
└── vitest.config.ts
```

FastAPI 后端 + React 前端，打包成 Docker 一键部署。
`docker-compose.yml` + `Dockerfile` 全容器化。

### 借鉴点
- HermesAlpha 的看板/面板可直接参考前端架构
- Docker 部署模式可作为标准模板

---

## 当前项目可借鉴点总结

| 维度 | Vibe-Trading 做法 | 适用项目 |
|------|------------------|---------|
| MCP 服务 | CLI+API+MCP 三层暴露 | 所有项目服务化 |
| Agent 编排 | LangGraph 状态机 | HermesAlpha 决策流程 |
| 策略引擎 | Signal Engine 模板 + 452 Alpha | HermesAlpha 策略库 |
| 回测 | 7 引擎 + 基准对比 | HermesAlpha 策略验证 |
| Shadow Account | 日志 → 规则提取 → 回测 → 优化 | 交易日志分析 |
| 数据源 | 18 源联邦 + opt-key | 所有数据需求 |
