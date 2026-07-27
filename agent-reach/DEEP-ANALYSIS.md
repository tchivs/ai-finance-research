# Agent-Reach 终极深度逆向分析

> 15 平台渠道 · Channel 抽象 · Doctor 诊断 · Glue Layer 哲学
> 源码: `/root/source/tmp/Agent-Reach/`
> 原始仓库: <https://github.com/Panniantong/Agent-Reach>
> 版本: v1.5.0 · 8396 行 Python · MIT

---

## 1. 设计哲学：Glue Layer（胶水层）

### 1.1 核心定位

```
┌──────────────────────────────────────────────────┐
│  AI Agent (Claude / Codex / Cursor / Hermes...)  │
└──────────────┬───────────────────────────────────┘
               │  agent-reach doctor (健康检查)
               │  agent-reach install (一键安装)
               │  agent-reach configure (配置 Cookie/Token)
               │
┌──────────────▼───────────────────────────────────┐
│            Agent Reach (胶水层)                    │
│  "安装器 + 诊断器 + 配置器"                        │
│  NOT a wrapper — 安装完就不管了                    │
└──────────────┬───────────────────────────────────┘
               │  Agent 直接调用上游工具
               │
    ┌──────────┼──────┬──────┬──────┬──────┐
    ▼          ▼      ▼      ▼      ▼      ▼
twitter-cli  yt-dlp  gh    mcporter  rdt   OpenCLI ...
```

**关键原则**：
- **NEVER modify upstream** — 永远不修改上游开源项目的源码
- **Only route and call** — 只路由和调用，不重新实现
- **安装后不管** — Agent 直接调上游工具 CLI，Agent Reach 不在运行路径上

**为什么这么设计**：如果 Agent Reach 是 wrapper，每次上游 API 变了都要更新 wrapper。作为 glue layer，它只在安装/诊断/配置环节参与，运行时零开销。

---

## 2. Channel 抽象基类

### 2.1 BaseChannel 契约

```python
# channels/base.py

class Channel(ABC):
    name: str = ""              # "youtube", "twitter"
    description: str = ""        # "YouTube 视频和字幕"
    backends: List[str] = []    # 有序候选后端
    tier: int = 0               # 0=零配置, 1=需免费Key, 2=需复杂设置
    active_backend: Optional[str] = None  # check() 设定

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """URL 是否属于此平台"""
        ...

    def ordered_backends(self, config=None) -> List[str]:
        """候选后端按优先级排序，支持用户 override"""
        candidates = list(self.backends)
        override = config.get(f"{self.name}_backend")
        if override:
            # 把 override 的后端移到列表首位
            for i, b in enumerate(candidates):
                if b == override or b.startswith(override):
                    candidates.insert(0, candidates.pop(i))
                    break
        return candidates

    def check(self, config=None) -> Tuple[str, str]:
        """检查上游工具是否可用 → (status, message)
        status: 'ok' / 'warn' / 'off' / 'error'
        """
        self.active_backend = self.backends[0] if self.backends else "内置"
        return "ok", f"{'、'.join(self.backends)}"
```

### 2.2 Tier 分级（安装难度）

| Tier | 含义 | 示例 |
|------|------|------|
| 0 | 零配置，装好即用 | GitHub (gh CLI)、Web (curl)、RSS |
| 1 | 需要免费 Key / 登录 | Twitter (auth_token)、Reddit (API key)、YouTube (API key) |
| 2 | 需要复杂设置 | Facebook、Instagram（需浏览器 Cookie + 反爬） |

### 2.3 15 个渠道完整列表

| 渠道 | 文件 | Tier | 后端候选 | 说明 |
|------|------|------|---------|------|
| GitHub | `github.py` | 0 | gh CLI | 代码仓库/Issue |
| YouTube | `youtube.py` | 0 | yt-dlp | 视频/字幕 |
| Twitter/X | `twitter.py` | 1 | twitter-cli → OpenCLI → bird | 推文/搜索/长文 |
| Reddit | `reddit.py` | 1 | rdt-cli | 帖子/评论 |
| Bilibili | `bilibili.py` | 1 | yt-dlp | B站视频 |
| 小红书 | `xiaohongshu.py` | 1 | 内置 xhs-sdk | 笔记/搜索 |
| 小宇宙 | `xiaoyuzhou.py` | 1 | podcast-cli | 播客/音频 |
| V2EX | `v2ex.py` | 0 | v2ex-cli | 社区帖子 |
| 雪球 | `xueqiu.py` | 1 | 内置 scraper | 股票/投资 |
| LinkedIn | `linkedin.py` | 2 | OpenCLI | 职场社交 |
| Facebook | `facebook.py` | 2 | OpenCLI | 社交网络 |
| Instagram | `instagram.py` | 2 | OpenCLI | 图片社交 |
| RSS | `rss.py` | 0 | 内置 feedparser | RSS/Atom |
| Exa Search | `exa_search.py` | 1 | exa API | AI 搜索 |
| Web | `web.py` | 0 | curl/readability | 通用网页 |

