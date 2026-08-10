# UZI-Skill 终极深度逆向分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/wbh604/UZI-Skill
> 分析基线：
> - `UZI-Skill`：commit `0acf25122cabf493e7bc442faff62ceceb7f2f02`
> 分析日期：2026-08-09
> 本地源码目录：
> - `src/UZI-Skill`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `UZI-Skill`：`fce996c33e70` → `0acf25122cab`

提交摘要：
- 0acf251 docs: bump 头部到 v3.9.4 并补更新日志 (kimi-k3)
- 39e24ae fix: 前端显示修复 + 美化 (v3.9.4 · kimi-k3)
- 9643965 chore: bump all manifests to v3.9.3
- 76ecb87 docs: bump header to v3.9.3 and add full release notes
- af04ceb fix: address Codex review on PR #98 (P1 fcf + P2 peers/viz)
- cd4a135 Merge pull request #98 from wbh604/release/v3.9.3-fixes
- 2594162 docs: add v3.9.3 changelog for Moutai-driven data/rendering fixes
- d9e1e94 fix(viz): don't render "(None)" next to consensus target price
受影响路径：
- `M	.claude-plugin/plugin.json`
- `M	.cursor-plugin/plugin.json`
- `M	.env.example`
- `M	AGENTS.md`
- `M	CLAUDE.md`
- `M	README.md`
- `M	README_EN.md`
- `M	RELEASE-NOTES.md`
- `M	SKILL.md`
- `M	docs/BUGS-LOG.md`
- `A	docs/plans/2026-08-05-global-peer-comparison.md`
- `M	gemini-extension.json`
- 其余 38 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->


> 版本: v3.9.1 · 66 位评委 · 22 维数据 · A/H/U 三市场
> 源码: `src/UZI-Skill/skills/deep-analysis/scripts/`
> 原始仓库: <https://github.com/wbh604/UZI-Skill>

---

## 1. Pipeline 架构全解

### 1.1 数据流图

```
用户输入 (ticker / 中文名)
    │
    ├── 中文名 → _preflight_guards 抛 ValueError → fallback legacy stage1
    ├── ETF/可转债 → 同上
    │
    ▼
pipeline.collect (wave-based 并发)
    │
    ├── Wave 1: 0_basic (单跑, 后续依赖 industry)
    ├── Wave 2: 非依赖 fetcher × max_workers=6 并发
    │   └── mini_racer fetcher 加锁串行 (threading.Lock)
    └── Wave 3: 依赖型 (3_macro/7_industry/9_futures/13_policy)
    │
    ▼
写 raw_data.json (legacy 兼容格式)
    │
    ▼
pipeline.score_from_cache
    ├── _autofill_qualitative_via_mx (MX API 补定性)
    ├── autofill_via_playwright (Playwright 兜底)
    ├── score_dimensions (22维打分)
    ├── generate_panel (66评委投票)
    └── generate_synthesis (DCF/LBO/BCG/Porter)
    │
    ▼
写 dimensions.json + panel.json + synthesis.json
    │
    ▼
pipeline.synthesize_and_render → rrt.stage2
    ├── self_review (20条硬规则 → _review_issues.json)
    ├── assemble_report (SVG + HTML 模板)
    └── HTML 报告 (~124KB 单文件)
```

### 1.2 Wave-based 并发编排

```python
# lib/pipeline/collect.py 核心

# Wave 1: 0_basic 必须先跑 (后续 fetcher 需要 industry)
basic_fetcher = get_fetcher("0_basic")
result = basic_fetcher.fetch(ticker)

# Wave 2: 非依赖型并发 (ThreadPoolExecutor max_workers=6)
non_dep_dims = [d for d in FETCHER_REGISTRY.keys()
                if d not in DEPENDENT_DIMS and d != "0_basic"]
with ThreadPoolExecutor(max_workers=6) as pool:
    futures = {pool.submit(fetch_one, dim, ticker): dim for dim in non_dep_dims}
    for future in as_completed(futures):
        dim_key = futures[future]
        result = future.result()
        out[dim_key] = result

# Wave 3: 依赖型串行 (需要 0_basic.industry)
for dim in DEPENDENT_DIMS:
    fetcher = get_fetcher(dim)
    out[dim] = fetcher.fetch(ticker, raw=out)
```

