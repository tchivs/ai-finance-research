# Vibe-Trading 终极深度逆向分析

> 79 技能 · 53 MCP 工具 · 9 回测引擎 · 5 组合优化器
> 源码: `/root/source/tmp/Vibe-Trading/`
> 原始仓库: <https://github.com/HKUDS/Vibe-Trading>

---

## 1. 79 技能生态

### 1.1 分类体系

| 类别 | 数量 | 代表技能 |
|------|------|---------|
| **数据源** | 15 | akshare, tushare, yfinance, eastmoney, ccxt, okx-market, mootdx, finnhub, edgar-sec-filings, sec-edgar |
| **策略** | 18 | ichimoku, candlestick, chanlun(缠论), elliott-wave, harmonic, smc, pair-trading, multi-factor, event-driven, seasonal, pine-script |
| **资产** | 12 | crypto-derivatives, convertible-bond, us-etf-flow, hk-connect-flow, defi-yield, onchain-analysis, stablecoin-flow, perp-funding-basis, token-unlock-treasury |
| **分析** | 18 | earnings-forecast, earnings-revision, factor-research, sentiment-analysis, liquidation-heatmap, market-microstructure, credit-analysis, geopolitical-risk |
| **输出/执行** | 8 | vnpy-export, report-generate, strategy-generate, trade-journal, execution-model, research-goal |
| **综合** | 8 | corporate-events, global-macro, sector-rotation, commodity-analysis, cross-market-strategy, behavioral-finance |

### 1.2 Shadow Account 系列（独特设计）

| 技能 | 功能 |
|------|------|
| `analyze_trade_journal` | 分析交易日志 |
| `extract_shadow_strategy` | 从交割单蒸馏策略 |
| `run_shadow_backtest` | 用蒸馏策略回测 |
| `render_shadow_report` | 渲染策略报告 |
| `scan_shadow_signals` | 扫描当前信号 |

---

## 2. 9 个回测引擎

### 2.1 BaseEngine 共享执行循环

```python
# backtest/engines/base.py

class BaseEngine(ABC):
    """共享的 bar-by-bar 执行循环"""

    def run_backtest(self, config):
        # 1. 数据加载 (data_map: code -> OHLCV DataFrame)
        # 2. 信号对齐 (_align: signal shift 1 bar + ffill)
        # 3. 可选: optimizer 调整权重
        # 4. bar-by-bar 执行:
        #    for each date:
        #        for each symbol:
        #            if can_execute(symbol, direction, bar):
        #                execute_trade(...)
        # 5. calc_metrics → artifacts
```

**信号对齐** (`_align` 函数)：
- 信号在**自己的交易日历**上 shift 1 bar（next-bar-open 语义）
- 然后 ffill 到统一日期索引
- 跨市场时 ffill_limit=10（春节可达 9-10 bar），单一市场用 5
- 最终权重归一化：`sum(abs(weights)) <= 1.0`

### 2.2 ChinaAEngine（A股引擎）

```python
class ChinaAEngine(BaseEngine):
    """A股市场规则"""

    # 手续费模型
    commission_rate = 0.00025   # 万2.5
    commission_min  = 5.0       # 最低5元
    stamp_tax       = 0.0005    # 万5（卖出 only）
    transfer_fee    = 0.00001   # 万0.1（双边）
    slippage        = 0.001     # 0.1%

    def can_execute(self, symbol, direction, bar):
        # 1. 禁止做空
        if direction == -1: return False
        # 2. T+1: 今天买的明天才能卖
        if direction == 0 and bar_date == entry_date: return False
        # 3. 涨跌停限制
        #    主板 ±10%, 创业板/科创板 ±20%, ST ±5%
        if pct_chg >= limit: return False  # 涨停买不进
        if pct_chg <= -limit: return False # 跌停卖不出

    def round_size(self, raw_size, price):
        return max(int(raw_size / 100) * 100, 0)  # 100股整手

    def calc_commission(self, size, price, direction, is_open):
        notional = size * price
        comm = max(notional * 0.00025, 5.0)  # 佣金
        comm += notional * 0.00001           # 过户费
        if not is_open:
            comm += notional * 0.0005        # 印花税(卖出)
        return comm
```

### 2.3 引擎清单

| 引擎 | 市场 | 特殊规则 |
|------|------|---------|
| `china_a` | A股 | T+1, 涨跌停, 印花税, 100股整手 |
| `china_futures` | 中国期货 | T+0, 保证金, 强平 |
| `global_equity` | 全球股票 | 通用规则 |
| `global_futures` | 全球期货 | 多交易所时区 |
| `crypto` | 加密 | 7×24, 无涨跌停 |
| `forex` | 外汇 | 杠杆, 隔夜利息 |
| `options_portfolio` | 期权 | 行权/到期 |
| `composite` | 多资产 | 跨市场组合 |
| `futures_base` | 期货基类 | 共享逻辑 |

