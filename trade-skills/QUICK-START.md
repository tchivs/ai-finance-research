# trade-skills 快速概览

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

## 一句话定位

`trade-skills` 是一个本地优先的美股交易研究工作台：Claude Code Skill 负责取数和研究编排，TypeScript 内核负责行情、指标、图表和持久化，Web 与 Electron 提供浏览器和桌面两种宿主。它同时是个人研究日志仓库，不是只提供 API 的通用交易服务。

## 当前目录结构

```text
packages/core/          @kansoku/core：业务内核、数据、指标、SQLite、协议
packages/shared/        跨包类型与时间工具
packages/pro-api/       Pro 插槽的公开类型契约
packages/bench/         交易/模型基准数据与运行器
packages/build-overlay/ 构建时 Pro overlay 同步
apps/server/            Hono HTTP/WS 宿主
apps/web/               Vite + React 前端
apps/desktop/           Electron 壳、typed IPC、Agent Kit、CLI
apps/license-worker/    license 相关 worker
apps/site/               发布站点
apps/video/              视频产物
.claude/skills/         研究 Skill 与共享脚本
journal/、stocks/        研究日志、图表快照和个股笔记
```

旧的根目录 `app/` 已迁移为 `apps/` + `packages/`，文档和调用路径应以当前 monorepo 为准。

## 核心数据流

```text
Longbridge CLI / FRED / SEC / GDELT
  -> @kansoku/core（取数、指标、研究契约）
  -> REST + WebSocket（浏览器）或 typed IPC（Electron）
  -> React Cockpit / 首页图表
  -> journal/*.md、journal/charts/data/*.json、SQLite app.db
```

图表类型包括 `flow`、`cohort`、`sepa`、`intraday`。服务端实时流统一走 `/api/ws`，客户端按频道订阅行情、图表、点评、持仓和分析结果。

## Skill 与研究工作流

仓库跟踪的 `.claude/skills/` 当前包含 14 个内置入口：`capital-rotation`、`chart`、`fred`、`gdelt`、`hithink-a-share`、`intraday-signal`、`korea-market`、`market-session-tracker`、`release`、`sec-edgar`、`stock-deep-dive`、`trade-gate`、`trading-discipline`、`trump-truth-monitor`。`pnpm install` 的 `prepare` 还会按 `skills-lock.json` 恢复外部 Skill 到 `.agents/skills/`，再链接到 `.claude/skills/`；这些是本地集成产物，不属于核心源码模块。Skill 负责工作流和落档，不直接替代 core 的指标计算。

研究结果落在 `journal/` 和 `stocks/{SYMBOL}.md`；图表 JSON 带 `schema_version`，运行流水和 AI 成本进入 SQLite，历史图表仍可由文件重建。

## 最值得借鉴的设计

1. **同一内核、多种宿主**：`createKernel()` 构建 API 内核，server 用 Hono/WS，desktop 用 Electron/IPC。
2. **窄视野高频 + 全视野低频**：服务端 commentator/analyst 负责自动跟踪，CLI Skill 负责完整研究和更新笔记。
3. **open-core 插槽**：公开 `core` 和 `pro-api` 只依赖类型契约，私有 Pro 通过组合点接入，缺失时回落免费模式。
4. **历史快照不可变**：实时数据不直接覆盖历史研判，文件保存图表内容，SQLite 保存运行索引和事件流水。

## 本地开发

```bash
pnpm install
pnpm dev          # 浏览器模式，web + server
pnpm dev:desktop  # Electron 模式
pnpm test
pnpm typecheck
pnpm start        # node 宿主，默认 http://localhost:5199
```

需要本机 Longbridge CLI 和账户数据；AI provider、行情和 license 能力还受环境变量、外部服务和 Pro 包可用性影响。仓库许可证是 AGPL-3.0 + Commons Clause，属于 source-available 组合，不应简单标成标准 OSI 开源项目。

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