**mini_racer 锁**：V8 isolate 非线程安全，`fetch_industry`、`fetch_capital_flow`、`fetch_valuation` 三个模块共享 `_MINI_RACER_LOCK`，并发时自动串行。

### 1.3 Feature Flags

| 环境变量 | 默认 | 作用 |
|---------|------|------|
| `UZI_PIPELINE` | `0` | =1 走新管道，否则走 legacy |
| `UZI_LEGACY` | `0` | =1 强制走 legacy |
| `UZI_PLAYWRIGHT_FORCE` | `0` | =1 强制启用 Playwright |
| `UZI_AK_CNINFO_FALLBACK` | `0` | =1 允许 akshare 慢路径 fallback（公告翻页）|

### 1.4 Phase 6c 解耦优化

**为什么这么设计**：v3.0 前 `pipeline.score` 调 `rrt.stage1(ticker)`，stage1 内部重新 collect 数据 + scoring，浪费 5-10 min/股。

Phase 6c 改为：pipeline 已经 collect 完 → 只调 rrt 里的**纯函数**（`score_dimensions`/`generate_panel`/`generate_synthesis`），不再调 stage1。

---

## 2. 22 维数据采集系统

### 2.1 Fetcher 注册表（工厂模式）

```python
# lib/pipeline/fetchers/registry.py

def _make_adapter(dim_key, legacy_module, required, optional,
                  args_fn, top_level=None, depends_on=None,
                  markets=("A","H","U"), sources=None) -> type:
    """工厂函数 · 生成 BaseFetcher 子类"""
    spec = FetcherSpec(dim_key=dim_key, required_fields=required, ...)
    # 用 type() 一次性创建，规避 __init_subclass__ 提前检查
    return type(cls_name, (BaseFetcher,), namespace)

FETCHER_REGISTRY = {
    "0_basic":       _make_adapter("fetch_basic",       ["name","price"], ...),
    "1_financials":  _make_adapter("fetch_financials",   ["roe","net_margin"], ...),
    "2_kline":       _make_adapter("fetch_kline",        [], ...),
    "3_macro":       _make_adapter("fetch_macro",        [], depends_on=["0_basic"], ...),
    # ... 共 22 个
}
```

### 2.2 完整 22 维清单

| # | dim_key | 采集内容 | 数据源 | 关键字段 |
|---|---------|---------|--------|---------|
| 0 | `0_basic` | 基础信息 | akshare | name, price, industry, market_cap, pe_ttm, pb, actual_controller |
| 1 | `1_financials` | 财报三表 | akshare | roe_history, revenue_history, net_margin, debt_ratio |
| 2 | `2_kline` | K线走势 | akshare | kline_daily, ma5/20/60, stage, ma_align |
| 3 | `3_macro` | 宏观环境 | akshare | rate_cycle, fx_trend, commodity (依赖 industry) |
| 4 | `4_peers` | 同行对比 | akshare | peer_table, rank |
| 5 | `5_chain` | 产业链 | akshare | upstream, downstream, client_concentration |
| 6 | `6_fund_holders` | 基金持仓 | akshare | total_funds_holding (top_level: fund_managers) |
| 6b | `6_research` | 研报评级 | akshare | coverage, target_price_avg |
| 7 | `7_industry` | 行业景气 | akshare/cninfo | tam, growth, lifecycle (依赖 industry) |
| 8 | `8_materials` | 原材料成本 | akshare | commodity_costs |
| 9 | `9_futures` | 期货数据 | akshare | futures_prices (依赖 industry) |
| 10 | `10_valuation` | 估值数据 | akshare | pe/pb/ps history |
| 11 | `11_governance` | 公司治理 | akshare | chairman, board |
| 12 | `12_capital_flow` | 资金流向 | akshare | main_5d_net, unlock_schedule |
| 13 | `13_policy` | 政策环境 | WebSearch | policy_items (依赖 industry) |
| 14 | `14_moat` | 护城河 | MX API | moat_score |
| 15 | `15_events` | 事件/公告 | cninfo直连 | news, notices |
| 16 | `16_lhb` | 龙虎榜 | akshare | lhb_count_30d, matched_youzi |
| 17 | `17_sentiment` | 舆情热度 | 雪球 | hot_rank |
| 18 | `18_trap` | 杀猪盘检测 | WebSearch | promo_traces |
| 19 | `19_contests` | 实盘赛 | 雪球 | xueqiu_cubes_total |