---

## 3. 回测指标计算

### 3.1 年化因子映射

```python
# backtest/metrics.py

_TRADING_DAYS = {"tushare": 252, "yfinance": 252, "okx": 365, "ccxt": 365}
_BARS_PER_DAY = {
    "1m":  {"tushare": 240, "okx": 1440, "yfinance": 390},
    "5m":  {"tushare": 48,  "okx": 288,  "yfinance": 78},
    "15m": {"tushare": 16,  "okx": 96,   "yfinance": 26},
    "1H":  {"tushare": 4,   "okx": 24,   "yfinance": 7},
    "1D":  {"tushare": 1,   "okx": 1,    "yfinance": 1},
}
```

### 3.2 交易统计

```python
def win_rate_and_stats(trades):
    return {
        "win_rate": len(wins) / len(trades),
        "profit_loss_ratio": avg_win / avg_loss,  # 盈亏比
        "max_consecutive_loss": max_consec,       # 最大连亏次数
        "avg_holding_bars": mean(holding_bars),   # 平均持仓bar数
        "profit_factor": gross_profit / gross_loss, # 盈利因子
    }
```

---

## 4. 5 个组合优化器

### 4.1 BaseOptimizer 抽象

```python
class BaseOptimizer(ABC):
    """滚动窗口 + 协方差矩阵 + 权重归一化"""

    def optimize(self, ret, pos, dates):
        for dt in dates:
            active = [c for c in codes if abs(pos.at[dt, c]) > 1e-9]
            if not active or i < self.lookback: continue
            window = ret.loc[:dt, active].tail(self.lookback)
            ctx = self._build_context(window, active)  # 子类实现
            weights = self._calc_weights(ctx)           # 子类实现
            for j, c in enumerate(active):
                sign = np.sign(pos.at[dt, c])
                result.at[dt, c] = sign * weights[j]    # 保留信号方向
```

### 4.2 RiskParityOptimizer（风险平价）

```python
class RiskParityOptimizer(BaseOptimizer):
    """Spinu (2013) 风格: inverse-vol 种子 + Newton 迭代"""

    def _calc_weights(self, ctx):
        cov = ctx["cov"]
        vols = np.sqrt(np.diag(cov))
        inv_vol = 1.0 / vols
        w = inv_vol / inv_vol.sum()  # 种子

        for _ in range(5):  # Newton 迭代
            port_vol = np.sqrt(w @ cov @ w)
            mrc = (cov @ w) / port_vol  # 边际风险贡献
            rc = w * mrc                # 风险贡献
            target = port_vol / n
            w = w * (target / (rc + 1e-12))
            w = w / w.sum()
        return w
```

### 4.3 优化器清单

| 优化器 | 算法 |
|--------|------|
| `max_diversification` | 最大化分散化比率 |
| `risk_parity` | 等风险贡献（Spinu 2013） |
| `equal_volatility` | 等波动率加权 |
| `mean_variance` | Markowitz 均值方差 |
| `base` | 抽象基类 |

---

## 5. MCP 三层架构

### 5.1 53 个 MCP 工具分类

