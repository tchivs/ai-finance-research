# Technology Stack

**Analysis Date:** 2026-07-09

## Languages

**Primary:**
- Markdown - Repository-local product surface. All detected project content is Markdown documentation: `00-INDEX.md`, `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`, and per-project dossiers such as `vibe-trading/QUICK-START.md` and `quantdinger/QUICK-START.md`.
- Chinese-language technical documentation - Most current-state analysis and recommendations are written in Chinese, with English identifiers, code blocks, and upstream project names embedded throughout `06-工程治理篇.md`, `08-数据采集与流水线篇.md`, `09-Agent-协作与设计哲学篇.md`, and `15-数据底座与采集底座篇.md`.

**Secondary:**
- Python - Referenced heavily as an upstream implementation language for financial data tools, FastAPI services, MCP servers, data workers, and zero-dependency skills. Examples are documented in `daily-stock-data/QUICK-START.md`, `tickflow-stock-panel/QUICK-START.md`, `privora-python-examples/QUICK-START.md`, `hhxg-market/QUICK-START.md`, and `awesome-finance-skills/QUICK-START.md`.
- TypeScript / JavaScript - Referenced for React/Vite dashboards, Node/Fastify servers, Bun/Node CLIs, and TypeScript MCP servers in `vibe-trading/QUICK-START.md`, `trade-skills/DEEP-ANALYSIS.md`, `snowball-cli/QUICK-START.md`, `magpie/QUICK-START.md`, and `agentic-china-data-tooling/QUICK-START.md`.
- Go - Referenced for the Wails desktop application and ADK/tool registration design in `jcp/QUICK-START.md` and `jcp/DEEP-ANALYSIS.md`.
- Vue - Referenced as the prebuilt frontend technology in QuantDinger's Trading OS stack in `quantdinger/QUICK-START.md`.

## Runtime

**Environment:**
- No local executable runtime detected for this repository. No `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, source files, or workflow files were detected under `/root/source/docs/aaa`; treat the repository as a documentation and knowledge-base artifact.
- Markdown consumers: humans, GSD planning agents, and future implementation agents. `00-INDEX.md` defines the repository as an external-project learning reference extracted from 37 AI + finance projects.

**Package Manager:**
- Not detected locally.
- Lockfile: missing locally. No `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `poetry.lock`, or equivalent lockfile was detected.

## Frameworks

**Core:**
- Markdown knowledge base - The only local framework is the dossier structure documented in `00-INDEX.md`: root synthesis/theme documents plus one `QUICK-START.md` and one `DEEP-ANALYSIS.md` per referenced project.
- GSD planning artifact integration - Generated maps live under `.planning/codebase/`; this file and `INTEGRATIONS.md` are intended to guide `/gsd-plan-phase` and `/gsd-execute-phase` workflows.

**Testing:**
- Not detected locally.
- Referenced testing and quality tools include `pytest`, `ruff`, `py_compile`, shell syntax checks, private-path leak checks, and web lint/build gates in `daily-stock-data/QUICK-START.md`, `daily-stock-analysis/QUICK-START.md`, and `06-工程治理篇.md`.
- Referenced frontend testing includes `vitest.config.ts` for the React/Vite dashboard in `vibe-trading/QUICK-START.md`.

**Build/Dev:**
- Not detected locally. There are no local build scripts, Dockerfiles, or CI workflows.
- Referenced build and deployment patterns include FastAPI + React + Docker Compose in `vibe-trading/QUICK-START.md`, single-container FastAPI/React deployment in `tickflow-stock-panel/QUICK-START.md`, Docker Compose with PostgreSQL/Redis/backend/frontend/mobile in `quantdinger/QUICK-START.md`, and Wails desktop packaging in `jcp/QUICK-START.md`.

## Key Dependencies

**Critical:**
- Markdown dossier structure - The planner should rely on `00-INDEX.md` for navigation and on `10-SYNTHESIS.md`, `17-落地路线图.md`, and `18-模式决策矩阵.md` for cross-project decisions.
- Per-project dossiers - Each subdirectory, for example `snowball-cli/QUICK-START.md`, `privora-python-examples/QUICK-START.md`, and `quant-buddy-skill/QUICK-START.md`, is an integration or architecture reference rather than runnable local code.
- External source snapshot references - Paths such as `/root/source/tmp/Vibe-Trading/` in `vibe-trading/DEEP-ANALYSIS.md` and `/root/source/tmp/QuantDinger/` in `quantdinger/QUICK-START.md` are documented upstream snapshot locations, not local dependencies of this repository.

