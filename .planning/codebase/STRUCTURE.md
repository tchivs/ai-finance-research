# Codebase Structure

**Analysis Date:** 2026-07-10

## Directory Layout

```text
aaa/
├── README.md                           # Standard repository entry point
├── 00-INDEX.md                         # Main navigation, reading routes, project catalog
├── 01-知识库使用与维护指南.md            # Documentation hierarchy, terminology, and maintenance
├── 06-工程治理篇.md                     # Engineering governance topic synthesis
├── 07-策略与信号系统篇.md               # Strategy and signal-system topic synthesis
├── 08-数据采集与流水线篇.md             # Data collection and pipeline topic synthesis
├── 09-Agent-协作与设计哲学篇.md         # Agent collaboration and design philosophy
├── 10-SYNTHESIS.md                      # Cross-project pattern synthesis
├── 11-UI-UX交互设计.md                  # UI/UX interaction topic synthesis
├── 12-剩余深度素材.md                   # Report/test/deploy/data-contract material
├── 13-终极提炼.md                       # Bug-driven and final distilled lessons
├── 14-跨项目深层精华.md                 # Deep cross-project comparison
├── 15-数据底座与采集底座篇.md           # Data foundation and local data lake patterns
├── 16-UI-UX设计借鉴总表.md              # UI/UX task matrix
├── 17-落地路线图.md                     # HermesAlpha and ashare-audit execution roadmap
├── 18-模式决策矩阵.md                   # Architecture and pattern decision matrix
├── 19-首批源码落地验证.md                # Commit-pinned source verification and implementation boundaries
├── 20-开发实施TODO.md                    # Actionable implementation checklist and phase gates
├── a-share-watch-butler/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── a-stock-data/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── agent-reach/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── agentic-china-data-tooling/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── ai-berkshire/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── ai-hedge-fund/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── alpha-evolution-lab/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── alphaagent/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── awesome-finance-skills/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── daily-stock-analysis/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── daily-stock-data/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── deepear/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── deepfund/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── financial-timeseries-foundation/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── hhxg-market/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── jcp/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── joinquant-skill/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── magpie/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── openashare/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── panwatch/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── privora-python-examples/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── qlib/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── quantaalpha/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── quant-autoresearch/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── quant-buddy-skill/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── quantdinger/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── pyportfolioopt/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── rd-agent/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── snowball-cli/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── tdx-market-data-clients/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── tickflow-stock-panel/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── trade-skills/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── tradingagents-family/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── uzi-skill/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── vibe-research/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── vibe-trading/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── vnpy/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── wudao-mcp/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
├── x2t/
│   ├── QUICK-START.md
│   └── DEEP-ANALYSIS.md
└── .planning/
    └── codebase/
        ├── ARCHITECTURE.md             # Generated GSD architecture map
        ├── STRUCTURE.md                # Generated GSD structure map
        ├── STACK.md                    # Documentation stack and tooling map
        ├── INTEGRATIONS.md             # External projects, APIs, and auth references
        ├── CONVENTIONS.md              # Documentation conventions
        ├── TESTING.md                  # Documentation validation status
        └── CONCERNS.md                 # Risks, debt, and validation gaps
```

## Directory Purposes

**Repository Root:**
- Purpose: Store top-level navigation, synthesis, topic, roadmap, and decision documents.
- Contains: `README.md`, `00-INDEX.md`, `01-知识库使用与维护指南.md`, numbered topic docs `06-工程治理篇.md` through `16-UI-UX设计借鉴总表.md`, decision docs `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`, source verification in `19-首批源码落地验证.md`, and implementation tracking in `20-开发实施TODO.md`.
- Key files: `README.md`, `00-INDEX.md`, `01-知识库使用与维护指南.md`, `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`, `19-首批源码落地验证.md`, `20-开发实施TODO.md`.

**Project Dossier Directories:**
- Purpose: Store one external project's quick orientation and deep architecture analysis.
- Contains: `QUICK-START.md` and `DEEP-ANALYSIS.md` in each project slug directory.
- Key files: `jcp/QUICK-START.md`, `jcp/DEEP-ANALYSIS.md`, `quantdinger/QUICK-START.md`, `quantdinger/DEEP-ANALYSIS.md`, `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`, `tickflow-stock-panel/QUICK-START.md`, `tickflow-stock-panel/DEEP-ANALYSIS.md`.

**`.planning/`:**
- Purpose: Store GSD-generated planning support artifacts.
- Contains: `.planning/codebase/`.
- Key files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/STACK.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/CONCERNS.md`.

**`.planning/codebase/`:**
- Purpose: Store codebase maps consumed by GSD planning and execution commands.
- Contains: Generated Markdown architecture, structure, stack, integration, convention, testing, and concern maps.
- Key files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/STACK.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/CONCERNS.md`.

## Key File Locations

