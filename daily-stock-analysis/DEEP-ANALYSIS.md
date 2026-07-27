# daily_stock_analysis 终极深度逆向分析

> 17 数据源联邦 · Web+Desktop+Bot 三端 · 10 CI workflow · 最详细 AGENTS.md
> 源码: `/root/source/tmp/daily_stock_analysis/`
> 原始仓库: <https://github.com/ZhuLinsen/daily_stock_analysis>

---

## 1. 多源数据联邦 + Fallback 体系

### 1.1 17 个数据源 Provider

| Provider | 大小(行) | 市场 | 主要数据 | 优先级 |
|---------|---------|------|---------|--------|
| `akshare_fetcher` | 2330 | A股/港股 | 全面(行情/财报/资金流/龙虎榜) | 1 (首选) |
| `tushare_fetcher` | 1326 | A股 | 全面(pro版) | 2 |
| `yfinance_fetcher` | 943 | 全球 | 行情/基本面 | 3 |
| `efinance_fetcher` | 1296 | A股 | 行情/财报 | 备选 |
| `baostock_fetcher` | 395 | A股 | 历史数据 | 备选 |
| `longbridge_fetcher` | 928 | 港股/美股 | 行情/基本面 | 港美优先 |
| `pytdx_fetcher` | 517 | A股 | 实时行情(通达信协议) | 低延迟 |
| `tickflow_fetcher` | 1130 | A股 | Tick数据 | 高频 |
| `tencent_fetcher` | 204 | A股/港股 | 实时行情 | 备选 |
| `finnhub_fetcher` | 169 | 美股 | 行情/新闻 | 美股备选 |
| `alphavantage_fetcher` | 181 | 全球 | 行情/基本面 | 国际备选 |
| `tw_institutional_fetcher` | 337 | 台湾 | 机构持仓 | 台湾专用 |
| `fundamental_adapter` | 532 | A股 | 财报适配 | akshare补充 |
| `yfinance_fundamental_adapter` | 368 | 全球 | 财报适配 | yfinance补充 |

### 1.2 策略模式 + 自动 Fallback

```python
# data_provider/base.py

class BaseFetcher(ABC):
    """抽象基类，定义统一接口"""

    name: str = "BaseFetcher"
    priority: int = 99  # 数字越小越优先

    @abstractmethod
    def _fetch_raw_data(self, stock_code, start_date, end_date) -> pd.DataFrame:
        """子类实现：从具体数据源获取原始数据"""

    @abstractmethod
    def _normalize_data(self, df, stock_code) -> pd.DataFrame:
        """子类实现：标准化列名为 STANDARD_COLUMNS"""

    # 通用技术指标计算在基类中实现
    def get_main_indices(self, region="cn"): ...
    def get_market_stats(self): ...
```

**标准化列名**：所有 provider 统一输出 `['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']`。

### 1.3 DataFetcherManager（策略管理器）

```python
# 核心逻辑（伪代码）
class DataFetcherManager:
    def __init__(self):
        self.fetchers = sorted_by_priority([
            AkshareFetcher(priority=1),
            TushareFetcher(priority=2),
            YfinanceFetcher(priority=3),
            # ...
        ])

    def get_stock_data(self, code, start, end):
        for fetcher in self.fetchers:
            try:
                df = fetcher.fetch(code, start, end)
                if df is not None and not df.empty:
                    return df  # 第一个成功的就用
            except RateLimitError:
                continue  # 限速，换下一个
            except DataSourceUnavailableError:
                continue  # 不可用，换下一个
        raise DataFetchError("所有数据源都失败了")
```

**防封禁策略**：
1. 每个 Fetcher 内置流控逻辑
2. 失败自动切换到下一个数据源
3. 指数退避重试机制

### 1.4 股票代码标准化

```python
def normalize_stock_code(stock_code: str) -> str:
    """支持各种格式 → 统一格式"""
    # 'SH600519' → '600519'
    # '000001.SZ' → '000001'
    # 'HK00700' → 'HK00700' (保留HK前缀)
    # '1810.HK' → 'HK01810' (规范为HK+5位)
    # 'AAPL' → 'AAPL' (美股原样保留)
    # '7203.T' → '7203.T' (日本Yahoo格式保留)
```

