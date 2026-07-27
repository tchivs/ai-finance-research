# Codebase Concerns

**Analysis Date:** 2026-07-10

## Tech Debt

**Manual repository catalog as single source of truth:**
- Issue: `00-INDEX.md` manually tracks 40 project directories, 80 project links, root topic docs, reading routes, and current-project borrowing priorities without an automated consistency check.
- Files: `00-INDEX.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/TESTING.md`
- Impact: New dossiers, renamed directories, or removed project docs can drift away from the index and become invisible to readers and GSD agents.
- Fix approach: Add a documentation validation script that compares filesystem directories against `00-INDEX.md`, checks every `<project>/QUICK-START.md` and `<project>/DEEP-ANALYSIS.md` pair, and fails on unindexed or orphaned documents.

**Inconsistent provenance header style:**
- Issue: Most project dossiers place `> 源码: ...` near the top, but seven project docs do not include a local source snapshot pointer in the opening block and instead use GitHub URL/version metadata or no source block.
- Files: `agent-reach/QUICK-START.md`, `ai-berkshire/QUICK-START.md`, `daily-stock-analysis/QUICK-START.md`, `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`, `uzi-skill/QUICK-START.md`, `vibe-trading/QUICK-START.md`
- Impact: Source freshness, reproducibility, and cross-document evidence strength vary by dossier, making it harder to know which snapshot each analysis was extracted from.
- Fix approach: Standardize every project doc header with upstream URL, local snapshot path or sanitized source ID, extraction date, and commit/tag when available.

**Absolute local paths embedded throughout the corpus:**
- Issue: The corpus contains many absolute workspace paths such as upstream snapshots under `/root/source/tmp/*`, current-project examples under `/root/source/HermesAlpha`, and repository paths under `/root/source/docs/aaa`.
- Files: `10-SYNTHESIS.md`, `17-落地路线图.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STACK.md`, `.planning/codebase/INTEGRATIONS.md`, project dossiers such as `quantdinger/QUICK-START.md`, `jcp/QUICK-START.md`, `privora-python-examples/QUICK-START.md`
- Impact: Absolute paths are useful for the current workstation but leak local layout, fail on other machines, and become stale when snapshots move.
- Fix approach: Keep absolute paths out of reader-facing guidance where possible; prefer sanitized provenance IDs or upstream URLs, and reserve local paths for generated maps marked as environment-specific.

**Large synthesis files accumulate many responsibilities:**
- Issue: Several files are long and mix evidence, recommendations, examples, and migration guidance in one document, including `tickflow-stock-panel/DEEP-ANALYSIS.md` at 731 lines, `quantdinger/DEEP-ANALYSIS.md` at 659 lines, `11-UI-UX交互设计.md` at 529 lines, and `uzi-skill/DEEP-ANALYSIS.md` at 489 lines.
- Files: `tickflow-stock-panel/DEEP-ANALYSIS.md`, `quantdinger/DEEP-ANALYSIS.md`, `11-UI-UX交互设计.md`, `uzi-skill/DEEP-ANALYSIS.md`
- Impact: Agents and humans must load large documents to extract narrow facts, increasing context cost and making localized updates risky.
- Fix approach: Add generated tables of contents and stable section anchors; split only when a section has a clear ownership boundary such as architecture, risk, contract, or migration notes.

## Known Bugs

No currently confirmed broken local Markdown links, incomplete dossier pairs, or stale line-count annotations remain after the 2026-07-10 documentation refresh. Automated regression checks are still missing, so these conditions can recur.

## Security Considerations

**Sensitive path leakage risk from absolute source paths:**
- Risk: Absolute paths expose workstation layout and source snapshot locations, including `/root/source/tmp/*`, `/root/source/HermesAlpha`, `/root/source/aaa`, and `/root/source/docs/aaa`.
- Files: `10-SYNTHESIS.md`, `17-落地路线图.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STACK.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/codebase/TESTING.md`, project dossiers such as `jcp/DEEP-ANALYSIS.md`, `quantdinger/QUICK-START.md`, `daily-stock-analysis/DEEP-ANALYSIS.md`
- Current mitigation: `15-数据底座与采集底座篇.md`, `daily-stock-data/QUICK-START.md`, and `.planning/codebase/TESTING.md` explicitly document private-path leak checks as a required practice.
- Recommendations: Add a local denylist scanner for absolute home/workspace paths and require an explicit allowlist for intentional provenance paths.