**Entry Points:**
- `README.md`: Start here when opening the repository through a standard Markdown viewer.
- `00-INDEX.md`: Start here for repository structure, goal-based reading routes, project catalog, topic index, and cross-project summary links.
- `01-知识库使用与维护指南.md`: Start here when adding, refreshing, validating, or publishing documentation.
- `10-SYNTHESIS.md`: Start here for the highest-level design-pattern synthesis across 40 projects.
- `17-落地路线图.md`: Start here for staged execution guidance for HermesAlpha and ashare-audit.
- `18-模式决策矩阵.md`: Start here when choosing among architecture patterns.
- `19-首批源码落地验证.md`: Start here before implementing patterns derived from daily_stock_data, tickflow-stock-panel, or QuantDinger.
- `20-开发实施TODO.md`: Start here to select the next implementation task and verify phase gates.

**Configuration:**
- Not detected. No `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `tsconfig.json`, or application config files are present under `/root/source/docs/aaa`.
- Project-local AI skill directories are not detected at `.claude/skills/` or `.agents/skills/`.

**Core Logic:**
- `06-工程治理篇.md`: Engineering governance and quality gate patterns.
- `07-策略与信号系统篇.md`: Strategy, signals, formulas, backtests, and suggestion pools.
- `08-数据采集与流水线篇.md`: Fetcher registry, fallback, probe, capability, and incremental pipeline patterns.
- `09-Agent-协作与设计哲学篇.md`: Agent team, MCP, skill, Moderator, and Agent Gateway patterns.
- `11-UI-UX交互设计.md`: UI/UX report, dashboard, SSE, and state handling patterns.
- `12-剩余深度素材.md`: Report assembly, data contracts, quality checklists, tests, CI/CD, and deployment patterns.
- `13-终极提炼.md`: BUGS-LOG, release notes, feature extraction, financial models, and methodology logs.
- `14-跨项目深层精华.md`: Cross-project deep comparison and representative positioning.
- `15-数据底座与采集底座篇.md`: Data foundation, CSV/PostgreSQL, Parquet/DuckDB/Polars, wrappers, repair windows, snapshots, and schema docs.
- `16-UI-UX设计借鉴总表.md`: UI/UX patterns organized by user task.

**Project Dossiers:**
- `jcp/QUICK-START.md`, `jcp/DEEP-ANALYSIS.md`: Wails desktop stock research, Moderator meetings, stock memory, OpenClaw HTTP path.
- `quantdinger/QUICK-START.md`, `quantdinger/DEEP-ANALYSIS.md`: AI Trading OS, Agent Gateway, scope/audit/idempotency, jobs, paper-only trading gate.
- `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`: A-share data collection foundation, shell wrappers, CSV/PostgreSQL modes, schema docs.
- `tickflow-stock-panel/QUICK-START.md`, `tickflow-stock-panel/DEEP-ANALYSIS.md`: Local data lake, workbench, CapabilitySet, StrategyDef, SSE and monitoring patterns.
- `uzi-skill/QUICK-START.md`, `uzi-skill/DEEP-ANALYSIS.md`: Pipeline analysis, judges, report rendering, quality gates, BUGS-LOG patterns.
- `agent-reach/QUICK-START.md`, `agent-reach/DEEP-ANALYSIS.md`: Glue layer, channel abstraction, probes, doctor diagnostics.
- `panwatch/QUICK-START.md`, `panwatch/DEEP-ANALYSIS.md`: Productized TradingAgents watch platform, alerts, budgets, cooldowns, suggestion pool.
- `snowball-cli/QUICK-START.md`, `snowball-cli/DEEP-ANALYSIS.md`: JSON CLI external data layer and public/auth command boundary.
- `hhxg-market/QUICK-START.md`, `hhxg-market/DEEP-ANALYSIS.md`: Static JSON snapshots, schema version, cache, date prompts, read-only API patterns.
- `privora-python-examples/QUICK-START.md`, `privora-python-examples/DEEP-ANALYSIS.md`: Bearer token, skill gateway, scope matrix, response shape, sensitive data boundary.
- `dojoagents/QUICK-START.md`, `dojoagents/DEEP-ANALYSIS.md`: Config-driven Agent Runtime, tool artifacts, session export, dashboard SSE, planning, plugins, and Gateway boundaries.
- `vnpy/QUICK-START.md`, `vnpy/DEEP-ANALYSIS.md`: Event-driven Gateway and OMS contracts, AlphaLab, order/trade lifecycle, and execution boundaries.
- `pyportfolioopt/QUICK-START.md`, `pyportfolioopt/DEEP-ANALYSIS.md`: Portfolio optimization, risk models, Black-Litterman, HRP, constraints, and discrete allocation boundaries.

**Testing:**
- Not applicable for this repository because it contains documentation only.
- Testing patterns from studied projects are documented in `12-剩余深度素材.md`, especially UZI-Skill test naming and daily_stock_analysis CI layering.

## Naming Conventions

**Files:**
- Root navigation file uses `00-INDEX.md`.
- Root topic files use two-digit numeric prefixes plus Chinese topic names, for example `06-工程治理篇.md`, `08-数据采集与流水线篇.md`, and `16-UI-UX设计借鉴总表.md`.
- Root synthesis and decision files use numeric prefixes with uppercase English or Chinese titles, for example `10-SYNTHESIS.md`, `17-落地路线图.md`, and `18-模式决策矩阵.md`.
- Project dossier files use fixed uppercase English names: `QUICK-START.md` and `DEEP-ANALYSIS.md`.
- Generated codebase maps use uppercase English names under `.planning/codebase/`: `ARCHITECTURE.md` and `STRUCTURE.md`.

**Directories:**
- Project directories use lowercase ASCII kebab-case slugs such as `daily-stock-data/`, `tickflow-stock-panel/`, `quant-buddy-skill/`, and `tdx-market-data-clients/`.
- Some project slugs preserve upstream naming without extra separators, such as `alphaagent/`, `quantdinger/`, `panwatch/`, and `openashare/`.
- Generated planning directories use dot-prefixed infrastructure names: `.planning/` and `.planning/codebase/`.

**Headings:**
- Root topic files use Chinese H1 titles and numbered Chinese sections, for example `# 补充三：数据采集与流水线 — Fetcher Registry、并发编排、网络自适应` in `08-数据采集与流水线篇.md`.
- Project quick starts commonly begin with `# <Project> 快速概览`, then `一句话定位`, workflow/key modules, transferable lessons, and cautions.
- Project deep analyses commonly begin with `# <Project> 深度分析` or `# <Project> 深度代码分析`, then architecture, flow, key abstractions, migration patterns, risks, and conclusions.