```python
# agent/mcp_server.py

# === 技能管理 (2) ===
@mcp.tool  list_skills()             # 列出79技能
@mcp.tool  load_skill(name)          # 加载技能

# === 研究目标 (4) ===
@mcp.tool  start_research_goal(...)  # 启动研究目标
@mcp.tool  get_research_goal(id)     # 查询进度
@mcp.tool  add_goal_evidence(...)    # 添加证据
@mcp.tool  update_research_goal_status(...)

# === 回测/因子 (4) ===
@mcp.tool  backtest(config)          # 回测执行
@mcp.tool  factor_analysis(...)      # 因子分析
@mcp.tool  analyze_options(...)      # 期权分析
@mcp.tool  pattern_recognition(...)  # 形态识别

# === 文件/网页 (5) ===
@mcp.tool  read_url(url)             # 网页读取
@mcp.tool  read_document(path)       # 文档读取
@mcp.tool  web_search(query)         # 网页搜索
@mcp.tool  write_file(path, content)
@mcp.tool  read_file(path)

# === 交易接口 (8) ===
@mcp.tool  trading_connections()     # 列出券商连接
@mcp.tool  trading_select_connection(id)
@mcp.tool  trading_check()           # 连接检查
@mcp.tool  trading_account()         # 账户信息
@mcp.tool  trading_positions()       # 持仓
@mcp.tool  trading_orders(...)       # 下单
@mcp.tool  trading_quote(codes)      # 实时行情
@mcp.tool  trading_history(...)      # 历史成交

# === A股数据 (12) ===
@mcp.tool  get_market_data(code)     # K线数据
@mcp.tool  get_fund_flow(code)       # 资金流向
@mcp.tool  get_dragon_tiger(code)    # 龙虎榜
@mcp.tool  get_northbound_flow()     # 北向资金
@mcp.tool  get_margin_trading(code)  # 融资融券
@mcp.tool  get_block_trades(code)    # 大宗交易
@mcp.tool  get_shareholder_count(code) # 股东人数
@mcp.tool  get_lockup_expiry(code)   # 解禁到期
@mcp.tool  get_sector_info()         # 板块信息
@mcp.tool  get_research_reports(code) # 研报
@mcp.tool  get_stock_news(code)      # 新闻
@mcp.tool  get_financial_statements(code) # 财报

# === 美股/全球 (4) ===
@mcp.tool  get_sec_filings(ticker)   # SEC 公告
@mcp.tool  get_stock_profile(ticker) # 公司概况
@mcp.tool  get_options_chain(ticker) # 期权链
@mcp.tool  get_macro_series(...)     # 宏观数据

# === 筛选/搜索 (3) ===
@mcp.tool  screen_market(...)        # 市场筛选
@mcp.tool  search_symbol(keyword)    # 代码搜索
@mcp.tool  iwencai_search(query)     # 问财搜索

# === Swarm/运行管理 (6) ===
@mcp.tool  list_swarm_presets()      # 预设团队
@mcp.tool  get_swarm_status(run_id)
@mcp.tool  get_run_result(run_id)
@mcp.tool  list_runs()
@mcp.tool  reap_stale_runs()         # 清理超时
@mcp.tool  retry_run(run_id)

# === Shadow Account (5) ===
@mcp.tool  analyze_trade_journal(path)
@mcp.tool  extract_shadow_strategy(...)
@mcp.tool  run_shadow_backtest(...)
@mcp.tool  render_shadow_report(...)
@mcp.tool  scan_shadow_signals(...)
```

### 5.2 MCP Server vs API Server 分工

| 层 | 职责 | 技术 |
|----|------|------|
| MCP Server | 给 AI Agent 用的工具接口 | FastMCP (@mcp.tool) |
| API Server | 给前端/Web 用的 REST API | FastAPI (134 endpoint) |
| Frontend | React SPA | Vite + Tailwind |

MCP 工具是 AI-first 的：输入输出都是结构化 JSON，适合 LLM 直接调用。API Server 额外处理 SSE 流推送、Pydantic 验证、前端路由。

---

## 6. Shadow Account（影子账户）

Shadow Account 是 Vibe-Trading 最独特的功能：

```
真实交易日志 (交割单)
    ↓ analyze_trade_journal
结构化分析 (胜率/盈亏比/持仓时间/品种分布)
    ↓ extract_shadow_strategy
策略蒸馏 (识别交易者的隐含策略模式)
    ↓ run_shadow_backtest
策略回测 (用蒸馏策略跑历史数据)
    ↓ render_shadow_report
可视化报告 (策略表现/回测对比)
    ↓ scan_shadow_signals
实时信号扫描 (当前市场是否出现类似信号)
```

**核心价值**：从交易者的真实交割单中提取隐含策略，而不是要求用户显式编写策略。

---

## 7. 对当前项目的借鉴建议

### HermesAlpha

| 借鉴点 | 来源 | 实施 |
|--------|------|------|
| A股回测引擎 | `china_a.py` | T+1/涨跌停/印花税/100股整手 |
| 53 MCP 工具分类 | `mcp_server.py` | AI-first 数据接口 |
| Shadow Account | 5个shadow技能 | 从交割单蒸馏策略 |
| Risk Parity | `risk_parity.py` | 组合权重优化 |
| 年化因子映射 | `metrics.py` | 正确年化不同数据源/频率 |

### ashare-audit

| 借鉴点 | 来源 | 实施 |
|--------|------|------|
| A股手续费模型 | `china_a.py` | 万2.5+最低5元+万5印花+万0.1过户 |
| 涨跌停判定 | `_price_limit()` | 主板10%/创业科创20%/ST5% |
| win_rate_and_stats | `metrics.py` | 胜率/盈亏比/最大连亏/盈利因子 |
| _TRADING_DAYS 映射 | `metrics.py` | 不同数据源的正确年化 |