**Token and authentication examples need continuous secret scanning:**
- Risk: The docs discuss Bearer tokens, cookie auth, API keys, provider env vars, gateway scopes, and auth storage patterns; future edits can accidentally paste real secrets into example sections.
- Files: `privora-python-examples/QUICK-START.md`, `privora-python-examples/DEEP-ANALYSIS.md`, `snowball-cli/QUICK-START.md`, `snowball-cli/DEEP-ANALYSIS.md`, `.planning/codebase/INTEGRATIONS.md`, `16-UI-UX设计借鉴总表.md`
- Current mitigation: No `.env*` files are present under `/root/source/docs/aaa`, and existing examples use placeholders or variable names rather than detected live secret files.
- Recommendations: Add a scanner for token-shaped values, cookie strings, private keys, `.env*` files, and auth headers before publishing or committing generated docs.

**Generated planning artifacts can amplify sensitive metadata:**
- Risk: `.planning/codebase/*.md` summarizes absolute paths, external auth concepts, env var names, provider names, and local repository shape; generated artifacts can spread sensitive context farther than the source docs.
- Files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STACK.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/CONCERNS.md`
- Current mitigation: Generated docs state that no local secrets or `.env*` files are detected.
- Recommendations: Run the same private-path and secret checks against `.planning/codebase/*.md` as against root docs and project dossiers.

## Performance Bottlenecks

**Manual full-corpus review is the only validation path:**
- Problem: The repository has 106 Markdown files and no local validation command, CI workflow, Markdown linter, link checker, or manifest-driven inventory.
- Files: `.planning/codebase/TESTING.md`, `.planning/codebase/CONVENTIONS.md`, `00-INDEX.md`
- Cause: The repo is a static knowledge base with no `package.json`, `pyproject.toml`, `.github/workflows/*`, or local executable check script.
- Improvement path: Add a lightweight script that validates links, project pairs, source headers, stale line counts, path leakage, and basic Markdown structure in one run.

**Large dossier files increase context and diff cost:**
- Problem: Large files such as `tickflow-stock-panel/DEEP-ANALYSIS.md`, `quantdinger/DEEP-ANALYSIS.md`, and `11-UI-UX交互设计.md` require broad reads for narrow updates.
- Files: `tickflow-stock-panel/DEEP-ANALYSIS.md`, `quantdinger/DEEP-ANALYSIS.md`, `11-UI-UX交互设计.md`, `12-剩余深度素材.md`
- Cause: Each document mixes architecture, implementation references, risks, migration advice, and conclusions without a generated anchor index.
- Improvement path: Add section anchors and a short local table of contents for any Markdown file over roughly 300 lines.

## Fragile Areas

**`00-INDEX.md` barrel-file edits:**
- Files: `00-INDEX.md`
- Why fragile: The file owns goal-based reading routes, topic summaries, 40 project rows, and 80 internal project links.
- Safe modification: Update `00-INDEX.md` together with filesystem changes and run an index validator that confirms every project row has both standard links.
- Test coverage: No automated duplicate-row, missing-link, project-count, or stale-line-count check exists.

**Cross-synthesis recommendation chain:**
- Files: `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`, `06-工程治理篇.md`, `15-数据底座与采集底座篇.md`, `16-UI-UX设计借鉴总表.md`
- Why fragile: These files convert project-specific observations into current-project defaults; a stronger claim in a synthesis file can outpace the evidence in the corresponding project dossier.
- Safe modification: When changing a recommendation, cite the source dossier and update the decision matrix if the recommendation affects interface, storage, Agent orchestration, UI, real-time, audit, strategy, or signal choices.
- Test coverage: No claim-to-source consistency checker or required citation format exists.

**Project dossier provenance:**
- Files: `agent-reach/QUICK-START.md`, `ai-berkshire/QUICK-START.md`, `daily-stock-analysis/QUICK-START.md`, `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`, `uzi-skill/QUICK-START.md`, `vibe-trading/QUICK-START.md`
- Why fragile: Missing or inconsistent source headers make future refreshes depend on memory or search rather than a stable provenance block.
- Safe modification: Add a standard provenance block before expanding these docs, then keep the same block in all future `QUICK-START.md` and `DEEP-ANALYSIS.md` files.
- Test coverage: No source-header checker exists.

**Generated planning context:**
- Files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/STACK.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/CONCERNS.md`
- Why fragile: GSD commands consume these docs as current context, but generated maps can become stale independently from the root corpus.
- Safe modification: Treat `.planning/codebase/*.md` as a coherent generated set; refresh related maps after structural, stack, quality, or concern changes.
- Test coverage: No generated-doc freshness marker or source-hash check exists.

## Scaling Limits

**Two-file dossier model scales linearly into index maintenance:**
- Current capacity: 40 project directories and 80 standard dossier files are present and complete.
- Limit: Every added project requires updates to `00-INDEX.md`, relevant root topic docs, `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`, and generated planning docs.
- Scaling path: Add project metadata front matter or a machine-readable manifest that generates project inventory, links, counts, and provenance summaries.

**Absolute source snapshot paths do not scale across machines:**
- Current capacity: 95 `/root/source/tmp/*` source references are present across the corpus, with 43 unique snapshot paths.
- Limit: The docs cannot verify whether those snapshots exist, match the analyzed version, or are available outside this workstation.
- Scaling path: Store upstream URL, commit hash, tag, or archive ID beside any local snapshot path; make local paths optional implementation notes rather than canonical provenance.

**Static Markdown has no change provenance:**
- Current capacity: `/root/source/docs/aaa` is not detected as a git repository in this workspace, and `.planning/codebase/STRUCTURE.md` records generated artifacts as not committed.
- Limit: Large generated or manual changes cannot be tied to commits, authors, or source-refresh events inside this folder.
- Scaling path: Keep this corpus in a versioned repository or maintain a refresh log that records source snapshot, extraction date, mapper focus, and generated docs updated.

## Dependencies at Risk

**Upstream source snapshots:**
- Risk: Dossier evidence depends on external source trees under `/root/source/tmp/*`, but no freshness check confirms those directories, commits, or contents still match the documentation.
- Impact: Implementation agents can copy patterns from stale or moved upstream code.
- Migration plan: Add a provenance manifest with upstream URL, commit/tag, local snapshot path, and last refresh date for each project dossier.

**External API and auth behavior references:**
- Risk: Provider behavior, gateway response shapes, token scopes, cookie flows, and API endpoints can change outside this repository.
- Impact: Docs such as `privora-python-examples/DEEP-ANALYSIS.md`, `snowball-cli/DEEP-ANALYSIS.md`, `wudao-mcp/QUICK-START.md`, and `.planning/codebase/INTEGRATIONS.md` can guide future implementation toward outdated auth or response assumptions.
- Migration plan: Mark volatile provider/API sections with source version or verification date, and add a refresh checklist for live API examples.

**Generated GSD context:**
- Risk: `.planning/codebase/*.md` is consumed by later planning and execution commands, but stale entries can quietly steer work to outdated paths or constraints.
- Impact: Downstream GSD phases can miss `CONCERNS.md`, rely on incomplete structure maps, or repeat known broken-link patterns.
- Migration plan: Regenerate all codebase maps after corpus structure changes and include a generated-at date plus source inventory count in each file.

## Missing Critical Features

**Local documentation validation command:**
- Problem: No local script or CI job validates Markdown links, project counts, source headers, stale counts, forbidden paths, or generated map freshness.
- Blocks: Reliable incremental remaps, safe project additions, and automated pre-commit/publish checks.
- Files: `.planning/codebase/TESTING.md`, `.planning/codebase/CONVENTIONS.md`, `00-INDEX.md`

**Provenance manifest:**
- Problem: Source provenance is embedded in prose and varies by file instead of living in a normalized manifest.
- Blocks: Source freshness checks, automated refresh workflows, and machine-readable “which upstream commit produced this doc” answers.
- Files: `jcp/QUICK-START.md`, `quantdinger/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`, `agent-reach/QUICK-START.md`, `vibe-trading/QUICK-START.md`

**Secret and private-path scanner:**
- Problem: The repository documents the need for private-path and secret leakage checks but does not implement them locally.
- Blocks: Safe publication of docs containing auth examples, local source paths, provider env var names, and generated planning summaries.
- Files: `daily-stock-data/QUICK-START.md`, `15-数据底座与采集底座篇.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/INTEGRATIONS.md`

**Generated map freshness check:**
- Problem: `.planning/codebase/ARCHITECTURE.md` and `.planning/codebase/STRUCTURE.md` were refreshed on 2026-07-10, but no automated check proves they remain synchronized with the source corpus.
- Blocks: Trustworthy GSD planning and execution context.
- Files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/CONCERNS.md`

**Terminology and contract consistency check:**
- Problem: Important terms such as `schema_version`, `from_cache`, `skillId`, `response_shape`, `task_id`, `data_id`, `raw_payload_hash`, and `paper_only` appear across many docs without a local glossary or consistency checker.
- Blocks: Consistent implementation of audit envelopes, data contracts, and UI trust states.
- Files: `06-工程治理篇.md`, `15-数据底座与采集底座篇.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`, `.planning/codebase/TESTING.md`

**Upstream limitation guards:**
- Problem: Some source-project docs explicitly describe incomplete upstream features or placeholders, but there is no local mechanism preventing those patterns from being treated as production-ready implementation guidance.
- Blocks: Safe reuse of `joinquant-skill` research-importer output, `privora-python-examples` quickstart examples, and `tickflow-stock-panel` monitor/pipeline patterns.
- Files: `joinquant-skill/QUICK-START.md`, `joinquant-skill/DEEP-ANALYSIS.md`, `privora-python-examples/QUICK-START.md`, `privora-python-examples/DEEP-ANALYSIS.md`, `tickflow-stock-panel/DEEP-ANALYSIS.md`

## Test Coverage Gaps

**Index integrity:**
- What's not tested: `00-INDEX.md` project rows, project count text, and 74 standard project links.
- Files: `00-INDEX.md`
- Risk: Project additions or edits create stale navigation and misleading metadata.
- Priority: High

**Dossier pairing and source headers:**
- What's not tested: Every project directory containing exactly `QUICK-START.md` and `DEEP-ANALYSIS.md`, plus a consistent provenance block in both files.
- Files: `agent-reach/QUICK-START.md`, `ai-berkshire/QUICK-START.md`, `daily-stock-analysis/QUICK-START.md`, `daily-stock-data/QUICK-START.md`, `daily-stock-data/DEEP-ANALYSIS.md`, `uzi-skill/QUICK-START.md`, `vibe-trading/QUICK-START.md`
- Risk: Future dossiers can be incomplete or untraceable even while matching the rough directory shape.
- Priority: High

**Internal link checking:**
- What's not tested: Relative Markdown links outside `00-INDEX.md`, especially generated docs under `.planning/codebase/`.
- Files: `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`
- Risk: Broken links reach planning agents and rendered documentation unnoticed.
- Priority: High

**Generated planning artifact freshness:**
- What's not tested: Whether `.planning/codebase/*.md` inventories match actual generated files and current source corpus counts.
- Files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/STACK.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/TESTING.md`, `.planning/codebase/CONCERNS.md`
- Risk: GSD commands consume stale repository maps.
- Priority: High

**Sensitive metadata leakage:**
- What's not tested: Absolute private paths, token-shaped values, auth headers, cookie strings, `.env*` files, private keys, local dumps, and generated-doc leakage.
- Files: `privora-python-examples/QUICK-START.md`, `snowball-cli/DEEP-ANALYSIS.md`, `15-数据底座与采集底座篇.md`, `.planning/codebase/INTEGRATIONS.md`
- Risk: Documentation publication leaks local environment details or real credentials introduced by future edits.
- Priority: High

**Markdown structure and formatting:**
- What's not tested: Table separators, closed fenced blocks, heading order, duplicate headings, and rendering-safe examples.
- Files: `jcp/DEEP-ANALYSIS.md`, `11-UI-UX交互设计.md`, `12-剩余深度素材.md`, `tickflow-stock-panel/DEEP-ANALYSIS.md`
- Risk: Rendered docs and automated parsers diverge from what authors intended.
- Priority: Medium

**Claim-to-source consistency:**
- What's not tested: Whether recommendations in synthesis and roadmap docs cite concrete project evidence and avoid treating incomplete upstream features as mature patterns.
- Files: `10-SYNTHESIS.md`, `17-落地路线图.md`, `18-模式决策矩阵.md`, `joinquant-skill/DEEP-ANALYSIS.md`, `privora-python-examples/DEEP-ANALYSIS.md`, `tickflow-stock-panel/DEEP-ANALYSIS.md`
- Risk: Future implementation plans inherit overconfident or stale guidance from synthesis docs.
- Priority: Medium

---

*Concerns audit: 2026-07-10*