**市场判定**：`_market_tag(code)` 返回 `cn/us/hk/jp/kr/tw`。

**特殊判定**：
- BSE（北交所）：`92xxxx / 43xxxx / 83xxxx / 87xxxx / 88xxxx`（排除 `900xxx` 沪B）
- 科创板/创业板：`688xxx / 30xxxx`（涨跌停 ±20%）
- ST 股：名称含 `ST`（涨跌停 ±5%）

---

## 2. 核心流程编排（pipeline.py）

### 2.1 数据流

```
用户输入 (stock_codes / market_review / schedule)
    │
    ▼
pipeline.py (3657行) ── 核心编排器
    ├── ThreadPoolExecutor 并发获取多只股票数据
    ├── 每只股票:
    │   ├── DataFetcherManager.get_stock_data() → OHLCV
    │   ├── 技术指标计算 (MA/MACD/RSI/KDJ/BOLL)
    │   ├── 筹码分布 (ChipDistribution)
    │   ├── 市场环境上下文 (DailyMarketContext)
    │   ├── 社交情绪 (SocialSentimentService)
    │   ├── 情报服务 (IntelligenceService)
    │   ├── AnalysisContextBuilder → 组装 LLM 上下文
    │   └── GeminiAnalyzer → LLM 分析 → AnalysisResult
    │
    ├── 决策信号提取 (decision_signal_extractor)
    ├── 报告生成 (report_language → normalize/localize)
    ├── 通知推送 (NotificationService → 多渠道)
    └── 诊断记录 (run_diagnostics)
```

### 2.2 关键设计

**AnalysisContextBuilder**：将技术指标、基本面、市场环境、情绪数据组装成结构化的 LLM 上下文包（context pack），控制 prompt 长度和信息密度。

**决策护栏**：
- `phase_decision_guardrail`：阶段性决策护栏（防止在不确定阶段给出确定性建议）
- `daily_market_context_guardrail`：每日市场环境护栏（极端行情时调整建议语气）

---

## 3. Bot 命令体系

### 3.1 命令分发器（dispatcher.py）

```python
class CommandDispatcher:
    """命令分发 + 自然语言路由 + 频率限制"""

    def __init__(self):
        self._commands: Dict[str, BotCommand] = {}
        self._rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

    def dispatch(self, message: BotMessage) -> BotResponse:
        # 1. 解析命令前缀 (/analyze, /ask, ...)
        # 2. 频率限制检查
        if not self._rate_limiter.is_allowed(message.user_id):
            return BotResponse("请求太频繁，请稍后再试")
        # 3. 匹配命令
        cmd = self.get_command(name)
        if cmd:
            return cmd.execute(message, args)
        # 4. 未匹配 → 尝试自然语言路由
        nl_result = self._try_nl_routing(message)
        if nl_result:
            return nl_result
        # 5. 仍未匹配 → 默认回复
        return BotResponse("未知命令")
```

### 3.2 RateLimiter（滑动窗口）

```python
class RateLimiter:
    """滑动窗口频率限制"""
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        # 清理过期请求
        self._requests[user_id] = [
            t for t in self._requests[user_id]
            if now - t < self.window_seconds
        ]
        if len(self._requests[user_id]) >= self.max_requests:
            return False
        self._requests[user_id].append(now)
        return True
```

### 3.3 自然语言路由（两层）

```python
async def _try_nl_routing(self, message) -> Optional[BotResponse]:
    """非命令消息 → LLM 意图解析 → 路由到命令"""

    # 激活条件（全部满足才走）：
    # 1. config.agent_nl_routing == True
    # 2. 私聊 或 被@提及
    # 3. config.agent_mode == True

    # Layer 1: 廉价正则预过滤（跳过明显无关的消息）
    if not self._passes_nl_prefilter(text):
        return None

    # Layer 2: LLM 意图解析
    parsed = await self._parse_intent_via_llm(text, config)
    # → {"intent": "analysis", "codes": ["600519"], "strategy": "趋势"}

    if intent == "chat":
        return await chat_cmd.execute_async(message, [text])
    if intent == "analysis" and codes:
        return await ask_cmd.execute_async(message, [code_str, strategy])
```

