<!-- refreshed: 2026-07-10 -->
# Architecture

**Analysis Date:** 2026-07-10

## System Overview

```text
Repository: /root/source/docs/aaa

+-------------------------------------------------------------+
|                  Navigation and Decision Layer               |
|  `README.md`  `00-INDEX.md`  `01-知识库使用与维护指南.md`    |
|  `10-SYNTHESIS.md`  `17-落地路线图.md`  `18~20 决策与执行` |
+--------------------+--------------------+-------------------+
                     |                    |
                     v                    v
+-------------------------------------------------------------+
|                  Cross-Topic Synthesis Layer                 |
|  `06-工程治理篇.md`  `07-策略与信号系统篇.md`              |
|  `08-数据采集与流水线篇.md`  `09-Agent-协作与设计哲学篇.md` |
|  `11-UI-UX交互设计.md`  `12-剩余深度素材.md`                |
|  `13-终极提炼.md`  `14-跨项目深层精华.md`                  |
|  `15-数据底座与采集底座篇.md`  `16-UI-UX设计借鉴总表.md`    |
+--------------------+--------------------+-------------------+
                     |                    |
                     v                    v
+-------------------------------------------------------------+
|                    Project Dossier Layer                     |
|  `<project>/QUICK-START.md` gives fast positioning.          |
|  `<project>/DEEP-ANALYSIS.md` gives detailed architecture.   |
|  Examples: `jcp/`, `quantdinger/`, `daily-stock-data/`,      |
|  `tickflow-stock-panel/`, `uzi-skill/`, `agent-reach/`       |
+-------------------------------------------------------------+
                     |
                     v
+-------------------------------------------------------------+
|                    Generated Planning Layer                  |
|  `ARCHITECTURE / STRUCTURE / STACK / INTEGRATIONS`           |
|  `CONVENTIONS / TESTING / CONCERNS`                          |
+-------------------------------------------------------------+
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Standard entry point | Introduces the corpus and links the main reading path. | `README.md` |
| Root index | Routes readers by goal, catalogs all 37 external project dossiers, and links every source document. | `00-INDEX.md` |
| Usage and maintenance guide | Defines document hierarchy, evidence confidence, terminology, provenance, update flow, and publication checks. | `01-知识库使用与维护指南.md` |
| Pattern synthesis | Extracts cross-project design patterns such as pipeline flow, fallback data sources, multi-agent roles, quality gates, MCP/CLI/gateway interfaces, data contracts, data lakes, watch systems, local skills, static snapshots, and auth boundaries. | `10-SYNTHESIS.md` |
| Execution roadmap | Converts the knowledge base into staged plans for HermesAlpha and ashare-audit, including data/tool boundaries, agent layers, watch flows, UI surfaces, audit layers, shared infrastructure, and success criteria. | `17-落地路线图.md` |
| Decision matrix | Chooses among interface, storage, agent orchestration, UI, real-time, audit, strategy, and signal patterns. | `18-模式决策矩阵.md` |
| Source verification | Pins selected repositories to commits, verifies real call paths and failure behavior, and records boundaries that must not be copied blindly. | `19-首批源码落地验证.md` |
| Implementation checklist | Converts the roadmap and source verification into ordered tasks, deliverables, phase gates, and completion criteria. | `20-开发实施TODO.md` |
| Engineering governance topic | Consolidates self-review gates, data integrity checks, cache discipline, network preflight, validation matrices, and Agent Gateway guardrails. | `06-工程治理篇.md` |
| Strategy and signal topic | Consolidates signal engines, Alpha Zoo, YAML strategies, StrategyDef, backtesting, four-direction signals, formulas, and suggestion pools. | `07-策略与信号系统篇.md` |
| Data pipeline topic | Consolidates fetcher registries, wave concurrency, data-source fallback, probe systems, capability detection, incremental pipelines, and external data layering. | `08-数据采集与流水线篇.md` |
| Agent collaboration topic | Consolidates multi-role teams, LangGraph/run state, MCP exposure, local skill governance, Moderator meetings, Agent Gateway, and skill contracts. | `09-Agent-协作与设计哲学篇.md` |
| UI/UX topic | Consolidates report rendering, SVG primitives, React workbenches, SSE timelines, RunFlow, dashboards, data-quality banners, and state/error UX. | `11-UI-UX交互设计.md` |
| Report/test/deploy topic | Consolidates report assembly, data contracts, quality checklists, test organization, CI/CD, deployment, and tool response contracts. | `12-剩余深度素材.md` |
| Bug-driven extraction topic | Captures BUGS-LOG structure, release-note patterns, feature extraction, financial models, and audit lessons from UZI-Skill. | `13-终极提炼.md` |
| Deep cross-project comparison | Compares skill ecosystems, Vibe-Trading, bot architectures, tickflow, QuantDinger, and representative project positioning. | `14-跨项目深层精华.md` |
| Data foundation topic | Consolidates CSV/PostgreSQL modes, Parquet/DuckDB/Polars local data lakes, wrapper scripts, incremental repair, snapshots, contracts, and leak checks. | `15-数据底座与采集底座篇.md` |
| UI/UX task matrix | Organizes UI lessons by user task: workbench, report, long task, cockpit, data quality, auth, trading permission, empty/error/loading states. | `16-UI-UX设计借鉴总表.md` |
| Fast project dossier | Gives one-screen orientation, workflow, key modules, transferable lessons, and copying cautions for a single external project. | `<project>/QUICK-START.md` such as `jcp/QUICK-START.md` |
| Deep project dossier | Gives detailed architecture, internal layers, data flow, implementation references, risks, and migration patterns for a single external project. | `<project>/DEEP-ANALYSIS.md` such as `quantdinger/DEEP-ANALYSIS.md` |
| Generated codebase map | Provides GSD planning agents with current repo architecture and placement rules. | `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md` |

## Pattern Overview

**Overall:** Hub-and-spoke knowledge-base architecture.

**Key Characteristics:**
- Root documents at `README.md`, `00-INDEX.md`, `01-知识库使用与维护指南.md`, `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`, and `19-首批源码落地验证.md` are the primary navigation, governance, verification, and decision layer.
- Numbered root topic files from `06-工程治理篇.md` through `16-UI-UX设计借鉴总表.md` act as horizontal synthesis over the project dossier layer.
- Every project dossier directory uses the paired-file contract: `<project>/QUICK-START.md` for fast orientation and `<project>/DEEP-ANALYSIS.md` for detailed architecture.
- Dossiers preserve provenance with upstream source pointers, for example `jcp/QUICK-START.md` line 4 and `quantdinger/DEEP-ANALYSIS.md` line 4.
- The repository contains Markdown documentation only. No executable source tree, package manifest, application entry point, or runtime configuration is present under `/root/source/docs/aaa`.
- Project-local skill directories are not present: `.claude/skills/` and `.agents/skills/` are not detected under `/root/source/docs/aaa`.

## Layers

**Navigation Layer:**
- Purpose: Route readers to the right synthesis docs and project dossiers by goal.
- Location: `README.md`, `00-INDEX.md`, `01-知识库使用与维护指南.md`
- Contains: Standard entry point, goal-based reading routes, project catalog, topic index, document hierarchy, terminology, provenance rules, and maintenance checks.
- Depends on: All root topic documents and all project dossier files linked from `00-INDEX.md`.
- Used by: Human readers and planning agents deciding which document sequence to load first.

**Decision Layer:**
- Purpose: Convert raw learnings into actionable project choices.
- Location: `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`
- Contains: Cross-project patterns, recommended defaults, phased execution routes, tradeoff matrices, anti-patterns, and success criteria.
- Depends on: Project dossiers such as `quantdinger/DEEP-ANALYSIS.md`, `tickflow-stock-panel/DEEP-ANALYSIS.md`, `daily-stock-data/DEEP-ANALYSIS.md`, and topic docs such as `06-工程治理篇.md`.
- Used by: GSD phase planning for architecture, refactor, integration, setup, and UI work.

**Cross-Topic Layer:**
- Purpose: Group reusable patterns across projects by engineering concern rather than by source project.
- Location: `06-工程治理篇.md`, `07-策略与信号系统篇.md`, `08-数据采集与流水线篇.md`, `09-Agent-协作与设计哲学篇.md`, `11-UI-UX交互设计.md`, `12-剩余深度素材.md`, `13-终极提炼.md`, `14-跨项目深层精华.md`, `15-数据底座与采集底座篇.md`, `16-UI-UX设计借鉴总表.md`
- Contains: Source-project lists, code-pattern examples, architecture diagrams, tables of transferable components, cautions, and migration guidance.
- Depends on: Project dossier layer and external source references embedded in each dossier.
- Used by: Implementation agents looking for conventions such as data contracts, Agent Gateway envelopes, StrategyDef, RunFlow, static snapshots, and UI state patterns.

**Project Dossier Layer:**
- Purpose: Preserve detailed learning from one external project at a time.
- Location: 40 project directories including `jcp/`, `quantdinger/`, `daily-stock-data/`, `tickflow-stock-panel/`, `uzi-skill/`, `agent-reach/`, `panwatch/`, `snowball-cli/`, `hhxg-market/`, `privora-python-examples/`, `vnpy/`, and `pyportfolioopt/`.
- Contains: Exactly two Markdown files per project: `QUICK-START.md` and `DEEP-ANALYSIS.md`.
- Depends on: External upstream repositories referenced inside dossiers, for example `/root/source/tmp/jcp/` in `jcp/QUICK-START.md` and `/root/source/tmp/QuantDinger/` in `quantdinger/QUICK-START.md`.
- Used by: Topic docs and future planners requiring source-specific detail.

**Generated Planning Layer:**
- Purpose: Store machine-consumable codebase maps for GSD planning/execution commands.
- Location: `.planning/codebase/`
- Contains: `ARCHITECTURE.md` and `STRUCTURE.md` generated from the current documentation repository.
- Depends on: The Markdown source corpus under `/root/source/docs/aaa`.
- Used by: `/gsd-plan-phase`, `/gsd-execute-phase`, and related GSD workflows.

## Data Flow

### Primary Knowledge Path

1. External project details are captured in per-project dossiers such as `jcp/QUICK-START.md`, `jcp/DEEP-ANALYSIS.md`, `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`, `quantdinger/QUICK-START.md`, and `quantdinger/DEEP-ANALYSIS.md`.
2. Cross-topic synthesis files extract reusable architecture concerns: governance in `06-工程治理篇.md`, strategy in `07-策略与信号系统篇.md`, data pipelines in `08-数据采集与流水线篇.md`, agent collaboration in `09-Agent-协作与设计哲学篇.md`, UI in `11-UI-UX交互设计.md`, and data foundations in `15-数据底座与采集底座篇.md`.
3. Meta-synthesis documents consolidate cross-topic findings into general principles: `10-SYNTHESIS.md`, `13-终极提炼.md`, and `14-跨项目深层精华.md`.
4. Decision documents turn principles into project execution guidance: `17-落地路线图.md` and `18-模式决策矩阵.md`.
5. `README.md` and `00-INDEX.md` expose the navigation map and goal-based reading routes; `01-知识库使用与维护指南.md` defines how evidence and recommendations are maintained.

### Reader Task Path

1. Start from `README.md` or `00-INDEX.md` and select a goal-based reading route.
2. Select a goal-specific root sequence such as UI work through `16-UI-UX设计借鉴总表.md` and `11-UI-UX交互设计.md`, or data foundation work through `15-数据底座与采集底座篇.md` and `08-数据采集与流水线篇.md`.
3. Drill into named project dossiers from the project catalog in `00-INDEX.md`, for example `tickflow-stock-panel/DEEP-ANALYSIS.md` for local data lake/workbench patterns or `quantdinger/DEEP-ANALYSIS.md` for Agent Gateway/audit patterns.
4. Return to `18-模式决策矩阵.md` when a tradeoff must be selected rather than merely understood.

**State Management:**
- Source state is static Markdown under `/root/source/docs/aaa`.
- Navigation state is manually maintained in `00-INDEX.md`.
- Generated planning state lives in `.planning/codebase/`.
- No runtime database, cache, background worker, package manager, or build output is present in `/root/source/docs/aaa`.

## Key Abstractions

**Project Dossier:**
- Purpose: Encapsulate one external project as a reusable learning unit.
- Examples: `jcp/QUICK-START.md`, `jcp/DEEP-ANALYSIS.md`, `quantdinger/QUICK-START.md`, `quantdinger/DEEP-ANALYSIS.md`, `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`.
- Pattern: Directory slug plus fixed two-file contract: `QUICK-START.md` for overview and `DEEP-ANALYSIS.md` for detail.

**Cross-Topic Article:**
- Purpose: Reframe many project-specific findings around one architectural concern.
- Examples: `06-工程治理篇.md`, `07-策略与信号系统篇.md`, `08-数据采集与流水线篇.md`, `09-Agent-协作与设计哲学篇.md`, `11-UI-UX交互设计.md`, `15-数据底座与采集底座篇.md`.
- Pattern: Root-level numbered Markdown with source-project list, examples, diagrams/tables, and explicit migration guidance.

**Decision Artifact:**
- Purpose: Preserve project-level choices and defaults.
- Examples: `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`.
- Pattern: High-level principles followed by tables that map choices to current-project guidance.

**Transferable Pattern:**
- Purpose: Make a source-project mechanism portable to HermesAlpha, ashare-audit, or similar projects.
- Examples: `ToolCallEnvelope` in `17-落地路线图.md`, `StrategyDef` in `07-策略与信号系统篇.md`, `CapabilitySet` in `06-工程治理篇.md`, `DataContract` in `15-数据底座与采集底座篇.md`, and `RunFlow` in `16-UI-UX设计借鉴总表.md`.
- Pattern: Introduce source, show structure, explain migration value, state cautions.

**Provenance Pointer:**
- Purpose: Keep documentation tied to upstream source locations without vendoring source code into this repo.
- Examples: `> 源码: /root/source/tmp/jcp/` in `jcp/QUICK-START.md`, `> 源码: /root/source/tmp/QuantDinger/` in `quantdinger/QUICK-START.md`, and `> 源码: /root/source/tmp/daily_stock_analysis/` in `daily-stock-analysis/DEEP-ANALYSIS.md`.
- Pattern: Place source pointer near the top of each dossier.

## Entry Points

**Standard Repository Entry:**
- Location: `README.md`
- Triggers: Reader opens the directory through a conventional Markdown repository viewer.
- Responsibilities: Explain scope, link the primary documents, and state the recommended reading sequence.

**Repository Navigator:**
- Location: `00-INDEX.md`
- Triggers: Reader needs to understand the corpus, select a project dossier, or choose a topic route.
- Responsibilities: Document structure, goal-based reading routes, project catalog, topic catalog, and synthesis catalog.

**Knowledge-Base Governance:**
- Location: `01-知识库使用与维护指南.md`
- Triggers: Reader adds or refreshes a dossier, changes a recommendation, or prepares the corpus for publication.
- Responsibilities: Define evidence confidence, provenance format, terminology, update order, and release checks.

**Pattern Summary:**
- Location: `10-SYNTHESIS.md`
- Triggers: Reader needs a high-level architecture pattern view before drilling into dossiers.
- Responsibilities: Consolidate 37 projects into common design patterns and action recommendations.

**Execution Planning:**
- Location: `17-落地路线图.md`
- Triggers: Reader needs staged implementation guidance for HermesAlpha or ashare-audit.
- Responsibilities: Define target shapes, phase slices, shared infrastructure, deferred items, and success standards.

**Architecture Selection:**
- Location: `18-模式决策矩阵.md`
- Triggers: Reader needs to decide between MCP, CLI, Agent Gateway, storage modes, agent orchestration, UI forms, real-time mechanisms, or audit depth.
- Responsibilities: Provide choice matrices and recommended defaults.

**Project-Specific Research:**
- Location: `<project>/QUICK-START.md` and `<project>/DEEP-ANALYSIS.md`, for example `tickflow-stock-panel/QUICK-START.md` and `tickflow-stock-panel/DEEP-ANALYSIS.md`.
- Triggers: Reader needs source-specific patterns, key files, flows, risks, or direct migration notes.
- Responsibilities: Preserve the external project's architecture and transferable lessons.

**Generated GSD Context:**
- Location: `.planning/codebase/ARCHITECTURE.md` and `.planning/codebase/STRUCTURE.md`
- Triggers: GSD planning/execution commands need repository context.
- Responsibilities: Explain how to navigate, extend, and maintain this documentation corpus.

## Architectural Constraints

- **Threading:** Not applicable. The repository is static Markdown under `/root/source/docs/aaa` and has no executable runtime.
- **Global state:** `00-INDEX.md` is the global navigation source and must stay in sync with root topic files and project dossiers.
- **Circular imports:** Not applicable. Markdown documents cross-reference each other through links in `00-INDEX.md`; there is no import graph.
- **Source boundary:** Upstream source paths such as `/root/source/tmp/jcp/` and `/root/source/tmp/QuantDinger/` are provenance references inside dossiers, not source files in this repository.
- **Pairing constraint:** A project dossier is complete only when both `<project>/QUICK-START.md` and `<project>/DEEP-ANALYSIS.md` exist.
- **Ordering constraint:** Root topical and decision documents use numeric prefixes such as `06-工程治理篇.md`, `10-SYNTHESIS.md`, and `18-模式决策矩阵.md`; keep new root docs ordered and linked from `00-INDEX.md`.
- **Generated context constraint:** `.planning/codebase/` is a generated support layer. Use `00-INDEX.md` and source Markdown files as content truth, then refresh generated maps when the source corpus changes.

## Anti-Patterns

### Unindexed Dossier Addition

**What happens:** A new project directory such as `<project>/` is added with `QUICK-START.md` and `DEEP-ANALYSIS.md`, but `00-INDEX.md` is not updated.
**Why it's wrong:** The navigation table in `00-INDEX.md` is the repository entry point; unlinked dossiers become invisible to goal-based reading routes and GSD agents.
**Do this instead:** Add the new directory under `/root/source/docs/aaa/<project>/`, update the project overview table in `00-INDEX.md`, and add any cross-topic findings to files such as `06-工程治理篇.md`, `08-数据采集与流水线篇.md`, or `16-UI-UX设计借鉴总表.md`.

### Project-Only Pattern Storage

**What happens:** A reusable mechanism is documented only in one dossier such as `quantdinger/DEEP-ANALYSIS.md`.
**Why it's wrong:** Future planners looking for a concern like audit, storage, UI, or agent governance load topic docs first and may miss the pattern.
**Do this instead:** Keep the detailed source explanation in the dossier and extract the reusable pattern into the relevant root topic document, for example Agent Gateway governance in `06-工程治理篇.md`, data storage in `15-数据底座与采集底座篇.md`, and UI task patterns in `16-UI-UX设计借鉴总表.md`.

### Vendored Source Dumps

**What happens:** External source code or large implementation extracts are copied into `/root/source/docs/aaa` instead of being summarized.
**Why it's wrong:** The repo is a curated knowledge base, not the upstream source tree. Source dumps make `00-INDEX.md` less reliable and blur the boundary between reference notes and source projects.
**Do this instead:** Keep upstream provenance pointers inside dossier headers, such as `jcp/QUICK-START.md:4`, and summarize architecture, flows, key files, and migration lessons in Markdown.

### Decision Without Matrix Linkage

**What happens:** A recommended default appears in a topic file such as `08-数据采集与流水线篇.md` but is not reflected in `18-模式决策矩阵.md`.
**Why it's wrong:** `18-模式决策矩阵.md` is the central selection guide; missing entries force readers to hunt through long topic docs.
**Do this instead:** Add tradeoff rows to `18-模式决策矩阵.md` when a pattern affects interface, storage, orchestration, UI, real-time, audit, or strategy choices.

## Error Handling

**Strategy:** Content-level risk handling through cautions, anti-patterns, deferred items, and audit guidance rather than runtime exception handling.

**Patterns:**
- Use `不该照搬的部分` sections in project dossiers such as `jcp/QUICK-START.md` to separate transferable patterns from unsafe copying.
- Use risk and caution sections such as `风险与改造建议` in deep dossiers like `jcp/DEEP-ANALYSIS.md`.
- Use `明确暂缓事项` in `17-落地路线图.md` to defer high-risk work such as full trading execution, large real-time market services, complex LangGraph state machines, and automatic live trading.
- Use `反模式清单` in `18-模式决策矩阵.md` to encode recurring architectural traps.

## Cross-Cutting Concerns

**Logging:** Runtime logging is not applicable for static Markdown. Provenance and traceability are handled through upstream source pointers in dossier headers such as `quantdinger/QUICK-START.md:4` and document links in `00-INDEX.md`.

**Validation:** No automated link checker, Markdown linter, or build step is detected under `/root/source/docs/aaa`. Validate by checking `00-INDEX.md`, confirming paired dossier files, and refreshing `.planning/codebase/` after structural changes.

**Authentication:** Not applicable for this repository. Authentication is discussed as a source-project pattern in `10-SYNTHESIS.md`, `18-模式决策矩阵.md`, `quantdinger/DEEP-ANALYSIS.md`, `snowball-cli/DEEP-ANALYSIS.md`, and `privora-python-examples/DEEP-ANALYSIS.md`.

**Navigation:** `00-INDEX.md` is the single entry point for readers. Keep new root docs and project dossiers linked there.

**Localization:** Root topic files use Chinese titles and content such as `06-工程治理篇.md`; project directory slugs use ASCII/kebab-case such as `daily-stock-data/` and `tickflow-stock-panel/`.

---

*Architecture analysis: 2026-07-09*
