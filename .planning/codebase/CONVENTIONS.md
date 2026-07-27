# Coding Conventions

**Analysis Date:** 2026-07-10

## Naming Patterns

**Files:**
- Use `README.md` as the conventional entry point, `00-INDEX.md` as the detailed navigation source, and `01-知识库使用与维护指南.md` as the documentation governance source. Use numbered root synthesis and decision documents for cross-project knowledge: `06-工程治理篇.md` through `18-模式决策矩阵.md`; use `19-首批源码落地验证.md` for commit-pinned implementation verification and `20-开发实施TODO.md` for task tracking.
- Use one directory per analyzed source project, named in lowercase project style or upstream name style: `uzi-skill/`, `daily-stock-data/`, `tickflow-stock-panel/`, `joinquant-skill/`, `privora-python-examples/`.
- Use exactly two standard per-project files when adding a new project: `QUICK-START.md` for the short orientation and `DEEP-ANALYSIS.md` for the detailed analysis, matching existing pairs like `magpie/QUICK-START.md` and `magpie/DEEP-ANALYSIS.md`.
- Keep `README.md` stable and concise. Keep `00-INDEX.md` as the navigation source for all root synthesis files and all per-project `QUICK-START.md` / `DEEP-ANALYSIS.md` links.

**Functions:**
- This repository has no executable source files. Function names appear only as referenced examples from analyzed projects, and must stay in inline code exactly as the source uses them: `self_review.py`, `data_integrity.py`, `StrategyLinter(ast.NodeVisitor)`, `parseDecision()`, `write_csv_table()`, `append_upsert_csv()`, `replace_csv_slice()`.
- When documenting reusable implementation patterns, name the concrete function or file first, then state the reusable principle. Examples: `daily-stock-data/DEEP-ANALYSIS.md` describes `scripts/storage_common.py` before extracting the CSV atomic-write convention; `joinquant-skill/DEEP-ANALYSIS.md` describes `scripts/strategy_lint.py` before extracting AST lint rules.

**Variables:**
- Use inline code for environment variables, schema fields, table names, and protocol fields: `STORAGE_BACKEND`, `DATA_DIR`, `schema_version`, `from_cache`, `skillId`, `params`, `response_shape`, `task_id`, `data_id`, `expression_id`.
- Preserve upstream field names and platform spellings even when they look unusual. `joinquant-skill/QUICK-START.md` explicitly notes that platform spelling such as `standardlize` must stay as-is rather than being normalized.

**Types:**
- Treat named contracts as first-class concepts and write them in code font: `ToolCallEnvelope`, `DataContract`, `CapabilitySet`, `StrategyDef`, `FactorMeta`, `ExtractedStrategy`, `RunStateStore`, `Issue`, `ICReport`.
- When introducing a contract, include its fields or invariants in a fenced block or table. Existing examples include `jcp/DEEP-ANALYSIS.md` for the Moderator JSON contract, `privora-python-examples/DEEP-ANALYSIS.md` for the skill gateway response envelope, and `quant-buddy-skill/DEEP-ANALYSIS.md` for exact tool-contract fields.

## Code Style

**Formatting:**
- Use GitHub-flavored Markdown. The repo contains Markdown files only; no `package.json`, formatter config, linter config, or executable source files were detected under `/root/source/docs/aaa`.
- Write prose primarily in Chinese, keeping product names, file names, APIs, commands, and protocol fields in English inline code. Existing examples are `10-SYNTHESIS.md`, `17-落地路线图.md`, and `18-模式决策矩阵.md`.
- Prefer short paragraphs followed by tables, numbered lists, or fenced diagrams. Long conceptual sections should be split with `---`, as seen in `06-工程治理篇.md`, `12-剩余深度素材.md`, and `13-终极提炼.md`.
- Use fenced blocks with an explicit language where helpful: `text` for architecture/data-flow diagrams, `python` for Python snippets, `json` for envelopes, `yaml` for workflows, `bash` for commands, `css` or `html` for UI snippets. Existing examples appear in `11-UI-UX交互设计.md`, `12-剩余深度素材.md`, and `privora-python-examples/DEEP-ANALYSIS.md`.
- Use tables for comparison, migration advice, and action lists. Standard columns include `项目`, `机制`, `可借鉴点`, `能力`, `来源`, `适用项目`, and `优先级`, as in `06-工程治理篇.md` and `10-SYNTHESIS.md`.

