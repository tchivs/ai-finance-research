# External Integrations

**Analysis Date:** 2026-07-09

## APIs & External Services

**Local Repository:**
- No executable API clients detected - `/root/source/docs/aaa` contains Markdown docs only, with no local source files or package manifests.
  - SDK/Client: Not applicable
  - Auth: Not applicable

**Market Data Providers Referenced:**
- Tushare - A-share daily data, trading calendar, stock basics, and provider priority examples.
  - SDK/Client: documented as `TushareFetcher` or Tushare scripts in `daily-stock-analysis/QUICK-START.md`, `daily-stock-data/QUICK-START.md`, and `08-数据采集与流水线篇.md`
  - Auth: `TUSHARE_TOKEN`
- AkShare / efinance / baostock / pytdx - A-share fallback providers and protocol clients.
  - SDK/Client: documented in `daily-stock-analysis/QUICK-START.md`, `daily-stock-data/QUICK-START.md`, and `agentic-china-data-tooling/QUICK-START.md`
  - Auth: usually public or provider-specific; no local credentials in this repo
- yfinance / Yahoo / Longbridge / Finnhub / AlphaVantage - US/HK/global market fallback and optional-key providers.
  - SDK/Client: documented in `daily-stock-analysis/QUICK-START.md`, `vibe-trading/QUICK-START.md`, and `awesome-finance-skills/QUICK-START.md`
  - Auth: optional provider keys; Longbridge/Finnhub/AlphaVantage keys are referenced conceptually, not stored locally
- Sina / Tencent / Eastmoney - public quote, capital flow, K-line, F10, and market-data fallback sources.
  - SDK/Client: documented in `magpie/QUICK-START.md`, `jcp/QUICK-START.md`, `a-stock-data/QUICK-START.md`, and `awesome-finance-skills/QUICK-START.md`
  - Auth: generally public HTTP; Eastmoney calls require rate limiting per `a-stock-data/QUICK-START.md`
- TDX / mootdx / Tongdaxin protocol - lower-level quote, K-line, order book, and reference data sources.
  - SDK/Client: documented in `jcp/QUICK-START.md`, `a-stock-data/QUICK-START.md`, `tdx-market-data-clients/QUICK-START.md`, and `daily-stock-data/QUICK-START.md`
  - Auth: not documented as required in this repo

**Financial Platforms and Data Products Referenced:**
- Snowball / Danjuan - quote, finance, F10, capital flow, social, KOL, and fund data via JSON CLI.
  - SDK/Client: TypeScript/Bun/Node CLI documented in `snowball-cli/QUICK-START.md`
  - Auth: public-first access, then cookie token in `~/.snowball-cli/token.json` if needed
- JoinQuant - strategy generation, platform API references, templates, factor lab, and AST lint.
  - SDK/Client: skill references and `jqskill_mcp/server.py` documented in `joinquant-skill/QUICK-START.md`
  - Auth: platform access is external; no local credentials in this repo
- Privora - Agent skill gateway examples for financial data and portfolio access.
  - SDK/Client: Python quickstart scripts and `POST /agent/skills/execute` documented in `privora-python-examples/QUICK-START.md`
  - Auth: `Authorization: Bearer <token>`, documented env vars `LG_AGENT_BASE_URL` and `LG_AGENT_TOKEN`
- hhxg-market - static A-share market snapshot, calendar, margin, and news data.
  - SDK/Client: zero-dependency Python scripts and `openapi.yaml` documented in `hhxg-market/QUICK-START.md`
  - Auth: public read-only endpoints; `x-openai-isConsequential: false` documented
- Wudao MCP - read-only A-share MCP data layer with workflow and profile-based tools.
  - SDK/Client: MCP server and skill documentation in `wudao-mcp/QUICK-START.md`
  - Auth: API key required before use, documented in `wudao-mcp/QUICK-START.md`

**LLM, Agent, and Model Services Referenced:**
- OpenAI-compatible providers and local Codex CLI - AI analysis and strategy/report generation surfaces.
  - SDK/Client: `backend/app/services/ai_provider.py` pattern in `tickflow-stock-panel/QUICK-START.md`, model/settings pages in `openashare/QUICK-START.md`
  - Auth: provider-specific API keys; not present locally