**Infrastructure:**
- Python ecosystem references - FastAPI, Flask, Pydantic, LangGraph, pytest, ruff, Polars, DuckDB, pandas, AkShare, yfinance, Tushare, pytdx, and script-based skills are recurring patterns in `vibe-trading/DEEP-ANALYSIS.md`, `daily-stock-analysis/QUICK-START.md`, `tickflow-stock-panel/QUICK-START.md`, `agentic-china-data-tooling/QUICK-START.md`, and `awesome-finance-skills/QUICK-START.md`.
- JavaScript/TypeScript ecosystem references - React, Vite, Tailwind, Next.js, Fastify, Node, Bun, Commander CLI, and Vue appear as referenced upstream technologies in `vibe-trading/QUICK-START.md`, `openashare/QUICK-START.md`, `trade-skills/DEEP-ANALYSIS.md`, `snowball-cli/QUICK-START.md`, `magpie/QUICK-START.md`, and `quantdinger/QUICK-START.md`.
- Agent and tool protocols - MCP, OpenClaw/OpenCode skills, Agent Gateway, Skill Gateway, JSON CLI, and read-only OpenAPI are the dominant interface patterns summarized in `10-SYNTHESIS.md`, `14-跨项目深层精华.md`, `18-模式决策矩阵.md`, `wudao-mcp/QUICK-START.md`, `joinquant-skill/QUICK-START.md`, and `privora-python-examples/QUICK-START.md`.
- Data/storage patterns - CSV, PostgreSQL, SQLite, Parquet, DuckDB, Polars, static JSON, Redis, and local cache directories are documented in `15-数据底座与采集底座篇.md`, `daily-stock-data/QUICK-START.md`, `tickflow-stock-panel/QUICK-START.md`, `magpie/QUICK-START.md`, `hhxg-market/QUICK-START.md`, and `quantdinger/QUICK-START.md`.

## Configuration

**Environment:**
- No local `.env*` files detected. Do not add secrets or runtime credentials to this documentation repository.
- Documented upstream environment variables include `TUSHARE_TOKEN` in `08-数据采集与流水线篇.md` and `daily-stock-analysis/QUICK-START.md`, `STORAGE_BACKEND=csv/postgres/both` in `daily-stock-data/QUICK-START.md` and `15-数据底座与采集底座篇.md`, `LG_AGENT_BASE_URL` and `LG_AGENT_TOKEN` in `privora-python-examples/QUICK-START.md`, `AGENT_LIVE_TRADING_ENABLED` in `quantdinger/QUICK-START.md`, and `DEMO_ACCESS_*` in `openashare/QUICK-START.md`.
- Use documented env vars as implementation references only. This repo does not validate, load, or require them.

**Build:**
- Build config files: Not detected locally.
- Referenced build config examples include `docker-compose.yml` and `Dockerfile` in `vibe-trading/QUICK-START.md`, `Dockerfile` and `docker-compose.yml` in `tickflow-stock-panel/QUICK-START.md`, and Docker Compose deployment in `quantdinger/QUICK-START.md`.

## Platform Requirements

**Development:**
- Local mapping and editing require only filesystem access to Markdown files under `/root/source/docs/aaa`.
- Add new project references as Markdown under a project subdirectory with `QUICK-START.md` and `DEEP-ANALYSIS.md`, then update `00-INDEX.md`, `10-SYNTHESIS.md`, and any relevant theme file such as `08-数据采集与流水线篇.md` or `15-数据底座与采集底座篇.md`.
- Keep executable assumptions out of the repo unless manifests and source files are intentionally introduced. If runtime code is added later, add the package manifest and update `.planning/codebase/STACK.md`.

**Production:**
- Not applicable locally. The repository is not a deployable application.
- Referenced production patterns are decision inputs for HermesAlpha and ashare-audit: static JSON snapshots from `hhxg-market/QUICK-START.md`, FastAPI/React workbenches from `tickflow-stock-panel/QUICK-START.md` and `openashare/QUICK-START.md`, scoped Agent Gateway from `quantdinger/QUICK-START.md`, and JSON CLI data adapters from `snowball-cli/QUICK-START.md`.

---

*Stack analysis: 2026-07-09*