### 2.3 Fallback 策略

```
akshare 主路径
    ↓ 失败/超时
东财直连 API (requests.post → eastmoney.com)
    ↓ 失败
Playwright 浏览器渲染 (UZI_PLAYWRIGHT_FORCE=1 或 lite profile)
    ↓ 失败
MX API 补齐定性维度 (_autofill_qualitative_via_mx)
    ↓ 失败
标记 data_gap, self_review 记 warning
```

**cninfo 翻页陷阱**（BUG #68）：`ak.stock_zh_a_disclosure_report_cninfo` 内部翻完 800+ 页才返回。修复：直连 cninfo API，pageSize=30，一次 HTTP ≤15s。

---

## 3. 评分系统深度解析

### 3.1 19 维度评分函数（score_dimensions）

每个维度评分 1-10，有权重 weight（3-5），最终加权平均 × 10 = fundamental_score (0-100)。

```python
# lib/pipeline/score_fns.py

def score_dimensions(raw: dict) -> dict:
    # 1 · 财报 (weight=5)
    roe = last_roe
    score_1 = 5  # baseline
    if roe >= 15: score_1 += 2
    elif roe >= 10: score_1 += 1
    elif roe < 5: score_1 -= 2
    if net_margin >= 15: score_1 += 1
    if growth >= 20: score_1 += 1
    if debt >= 60: score_1 -= 1
    score_1 = max(1, min(10, score_1))  # clamp

    # 2 · K线 (weight=4)
    if "Stage 2" in stage: score_2 += 2
    if "多头" in ma_align: score_2 += 1
    if max_drawdown <= -30: score_2 -= 1

    # 12 · 资金流向 (weight=4)
    if main_5d_net > 0: score_12 += 2
    elif main_5d_net < 0: score_12 -= 1

    # 18 · 杀猪盘 (weight=5, 默认安全 9分)
    out["18_trap"] = {"score": 9, "weight": 5, "label": "🟢 未发现推广痕迹"}

    # 19 · 实盘赛 (weight=4)
    score_19 = 5 + min(3, xq_total // 5) + min(2, high_return_cubes)

    # Overall
    total_weighted = sum(v["score"] * v["weight"] for v in out.values())
    total_weight = sum(v["weight"] for v in out.values())
    fundamental = total_weighted / total_weight * 10
```

### 3.2 特征提取层（stock_features.py）

**核心设计**：这是所有评委规则的**唯一数据源**。评委 criteria 只读 features dict，永远不碰 raw_data。

```python
# lib/stock_features.py
# ~60 个标准化字段，从 raw_data.dimensions 提取

def extract_features(raw: dict, dims: dict) -> dict:
    f = {}
    # BASIC / PRICE
    f["code"] = basic.get("code")
    f["price"] = _f(basic.get("price"))
    f["market_cap_yi"] = _f(...)
    f["industry"] = basic.get("industry")

    # FINANCIALS (标准化)
    f["roe_latest"] = _last(roe_hist)
    f["roe_5y_avg"] = _avg(roe_hist[-5:])
    f["roe_5y_min"] = _min(roe_hist[-5:])
    f["roe_5y_above_15"] = sum(1 for v in roe_hist[-5:] if _f(v) > 15)
    f["revenue_latest_yi"] = _last(rev_hist)
    f["revenue_growth_yoy"] = _pct_change(rev_hist)
    f["net_margin"] = _last(np_hist) / _last(rev_hist) * 100
    f["debt_ratio"] = _f(health.get("debt_ratio"))
    f["fcf_positive"] = fcf > 0

    # 派生特征
    f["ai_chain_hit"] = _check_ai_chokepoint(basic, chain, industry)
    f["ai_chokepoint_score"] = _score_chokepoint(...)
    # ... 共 ~60 个
    return f
```