- Claude / Cursor / OpenClaw / OpenCode / Codex / Gemini - Agent clients and skill consumers.
  - SDK/Client: MCP and skill surfaces documented in `vibe-trading/QUICK-START.md`, `wudao-mcp/QUICK-START.md`, `awesome-finance-skills/QUICK-START.md`, and `09-Agent-协作与设计哲学篇.md`
  - Auth: client-specific external configuration
- Kronos / FinCast / BERT / torch / transformers - time-series and sentiment model dependencies for referenced skills.
  - SDK/Client: documented in `awesome-finance-skills/QUICK-START.md` and `financial-timeseries-foundation/QUICK-START.md`
  - Auth: local weights or model provider access; checkpoint path governance is called out in `awesome-finance-skills/QUICK-START.md`

**Notification and Bot Channels Referenced:**
- Feishu, DingTalk, Discord, Telegram, email SMTP, Pushover, enterprise WeChat - notification and IM surfaces for analysis reports, alerts, and bots.
  - SDK/Client: documented in `daily-stock-analysis/QUICK-START.md`, `magpie/QUICK-START.md`, and `14-跨项目深层精华.md`
  - Auth: webhook URLs, bot tokens, SMTP credentials, or platform-specific secrets managed outside this repo

## Data Storage

**Databases:**
- Not detected locally. The repository stores knowledge as Markdown files only.
- CSV/PostgreSQL dual backend - documented for `daily_stock_data` in `daily-stock-data/QUICK-START.md` and `15-数据底座与采集底座篇.md`.
  - Connection: `STORAGE_BACKEND=csv/postgres/both`; PostgreSQL connection details are external
  - Client: Python scripts and storage helpers, not present locally
- SQLite - documented for watchlists, alerts, quote cache, research memory, citations, sessions, and checkpoints in `magpie/QUICK-START.md`, `awesome-finance-skills/QUICK-START.md`, `openashare/QUICK-START.md`, and `tradingagents-family/QUICK-START.md`.
  - Connection: local `.db` files in upstream patterns
  - Client: `better-sqlite3`, Python sqlite, or app-specific stores depending on upstream project
- PostgreSQL runtime - documented for jobs, audit logs, strategy/order/backtest state, and long-lived trading systems in `quantdinger/QUICK-START.md` and `18-模式决策矩阵.md`.
  - Connection: external database URL or Docker Compose service
  - Client: Flask services and migrations in referenced upstream project
- DuckDB + Parquet + Polars - documented local data-lake stack for market history and audit narrow tables in `tickflow-stock-panel/QUICK-START.md`, `agentic-china-data-tooling/QUICK-START.md`, and `15-数据底座与采集底座篇.md`.
  - Connection: local Parquet directories and in-memory DuckDB views
  - Client: Polars and DuckDB in referenced implementations
- Redis - documented as part of QuantDinger deployment in `quantdinger/QUICK-START.md`.
  - Connection: Docker Compose service in upstream pattern
  - Client: backend runtime support, not local

**File Storage:**
- Local Markdown files are the committed product surface: `00-INDEX.md`, root theme documents, and per-project `QUICK-START.md` / `DEEP-ANALYSIS.md` files.
- Referenced file-storage patterns include static JSON snapshots in `hhxg-market/QUICK-START.md`, run directories in `09-Agent-协作与设计哲学篇.md`, CSV atomic writes in `daily-stock-data/QUICK-START.md`, and Parquet partitions in `tickflow-stock-panel/QUICK-START.md`.

**Caching:**
- Not implemented locally.
- Referenced caches include `~/.cache/hhxg-market` in `hhxg-market/QUICK-START.md`, `quote_cache` in `magpie/QUICK-START.md`, same-day analysis cache in `panwatch/QUICK-START.md`, search/detail caches in `awesome-finance-skills/QUICK-START.md`, ETag/stale-while-revalidate in `openashare/QUICK-START.md`, and UZI-Skill TTL cache tiers in `06-工程治理篇.md`.

## Authentication & Identity

**Auth Provider:**
- None locally.
- Custom Bearer Token gateways - Privora uses `Authorization: Bearer <token>` and scope-limited `skillId + params` calls in `privora-python-examples/QUICK-START.md`; QuantDinger uses `qd_agent_*` Bearer tokens and R/W/B/N/C/T scopes in `quantdinger/QUICK-START.md`.
- Cookie-based auth - Snowball CLI uses Chrome/Chromium CDP, manual login, or pasted cookie tokens in `snowball-cli/QUICK-START.md`.
- JWT / demo access cookies - QuantDinger separates human JWT routes from Agent Gateway tokens in `quantdinger/QUICK-START.md`; OpenAshare references demo access cookies in `openashare/QUICK-START.md`.
- API keys - Wudao MCP requires an API key in `wudao-mcp/QUICK-START.md`; market/LLM providers require external keys according to their upstream docs.