**Linting:**
- Not detected. No Markdown lint config, spellcheck config, link-check config, or CI config exists in this repository.
- Apply manual Markdown hygiene: one H1 per file, heading levels in order, fenced blocks closed, table separators present, file names in prose wrapped in backticks, and navigation targets expressed as Markdown links.
- Do not introduce raw environment values, credentials, cookies, tokens, or private paths. The repo documents this as a quality principle in `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`, and `15-数据底座与采集底座篇.md`.

## Import Organization

**Order:**
1. Per-project evidence: add or update `PROJECT/QUICK-START.md` and `PROJECT/DEEP-ANALYSIS.md` with source baseline, workflows, risks, limitations, and migration advice.
2. Cross-topic synthesis: add or update the relevant numbered root topic file such as `06-工程治理篇.md`, `09-Agent-协作与设计哲学篇.md`, `15-数据底座与采集底座篇.md`, or `16-UI-UX设计借鉴总表.md`.
3. Decision/roadmap surfaces: reflect reusable patterns in `10-SYNTHESIS.md`, `17-落地路线图.md`, or `18-模式决策矩阵.md` only when they affect current recommendations.
4. Root orientation: update `00-INDEX.md` when adding or renaming a root synthesis file or project directory; update `README.md` only when a primary entry document changes.

**Path Aliases:**
- Not applicable. This repository has no source-code import aliases.
- Use repo-relative Markdown paths for internal references, as in `00-INDEX.md`: `uzi-skill/QUICK-START.md`, `uzi-skill/DEEP-ANALYSIS.md`, `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`.
- Use inline code for upstream source paths mentioned inside analysis files: `/root/source/tmp/UZI-Skill/skills/deep-analysis/scripts/` in `uzi-skill/DEEP-ANALYSIS.md`, `/root/source/tmp/joinquant-skill/` in `joinquant-skill/DEEP-ANALYSIS.md`, and `/root/source/tmp/privora-python-examples/` in `privora-python-examples/DEEP-ANALYSIS.md`.

## Document Structure

**Root Index:**
- Keep `00-INDEX.md` as the reading map. It should show goal-based reading routes, document hierarchy, project catalog, root topic summaries, and core decision documents without duplicating detailed implementation guidance.
- Add new project rows in `00-INDEX.md` with both quick and deep links, following rows like `UZI-Skill`, `daily_stock_data`, `joinquant-skill`, `magpie`, and `Privora Python Examples`.

**Usage and Maintenance Guide:**
- Keep `01-知识库使用与维护指南.md` authoritative for evidence confidence, dossier structure, provenance, terminology, update flow, and publication checks.
- Move durable documentation rules into the guide instead of repeating them across the index and synthesis files.

**Quick-Start Documents:**
- Use `PROJECT/QUICK-START.md` for a compact, decision-oriented overview. Existing structure usually includes: title, one-sentence positioning, core workflow or module table, most valuable design patterns, current-project migration points, risks, and conclusion.
- Keep quick starts short enough to scan. Examples: `joinquant-skill/QUICK-START.md`, `magpie/QUICK-START.md`, `privora-python-examples/QUICK-START.md`, and `daily-stock-data/QUICK-START.md`.

**Deep Analysis Documents:**
- Use `PROJECT/DEEP-ANALYSIS.md` for architecture, exact contracts, workflows, failure modes, quality gates, and migration models.
- Start with an H1 and a short blockquote naming the technology shape and upstream source path, as in `jcp/DEEP-ANALYSIS.md`, `hhxg-market/DEEP-ANALYSIS.md`, and `snowball-cli/DEEP-ANALYSIS.md`.
- Prefer numbered sections: `## 1. 架构定位`, `## 2. ...`, ending with `风险与改造建议` and `结论` when applicable.
- Include concrete file names from the analyzed project where available, even though those files are external references. Examples: `scripts/strategy_lint.py` in `joinquant-skill/DEEP-ANALYSIS.md`, `scripts/_common.py` in `hhxg-market/DEEP-ANALYSIS.md`, `src/engine.ts` in `magpie/DEEP-ANALYSIS.md`.