**LLM 意图解析**：
```python
async def _parse_intent_via_llm(text, config) -> Optional[dict]:
    messages = [
        {"role": "system", "content": _NL_PARSE_PROMPT},
        {"role": "user", "content": text},
    ]
    resp = adapter.call_text(messages, temperature=0, max_tokens=200, timeout=10)
    return _parse_intent_payload(resp.content)
    # → {"intent": "analysis", "codes": ["600519"], "strategy": "趋势"}
```

### 3.4 命令清单

| 命令 | 文件大小 | 功能 |
|------|---------|------|
| `/analyze` | 3.6KB | 分析单只股票 |
| `/ask` | **27KB** | 问答（最复杂，支持多股/策略/上下文） |
| `/batch` | 3.6KB | 批量分析 |
| `/chat` | 3.6KB | 自由对话 |
| `/help` | 3.8KB | 帮助 |
| `/history` | 5.9KB | 历史记录 |
| `/market` | 5.2KB | 市场概览 |
| `/research` | 5.4KB | 深度研究 |
| `/status` | 8.1KB | 系统状态 |
| `/strategies` | 3.8KB | 策略管理 |

### 3.5 多平台适配

```
bot/platforms/
├── base.py            — 抽象基类（send/receive/format/parse）
├── dingtalk.py        — 钉钉 Webhook (9.7KB)
├── dingtalk_stream.py — 钉钉 Stream 模式 (11.5KB)
├── discord.py         — Discord (12.6KB)
└── feishu_stream.py   — 飞书 Stream (24.1KB，最大)
```

每个平台实现统一的 `base.py` 接口，上层 dispatcher 不需要知道是哪个平台。

---

## 4. CI/CD 生态

### 4.1 10 个 GitHub Actions Workflow

| Workflow | 触发 | 功能 | 阻断? |
|---------|------|------|-------|
| `ci.yml` | PR → main | 4阶段门控 | ✅ |
| `00-daily-analysis.yml` | cron | 每日自动分析+推送 | — |
| `auto-tag.yml` | commit msg 含 #patch/#minor/#major | 自动版本号 | — |
| `create-release.yml` | tag push | 创建 GitHub Release | — |
| `desktop-release.yml` | tag push | Electron 打包发布 | — |
| `docker-publish.yml` | tag push | Docker Hub 发布 | — |
| `ghcr-dockerhub.yml` | push main | GHCR + DockerHub 双推 | — |
| `network-smoke.yml` | cron + PR | pytest -m network | ❌ 观测 |
| `pr-review.yml` | PR | AI 审查 + 自动标签 | ❌ 辅助 |
| `stale.yml` | cron | 关闭陈旧 issue | — |

### 4.2 ci_gate.sh 分阶段门控

```bash
#!/bin/bash
# 4阶段门控，可单独执行也可全跑

syntax_check()        # Python py_compile 关键文件
flake8_checks()       # flake8 --select=E9,F63,F7,F82 (只查致命错误)
deterministic_checks() # scripts/test.sh code + yfinance (离线确定性测试)
offline_test_suite()  # pytest -m "not network" (非网络测试)

# 用法：
./scripts/ci_gate.sh all          # 全跑
./scripts/ci_gate.sh syntax      # 只跑语法检查
./scripts/ci_gate.sh offline-tests # 只跑离线测试
```

### 4.3 CI 4 阶段架构

```yaml
# .github/workflows/ci.yml

jobs:
  changes:           # 路径过滤（只检测改了什么）
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}

  ai-governance:     # AGENTS.md 唯一真源校验
    run: python scripts/check_ai_assets.py

  backend-gate:      # 后端门控
    steps:
      - ci_gate.sh syntax      # Python 语法检查
      - ci_gate.sh flake8      # 致命错误检查
      - ci_gate.sh deterministic # 确定性测试
      - ci_gate.sh offline-tests # 离线测试

  docker-build:      # Docker 构建 + 关键模块导入 smoke
    run: docker build + python -c "import main; import src.core.pipeline"

  web-gate:          # 前端门控（仅在 apps/dsa-web/ 改动时触发）
    run: npm ci && npm run lint && npm run build
```