## Monitoring & Observability

**Error Tracking:**
- None locally.
- Referenced patterns include source health snapshots/history in `agentic-china-data-tooling/QUICK-START.md`, `/doctor` style provider checks in `10-SYNTHESIS.md`, CapabilitySet startup detection in `tickflow-stock-panel/QUICK-START.md`, Agent Gateway audit rows in `quantdinger/QUICK-START.md`, and schema/cache/date warnings in `hhxg-market/QUICK-START.md`.

**Logs:**
- Local repo logs: Not applicable.
- Referenced logs include `logs/` directories from shell wrappers in `daily-stock-data/QUICK-START.md`, UI debug logs via DBLogHandler in `panwatch/QUICK-START.md`, Agent job/audit records in `quantdinger/QUICK-START.md`, and tool invocation envelopes in `17-落地路线图.md`.

## CI/CD & Deployment

**Hosting:**
- Not applicable locally. This repository is not deployed.
- Referenced hosting/deployment patterns include Docker Compose in `vibe-trading/QUICK-START.md`, single-container self-hosting in `tickflow-stock-panel/QUICK-START.md`, multi-container Trading OS deployment in `quantdinger/QUICK-START.md`, static JSON/OpenAPI publishing in `hhxg-market/QUICK-START.md`, and local desktop/Wails distribution in `jcp/QUICK-START.md`.

**CI Pipeline:**
- None detected locally. No `.github/workflows/*` files were found.
- Referenced CI checks include ruff, `py_compile`, pytest, shell syntax checks, private-path leak checks, Docker build gates, frontend lint/build gates, and AI governance checks in `daily-stock-data/QUICK-START.md`, `daily-stock-analysis/QUICK-START.md`, and `06-工程治理篇.md`.

## Environment Configuration

**Required env vars:**
- Local repository: None detected.
- Referenced, implementation-facing env vars and config names include `TUSHARE_TOKEN` in `daily-stock-analysis/QUICK-START.md`, `STORAGE_BACKEND` in `daily-stock-data/QUICK-START.md`, `LG_AGENT_BASE_URL` and `LG_AGENT_TOKEN` in `privora-python-examples/QUICK-START.md`, `AGENT_LIVE_TRADING_ENABLED` in `quantdinger/QUICK-START.md`, and `DEMO_ACCESS_*` in `openashare/QUICK-START.md`.
- Referenced proxy/network env handling appears in `06-工程治理篇.md` and includes `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY`.

**Secrets location:**
- Local repository: No `.env*` files detected; no secret files were read or required.
- Referenced external secret locations include environment variables for API tokens, provider-specific config files, Snowball cookie storage at `~/.snowball-cli/token.json` in `snowball-cli/QUICK-START.md`, and gateway tokens managed outside the repo in `privora-python-examples/QUICK-START.md` and `quantdinger/QUICK-START.md`.

## Webhooks & Callbacks

**Incoming:**
- None locally.
- Referenced incoming surfaces include OpenClaw `POST /analyze` in `jcp/QUICK-START.md`, QuantDinger `/api/agent/v1` and `/jobs/{id}/stream` in `quantdinger/QUICK-START.md`, Privora `POST /agent/skills/execute` in `privora-python-examples/QUICK-START.md`, FastAPI REST/SSE routes in `openashare/QUICK-START.md` and `tickflow-stock-panel/QUICK-START.md`, and local Magpie HTTP API on `127.0.0.1:17891` in `magpie/QUICK-START.md`.

**Outgoing:**
- None locally.
- Referenced outgoing notifications include Feishu webhook/stdout in `magpie/QUICK-START.md`, enterprise WeChat, Feishu, Telegram, SMTP email, and Pushover in `daily-stock-analysis/QUICK-START.md`, DingTalk/Discord/Feishu stream adapters in `14-跨项目深层精华.md`, and provider HTTP/API calls to Snowball, Tushare, Eastmoney, Sina, Tencent, Privora, hhxg, and other market data services documented across the project dossiers.

---

*Integration audit: 2026-07-09*
