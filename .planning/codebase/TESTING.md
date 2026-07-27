# Testing Patterns

**Analysis Date:** 2026-07-09

## Test Framework

**Runner:**
- Not detected for this repository. `/root/source/docs/aaa` is a Markdown-only documentation/knowledge-base repo with files such as `00-INDEX.md`, `10-SYNTHESIS.md`, and per-project pairs like `uzi-skill/QUICK-START.md` and `uzi-skill/DEEP-ANALYSIS.md`.
- No `package.json`, `pytest.ini`, `vitest.config.ts`, `jest.config.*`, GitHub Actions workflow, or executable source files were detected in `/root/source/docs/aaa`.
- The repository documents automated testing patterns from analyzed projects in `12-剩余深度素材.md`, but it does not implement those test suites locally.

**Assertion Library:**
- Not detected locally.
- Manual assertions are expressed as documentation rules, acceptance criteria, quality gates, checklists, and audit fields in files such as `06-工程治理篇.md`, `12-剩余深度素材.md`, `17-落地路线图.md`, and `18-模式决策矩阵.md`.

**Run Commands:**
```bash
rg --files -g '*.md' /root/source/docs/aaa                 # Inventory Markdown files
rg -n 'TODO|FIXME|HACK|XXX|待补充|占位' /root/source/docs/aaa # Find obvious unfinished markers
rg -n '\[→\]\([^)]+\)' /root/source/docs/aaa/00-INDEX.md   # Review index links
rg -n 'schema_version|from_cache|response_shape|scope|critical|warning' /root/source/docs/aaa # Spot validation terms
```

## Test File Organization

**Location:**
- No local test directory exists under `/root/source/docs/aaa`.
- Validation knowledge is embedded in root synthesis docs: `06-工程治理篇.md` for quality gates, `12-剩余深度素材.md` for testing/CI patterns, `13-终极提炼.md` for bug-regression logging, `17-落地路线图.md` for acceptance criteria, and `18-模式决策矩阵.md` for anti-pattern checks.
- Project-specific validation patterns are documented in `uzi-skill/DEEP-ANALYSIS.md`, `daily-stock-data/DEEP-ANALYSIS.md`, `joinquant-skill/DEEP-ANALYSIS.md`, `quant-buddy-skill/DEEP-ANALYSIS.md`, `hhxg-market/DEEP-ANALYSIS.md`, and `privora-python-examples/DEEP-ANALYSIS.md`.

**Naming:**
- Local docs use `QUICK-START.md` and `DEEP-ANALYSIS.md`, not `*.test.*` or `*.spec.*` files.
- Referenced upstream test naming is documented in `12-剩余深度素材.md`: version/issue-oriented files such as `tests/test_v2_10_4_fixes.py`, `tests/test_v3_5_0_school_lock.py`, `tests/test_v3_9_1_toc_collapse.py`, and `tests/test_no_regressions.py`.

**Structure:**
```text
/root/source/docs/aaa/
├── 00-INDEX.md                         # Manual navigation/link validation target
├── 06-工程治理篇.md                       # Quality gate and self-check reference
├── 12-剩余深度素材.md                     # Test/CI/release validation reference
├── 13-终极提炼.md                         # BUGS-LOG and regression documentation reference
├── 17-落地路线图.md                       # Acceptance criteria reference
├── 18-模式决策矩阵.md                     # Anti-pattern and decision validation reference
└── <project>/
    ├── QUICK-START.md                   # Quick orientation; validate positioning and migration points
    └── DEEP-ANALYSIS.md                 # Evidence, contracts, risks, and detailed validation patterns
```

## Test Structure

**Suite Organization:**
```markdown
## Manual Documentation Review

- [ ] `00-INDEX.md` lists the project directory and both standard documents.
- [ ] `PROJECT/QUICK-START.md` states one-sentence positioning, core workflow/modules, migration points, and risks.
- [ ] `PROJECT/DEEP-ANALYSIS.md` includes upstream source path, architecture, contracts, validation rules, risks, and conclusion.
- [ ] Root synthesis files mention the new pattern only if it generalizes beyond one project.
- [ ] All file paths, commands, fields, and schema names are wrapped in backticks.
- [ ] Claims about quality gates include severity, evidence, impact, and fix or migration approach.
```