---

## 3. Probe 系统（真实健康探测）

### 3.1 问题背景

`shutil.which()` 只检查文件是否存在，但：
- pipx/uv 装的工具在系统 Python 升级后，shebang 指向已删除的解释器
- `which()` 找到了文件，但执行时 `FileNotFoundError`
- 这让 doctor 报告"已安装"，实际不可用

### 3.2 ProbeResult 四态分类

```python
# probe.py

@dataclass
class ProbeResult:
    status: str  # "ok" | "missing" | "broken" | "timeout" | "error"
    output: str = ""
    hint: str = ""

def probe_command(cmd, args=("--version",), timeout=10, retries=0, package=None):
    """真实执行 cmd，区分三种失败模式"""
    path = shutil.which(cmd)
    if not path:
        return ProbeResult("missing")        # 不在 PATH

    try:
        r = subprocess.run([path, *args], timeout=timeout, ...)
    except FileNotFoundError:
        return ProbeResult("broken",         # which 找到但 exec 失败
            hint="命令存在但无法执行——venv 解释器丢失。重装：uv tool install --force")
    except subprocess.TimeoutExpired:
        return ProbeResult("timeout")

    if r.returncode in (126, 127):
        return ProbeResult("broken", ...)    # exit 126/127 = found but not executable

    return ProbeResult("ok", output=r.stdout + r.stderr)
```

**为什么这么设计**：doctor 报告的每个"✅"都基于**真实执行**，不是文件存在性检查。broken 状态会直接给出重装命令。

---

## 4. Doctor 诊断系统

### 4.1 设计原则

```python
# doctor.py

def check_all(config) -> Dict[str, dict]:
    """遍历所有 channel，收集健康状态"""
    results = {}
    for ch in get_all_channels():
        try:
            status, message = ch.check(config)  # 每个 channel 自己知道怎么检查
            active = ch.active_backend
        except Exception as e:
            # 关键：单个 channel 崩溃不能拖垮整个报告
            status, message, active = "error", f"体检异常：{e}", None
        results[ch.name] = {status, message, tier, backends, active_backend}
    return results
```

### 4.2 分层渲染

```
Agent Reach 状态
========================================
图例：✅ 可用  [!] 已装但需配置/登录  [X] 未安装

✅ 装好即用：
  ✅ GitHub — gh CLI 可用
  ✅ YouTube — yt-dlp 可用
  ✅ RSS — 内置 feedparser
  [X] V2EX — v2ex-cli 未安装

可选渠道（已安装）：
  ✅ Twitter/X 推文 — twitter-cli 完整可用
  [!] Reddit — rdt-cli 已安装但未配置 API key

状态：8/15 个渠道可用
还有 5 个可选渠道可以解锁（Facebook、Instagram、...），
告诉你的 Agent「帮我装 XXX」即可

[!] 安全提示：config.yaml 权限过宽（其他用户可读）
   修复：chmod 600 ~/.agent-reach/config.yaml
```

**设计亮点**：
- Tier 0（零配置）优先展示 → 用户立刻看到什么能用
- 未安装的 Tier 1/2 汇总一行 → 不刷屏
- 安全提示：config.yaml 含 Cookie/Token，权限不能过宽

---

## 5. Cookie 自动提取

### 5.1 多平台 Cookie 批量提取

```python
# cookie_extract.py

PLATFORM_SPECS = [
    {"name": "Twitter/X",    "domains": [".x.com", ".twitter.com"],
     "cookies": ["auth_token", "ct0"], "config_key": "twitter"},
    {"name": "XiaoHongShu",  "domains": [".xiaohongshu.com"],
     "cookies": None, "config_key": "xhs"},  # None = 全部 cookie
    {"name": "Bilibili",     "domains": [".bilibili.com"],
     "cookies": ["SESSDATA", "bili_jct"]},
    {"name": "Xueqiu",       "domains": [".xueqiu.com"],
     "cookies": None},
]

def extract_all(browser="chrome") -> Dict[str, dict]:
    """一次提取所有平台 Cookie"""
    # 优先用 rookiepy (Rust, 更稳定)
    # fallback browser_cookie3
```

