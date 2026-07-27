# ai-berkshire 终极深度逆向分析

> 17 个分析技能 · 四大师方法论 · 双平台兼容 (Claude Code + Codex)
> 源码: `/root/source/tmp/ai-berkshire/`
> 原始仓库: <https://github.com/xbtlin/ai-berkshire>

---

## 1. 四大师方法论体系

### 1.1 四视角分工

| 大师 | 视角 | 核心问题 | 语言风格 | 关注维度 |
|------|------|---------|---------|---------|
| 段永平 | 生意本质 | 这门生意变好了还是变差了？ | 口语化、直白、引用"本分" | 商业模式、管理层诚信 |
| 巴菲特 | 护城河/财务质量 | 赚的是真钱还是假钱？ | 引用致股东信、幽默 | ROE、现金流、护城河 |
| 芒格 | 竞争格局 | 竞争格局在怎么变？ | 逆向思维、多元思维模型 | 失败路径、风险 |
| 李录 | 文明级趋势 | 有什么风险信号？ | 文明史观、长期主义 | 文明级范式转移、终局 |

### 1.2 四层深度流程

```
快速过滤（quality-screen 7条去劣）
    ↓ 幸存者
粗筛（industry-funnel 第2层：5条硬指标）
    ↓ ≤10家
精细分析（industry-funnel 第3层：每家300-500字结构化）
    ↓ 终选3家
四大师深度（每家800-1200字，段/巴/芒/李四视角）
```

---

## 2. 17 个分析技能逐一拆解

### 2.1 技能总览

| # | 技能 | 大小 | 阶段 | 核心功能 |
|---|------|------|------|---------|
| 1 | `industry-funnel` | 10KB | 筛选 | 四层漏斗：全市场→30家→10家→3家 |
| 2 | `quality-screen` | 7KB | 筛选 | 7条去劣硬指标 + 3条豁免 |
| 3 | `bottleneck-hunter` | 18KB | 筛选 | 供应链瓶颈套利（第二/三层瓶颈） |
| 4 | `investment-research` | 11KB | 研究 | 四大师综合分析单股 |
| 5 | `investment-team` | 10KB | 研究 | 4角色并行分析 |
| 6 | `investment-checklist` | 10KB | 研究 | 买入前最终检查清单 |
| 7 | `private-company-research` | 45KB | 研究 | 非上市公司深度研究（最大技能） |
| 8 | `industry-research` | 9KB | 行业 | 产业链全景分析 |
| 9 | `earnings-review` | 9KB | 财报 | 单季业绩快速解读 |
| 10 | `earnings-team` | 17KB | 财报 | 四大师+编辑+读者三阶段闭环 |
| 11 | `thesis-tracker` | 8KB | 追踪 | 买入后纪律系统 |
| 12 | `news-pulse` | 12KB | 新闻 | 4Agent并行异动归因 |
| 13 | `portfolio-review` | 7KB | 组合 | 仓位管理与优化 |
| 14 | `management-deep-dive` | 10KB | 管理 | 管理层质量评估 |
| 15 | `deep-company-series` | 9KB | 研究 | 系列深度公司研究 |
| 16 | `dyp-ask` | 8KB | 研究 | 段永平视角问答 |
| 17 | `wechat-article` | 10KB | 发布 | 研究成果→公众号文章 |

### 2.2 industry-funnel（四层漏斗）详解

```
第一层：全市场扫描 → 30-60家
  - 按行业/主题/指数/市场拉取候选
  - A/B/C 入选类别（A=主业纯正，B=部分相关，C=观察）
  - 关键自查：行业占比<30%标"非纯正"，中国/亚洲市场不能漏

第二层：5条硬指标粗筛 → ≤10家
  - PE合理 / ROE>15% / 现金流为正且占净利>70% / 负债率<60% / 护城河≥★★★
  - 保留规则：5条全及格→保留，4条+1接近→标黄，<4条→淘汰

第三层：精细分析 → ≤10家（每家300-500字）
  - 商业模式一句话 / 财务质量 / 护城河深度 / 主要风险 / 估值快评
  - 终选3家按"投资组合互补性"选（非打分排序）：
    高确定低弹性（巴菲特型）+ 中等确定中等弹性（成长型）+ 高弹性高风险（期权型）

第四层：四大师深度（每家800-1200字）
  - 段永平视角：生意本质 + "本分"
  - 巴菲特视角：五类护城河打分（★1-5）
  - 芒格视角：前3失败路径 + 最坏情景估值
  - 李录视角：文明级趋势定位 + 10-20年终局
```

