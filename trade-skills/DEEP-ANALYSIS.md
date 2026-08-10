# trade-skills 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Innei/trade-skills.git
> 分析基线：
> - `trade-skills`：commit `3134acf707c6556dd9c213b2eb96cc55abcb924c`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/trade-skills`
<!-- source-sync:end -->

<!-- source-sync:changes:start -->
## 本次源码同步复核

> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。

### `trade-skills`：`d6d525074881` → `3134acf707c6`

提交摘要：
- 3134acf7 release(desktop): v0.33.1 (#122)
- cbec8a4a feat(telemetry): report anonymous screen views to VibeLoft from the desktop app
- fd56ef3a chore: remove dead code and unused dependencies (knip-assisted sweep)
- 47b1adbe refactor(build-overlay): project unsuffixed overlay sources to .pro destinations
- e6ccf314 release(desktop): v0.33.0 (#120)
- 1ebf4ad3 feat(analytics): report to kansoku-analytics from the app (#119)
- e87f6307 fix(ci): point --prepackaged at the .app, not its parent directory (#118)
- dad2ba3c fix(training): name a question asked at the open 开局, not B-1 (#117)
受影响路径：
- `M .claude/launch.json`
- `M .claude/skills/_shared/client.py`
- `M .claude/skills/capital-rotation/SKILL.md`
- `M .claude/skills/capital-rotation/templates/rotation-snapshot.md`
- `M .claude/skills/chart/SKILL.md`
- `M .claude/skills/fred/SKILL.md`
- `M .claude/skills/fred/aliases.json`
- `M .claude/skills/gdelt/SKILL.md`
- `A .claude/skills/hithink-a-share/SKILL.md`
- `A .claude/skills/hithink-a-share/scripts/_common.py`
- `A .claude/skills/hithink-a-share/scripts/calendar.py`
- `A .claude/skills/hithink-a-share/scripts/financials.py`
- 其余 1878 个变更路径见 `.planning/source-sync.json`。
<!-- source-sync:changes:end -->

## 1. 系统边界与当前 monorepo

项目由“研究仓库”和“本地看盘应用”两部分组成。研究仓库保存 `.claude/skills/`、`journal/`、`stocks/` 和运行产生的图表快照；应用仓库位于同一个 pnpm workspace，业务内核集中在 `packages/core/`，宿主和界面位于 `apps/`。

当前结构已经不是旧版 `app/` 单应用：

```text
packages/core/          @kansoku/core，业务和数据内核
packages/shared/        ChartDoc、时间和跨包类型
packages/pro-api/       Pro 组合的纯类型契约
packages/bench/         基准数据和评测运行器
packages/bench-report-ui 基准报告界面
packages/build-overlay  Pro overlay 构建同步
apps/server/            HTTP/WS 服务器宿主
apps/web/               Vite + React 浏览器界面
apps/desktop/           Electron、IPC、Agent Kit、CLI
apps/license-worker/    license worker
apps/site/、apps/video/  发布站点和视频工具
.claude/skills/         数据源、研究、交易纪律和发布 Skill
```

`packages/core/src/` 继续按能力域拆分为 `marketdata`、`analysis`、`charts`、`realtime`、`cockpit`、`overview`、`research`、`settings`、`credentials`、`license`、`pro` 等模块。这种分层让指标计算和持久化不依赖某一种 UI 或传输方式。

## 2. 服务端启动和请求流

codebase-memory 在当前 commit 识别到以下关键入口：

```text
apps/server/src/main.node.ts
  -> startHost(port, isDevKernel, extraModules)
  -> createKernel(extraModules)
  -> createApplication(RootModule, { globalPrefix: '/api' })
  -> AppModule + AppExceptionFilter