**路径粒度触发**：只有 `apps/dsa-web/` 改动时才跑前端 CI，不浪费资源。

### 4.4 自动版本管理

```yaml
# auto-tag.yml
# commit msg 含 #patch / #minor / #major → 自动 bump 版本号 + tag
# opt-in: 不含这些标记的 commit 不触发
```

---

## 5. AGENTS.md 治理（所有项目中最详细的）

### 5.1 AI 协作资产治理

```python
# scripts/check_ai_assets.py 校验：
AGENTS.md            # ← 唯一真源
CLAUDE.md            # ← 必须是 AGENTS.md 的软链接
.github/copilot-instructions.md  # ← Copilot 镜像
.github/instructions/*.md        # ← 分层补充
.claude/skills/                  # ← 协作技能
.claude/reviews/                 # ← 分析产物（不入库）
```

### 5.2 验证矩阵（按改动面执行）

| 改动面 | 适用范围 | 必须执行 |
|--------|---------|---------|
| Python 后端 | main.py, src/, data_provider/, api/, bot/ | `ci_gate.sh` |
| Web 前端 | apps/dsa-web/ | `npm ci && lint && build` |
| 桌面端 | apps/dsa-desktop/ | 先构建 Web 再构建 Desktop |
| API/Schema | api/, src/schemas/, src/services/ | 后端验证 + 客户端构建 |
| 文档/治理 | README, docs/, AGENTS.md | 确认命令/文件名一致 |
| 工作流/脚本 | .github/, scripts/, docker/ | 最接近改动面的验证 |
| 网络/依赖 | timeout/retry/fallback | 离线检查 + 在线验证 |

### 5.3 稳定性护栏（7 条红线）

1. **配置与运行入口**：修改 `.env` 语义要评估 Docker/Actions/API/Web/Desktop 全链路影响
2. **数据源 fallback**：单一数据源失败不应拖垮整个分析流程
3. **API/Web/Desktop 兼容**：默认追加字段不删除，提供兼容层
4. **报告/Prompt/通知**：修改报告结构要检查上下游消费方
5. **工作流/发布/打包**：自动 tag 保持 opt-in（#patch/#minor/#major）
6. **Prompt 修改**：修改 `EXTRACT_PROMPT` 时必须附完整 prompt 到 PR
7. **截图证据**：修改 UI/报告渲染必须附截图

### 5.4 贡献质量底线

```
- 不接受堆叠代码量替代真实设计收敛
- 不接受 AI 生成后未经人工语义审查的代码
- 不接受只在被指出位置追加局部 patch（必须检查所有相关入口）
- 多轮 review 后仍出现同类漂移 → 要求关闭重做
```

---

## 6. 对当前项目的借鉴建议

### HermesAlpha

| 借鉴点 | 来源 | 实施 |
|--------|------|------|
| 17 数据源联邦 | `data_provider/` | 多源 fallback + 自动切换 |
| DataFetcherManager | `base.py` | 策略模式统一接口 |
| AnalysisContextBuilder | `pipeline.py` | 组装结构化 LLM 上下文 |
| decision_guardrail | `pipeline.py` | 阶段性决策护栏 |
| stock_code 标准化 | `normalize_stock_code()` | SH/SZ/HK/US/JP/KR/TW 统一 |

### ashare-audit

| 借鉴点 | 来源 | 实施 |
|--------|------|------|
| ci_gate.sh 4阶段 | `scripts/ci_gate.sh` | syntax → flake8 → deterministic → offline-tests |
| 路径粒度 CI | `ci.yml` | 只在改动面触发对应检查 |
| 验证矩阵 | AGENTS.md | 按改动面执行的检查列表 |
| AI 资产治理 | `check_ai_assets.py` | AGENTS.md 唯一真源 + 软链接校验 |
| 贡献质量底线 | AGENTS.md | 拒绝 AI 生成未审查代码 |