### 5.2 两套后端

| 后端 | 语言 | 稳定性 | 安装 |
|------|------|--------|------|
| rookiepy | Rust | 高（推荐） | `pip install rookiepy` |
| browser_cookie3 | Python | 中（Chrome 更新易破） | `pip install browser-cookie3` |

---

## 6. Twitter 多后端探测（最复杂的 Channel）

Twitter 是多后端设计的典范：

```python
class TwitterChannel(Channel):
    backends = ["twitter-cli", "OpenCLI", "bird CLI (legacy)"]

    def check(self, config):
        """两段式探测：先收集全部候选，再按优先级选"""

        findings = []
        for backend in self.ordered_backends(config):
            if backend == "twitter-cli":
                result = self._check_twitter_cli()
            elif backend == "OpenCLI":
                result = self._check_opencli()
            elif backend == "bird CLI (legacy)":
                result = self._check_bird()
            if result is not None:  # None = 未安装，不参与候选
                findings.append((backend, *result))

        # 先找 ok，没有 ok 才找 warn
        for wanted in ("ok", "warn"):
            for backend, status, message in findings:
                if status == wanted:
                    self.active_backend = backend
                    return status, message
```

**为什么两段式**：如果 twitter-cli "装了但未登录"（warn），OpenCLI "完整可用"（ok），按简单顺序会停在 twitter-cli 的 warn 上，挡住 OpenCLI。两段式确保优先选 ok 的后端。

---

## 7. MCP Server

```python
# integrations/mcp_server.py

def create_server():
    server = Server("agent-reach")

    @server.list_tools()
    async def list_tools():
        return [Tool(name="get_status",
            description="Get Agent Reach status: which channels are available")]

    @server.call_tool()
    async def call_tool(name, arguments):
        if name == "get_status":
            result = eyes.doctor_report()
        return [TextContent(type="text", text=str(result))]
```

MCP 只暴露一个工具 `get_status`——因为 Agent Reach 的定位是安装器/诊断器，不是运行时 wrapper。Agent 调 `get_status` 看哪些渠道可用，然后直接调上游工具。

---

## 8. CLI 命令体系（1834行）

| 命令 | 功能 |
|------|------|
| `agent-reach setup` | 交互式配置向导 |
| `agent-reach install --env=auto` | 一键自动安装 |
| `agent-reach install --channels twitter,reddit` | 安装指定渠道 |
| `agent-reach install --safe` | 安全模式（不改系统） |
| `agent-reach install --dry-run` | 预览不执行 |
| `agent-reach configure twitter-cookies "auth_token=xxx; ct0=yyy"` | 手动配置 |
| `agent-reach configure --from-browser chrome` | 从浏览器自动提取 Cookie |
| `agent-reach doctor` | 健康检查（文本报告） |
| `agent-reach doctor --json` | JSON 格式（给程序读） |
| `agent-reach uninstall` | 完全卸载 |
| `agent-reach skill --install` | 安装 SKILL.md 到 Agent 技能目录 |
| `agent-reach transcribe <url>` | 音频/视频转文字 (Groq/OpenAI Whisper) |
| `agent-reach format xhs` | 格式化小红书输出 |
| `agent-reach watch` | 定时健康检查 + 更新检查 |
| `agent-reach check-update` | 检查新版本 |

---

## 9. 对当前项目的借鉴建议

### HermesAlpha

| 借鉴点 | 来源 | 实施 |
|--------|------|------|
| Doctor 诊断模式 | doctor.py | 数据源/Provider 健康检查（不止 `which()`，真实探测） |
| 雪球 Channel | xueqiu.py | 雪球数据抓取（319行，含 Cookie 管理） |
| 小红书 Channel | xiaohongshu.py | 情绪数据采集（258行） |

### ashare-audit

| 借鉴点 | 来源 | 实施 |
|--------|------|------|
| 单 channel 崩溃不拖垮全局 | doctor.py | `try/except` 包裹每个检查项 |
| Probe broken 状态 | probe.py | 检测 stale venv / 已删除解释器 |
| Channel 契约测试 | test_channel_contracts.py | 每个 Channel 必须实现 can_handle + check |
