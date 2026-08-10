# daily_stock_analysis — 设计分析与借鉴

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/ZhuLinsen/daily_stock_analysis
> 分析基线：
> - `daily_stock_analysis`：commit `396d43a4c76ffa940e2b9aea7bbe8686343c694a`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/daily_stock_analysis`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `daily_stock_analysis`：`905c339d80ad` → `396d43a4c76f`

提交摘要：
- 396d43a docs: prepare v3.30.0 release (#2180)
- 071c5aa fix: stabilize Xiaohongshu share image caption (#2179)
- 40b8c6c fix: 修复首页移动端个股栏触摸滚动 (#2171)
- 5698068 fix: split level-one headings without recursion (#2176)
- 46d5bf3 fix: 恢复桌面端报告分享图 (#2169)
- ed848da feat: persist Agent Chat Skill selection by session (#2160)
- ae19329 fix: stabilize watchlist details and workspace state (#2126)
- 03dd26a ci: shard backend tests across runners (#2165)
受影响路径：
- `M	.env.example`
- `A	.github/ci-test-durations.json`
- `M	.github/requirements-ci.txt`
- `M	.github/workflows/00-daily-analysis.yml`
- `M	.github/workflows/ci.yml`
- `M	.github/workflows/docker-publish.yml`
- `M	.gitignore`
- `M	README.md`
- `A	THIRD_PARTY_NOTICES.md`
- `M	api/deps.py`
- `M	api/v1/endpoints/__init__.py`
- `M	api/v1/endpoints/agent.py`
- 其余 229 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> 原始仓库: <https://github.com/ZhuLinsen/daily_stock_analysis>
**定位**: LLM 驱动多市场股票智能分析系统  
**版本分析**: 最新

---

## 1. 多数据源策略层（核心亮点）

### 策略模式 + 自动故障切换

```
DataFetcherManager
├── TushareFetcher (priority 0)
├── EfinanceFetcher (priority 0)  ← 同优先级，按初始化顺序
├── AkshareFetcher (priority 1)
├── PytdxFetcher (priority 2)     ← 通达信协议
├── BaostockFetcher (priority 3)
├── YfinanceFetcher (priority 4)
├── LongbridgeFetcher (priority 5) ← 长桥 OpenAPI 美股/港股兜底
└── FinnhubFetcher / AlphaVantageFetcher (optional)
```

### 动态优先级
- **配置了 TUSHARE_TOKEN** → Tushare 升至最高优先级
- **未配置** → Efinance 升至最高优先级
- Longbridge 作为港股/美股最后兜底

### 基类设计
```python
class BaseFetcher:
    """Abstract base for all data fetchers"""
    PRIORITY: int
    def fetch_kline(self, code, ...) -> DataFrame
    def fetch_quote(self, code, ...) -> DataFrame
    def can_handle(self, code) -> bool  # 判断是否支持该市场/代码
```

### 借鉴点
- **当前项目的多数据源整合**可直接复用此策略模式：
  - ashare-audit 的 akshare_provider 拆分可参考此结构
  - 优先级动态调整 + 故障自动切换 = 提高数据可用性
- `can_handle()` 接口 → 市场路由判断

---

## 2. YAML 策略声明式定义

### 策略定义（示例：龙头策略）
```yaml
name: dragon_head
display_name: 龙头策略
description: 板块轮动中识别龙头股
category: trend
core_rules: [2, 7]
required_tools:
  - get_realtime_quote
  - get_sector_rankings
  - search_stock_news
default_priority: 90
market_regimes: [sector_hot]
instructions: |
  评估标准：
  1. 板块领涨地位...
  2. 换手率与动能...
  ...
  评分调整：
  - 确认为龙头股：sentiment_score +10