### 2.3 quality-screen（7条去劣）详解

```python
# 7条硬指标
1. 10年平均ROE < 8%           → 排除
2. 5年累计自由现金流为负        → 排除
3. 利息覆盖倍数 < 2倍          → 排除
4. 长期毛利率 < 15%            → 排除
5. 经营现金流/净利润 < 0.7     → 排除
6. 长期净利率 < 5%             → 排除
7. 5年总股本膨胀 > 20%（非并购）→ 排除

# 3条豁免规则
A. 战略投入期豁免（ROE不达标但收入增速>20%）
B. 并购整合期豁免（短期负债率/股本膨胀）
C. 股东回购豁免（股本缩减是好事）
```

**核心原则**：宁可漏网不可误杀。

### 2.4 bottleneck-hunter（供应链瓶颈）详解

**核心理念**：不问"AI推荐什么"，问"哪一环会先不够用？"

```
趋势筛选（4条标准）：
  - 持续性 ≥ 3-5年
  - 物理性（需要实际硬件建设）
  - 规模性（全球Capex > 500亿美元/年）
  - 加速性（需求增速 > 供给扩产速度）

层级穿透：
  第一层（已定价）：GPU、HBM、电力
  第二层（alpha）：光模块、激光器、InP衬底
  第三层（深度alpha）：SOI晶圆、外延设备、IC载板
```

### 2.5 thesis-tracker（投资论文追踪）详解

```python
# 模式A：建立论文
investment_thesis = {
    "买入理由": "...",        # 为什么买
    "估值锚点": {pe_range, safety_margin},
    "关键指标": [...],        # 每季度跟踪什么
    "卖出条件": [             # 买入前就写好！
        "基本面恶化（ROE连续2季<10%）",
        "估值严重透支（PE>历史90%分位）",
        " thesis 被证伪（核心逻辑变化）"
    ]
}

# 模式B：追踪检查（每季度）
for condition in sell_conditions:
    if condition.triggered():
        alert("卖出条件触发！")
    else:
        log("继续持有，thesis 完整")
```

### 2.6 earnings-team（财报精读团队）三阶段

```
阶段一·研究（4大师并行精读）：
  - 段永平：生意变好了还是变差了？
  - 巴菲特：赚的是真钱还是假钱？
  - 芒格：竞争格局在怎么变？
  - 李录：有什么风险信号？

阶段二·合成：
  - Team Lead 综合四视角 → 研究报告初稿

阶段三·发布：
  - 编辑Agent → 改写公众号文章
  - 读者评审Agent → 提修改意见
  - Team Lead → 定稿
```

### 2.7 news-pulse（异动归因）详解

```
4个并行Agent侦察：
  - Agent 1：公司事件（财报/管理层变动/产品发布）
  - Agent 2：监管政策（行业政策/监管行动）
  - Agent 3：行业对手（竞争对手动态）
  - Agent 4：市场情绪（社交媒体/分析师评级）

输出：事件时间线 + 异动主因判断 + 是否触发论文重审
```

---

## 3. tools/ 质量验证工具

### 3.1 financial_rigor.py（零外部依赖）