## Where to Add New Code

**New Feature:**
- Primary code: Not applicable. This repository stores documentation only under `/root/source/docs/aaa`.
- Tests: Not applicable. If adding documentation validation, document the validation command in `00-INDEX.md` and place generated GSD context in `.planning/codebase/`.

**New Project Dossier:**
- Implementation: Create a new directory at `<project-slug>/` with `<project-slug>/QUICK-START.md` and `<project-slug>/DEEP-ANALYSIS.md`.
- Navigation: Add the project to `00-INDEX.md` under the directory tree and project overview table.
- Synthesis: Add reusable findings to relevant root topic files such as `06-工程治理篇.md`, `08-数据采集与流水线篇.md`, `09-Agent-协作与设计哲学篇.md`, `15-数据底座与采集底座篇.md`, or `16-UI-UX设计借鉴总表.md`.
- Decision updates: Update `10-SYNTHESIS.md` or `18-模式决策矩阵.md` when the new project changes a recommended default or tradeoff.

**New Cross-Topic Pattern:**
- Implementation: Prefer updating an existing root topic document when the concern matches an established file, for example governance in `06-工程治理篇.md`, strategy in `07-策略与信号系统篇.md`, data pipelines in `08-数据采集与流水线篇.md`, agents in `09-Agent-协作与设计哲学篇.md`, UI in `11-UI-UX交互设计.md` or `16-UI-UX设计借鉴总表.md`, and data foundations in `15-数据底座与采集底座篇.md`.
- Navigation: Update `00-INDEX.md` if the pattern affects reading routes or topic summaries.
- Decision updates: Update `18-模式决策矩阵.md` if the pattern changes a choice among interface, storage, orchestration, UI, real-time, audit, or strategy options.

**New Current-Project Planning Guidance:**
- Implementation: Add staged delivery guidance to `17-落地路线图.md`.
- Decision support: Add tradeoff rows or defaults to `18-模式决策矩阵.md`.
- Summary support: Add cross-project principles to `10-SYNTHESIS.md` if the guidance generalizes beyond one project.

**Utilities:**
- Shared helpers: Not applicable. There is no shared utility code in `/root/source/docs/aaa`.
- Documentation helper notes belong in root Markdown files such as `00-INDEX.md` or generated maps under `.planning/codebase/`.

## Special Directories

**`.planning/`:**
- Purpose: GSD planning artifacts.
- Generated: Yes.
- Committed: Not detected because `/root/source/docs/aaa` is not a git repository.

**`.planning/codebase/`:**
- Purpose: Generated codebase maps consumed by GSD commands.
- Generated: Yes.
- Committed: Not detected because `/root/source/docs/aaa` is not a git repository.

**Project dossier directories such as `jcp/`, `quantdinger/`, `daily-stock-data/`, and `tickflow-stock-panel/`:**
- Purpose: Curated source-project learning documents.
- Generated: No.
- Committed: Not detected because `/root/source/docs/aaa` is not a git repository.

## Maintenance Rules

- Update `00-INDEX.md` whenever a root topic file or project dossier is added, removed, or renamed.
- Keep `README.md` limited to stable entry links; keep detailed navigation in `00-INDEX.md`.
- Follow `01-知识库使用与维护指南.md` for provenance, terminology, evidence confidence, and publication checks.
- Keep each project directory complete with both `QUICK-START.md` and `DEEP-ANALYSIS.md`.
- Keep upstream source provenance near the top of dossier files, as in `jcp/QUICK-START.md` and `quantdinger/QUICK-START.md`.
- Keep generalizable lessons in root topic docs; do not leave reusable architecture knowledge only inside a single project dossier.
- Refresh `.planning/codebase/ARCHITECTURE.md` and `.planning/codebase/STRUCTURE.md` after major changes to root docs or dossier directories.

---

*Structure analysis: 2026-07-10*