**为什么这么设计**：raw_data 是非结构化的（不同 fetcher 返回不同格式），特征层做**一次性标准化**，评委规则只引用稳定 key 名。改 fetcher 不影响评委逻辑。

---

## 4. 66 评委系统

### 4.1 九组完整名单

| 组 | 流派 | 人数 | 代表评委 |
|----|------|------|---------|
| **A** | 经典价值 | 6 | 巴菲特、格雷厄姆、费雪、芒格、邓普顿、卡拉曼 |
| **B** | 成长投资 | 9 | 彼得·林奇、欧奈尔、彼得·蒂尔、木头姐、安德森、纳瓦尔、格斯特纳 |
| **C** | 宏观对冲 | 4 | 索罗斯、达里奥、塔勒布、德鲁肯米勒 |
| **D** | 技术分析 | 4 | 威廉、米纳尔维尼、温斯坦、欧奈尔 |
| **E** | 中国价值 | 5 | 段永平、张磊、谢治宇、冯柳、邓晓峰 |
| **F** | A股游资 | 24 | 章盟主、孙哥、赵老哥、炒股养家、**股海贼王**(v3.9.0蒸馏) |
| **G** | 量化系统 | 4 | 西蒙斯、索普、大卫·肖、阿斯尼斯 |
| **H** | 科技领袖 | 4 | 黄仁勋、马斯克、奥特曼、塞勒 |
| **I** | AI卡位 | 1 | Serenity (瓶颈猎手) |

### 4.2 Consensus 混合公式

```python
# v2.15.5 · 混合 consensus（连续分 + 离散票）

# 分量1: score 均值 (active only)
score_mean = sum(active_scores) / len(active_scores)

# 分量2: vote 比例
vote_weighted = (bullish + 0.6 * neutral) / active_count * 100

# 混合 + 极化
consensus_raw = 0.65 * score_mean + 0.35 * vote_weighted
consensus = polarize(consensus_raw, k=1.30)  # 50为中心，距离×1.30
```

**为什么混合**：v2.11 单一公式只看 signal 计数，把连续 score 压成 3 分类，导致多数股 consensus 聚集 40-55 区间分不开。加入 score_mean 保留"程度"信息。

### 4.3 SCHOOL_LOCK 机制

评委可被锁定为特定流派主导（如 `--school value` 锁定 A/E 组），非该流派的评委 signal 降权。

### 4.4 股海贼王蒸馏方法论（v3.9.0）

```
3898 张淘股吧实盘截图
    ↓ OCR + 结构化
8951 笔交割单（买/卖/持仓）
    ↓ 行为统计分析
5069 条发言蒸馏
    ↓ 规则提取
ghzw 评委规则引擎
    ├── 超短接力 (涨停板打板/接力)
    ├── 题材主线 (板块轮动识别)
    └── 格局票 (中线趋势持有)
```

---

## 5. 机构级财务模型

### 5.1 五大模型

| 模型 | 函数 | 用途 |
|------|------|------|
| DCF | `compute_dcf(features)` | WACC + 2-stage FCF + 终值 + 5×5 敏感性表 |
| Comps | `build_comps_table(features)` | 同行倍数 + 百分位 + 隐含价格 |
| 3-Statement | `project_three_stmt(features)` | 5年 IS/BS/CF 预测 + 三表联动 |
| LBO | `quick_lbo(features)` | entry EV + 债务表 + exit IRR/MOIC |
| Accretion | `accretion_dilution(features)` | 并购 pro-forma EPS |

### 5.2 A 股默认参数