```python
# tools/financial_rigor.py — 使用 Decimal 精确运算，无浮点误差

_CTX = Context(prec=28, rounding=ROUND_HALF_EVEN)

def verify_market_cap(price, shares, reported_cap, currency):
    """验算 市值 = 股价 × 总股本 vs 报告值"""
    calculated = exact(price) * exact(shares)
    deviation = abs(calculated - reported_cap) / reported_cap * 100
    if deviation > 5%: return FAIL  # 股本/单位/股价问题
    if deviation > 1%: return WARN

def verify_valuation(price, eps, bvps, fcf_per_share, dividend):
    """PE = price/eps, PB = price/bvps, ROE = eps/bvps"""
    # 同时算盈利收益率、P/FCF、FCF Yield、股息率

def cross_validate(field, values, unit):
    """多源交叉验证：同一字段从年报/Yahoo/StockAnalysis取值，检查偏差"""

def benford(values):
    """本福特定律检验：数据是否被人为操纵"""
```

### 3.2 report_audit.py（报告抽检）

```python
# 三步工作流：
# Step 1: extract — 从 Markdown 报告中正则提取所有数字（亿元/x/%/万亿/B/T）
# Step 2: Claude 对抽检清单逐条从可靠信源取数
# Step 3: verdict — 比对，15%偏差以上→打回

_PATTERNS = [
    (r'([\d,，\.]+)\s*%',        '%',    'percent'),
    (r'([\d,，\.]+)\s*亿(元|美元|港元)?', '亿', 'hundred_million'),
    (r'([\d,，\.]+)\s*[xX倍]',   'x',    'multiple'),
    (r'([\d,，\.]+)\s*万亿',      '万亿', 'trillion'),
]
```

### 3.3 其他工具

| 工具 | 大小 | 功能 |
|------|------|------|
| `ashare_data.py` | 11KB | A股数据获取 |
| `momentum_backtest.py` | 16KB | 动量回测 |
| `momentum_backtest_v2.py` | 18KB | 动量回测 v2 |
| `morningstar_fair_value.py` | 6KB | 晨星公允价值 |
| `stock_screener.py` | 14KB | 股票筛选器 |
| `xueqiu_scraper.py` | 17KB | 雪球数据抓取 |

---

## 4. 信息可得性分级（A/B/C 评级）

这是 ai-berkshire 最独特的设计之一——根据资料可得性调整分析深度。

| 等级 | 特征 | 策略 |
|------|------|------|
| **A 级** | 完整财报原文 + 电话会纪要 | 正常执行全部步骤 |
| **B 级** | 部分原文或第三方汇总 | 标注"非原始来源"，降低附注分析权重 |
| **C 级** | 仅新闻摘要/数据网站 | 聚焦核心数据变化，跳过附注挖掘 |

**为什么这么设计**：不同市场（A/H/U）、不同市值公司的信息可得性差异巨大。强行对C级做A级的深度分析只会产出幻觉。

---

## 5. AGENTS.md 治理规则

### 5.1 双平台兼容策略

```
skills/*.md           ← 唯一真源 (canonical)
    ↓ sync-codex-skills.py
codex-skills/*/SKILL.md  ← 自动生成（不手动编辑）
    ↓ sync-codex-prompts.py
codex-prompts/*.md     ← slash-command 兼容层
```

**规则**：修改 `skills/*.md` 后必须运行 `python3 scripts/sync-codex-skills.py`。

### 5.2 研究质量规则

- 财务数据必须来自至少**两个独立来源**
- 使用 `financial_rigor.py` 做精确验算
- 使用 `report_audit.py` 做发布前抽检
- 低置信度结论必须标注

---

## 6. 对当前项目的借鉴建议

### HermesAlpha

| 借鉴点 | 来源技能 | 实施 |
|--------|---------|------|
| 四大师评委 v2 | investment-research | 在现有评分系统上叠加段/巴/芒/李四视角 |
| 信息可得性分级 | 所有技能 | A/B/C 评级影响 LLM 分析深度 |
| report_audit 抽检 | report_audit.py | 报告发布前自动抽检 15% 数据点 |
| Benford 检验 | financial_rigor.py | 检测数据源是否被操纵 |

### ashare-audit

| 借鉴点 | 来源技能 | 实施 |
|--------|---------|------|
| 7条去劣硬指标 | quality-screen | 筛选层第一道门 |
| 四层漏斗 | industry-funnel | 从全市场到 3 家的标准化流程 |
| cross_validate | financial_rigor.py | 多源交叉验证 |