**Cross-Project Synthesis:**
- Use numbered root files for horizontal topics. `06-工程治理篇.md` owns quality gates, self-checks, data integrity, and audit boundaries. `09-Agent-协作与设计哲学篇.md` owns Agent collaboration, `SKILL.md` contracts, and tool boundaries. `12-剩余深度素材.md` owns tests, CI/CD, release, and data-contract material. `15-数据底座与采集底座篇.md` owns data foundation patterns. `16-UI-UX设计借鉴总表.md` owns UI validation and trust-state patterns.
- Use `10-SYNTHESIS.md` for distilled cross-project patterns and action suggestions, not raw project details.
- Use `17-落地路线图.md` for phased implementation and acceptance criteria. Use `18-模式决策矩阵.md` for choosing between architectures and naming anti-patterns.

## Cross-Reference Patterns

**Internal Links:**
- In `00-INDEX.md`, project links use the label “阅读” and root-relative targets such as `uzi-skill/QUICK-START.md` and `uzi-skill/DEEP-ANALYSIS.md`.
- In prose, reference internal files with backticks rather than bare text: `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`.

**Evidence Links:**
- Every reusable claim should point to a concrete project doc or root synthesis doc. For example, quality-gate claims should cite `06-工程治理篇.md`, test/CI claims should cite `12-剩余深度素材.md`, and tool-envelope claims should cite `quant-buddy-skill/DEEP-ANALYSIS.md`, `privora-python-examples/DEEP-ANALYSIS.md`, or `snowball-cli/DEEP-ANALYSIS.md`.
- Do not cite only a project name when a file exists. Prefer `magpie/DEEP-ANALYSIS.md` over “magpie”, and `hhxg-market/DEEP-ANALYSIS.md` over “hhxg”.

**Current-Project Mapping:**
- Use `HermesAlpha` and `ashare-audit` as target columns when extracting migration advice, following `10-SYNTHESIS.md`, `17-落地路线图.md`, and `16-UI-UX设计借鉴总表.md`.
- Use priority labels `P1`, `P2`, `P3` in action tables, as in `06-工程治理篇.md`, `09-Agent-协作与设计哲学篇.md`, `11-UI-UX交互设计.md`, and `15-数据底座与采集底座篇.md`.

## Error Handling

**Patterns:**
- Treat “silent graceful degradation” as a documented anti-pattern. `13-终极提炼.md` calls out `.get(g, 1.0)` hiding six defects; `18-模式决策矩阵.md` warns that “优雅降级” must not swallow structural errors.
- Use hard gates for critical data or structure failures. `06-工程治理篇.md` describes critical checks like `all_dims_exist`, `empty_dims`, `coverage_threshold`, and `agent_analysis_exists`; `uzi-skill/DEEP-ANALYSIS.md` describes refusing HTML generation when `_review_issues.json` has critical issues.
- Separate `critical`, `warning`, and `info` levels when documenting quality issues. Use the Issue fields shown in `06-工程治理篇.md` and `uzi-skill/DEEP-ANALYSIS.md`: `severity`, `category`, `dim`, `issue`, `evidence`, `suggested_fix`.
- Document error impact and next action, not only the failure. `16-UI-UX设计借鉴总表.md` states error copy should include what happened, which results are affected, and what the user can do now.
- For API/tool docs, distinguish transport success from business success. `quant-buddy-skill/DEEP-ANALYSIS.md` notes HTTP 200 does not imply business success; `privora-python-examples/DEEP-ANALYSIS.md` distinguishes public ping failure, missing token, `401`, `403`, `success=false`, and non-JSON responses.

## Logging

**Framework:** Not applicable; this is a Markdown documentation repository.

**Patterns:**
- When documenting runtime or Agent tools, require provenance fields rather than vague “logs”. Existing docs repeatedly specify `command`, `skillId`, `params`, `response_shape`, `raw_payload_hash`, `session`, `version`, `task_id`, `job_id`, `from_cache`, `source`, and `fetched_at`.
- Use `snowball-cli/DEEP-ANALYSIS.md` as the model for command-level provenance, `privora-python-examples/DEEP-ANALYSIS.md` for response-envelope provenance, `quant-buddy-skill/DEEP-ANALYSIS.md` for session/version provenance, and `17-落地路线图.md` for acceptance criteria that require tool-call traceability.
- For long-running workflows, document run artifacts and resumability. `09-Agent-协作与设计哲学篇.md` describes `runs/<timestamp_uuid>/req.json`, `state.json`, `logs/`, and `artifacts/`; `jcp/DEEP-ANALYSIS.md` describes recoverable meeting state fields.