**Patterns:**
- Setup pattern: start at `00-INDEX.md`, then read the relevant root topic files such as `06-工程治理篇.md`, `12-剩余深度素材.md`, `15-数据底座与采集底座篇.md`, and `18-模式决策矩阵.md` before editing per-project docs.
- Review pattern: compare `QUICK-START.md` and `DEEP-ANALYSIS.md` for the same project so positioning, risks, and migration points do not contradict each other. Example pairs include `daily-stock-data/QUICK-START.md` with `daily-stock-data/DEEP-ANALYSIS.md`, and `joinquant-skill/QUICK-START.md` with `joinquant-skill/DEEP-ANALYSIS.md`.
- Assertion pattern: document exact fields or rules, not only outcomes. `privora-python-examples/DEEP-ANALYSIS.md` asserts `data` is an array and `pagination` is top-level; `quant-buddy-skill/DEEP-ANALYSIS.md` asserts `data_id` is for `readData` and `expression_id` is not.
- Regression pattern: when a defect or trap is documented, include future modification guidance. `13-终极提炼.md` defines the expected bug-entry fields: `症状`, `位置`, `根因`, `影响`, `修法`, `验证`, `回归测试`, and `未来改该区域注意事项`.

## Mocking

**Framework:** Not applicable locally.

**Patterns:**
```markdown
Manual equivalent of mocking:

1. Treat upstream source snippets in `PROJECT/DEEP-ANALYSIS.md` as reference evidence, not executable local fixtures.
2. Mark whether a referenced behavior is directly implemented upstream, only a migration suggestion, or a current-project acceptance criterion.
3. Do not claim `/root/source/docs/aaa` runs a command, test, API, or linter unless a local executable/config exists.
```

**What to Mock:**
- For future automated documentation checks, use synthetic project directories with `QUICK-START.md` and `DEEP-ANALYSIS.md` to verify index-link and structure checks.
- For future validation of API/tool documentation, use small sample envelopes like the `skillId` example in `privora-python-examples/DEEP-ANALYSIS.md` and the tool-contract fields in `quant-buddy-skill/DEEP-ANALYSIS.md`.

**What NOT to Mock:**
- Do not fake upstream test results. `12-剩余深度素材.md` describes UZI-Skill, daily_stock_analysis, Vibe-Trading, and other projects; those tests are reference material, not local passing tests.
- Do not invent source paths. If a file path is not present in a project doc, write “Not detected” rather than filling a plausible name.
- Do not mock secrets, tokens, cookies, or environment values. `snowball-cli/DEEP-ANALYSIS.md` and `privora-python-examples/DEEP-ANALYSIS.md` document token boundaries; local docs must never include token values.

## Fixtures and Factories

**Test Data:**
```json
{
  "skillId": "dataasset.data.get",
  "required_scopes": ["dataasset.data.get"],
  "pathParams": {"id": 123},
  "query": {
    "filter_column": "stock_num",
    "filter_op": "eq",
    "filter_value": "600519"
  },
  "response_shape": {
    "success": "boolean",
    "data": "array",
    "totalElements": "number"
  },
  "sensitive": false
}
```

**Location:**
- Example schemas and data-contract snippets live inline in documentation files rather than fixture files. Use `privora-python-examples/DEEP-ANALYSIS.md` for skill-gateway envelopes, `jcp/DEEP-ANALYSIS.md` for Moderator contracts, `quant-buddy-skill/DEEP-ANALYSIS.md` for tool-contract fields, and `hhxg-market/DEEP-ANALYSIS.md` for static snapshot fields.
- The local repo has no `fixtures/`, `tests/fixtures/`, or generated validation data directory.

## Coverage

**Requirements:** None enforced by tooling.

**View Coverage:**
```bash
rg --files -g '*.md' /root/source/docs/aaa | wc -l          # Count docs under review
rg -n 'QUICK-START.md|DEEP-ANALYSIS.md' /root/source/docs/aaa/00-INDEX.md # Check index coverage
rg -n '风险与改造建议|不该照搬|结论|当前项目行动清单' /root/source/docs/aaa # Check recurring review sections
```

**Manual Coverage Targets:**
- `00-INDEX.md` should list every project directory and both standard files.
- Each project directory such as `jcp/`, `magpie/`, `hhxg-market/`, `snowball-cli/`, and `privora-python-examples/` should contain `QUICK-START.md` and `DEEP-ANALYSIS.md`.
- Every root topic file should have a distinct ownership area: quality in `06-工程治理篇.md`, strategy in `07-策略与信号系统篇.md`, data pipelines in `08-数据采集与流水线篇.md`, Agent collaboration in `09-Agent-协作与设计哲学篇.md`, UI in `11-UI-UX交互设计.md` and `16-UI-UX设计借鉴总表.md`, data foundations in `15-数据底座与采集底座篇.md`, roadmap in `17-落地路线图.md`, and decisions in `18-模式决策矩阵.md`.
- Cross-project recommendations in `10-SYNTHESIS.md`, `17-落地路线图.md`, and `18-模式决策矩阵.md` should trace back to concrete project files like `uzi-skill/DEEP-ANALYSIS.md`, `daily-stock-data/DEEP-ANALYSIS.md`, `quant-buddy-skill/DEEP-ANALYSIS.md`, or `joinquant-skill/DEEP-ANALYSIS.md`.

## Test Types

