# Repository Guidelines

## Project Structure & Module Organization

This repository is a Markdown research library for AI and finance open-source projects. Core knowledge documents live under `docs/`: `docs/00-INDEX.md` is the entry point, `docs/06`-`docs/16` contain thematic analyses, and `docs/17`-`docs/22` contain plans, decisions, verification, evaluation, and the workbench PRD. Each project directory contains `QUICK-START.md` and `DEEP-ANALYSIS.md`. Cloned upstream repositories live under `src/` and are evidence snapshots, not modules of this repository. The reusable synchronization workflow is in `.codex/skills/github-project-docs/`; OpenCode discovers the same skill through `agents/skills`.

## Build, Test, and Development Commands

There is no single application build. Use the following checks from the repository root:

```bash
python3 agents/skills/github-project-docs/scripts/sync_research.py --all --dry-run
python3 docs-site/scripts/sync_content.py
hugo --source docs-site --minify
git diff --check
```

Use `--all --pull --update-doc-metadata` to fetch clean, fast-forwardable source repositories and refresh managed source metadata. Use `--add OWNER/REPO --pull --update-doc-metadata` for a new project. Review `.planning/source-sync.md` before editing analysis prose.

## Coding Style & Naming Conventions

Documentation is UTF-8 Markdown. Keep headings descriptive, use relative links, and preserve the existing numbered top-level filenames. Project directories use lowercase kebab-case where possible; use `QUICK-START.md` and `DEEP-ANALYSIS.md` exactly. Python scripts use 4-space indentation, type hints, `snake_case` names, and standard-library dependencies unless a dependency is necessary.

## Testing Guidelines

There is no central test framework for the documentation library. Every source-sync change should pass the dry-run mapping check and `git diff --check`; Hugo content generation and site build should also succeed. For document changes, verify both project files exist, links resolve, source commit metadata is present, and `docs/00-INDEX.md` has no orphaned entries. Do not treat an upstream README as source verification; inspect the relevant code and call paths.

## Commit & Pull Request Guidelines

Existing commits use concise Conventional Commit-style subjects such as `docs: initialize AI finance research library.` and `docs: add DEEP-ANALYSIS + QUICK-START ...`. Use `docs:`, `feat:`, `fix:`, or `chore:` with a specific summary. Pull requests should describe affected projects, source commits, changed evidence, validation commands, and any updated cross-project conclusions. Do not include secrets, tokens, cookies, private paths, or generated dependency trees.

## Source and Evidence Rules

Record the upstream URL, exact commit, analysis date, limitations, and unverified items. Separate verified code facts, cross-project patterns, and current recommendations. Update thematic or decision documents only when the new evidence changes a cross-project conclusion.