```python
DEFAULT_RF = 0.025          # 10年期中国国债收益率
DEFAULT_ERP = 0.06           # A股历史股权风险溢价
DEFAULT_BETA = 1.00
DEFAULT_TAX = 0.25           # 标准税率 (高新企业 15%)
DEFAULT_TERMINAL_G = 0.025   # 长期名义 GDP
```

### 5.3 methodology_log 可追溯机制

每个模型的返回 dict 里都带 `methodology_log` 列表，记录每步计算过程：

```python
return {
    "intrinsic_per_share": 85.2,
    "safety_margin_pct": 32.5,
    "methodology_log": [
        "Step 1 · WACC = rf(2.5%) + beta(1.0) × ERP(6%) = 8.5%",
        "Step 2 · Base FCF = revenue × net_margin × 0.8 = 12.3亿",
        "Step 3 · Stage1 PV (5yr, g=10%) = 55.8亿",
        "Step 4 · Terminal PV (g=2.5%) = 210.4亿",
        "Step 5 · Equity = EV - debt + cash = 256亿",
        "Step 6 · Per share = 256 / 3.0 = 85.2元",
    ],
}
```

**为什么这么设计**：报告能引用"为什么这个数是这个值"，而不是黑盒输出一个 DCF 结果。

### 5.4 IC Memo（投资委员会备忘录）

```python
def build_ic_memo(features, raw_data, dcf_result, comps_result) -> dict:
    """结构化 IC 备忘录 · 8 章节"""
    return {
        "I_exec_summary": {"headline": "🟢 强烈建议通过", "top_3_risks": [...]},
        "II_company_overview": {...},
        "III_industry_market": {"tam": ..., "growth": ..., "lifecycle": ...},
        "IV_financial_analysis": {"roe_5yr": [...], "fcf_positive": True},
        "V_valuation": {"dcf": {...}, "comps": {...}},
        "VI_risks_mitigants": [...],
        "VII_returns_scenarios": {...},  # 牛/中/熊三情景
        "VIII_recommendation": "推荐投委会批准建仓",
    }
```

---

## 6. 报告渲染引擎

### 6.1 SVG 原语系统（19 个）

```python
# lib/report/svg_primitives.py

COLOR_BULL = "#059669"  # 看多绿
COLOR_BEAR = "#dc2626"  # 看空红
COLOR_GOLD = "#d97706"  # 高亮金
COLOR_CYAN = "#0891b2"  # 数据青

# 19 个纯渲染函数：
svg_sparkline()       # 迷你折线图
svg_h_bar_compare()   # 水平对比柱
svg_donut()           # 环形图
svg_gauge()           # 半圆仪表盘
svg_radar()           # 五轴雷达图
svg_signal_lights()   # 信号灯
svg_supply_flow()     # 供应链流向
svg_timeline()        # 时间线
svg_bars()            # 柱状图
svg_candlestick()     # K线
svg_pe_band()         # PE带
svg_progress_row()    # 进度条
svg_peer_table()      # 同行表
svg_unlock_timeline() # 解禁时间线
svg_dividend_combo()  # 分红组合
svg_institutional_quarters() # 机构持仓
svg_thermometer()     # 温度计
svg_radar()           # 雷达图
```

**为什么纯 SVG**：HTML 报告是 124KB 单文件，不用任何 JS。SVG 内联在 HTML 里，双击打开即可查看。

### 6.2 评委面板渲染

```python
# lib/report/panel_cards.py

GROUP_LABELS = {
    "A": "价值", "B": "成长", "C": "宏观", "D": "技术",
    "E": "中国", "F": "游资", "G": "量化", "H": "科技", "I": "卡位"
}

def render_jury_seat(inv): """单个评委座位卡（可点击跳转评论）"""
def render_chat_message(inv): """微信气泡式评论 + 展开完整结论"""
def render_vote_bars(vote_dist): """投票分布柱状图"""
def render_top3_bulls(investors): """前3看多"""
def render_top3_bears(investors): """前3看空"""
```

每个评委卡片包含：头像、名字、流派标签、signal dot、评分徽章、一句话评论（persona voice）、完整结论（可展开：命中规则、未命中规则、理想买入价、时间框架、仓位风格、翻盘条件）。