```

### 全部 16 个策略
| 策略文件 | 类型 |
|----------|------|
| dragon_head.yaml | 龙头策略 |
| volume_breakout.yaml | 放量突破 |
| shrink_pullback.yaml | 缩量回踩 |
| ma_golden_cross.yaml | 均线金叉 |
| bull_trend.yaml | 多头趋势 |
| hot_theme.yaml | 热点题材 |
| bottom_volume.yaml | 底部放量 |
| chan_theory.yaml | 缠论 |
| wave_theory.yaml | 波浪理论 |
| box_oscillation.yaml | 箱体震荡 |
| emotion_cycle.yaml | 情绪周期 |
| one_yang_three_yin.yaml | 一阳三阴 |
| event_driven.yaml | 事件驱动 |
| growth_quality.yaml | 成长质量 |
| expectation_repricing.yaml | 预期重定价 |

### YAML 定义的优点
- 非开发者也能添加/修改策略
- 统一结构，便于管理和测试
- `market_regimes` → 策略和市场阶段绑定

### 借鉴点
- 当前项目用硬编码的策略逻辑 → 改为声明式 YAML 更灵活
- `required_tools` 声明依赖 → 前置检查可用性
- `market_regimes` → 只在特定市场条件下启用

---

## 3. 通知系统

### 多渠道路由
```python
src/notification.py:
- 企业微信 Webhook
- 飞书 Webhook
- Telegram Bot
- 邮件 SMTP
- Pushover（手机/桌面推送）
```

### 通知能力抽象
```python
src/notification_capabilities.py   # 能力定义
src/notification_contracts.py      # 合约接口
src/notification_routing.py        # 路由逻辑
src/notification_noise.py          # 噪音控制（避免轰炸）
```

### 特色
- 一个渠道失败不影响其他
- 噪音控制：限制同一条推送重复发送
- 报告类型区分（日报/即时报/预警）

### 借鉴点
- 当前项目的通知系统（HermesAlpha 已有 Telegram/飞书/邮件）可吸收：
  - 按推送类型路由（非全量发）
  - 单渠道失败不影响主流程
  - Hermes 的 `cronjob` 的 `deliver` 逻辑可与此结合

---

## 4. 市场阶段分析系统

```
src/core/
├── market_review.py          # 大盘分析
├── market_review_lock.py     # 分析互斥锁
├── market_review_runtime.py  # 运行时
├── market_profile.py         # 市场画像
├── market_strategy.py        # 策略匹配
├── trading_calendar.py       # 交易日历
└── config_manager.py         # 配置管理
```

### 市场阶段输出
- 大盘情绪（牛/熊/震荡）
- 板块轮动阶段
- 成交量分析
- 风险提示

### 借鉴点
- 阶段分析 + 策略匹配 → 市场画像决定用什么策略

---

## 5. AGENTS.md 质量治理（高亮参考）

这是见过的最严谨的 AI 协作治理文件之一。

### 验证矩阵
| 检查项 | 来源 | 是否阻断 |
|--------|------|---------|
| ai-governance | AGENTS.md/CLAUDE.md 一致性 | 是 |
| backend-gate | ci_gate.sh 脚本 | 是 |
| docker-build | 构建验证 | 是 |
| web-gate | lint+build | 是（触发时） |
| network-smoke | pytest network | 否，观测项 |
| pr-review | 静态检查+AI审查 | 否，辅助项 |

### 稳定性护栏
- 修改 `.env` 语义 → 同时评估本地/Docker/GitHub Actions/API/Web/Desktop 影响
- 新配置优先「不配置也可运行，配置后增强能力」
- 单一数据源/通知渠道失败不应拖垮整个流程
- 改 API/Schema/认证时，同时检查后端/Web/Desktop 兼容性

### 借鉴点
- 当前项目的 AGENTS.md / CLAUDE.md 可吸收这些质量护栏规则
- 验证矩阵思想 → 每类改动对应最简验证集
- 「稳定性护栏」条款 → 避免单点故障级联

---

## 6. 完整项目结构层次

```
├── main.py                     # CLI 入口
├── server.py                   # FastAPI 入口
├── webui.py                    # Web UI 入口
├── src/
│   ├── core/                   # 核心流程编排
│   ├── services/               # 业务服务
│   ├── repositories/           # 数据访问
│   ├── schemas/                # 数据结构
│   ├── agent/                  # Agent 层
│   ├── llm/                    # LLM 适配
│   ├── utils/                  # 工具
│   └── notification_sender/    # 通知发送
├── data_provider/              # 数据源（独立包）
├── strategies/                 # YAML 策略
├── api/                        # REST API
├── bot/                        # IM 机器人
│   ├── platforms/              # 各平台适配
│   ├── commands/               # 命令处理
│   └── dispatcher.py           # 消息路由
├── apps/                       # 前端
│   ├── dsa-web/                # Web 前端
│   └── dsa-desktop/            # 桌面端
├── scripts/                    # CI/部署脚本
├── docker/                     # Docker 配置
└── tests/                      # 测试
```

层次清晰，模块间边界明确，适合做大型项目的目录结构模板。

---

## 当前项目可借鉴点总结

| 维度 | daily_stock_analysis 做法 | 适用项目 |
|------|--------------------------|---------|
| 数据源 | 策略模式 + 动态优先级 + 自动 fallback | ashare-audit |
| 策略 | YAML 声明式 + 市场阶段绑定 | 策略系统 |
| 通知 | 多渠道 + 路由 + 噪音控制 | HermesAlpha 通知 |
| 质量治理 | 验证矩阵 + 稳定性护栏 | 所有项目的 AGENTS.md |
| 组织架构 | 清晰的分层目录 + 模块边界 | 大型项目模板 |
