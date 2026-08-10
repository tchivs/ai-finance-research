#!/usr/bin/env python3
"""Pull source repositories and record the evidence baseline for the docs library."""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = ROOT / "src"
DOC_ROOT = ROOT
KNOWLEDGE_ROOT = ROOT / "docs"
PLAN_ROOT = ROOT / ".planning"
INDEX_PATH = KNOWLEDGE_ROOT / "00-INDEX.md"
START_MARKER = "<!-- source-sync:start -->"
END_MARKER = "<!-- source-sync:end -->"
INDEX_START_MARKER = "<!-- github-project-docs:index:start -->"
INDEX_END_MARKER = "<!-- github-project-docs:index:end -->"
CHANGE_START_MARKER = "<!-- source-sync:changes:start -->"
CHANGE_END_MARKER = "<!-- source-sync:changes:end -->"
METADATA_PREFIXES = (
    "> 上游项目：",
    "> 分析基线：",
    "> 分析日期：",
    "> 本地源码目录：",
    "> 本地源码：",
)


@dataclasses.dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclasses.dataclass
class SourceRepo:
    name: str
    path: Path
    remote: str
    branch: str
    upstream: str
    head: str
    head_short: str
    dirty: bool


def run_git(repo: Path, *args: str, timeout: int = 180) -> CommandResult:
    command = [
        "git",
        "-c",
        f"safe.directory={repo}",
        "-C",
        str(repo),
        *args,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandResult(1, "", str(exc))
    return CommandResult(result.returncode, result.stdout.strip(), result.stderr.strip())


def run_clone(url: str, destination: Path, timeout: int = 900) -> CommandResult:
    try:
        result = subprocess.run(
            ["git", "clone", url, str(destination)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandResult(1, "", str(exc))
    return CommandResult(result.returncode, result.stdout.strip(), result.stderr.strip())


def git_value(repo: Path, *args: str) -> str:
    result = run_git(repo, *args)
    return result.stdout if result.returncode == 0 else ""


def working_tree_dirty(repo: Path) -> bool:
    """Ignore the local codebase-memory artifact when checking source changes."""
    status = git_value(repo, "status", "--porcelain")
    for line in status.splitlines():
        path = line[3:].strip().strip('"') if len(line) >= 3 else ""
        if path == ".codebase-memory" or path.startswith(".codebase-memory/"):
            continue
        return True
    return False


def canonical_repo_url(value: str) -> str:
    value = value.strip().rstrip(".,;`)")
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    parsed = urlsplit(value)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return ""
    path = parsed.path.strip("/").removesuffix(".git")
    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        return ""
    return f"github.com/{parts[0].lower()}/{parts[1].lower()}"


def parse_add_spec(spec: str) -> tuple[str, str]:
    """Return (source directory, clone URL) for URL, OWNER/REPO, or NAME=URL."""
    raw = spec.strip()
    custom_name = ""
    if "=" in raw:
        custom_name, raw = raw.split("=", 1)
        custom_name = re.sub(r"[^A-Za-z0-9._-]+", "-", custom_name).strip("-._")
        if not custom_name:
            raise SystemExit(f"Invalid project directory in --add: {spec}")
    candidate = raw.strip().rstrip("/")
    if candidate.startswith("github.com/"):
        candidate = "https://" + candidate
    elif re.fullmatch(r"[^/\s]+/[^\s/]+", candidate):
        candidate = "https://github.com/" + candidate
    repo_key = canonical_repo_url(candidate)
    if not repo_key:
        raise SystemExit(
            f"Invalid GitHub project: {spec}. Use https://github.com/OWNER/REPO, OWNER/REPO, or NAME=https://github.com/OWNER/REPO"
        )
    repo_name = repo_key.rsplit("/", 1)[1]
    return custom_name or repo_name, candidate


def add_sources(specs: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    additions: list[dict[str, str]] = []
    added_names: list[str] = []
    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        local_candidate = SOURCE_ROOT / spec.strip()
        if (
            "=" not in spec
            and "//" not in spec
            and "/" not in spec
            and local_candidate.is_dir()
            and (local_candidate / ".git").exists()
        ):
            current_remote = git_value(local_candidate, "remote", "get-url", "origin")
            additions.append(
                {
                    "spec": spec,
                    "source_dir": local_candidate.name,
                    "remote": current_remote,
                    "status": "already_present",
                }
            )
            added_names.append(local_candidate.name)
            continue
        name, url = parse_add_spec(spec)
        destination = SOURCE_ROOT / name
        record = {"spec": spec, "source_dir": name, "remote": url, "status": ""}
        if destination.exists():
            if not (destination / ".git").exists():
                record["status"] = "failed"
                record["error"] = f"destination exists and is not a Git repository: {destination}"
                additions.append(record)
                continue
            current_remote = git_value(destination, "remote", "get-url", "origin")
            if canonical_repo_url(current_remote) != canonical_repo_url(url):
                record["status"] = "failed"
                record["error"] = f"existing origin differs: {current_remote or '(missing)'}"
                additions.append(record)
                continue
            record["status"] = "already_present"
            additions.append(record)
            added_names.append(name)
            continue
        cloned = run_clone(url, destination)
        if cloned.returncode != 0:
            record["status"] = "clone_failed"
            record["error"] = cloned.stderr or cloned.stdout
        else:
            record["status"] = "cloned"
            added_names.append(name)
        additions.append(record)
    return additions, added_names


def compact_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def discover_sources() -> list[SourceRepo]:
    sources: list[SourceRepo] = []
    if not SOURCE_ROOT.exists():
        return sources
    for path in sorted(SOURCE_ROOT.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_dir() or not (path / ".git").exists():
            continue
        remote = git_value(path, "remote", "get-url", "origin")
        branch = git_value(path, "symbolic-ref", "--quiet", "--short", "HEAD") or "(detached)"
        upstream = git_value(path, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        head = git_value(path, "rev-parse", "HEAD")
        sources.append(
            SourceRepo(
                name=path.name,
                path=path,
                remote=remote,
                branch=branch,
                upstream=upstream,
                head=head,
                head_short=head[:12],
                dirty=working_tree_dirty(path),
            )
        )
    return sources


def discover_docs() -> dict[str, dict[str, object]]:
    docs: dict[str, dict[str, object]] = {}
    for path in sorted(DOC_ROOT.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_dir() or path.name in {".git", ".planning", ".codex", "src"}:
            continue
        quick = path / "QUICK-START.md"
        deep = path / "DEEP-ANALYSIS.md"
        if not quick.exists() and not deep.exists():
            continue
        text_parts = []
        for doc_path in (deep, quick):
            if doc_path.exists():
                text_parts.append(doc_path.read_text(encoding="utf-8", errors="replace"))
        urls = re.findall(r"https?://github\.com/[^\s)<>\"]+", "\n".join(text_parts))
        repo_urls = []
        for url in urls:
            canonical = canonical_repo_url(url)
            if canonical and canonical not in repo_urls:
                repo_urls.append(canonical)
        docs[path.name] = {
            "path": path,
            "quick": quick if quick.exists() else None,
            "deep": deep if deep.exists() else None,
            "repo_urls": repo_urls,
        }
    return docs


def map_sources_to_docs(sources: list[SourceRepo], docs: dict[str, dict[str, object]]) -> dict[str, str]:
    by_url: dict[str, str] = {}
    for name, info in docs.items():
        for repo_url in info.get("repo_urls", []):
            by_url[str(repo_url)] = name
    by_name = {compact_name(name): name for name in docs}
    mapping: dict[str, str] = {}
    for source in sources:
        source_key = compact_name(source.name)
        if source_key in by_name:
            mapping[source.name] = by_name[source_key]
            continue
        remote_key = canonical_repo_url(source.remote)
        if remote_key and remote_key in by_url:
            mapping[source.name] = by_url[remote_key]
            continue
    return mapping


def snapshot(repo: SourceRepo) -> dict[str, object]:
    return {
        "head": repo.head,
        "head_short": repo.head_short,
        "branch": repo.branch,
        "upstream": repo.upstream,
        "dirty": repo.dirty,
    }


def pull_source(repo: SourceRepo, do_pull: bool, dry_run: bool) -> dict[str, object]:
    before = snapshot(repo)
    result: dict[str, object] = {
        "source_dir": repo.name,
        "remote": repo.remote,
        "before": before,
        "status": "unchanged",
        "changed_files": [],
        "commits_added": 0,
        "error": "",
    }
    if dry_run:
        result["status"] = "dry_run"
        return result
    if not do_pull:
        result["status"] = "not_pulled"
        return result
    if repo.dirty:
        result["status"] = "skipped_dirty"
        result["error"] = "working tree has local changes"
        return result
    if repo.branch == "(detached)":
        result["status"] = "skipped_detached"
        result["error"] = "HEAD is detached"
        return result
    if not repo.upstream:
        result["status"] = "skipped_no_upstream"
        result["error"] = "current branch has no upstream"
        return result

    fetched = run_git(repo.path, "fetch", "--prune", "origin", timeout=600)
    if fetched.returncode != 0:
        result["status"] = "fetch_failed"
        result["error"] = fetched.stderr or fetched.stdout
        return result

    merged = run_git(repo.path, "merge", "--ff-only", repo.upstream, timeout=600)
    if merged.returncode != 0:
        result["status"] = "pull_failed"
        result["error"] = merged.stderr or merged.stdout
        return result

    after_head = git_value(repo.path, "rev-parse", "HEAD")
    after = {
        "head": after_head,
        "head_short": after_head[:12],
        "branch": repo.branch,
        "upstream": repo.upstream,
        "dirty": working_tree_dirty(repo.path),
    }
    result["after"] = after
    if after_head != repo.head:
        result["status"] = "updated"
        diff = run_git(repo.path, "diff", "--name-status", repo.head, after_head)
        result["changed_files"] = diff.stdout.splitlines() if diff.stdout else []
        count = git_value(repo.path, "rev-list", "--count", f"{repo.head}..{after_head}")
        result["commits_added"] = int(count) if count.isdigit() else 0
        log = run_git(repo.path, "log", "--format=%h %s", f"{repo.head}..{after_head}")
        result["commit_summaries"] = log.stdout.splitlines()[:12] if log.stdout else []
    return result


def metadata_block(records: list[dict[str, object]], analyzed_on: str) -> list[str]:
    lines = [START_MARKER, "> 上游项目："]
    for record in records:
        lines.append(f"> - {record.get('remote') or 'unknown'}")
    lines.append("> 分析基线：")
    for record in records:
        before = record.get("before", {})
        after = record.get("after", before)
        head = str(after.get("head", before.get("head", "unknown")))
        lines.append(f"> - `{record['source_dir']}`：commit `{head}`")
    lines.append(f"> 分析日期：{analyzed_on}")
    lines.append("> 本地源码目录：")
    for record in records:
        lines.append(f"> - `src/{record['source_dir']}`")
    lines.append(END_MARKER)
    return lines


def change_block(records: list[dict[str, object]]) -> list[str]:
    updated_records = [record for record in records if record.get("status") == "updated"]
    if not updated_records:
        return []
    lines = [
        CHANGE_START_MARKER,
        "## 本次源码同步复核",
        "",
        "> 以下内容由 Git 提交和变更路径生成，用于定位源码复核范围，不替代架构结论。",
    ]
    for record in updated_records:
        before = record.get("before", {})
        after = record.get("after", before)
        old_short = str(before.get("head_short", "unknown"))
        new_short = str(after.get("head_short", "unknown"))
        lines.extend(["", f"### `{record['source_dir']}`：`{old_short}` → `{new_short}`", ""])
        summaries = record.get("commit_summaries", [])
        if summaries:
            lines.append("提交摘要：")
            lines.extend(f"- {summary}" for summary in summaries[:8])
        changed_files = record.get("changed_files", [])
        if changed_files:
            lines.append("受影响路径：")
            lines.extend(f"- `{path}`" for path in changed_files[:12])
            if len(changed_files) > 12:
                lines.append(f"- 其余 {len(changed_files) - 12} 个变更路径见 `.planning/source-sync.json`。")
    lines.append(CHANGE_END_MARKER)
    return lines


def update_doc(path: Path, records: list[dict[str, object]], analyzed_on: str) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    existing_match = re.search(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        original,
        flags=re.DOTALL,
    )
    effective_date = analyzed_on
    if existing_match:
        existing_block = existing_match.group(0)
        current_heads = []
        for record in records:
            before = record.get("before", {})
            after = record.get("after", before)
            current_heads.append(str(after.get("head", before.get("head", ""))))
        paths_current = all(f"`src/{record['source_dir']}`" in existing_block for record in records)
        heads_current = all(head and head in existing_block for head in current_heads)
        date_match = re.search(r"^> 分析日期：([^\n]+)$", existing_block, flags=re.MULTILINE)
        if paths_current and heads_current and date_match:
            effective_date = date_match.group(1).strip()
    text = re.sub(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER) + r"\s*",
        "",
        original,
        flags=re.DOTALL,
    )
    text = re.sub(
        re.escape(CHANGE_START_MARKER) + r".*?" + re.escape(CHANGE_END_MARKER) + r"\s*",
        "",
        text,
        flags=re.DOTALL,
    )
    for record in records:
        source_name = str(record["source_dir"])
        for prefix in ("/root/source/tmp/", "/root/source/docs/aaa/src/"):
            text = text.replace(f"{prefix}{source_name}/", f"src/{source_name}/")
    lines = [line for line in text.splitlines() if not line.startswith(METADATA_PREFIXES)]
    title_index = next((index for index, line in enumerate(lines) if line.startswith("# ")), -1)
    insert_at = title_index + 1 if title_index >= 0 else 0
    block = metadata_block(records, effective_date)
    changes = change_block(records)
    updated_lines = lines[:insert_at] + ["", *block, ""]
    if changes:
        updated_lines.extend([*changes, ""])
    updated_lines.extend(lines[insert_at:])
    updated = "\n".join(updated_lines).rstrip() + "\n"
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def default_doc_name(source_name: str) -> str:
    return re.sub(r"_+", "-", source_name).lower()


def create_doc_skeletons(source: SourceRepo, doc_name: str, analyzed_on: str) -> list[str]:
    doc_dir = DOC_ROOT / doc_name
    doc_dir.mkdir(parents=True, exist_ok=True)
    quick = doc_dir / "QUICK-START.md"
    deep = doc_dir / "DEEP-ANALYSIS.md"
    if not quick.exists():
        quick.write_text(
            f"# {source.name}\n\n"
            "## 一句话定位\n\n"
            "待源码分析。\n\n"
            "## 核心流程\n\n"
            "待源码分析。\n\n"
            "## 最值得借鉴的设计\n\n"
            "待源码分析。\n\n"
            "## 限制\n\n"
            "待源码分析。\n\n"
            "## 深度分析\n\n"
            "[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)\n",
            encoding="utf-8",
        )
    if not deep.exists():
        deep.write_text(
            f"# {source.name} 深度分析\n\n"
            "## 系统边界\n\n"
            "待源码分析。\n\n"
            "## 关键模块\n\n"
            "待源码分析。\n\n"
            "## 执行流与数据流\n\n"
            "待源码分析。\n\n"
            "## 契约、状态与持久化\n\n"
            "待源码分析。\n\n"
            "## 质量、安全、性能与运维\n\n"
            "待源码分析。\n\n"
            "## 可迁移模式与限制\n\n"
            "待源码分析。\n",
            encoding="utf-8",
        )
    record = {
        "source_dir": source.name,
        "remote": source.remote,
        "before": snapshot(source),
        "after": snapshot(source),
    }
    changed = []
    for path in (quick, deep):
        if update_doc(path, [record], analyzed_on):
            changed.append(str(path.relative_to(ROOT)))
    return changed


def update_pending_index(doc_names: list[str]) -> bool:
    if not doc_names or not INDEX_PATH.exists():
        return False
    original = INDEX_PATH.read_text(encoding="utf-8", errors="replace")
    rows = [
        INDEX_START_MARKER,
        "## 自动发现项目（待分类）",
        "",
        "| 项目 | 快速概览 | 深度分析 |",
        "|---|---|---|",
    ]
    for doc_name in sorted(set(doc_names)):
        rows.append(
            f"| `{doc_name}` | [{doc_name}/QUICK-START.md](../{doc_name}/QUICK-START.md) | [{doc_name}/DEEP-ANALYSIS.md](../{doc_name}/DEEP-ANALYSIS.md) |"
        )
    rows.extend([INDEX_END_MARKER])
    block = "\n".join(rows)
    if INDEX_START_MARKER in original and INDEX_END_MARKER in original:
        updated = re.sub(
            re.escape(INDEX_START_MARKER) + r".*?" + re.escape(INDEX_END_MARKER),
            block,
            original,
            flags=re.DOTALL,
        )
    else:
        updated = original.rstrip() + "\n\n" + block + "\n"
    if updated == original:
        return False
    INDEX_PATH.write_text(updated, encoding="utf-8")
    return True


def write_reports(
    results: list[dict[str, object]],
    mapping: dict[str, str],
    docs: dict[str, dict[str, object]],
    additions: list[dict[str, str]],
    created_docs: list[str],
) -> None:
    PLAN_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": "src",
        "doc_root": ".",
        "knowledge_root": "docs",
        "added_projects": additions,
        "created_docs": created_docs,
        "projects": results,
        "mapping": mapping,
        "unmapped_sources": sorted(name for name in (item["source_dir"] for item in results) if name not in mapping),
        "unmapped_docs": sorted(name for name in docs if name not in mapping.values()),
    }
    (PLAN_ROOT / "source-sync.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    rows = [
        "# 源码同步报告",
        "",
        f"> 生成时间：{payload['generated_at']}",
        "> 说明：源码拉取由脚本完成；正文更新必须根据变更文件重新核对源码证据。",
        "",
        "| 源码目录 | 文档目录 | 状态 | 基线 | 新基线 | 新增提交 | 文档动作 |",
        "|---|---|---|---|---|---:|---|",
    ]
    for item in results:
        source_name = str(item["source_dir"])
        doc_name = mapping.get(source_name, "-")
        before = item.get("before", {})
        after = item.get("after", before)
        before_short = str(before.get("head_short", "-"))
        after_short = str(after.get("head_short", before_short))
        status = str(item.get("status", "unknown"))
        doc_action = str(item.get("doc_action", "待人工核对"))
        rows.append(
            f"| `{source_name}` | `{doc_name}` | `{status}` | `{before_short}` | `{after_short}` | {item.get('commits_added', 0)} | {doc_action} |"
        )
    rows.extend(
        [
            "",
            "## 本次新增项目",
            "",
            "- " + ("；".join(f"`{item['source_dir']}` ({item['status']})" for item in additions) or "无"),
            "",
            "## 待处理",
            "",
            "- 变更项目：" + (", ".join(f"`{item['source_dir']}`" for item in results if item.get("status") == "updated") or "无"),
            "- 未映射源码：" + (", ".join(f"`{name}`" for name in payload["unmapped_sources"]) or "无"),
            "- 未映射文档：" + (", ".join(f"`{name}`" for name in payload["unmapped_docs"]) or "无"),
            "",
            "## Agent 后续动作",
            "",
            "1. 阅读 `.planning/source-sync.json` 中变更项目的 `changed_files`。",
            "2. 固定新 `after.head`，重新核对 QUICK-START 与 DEEP-ANALYSIS 的事实、限制和调用链。",
            "3. 只有跨项目结论确实变化时，才更新专题、综合、决策矩阵和路线图。",
        ]
    )
    (PLAN_ROOT / "source-sync.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def select_sources(sources: list[SourceRepo], docs: dict[str, dict[str, object]], mapping: dict[str, str], names: list[str]) -> list[SourceRepo]:
    if not names:
        return sources
    aliases: dict[str, dict[str, SourceRepo]] = {}
    for source in sources:
        aliases.setdefault(source.name, {})[source.name] = source
        aliases.setdefault(compact_name(source.name), {})[source.name] = source
        doc_name = mapping.get(source.name)
        if doc_name:
            aliases.setdefault(doc_name, {})[source.name] = source
            aliases.setdefault(compact_name(doc_name), {})[source.name] = source
    missing = [name for name in names if name not in aliases]
    if missing:
        known = ", ".join(sorted(source.name for source in sources))
        raise SystemExit(f"Unknown project(s): {', '.join(missing)}\nKnown source dirs: {known}")
    selected: dict[str, SourceRepo] = {}
    for name in names:
        selected.update(aliases[name])
    return [selected[name] for name in sorted(selected)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="process all repositories under src/")
    parser.add_argument("--project", action="append", default=[], help="source or doc directory; repeatable")
    parser.add_argument(
        "--add",
        action="append",
        default=[],
        metavar="PROJECT",
        help="clone URL, OWNER/REPO, or NAME=GitHub URL into src/; repeatable",
    )
    parser.add_argument("--pull", action="store_true", help="fetch origin and fast-forward clean tracked branches")
    parser.add_argument("--dry-run", action="store_true", help="inspect repositories without fetching or writing docs")
    parser.add_argument("--update-doc-metadata", action="store_true", help="write managed source metadata into mapped docs")
    parser.add_argument("--no-create-docs", action="store_true", help="do not create QUICK-START/DEEP-ANALYSIS for --add")
    args = parser.parse_args()
    if args.dry_run and (args.update_doc_metadata or args.add):
        parser.error("--dry-run cannot be combined with --add or --update-doc-metadata")

    additions: list[dict[str, str]] = []
    added_names: list[str] = []
    if args.add:
        additions, added_names = add_sources(args.add)
        clone_failures = [item for item in additions if item["status"] in {"failed", "clone_failed"}]
        if clone_failures:
            details = "; ".join(f"{item['source_dir']}: {item.get('error', 'unknown error')}" for item in clone_failures)
            raise SystemExit(f"Project add failed: {details}")

    sources = discover_sources()
    docs = discover_docs()
    mapping = map_sources_to_docs(sources, docs)
    analyzed_on = date.today().isoformat()
    created_docs: list[str] = []
    if args.add and not args.no_create_docs:
        for source in sources:
            if source.name not in added_names or source.name in mapping:
                continue
            doc_name = default_doc_name(source.name)
            created_docs.extend(create_doc_skeletons(source, doc_name, analyzed_on))
        if created_docs:
            update_pending_index(sorted({default_doc_name(name) for name in added_names if name not in mapping}))
        docs = discover_docs()
        mapping = map_sources_to_docs(sources, docs)

    requested_projects = list(args.project)
    if args.add and not args.all and not requested_projects:
        requested_projects = added_names
    selected = select_sources(sources, docs, mapping, requested_projects)
    results: list[dict[str, object]] = []
    failures = 0

    for repo in selected:
        item = pull_source(repo, args.pull, args.dry_run)
        source_name = repo.name
        doc_name = mapping.get(source_name)
        item["doc_dir"] = doc_name or ""
        item["doc_action"] = "unmapped"
        if doc_name:
            item["doc_action"] = "mapped; run agent review"
        if item["status"] in {"fetch_failed", "pull_failed"}:
            failures += 1
        results.append(item)

    if args.update_doc_metadata:
        records_by_doc: dict[str, list[dict[str, object]]] = {}
        for item in results:
            doc_name = str(item.get("doc_dir", ""))
            if doc_name:
                records_by_doc.setdefault(doc_name, []).append(item)
        for doc_name, records in records_by_doc.items():
            info = docs[doc_name]
            updated_files = []
            for key in ("quick", "deep"):
                doc_path = info.get(key)
                if isinstance(doc_path, Path) and update_doc(doc_path, records, analyzed_on):
                    updated_files.append(str(doc_path.relative_to(ROOT)))
            action = "metadata_updated" if updated_files else "metadata_current"
            for item in records:
                item["doc_action"] = action
                item["metadata_files"] = updated_files

    write_reports(results, mapping, docs, additions, created_docs)
    changed = [item for item in results if item.get("status") == "updated"]
    print(f"Processed {len(results)} source repositories")
    if additions:
        print(f"Added {sum(1 for item in additions if item['status'] in {'cloned', 'already_present'})} repositories")
    print(f"Updated {len(changed)} repositories")
    print(f"Mapped docs: {sum(1 for item in results if item.get('doc_dir'))}/{len(results)}")
    print(f"Report: {PLAN_ROOT / 'source-sync.md'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