---

## 7. 质量门控与自检

### 7.1 self_review.py（~20 条硬规则）

```python
# lib/self_review.py

@dataclass
class Issue:
    severity: str    # critical / warning / info
    category: str    # industry / data / valuation / panel / consistency
    dim: str         # 关联维度
    issue: str       # 问题描述
    evidence: str    # 触发值
    suggested_fix: str

# 检查函数列表：
check_industry_mapping_sanity()  # BUG#R10: 行业被误映射
check_all_dims_exist()           # 应跑维度必须存在 (profile-aware)
check_empty_dims()               # 有key但data空的维度
check_valuation_sanity()         # PE/PB 合理性
check_panel_consistency()        # 评委评分一致性
check_hk_specific()              # 港股特有检查
# ... 共 ~20 条
```

**HARD-GATE 机制**：`stage2` 检查 `_review_issues.json`，critical != 0 时**拒绝生成 HTML**。

### 7.2 data-contracts.md（JSON Schema 契约）

定义 5 个 Task 间传递数据的 JSON Schema：
- DCF 输出格式
- IC Memo 格式
- Porter 五力输出格式
- 评委 Panel 格式
- Synthesis 格式

约束 LLM 产出结构，不是自由文本。

---

## 8. 工程治理

### 8.1 BUGS-LOG Top 教训

| # | 教训 | 来源 |
|---|------|------|
| 1 | **优雅降级是毒药** | v3.8.1: `.get(g, 1.0)` 让 6 个缺陷潜行两版本 |
| 2 | **加评委要改 6 处配套层** | v3.8.1: investor_db → criteria → avatars → MARKET_SCOPE → PERSONAS → STYLE_GROUP_WEIGHTS |
| 3 | **akshare 翻页死结** | #68: cninfo 公告 854 页拖几小时 |
| 4 | **AI 关键词误匹配** | v3.6.3: 裸 `ar`/`vr` 匹配到 market/margin |
| 5 | **NOK ADR 被当 A 股** | v3.7.2: 顶层 market 字段丢失 |
| 6 | **mini_racer 非线程安全** | V8 isolate 需要锁 |
| 7 | **profile-aware 检查** | lite 模式只跑 7 维，不能报 critical missing |
| 8 | **consensus 极化** | rule-engine 天生居中，需 polarize 拉开 |
| 9 | **stage1 重复 collect** | Phase 6c: 解耦省 5-10min/股 |
| 10 | **资料可得性影响深度** | A/B/C 分级 |

### 8.2 版本管理

`.version-bump.json` 集中管理版本号，commit msg 里 `#patch`/`#minor`/`#major` 触发自动 bump。

---

## 9. 可直接复用的代码模式

| 模式 | 文件路径 | 行号 | 用途 |
|------|---------|------|------|
| wave-based 并发 + 锁 | `lib/pipeline/collect.py` | L60-120 | HermesAlpha 数据采集并发编排 |
| 特征提取层 | `lib/stock_features.py` | L100-200 | 评委/策略只读 features 不碰 raw |
| _make_adapter 工厂 | `lib/pipeline/fetchers/registry.py` | L25-55 | 统一 fetcher 注册 |
| consensus 混合公式 | `lib/pipeline/score_fns.py` | L380-420 | 评委聚合 |
| self_review Issue | `lib/self_review.py` | L25-40 | 质量门控 |
| compute_dcf + methodology_log | `lib/fin_models.py` | L80-160 | DCF 可追溯 |
| SVG 原语 | `lib/report/svg_primitives.py` | 全文件 | 无 JS 纯 SVG 图表 |
| polarize 拉伸 | `lib/pipeline/score_fns.py` | L410 | 分数极化 |
| _f() 安全 float | `lib/pipeline/score_fns.py` | L30 | 百分号/逗号/中文货币解析 |
| BUGS-LOG 8字段格式 | `docs/BUGS-LOG.md` | 全文件 | 防再犯日志 |