**Unit Tests:**
- Not used locally. No executable units exist in `/root/source/docs/aaa`.
- Unit-test patterns from analyzed projects are documented in `12-剩余深度素材.md`, including UZI-Skill versioned regression tests and Vibe-Trading Vitest component tests.

**Integration Tests:**
- Not used locally.
- Integration-style validation is documented as concepts: daily_stock_analysis CI gates in `12-剩余深度素材.md`, Privora public ping/token/scope flow in `privora-python-examples/DEEP-ANALYSIS.md`, and hhxg-market static snapshot schema/date/cache checks in `hhxg-market/DEEP-ANALYSIS.md`.

**E2E Tests:**
- Not used locally.
- E2E-style UI and workflow patterns are reference material only, described in `11-UI-UX交互设计.md`, `16-UI-UX设计借鉴总表.md`, and `12-剩余深度素材.md`.

**Documentation Validation:**
- Link validation: manually check `00-INDEX.md` links to each `QUICK-START.md` and `DEEP-ANALYSIS.md`.
- Structure validation: ensure new project docs follow the quick/deep split and include source path, risks, migration points, and conclusion.
- Consistency validation: verify that `10-SYNTHESIS.md`, `17-落地路线图.md`, and `18-模式决策矩阵.md` do not make stronger claims than the per-project evidence supports.
- Quality vocabulary validation: ensure terms like `critical`, `warning`, `schema_version`, `from_cache`, `scope`, `response_shape`, `paper_only`, and `raw_payload_hash` are used consistently with their source docs.

## Common Patterns

**Async Testing:**
```text
Reference pattern only:

submit job / start stream
    -> capture task_id or job_id
    -> stream progress events
    -> on interruption, resume with Last-Event-ID, trace_id, or task_id
    -> verify final result and audit trail
```

- This pattern is documented in `quant-buddy-skill/DEEP-ANALYSIS.md` for SSE/resume, `11-UI-UX交互设计.md` for `useSSE` reconnect/dedup/resume behavior, and `17-落地路线图.md` for job stream acceptance criteria.
- Local documentation checks should verify that async or long-running workflows mention state, resume behavior, failure categories, and final artifacts.

**Error Testing:**
```text
Manual review pattern:

1. Identify the failure class: critical, warning, info, transport, auth, scope, schema, cache, or data-quality.
2. Confirm the doc states the trigger condition.
3. Confirm the doc states user-visible symptoms or affected output.
4. Confirm the doc states mitigation, retry, recovery, or explicit limitation.
5. Confirm the doc does not hide structural failures behind graceful degradation.
```

- Use `06-工程治理篇.md` for severity and self-review fields.
- Use `13-终极提炼.md` for regression-entry expectations and anti-silent-degradation guidance.
- Use `privora-python-examples/DEEP-ANALYSIS.md` for auth/scope/API response error categories.
- Use `hhxg-market/DEEP-ANALYSIS.md` for schema/date/cache error checks.
- Use `magpie/DEEP-ANALYSIS.md` for alert-rule smoke testing via synthetic `test-fire`.

## Manual Review Checklist

```markdown
## Content Integrity
- [ ] The document names the exact project files it relies on, such as `scripts/strategy_lint.py` or `src/engine.ts`.
- [ ] The document distinguishes implemented upstream behavior from migration advice for HermesAlpha or ashare-audit.
- [ ] Every critical recommendation has source evidence in a project doc or numbered root synthesis doc.

## Structure
- [ ] One H1 only.
- [ ] Headings follow a clear numbered or thematic sequence.
- [ ] Tables have header separators and consistent columns.
- [ ] Fenced code blocks are closed and use an appropriate language tag.

## Quality Gates
- [ ] Hard gates are named when structural failures must block output.
- [ ] Warnings and degraded data include date/source/cache/scope context.
- [ ] Agent or tool actions include provenance fields, not only final natural-language output.

## Repository Hygiene
- [ ] No token, cookie, secret, local dump, or private environment value is included.
- [ ] Internal links in `00-INDEX.md` resolve to actual files.
- [ ] New directories follow the two-file `QUICK-START.md` / `DEEP-ANALYSIS.md` convention.
```

## Validation Gaps

- No automated Markdown formatter or linter is configured for `/root/source/docs/aaa`.
- No automated internal link checker validates `00-INDEX.md` links.
- No CI checks for table formatting, heading order, duplicate project rows, or stale root synthesis references.
- No automated source freshness check verifies that upstream paths like `/root/source/tmp/joinquant-skill/` or `/root/source/tmp/privora-python-examples/` still match the documentation.
- No automated secret/private-path scanner is configured locally, even though the need for private-leak checks is documented in `daily-stock-data/DEEP-ANALYSIS.md` and `15-数据底座与采集底座篇.md`.
- No automated terminology consistency check enforces fields such as `schema_version`, `from_cache`, `skillId`, `response_shape`, `task_id`, and `raw_payload_hash`.

---

*Testing analysis: 2026-07-09*