```

`startHost()` 负责宿主层职责：把 kernel 的 fetch 接到 Hono 的 `/api/*`，托管 `/legacy/*` 历史图表，生产环境静态托管 `apps/web/dist`，并在 `/api/ws` 挂载 WebSocket。开发模式由 Vite 提供前端热更新并代理 API；生产模式由 node 宿主在 5199 端口提供已构建前端和 API。

启动前 `initServerHostRuntime()` 加载 dotenv，初始化 credential provider、认证 URL 打开器、watchlist/Longbridge 区域存储、AI 设置、license manager 和定时复验。它还设置 prompt cache 保留策略，因此运行时配置和数据库初始化是 kernel 能够稳定启动的前置契约。

核心数据流是：Longbridge CLI/外部 Skill -> `packages/core` 取数和指标计算 -> ChartDoc/分析结果 -> REST 或 WebSocket -> React。实时行情、图表、点评、分析、持仓和 benchmark 使用单条 `/api/ws` 连接，通过 `sub/unsub` 消息和 `key` 路由多路频道。

## 3. 桌面宿主、IPC 与 Agent Kit

`apps/desktop/src/boot/kernel.ts` 的 `bootKernel()` 是 Electron 模式的组合入口，顺序具有约束：

1. 初始化 server host runtime，并在开发/打包环境选择不同的 AI secret box；
2. `loadPro()` 加载可选 Pro bundle；
3. 创建同一个 server kernel，加载 server Pro modules；
4. 加载 desktop edition composition，失败时记录并进入 free mode；
5. 建立 realtime bridge、激活 Pro composition、注册 credential IPC；
6. 通过 `/api/health` 做 kernel 自检，再启动 Pro 激活状态观察器。

桌面端把 core 能力包装成类型化 IPC，按 `charts`、`chat`、`capabilities`、`credentials`、`license`、`overview`、`research`、`settings`、`symbols` 等域分组。浏览器使用 HTTP/WS，Electron 使用 IPC/realtime bridge，业务层不需要复制一套指标实现。

Agent Kit 负责在用户数据根目录维护 `.claude/skills` 链接和模板化 `AGENTS.md`/`CLAUDE.md`。`ensureBundledSkills()` 会优先保留用户已有的真实 Skill 目录，否则建立指向 bundled skills 的符号链接。CLI 的 `chart create` 读取 JSON 或 stdin，经 core chart service 创建图表并输出带 deep link 的结果；它必须在数据根目录解析后动态导入 core，避免导入时路径环境尚未就绪。

## 4. Skill、图表和研究状态

仓库跟踪的 `.claude/skills/` 当前覆盖 14 个内置入口：

- 数据和资讯：`fred`、`sec-edgar`、`gdelt`、`trump-truth-monitor`、`hithink-a-share`、`korea-market`；
- 交易研究：`intraday-signal`、`capital-rotation`、`market-session-tracker`、`stock-deep-dive`；
- 纪律和交付：`trade-gate`、`trading-discipline`、`chart`、`release`；
- `_shared/` 提供缓存、环境变量、限流和结构化成功/失败输出协议。

安装时 `package.json` 的 `prepare` 会读取 `skills-lock.json`，把外部 Skill 恢复到 `.agents/skills/`，并将它们链接进 `.claude/skills/`。因此工作树安装后可能出现 33 个 Skill 链接，但其中 14 个来自本仓库，其他是锁定的外部研究/工具 Skill，不能当作 `packages/core` 的代码依赖。

Skill 负责调用顺序和落档位置，core 负责业务计算。图表文档写入 `journal/charts/data/YYYY-MM-DD-<slug>.json`，包含 `schema_version`；SQLite `app.db` 保存 `comments`、`ai_usage`、`chart_meta`、`outcomes` 等运行流水和索引；`stocks/{SYMBOL}.md` 是六面研究笔记。实时行情只用于刷新，不覆盖已经写入的研判快照。

图表类型是 `flow`、`cohort`、`sepa`、`intraday`。其中 `sepa` 侧重收盘级趋势模板和入场计划，`intraday` 组合 5m/15m/1h K 线、MACD、均线、形态/背离标注和 Bull/Base/Bear 情景。Cockpit 将预测、环境、新闻、复盘、笔记和 AI 点评组合到单标的页面。

## 5. Pro 插槽、license 与安全边界

公开仓库的免费能力包括图表、行情、journal 和 core。AI commentator、analyst、deep-dive、追问、收盘小结和 scheduler 等能力由独立 `@kansoku/pro` 提供。`packages/pro-api` 只公开接口和类型；各宿主在组合点注册 modules、channels 和 hooks。Pro 不存在或加载失败时，core 通过默认 hook 回落免费模式，而不是让调用方到处判空。

Web 通过 `/api/capabilities` 获取 `{ pro, licensed, license? }`，桌面端有同名 IPC。未安装 Pro 与已安装但未授权是两个状态：前者隐藏 AI 入口，后者显示锁定/订阅状态。license 状态和 AI key 进入本地存储，生产桌面使用 safeStorage 包装密钥；公开代码不包含私有授权判断逻辑。

研究 deep-dive 的写入边界也很明确：代理只能通过固定的 `write_note` 更新 `stocks/{SYMBOL}.md`，bash 工具拒绝重定向和删除/复制类命令，前后检查 Git 状态并报告意外修改。这比让模型直接获得仓库写权限更容易审计。

## 6. 本次远端结构变化

从旧本地基线到 `3134acf707c6`，最重要的变化是应用结构迁移和桌面化：

- 旧 `app/` 被拆为 `apps/` 宿主与 `packages/` 共享内核；
- 新增 Electron desktop、typed IPC、Agent Kit、桌面 CLI、Sparkle 更新和数据根目录管理；
- server 由可复用 kernel + Hono host 组成，浏览器/桌面共享业务模块；
- Pro overlay、`packages/pro-api` 和 license/能力广播成为公开 core 的边界；
- `.claude/skills/` 增加/整理了 `hithink-a-share`、`korea-market`、`trade-gate`、`trading-discipline`、`release` 等工作流，数据源和交易纪律更加独立。

因此旧文档中把源码写成 `app/server`、`app/web`，或把 desktop 描述为未来计划，均已失效。

## 7. 测试、运行和限制

根目录命令：

```bash
pnpm install
pnpm dev
pnpm dev:desktop
pnpm test
pnpm typecheck
pnpm --filter @kansoku/web build
pnpm start
```

测试覆盖 core、server、web、desktop、bench 和构建 overlay；重点包括指标金标、chart CRUD、IPC parity、启动组合顺序、Agent Kit 链接、数据根目录校验和许可证状态。分析本身未执行需要依赖安装、macOS Electron、Longbridge 登录、AI key 或私有 Pro 的完整端到端流程。

主要限制：依赖 Longbridge CLI 和外部数据源；桌面发行版偏向 macOS Apple Silicon；公开仓库的 license 是 AGPL-3.0 + Commons Clause，属于 source-available 组合；AI/Pro 能力不是公开 core 的完整实现。迁移到其他项目时应优先复用“共享内核 + 多宿主 + 结构化落档 + 受限写入”，不要直接复制 provider、券商客户端或授权逻辑。