## Comments

**When to Comment:**
- Use explanatory prose before diagrams or snippets to state why the pattern matters. Existing files usually introduce a principle, then show a table or code block, as in `15-数据底座与采集底座篇.md` and `18-模式决策矩阵.md`.
- Add “借鉴点”, “风险与改造建议”, “不该照搬的部分”, or “当前项目行动清单” sections when a pattern has migration implications.

**JSDoc/TSDoc:**
- Not applicable to this repository.
- When quoting upstream code behavior, prefer prose plus small snippets over full code dumps. `uzi-skill/DEEP-ANALYSIS.md`, `daily-stock-data/DEEP-ANALYSIS.md`, and `joinquant-skill/DEEP-ANALYSIS.md` quote only the parts needed to explain the pattern.

## Function Design

**Size:**
- Not applicable for local executable functions. For documentation sections, keep one section focused on one idea: architecture, contract, workflow, risk, migration, or conclusion.
- Deep sections may be long, but must remain navigable through numbered headings and tables. `11-UI-UX交互设计.md` and `12-剩余深度素材.md` are examples of long files that stay structured.

**Parameters:**
- When documenting APIs or tool calls, list exact required fields and constraints. Use the tool-contract table style from `quant-buddy-skill/DEEP-ANALYSIS.md` and the JSON envelope style from `privora-python-examples/DEEP-ANALYSIS.md`.
- Freeze user conditions when documenting formula/query workflows. `quant-buddy-skill/DEEP-ANALYSIS.md` explicitly forbids changing percentages, time windows, asset universes, and event definitions.

**Return Values:**
- Always document response shape when discussing APIs, CLIs, gateways, or Agent tools. Examples include `success/data/pagination` in `privora-python-examples/DEEP-ANALYSIS.md`, `csv_url` for large outputs in `quant-buddy-skill/DEEP-ANALYSIS.md`, and JSON-only CLI output in `snowball-cli/DEEP-ANALYSIS.md`.
- For reports and research outputs, document source/citation fields and data-quality indicators. `16-UI-UX设计借鉴总表.md` and `18-模式决策矩阵.md` both require citation, raw data, and data-quality visibility.

## Module Design

**Exports:**
- Treat each Markdown file as a module with a clear role. `00-INDEX.md` exports navigation, root numbered files export thematic synthesis, project `QUICK-START.md` files export orientation, and project `DEEP-ANALYSIS.md` files export evidence and detailed migration patterns.
- Avoid duplicating detailed project analysis in root synthesis files. Root files should summarize and cross-reference; detailed file paths and long workflows belong in the per-project `DEEP-ANALYSIS.md` file.

**Barrel Files:**
- `00-INDEX.md` is the barrel file for the knowledge base. Keep it synchronized with every new project directory and root synthesis file.
- `10-SYNTHESIS.md` acts as the conceptual barrel for cross-project patterns. Update it when a new pattern is general enough to influence `17-落地路线图.md` or `18-模式决策矩阵.md`.

## Quality Rules

- Prefer concrete, auditable claims over abstract praise. A useful entry names files such as `scripts/strategy_lint.py`, tables such as `alert_rules`, fields such as `schema_version`, and validation behavior such as `critical != 0` refusing output.
- Preserve uncertainty and risk. Use explicit “风险与改造建议” sections like `jcp/DEEP-ANALYSIS.md`, `hhxg-market/DEEP-ANALYSIS.md`, `magpie/DEEP-ANALYSIS.md`, and `snowball-cli/DEEP-ANALYSIS.md`.
- Mark non-production or incomplete capabilities clearly. `privora-python-examples/QUICK-START.md` and `privora-python-examples/DEEP-ANALYSIS.md` call out quickstart-only and coming-soon areas.
- Use `critical` hard gates for structural errors, `warning` for degraded or partial data, and visible date/cache/source labels for static snapshots.
- For financial AI and Agent tools, always document authentication, scope, data source, cache/date state, response shape, and audit trail when they are relevant.

---

*Convention analysis: 2026-07-09*
