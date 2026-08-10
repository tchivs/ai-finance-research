#!/usr/bin/env python3
"""Build Hugo content from the research library without changing source documents."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "docs-site"
CONTENT = SITE / "content"
PROJECT_GROUPS_FILE = SITE / "data" / "project_groups.json"

CORE_SLUGS = {
    "00-INDEX.md": "index",
    "01-知识库使用与维护指南.md": "maintenance",
    "06-工程治理篇.md": "engineering-governance",
    "07-策略与信号系统篇.md": "strategy-signals",
    "08-数据采集与流水线篇.md": "data-pipelines",
    "09-Agent-协作与设计哲学篇.md": "agent-collaboration",
    "10-SYNTHESIS.md": "synthesis",
    "11-UI-UX交互设计.md": "ui-ux-interaction",
    "12-剩余深度素材.md": "remaining-materials",
    "13-终极提炼.md": "engineering-lessons",
    "14-跨项目深层精华.md": "cross-project-insights",
    "15-数据底座与采集底座篇.md": "data-foundation",
    "16-UI-UX设计借鉴总表.md": "ui-ux-reference",
    "17-落地路线图.md": "delivery-roadmap",
    "18-模式决策矩阵.md": "decision-matrix",
    "19-首批源码落地验证.md": "source-verification",
    "20-开发实施TODO.md": "implementation-todo",
    "21-项目价值评估与方法论.md": "project-evaluation",
    "22-量化工作台设计PRD.md": "quant-workbench-prd",
}


def quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def summary_candidate(line: str) -> str:
    value = line.strip()
    if not value or value.startswith(("<!--", "#", "- ", ">", "```", "|")):
        return ""
    if value in {"提交摘要：", "受影响路径："} or value.endswith(("：", ":")):
        return ""
    value = re.sub(r"^\*\*(?:定位|产品定位)\*\*[:：]\s*", "", value)
    return value.strip()


def summary(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        heading = line.strip()
        if heading.startswith("## ") and ("一句话定位" in heading or "产品定位" in heading):
            for candidate in lines[index + 1 : index + 8]:
                value = summary_candidate(candidate)
                if value:
                    return value[:180]
    for line in lines:
        value = summary_candidate(line)
        if value:
            return value[:180]
    return "可审计的源码研究与架构参考。"


def project_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"


def load_project_groups() -> tuple[list[dict], dict[str, dict]]:
    data = json.loads(PROJECT_GROUPS_FILE.read_text(encoding="utf-8"))
    groups = data["groups"]
    project_groups: dict[str, dict] = {}
    for group in groups:
        for slug in group["projects"]:
            if slug in project_groups:
                raise ValueError(f"Project appears in multiple groups: {slug}")
            project_groups[slug] = group
    return groups, project_groups


def upstream_url(text: str) -> str:
    match = re.search(r"https://github\.com/[^\s)]+", text)
    return match.group(0).rstrip(".,") if match else ""


def strip_first_heading(text: str) -> str:
    match = re.match(r"\s*# [^\n]+\n+", text)
    if match:
        return text[match.end() :].lstrip("\n")
    return text


def rewrite_links(text: str, core_lookup: dict[str, str], current_project: str = "") -> str:
    pattern = re.compile(r"(\]\()([^\s)]+)(\))")

    def replace(match: re.Match[str]) -> str:
        url = match.group(2)
        if url.startswith(("http://", "https://", "mailto:", "#", "/")):
            return match.group(0)
        path, separator, anchor = url.partition("#")
        normalized = path.removeprefix("./").removeprefix("../")
        if current_project and normalized == "DEEP-ANALYSIS.md":
            target = f"/projects/{current_project}/deep-analysis/"
        elif current_project and normalized == "QUICK-START.md":
            target = f"/projects/{current_project}/quick-start/"
        elif normalized in core_lookup:
            target = f"/library/{core_lookup[normalized]}/"
        else:
            project_match = re.fullmatch(r"([^/]+)/(?:(QUICK-START)|(DEEP-ANALYSIS))\.md", normalized)
            if project_match:
                target = f"/projects/{project_slug(project_match.group(1))}/"
                target += "quick-start/" if project_match.group(2) else "deep-analysis/"
            else:
                return match.group(0)
        fragment = f"#{anchor}" if separator else ""
        shortcode = '{{< relref "' + target.rstrip("/") + '" >}}'
        return f"{match.group(1)}{shortcode}{fragment}{match.group(3)}"

    return pattern.sub(replace, text)


def frontmatter(
    title: str,
    description: str,
    weight: int,
    source_file: str,
    kind: str,
    category: dict | None = None,
) -> str:
    fields = (
        "---\n"
        f"title: {quote(title)}\n"
        f"description: {quote(description)}\n"
        f"weight: {weight}\n"
        f"source_file: {quote(source_file)}\n"
        f"kind: {quote(kind)}\n"
    )
    if category:
        fields += f"category: {quote(category['slug'])}\n"
        fields += f"category_title: {quote(category['title'])}\n"
    return fields + "---\n\n"


def write_page(
    path: Path,
    title: str,
    description: str,
    weight: int,
    source: Path,
    body: str,
    kind: str,
    category: dict | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        frontmatter(title, description, weight, str(source.relative_to(ROOT)), kind, category)
        + "<!-- Generated by docs-site/scripts/sync_content.py. Edit the source document instead. -->\n\n"
        + body.rstrip()
        + "\n",
        encoding="utf-8",
    )


def clean_generated() -> None:
    for section in (CONTENT / "library", CONTENT / "projects"):
        section.mkdir(parents=True, exist_ok=True)
        for child in section.iterdir():
            if child.is_dir():
                shutil.rmtree(child)


def main() -> None:
    clean_generated()
    groups, project_groups = load_project_groups()
    default_group = next(group for group in groups if group["slug"] == "uncategorized")
    root_docs = {path.name: path for path in (ROOT / "docs").glob("*.md") if path.name in CORE_SLUGS}
    core_lookup = {name: slug for name, slug in CORE_SLUGS.items() if name in root_docs}

    for filename, slug in CORE_SLUGS.items():
        source = root_docs.get(filename)
        if source is None:
            continue
        text = source.read_text(encoding="utf-8")
        title = first_heading(text, filename.removesuffix(".md"))
        body = rewrite_links(strip_first_heading(text), core_lookup)
        number = re.match(r"\d+", filename)
        write_page(
            CONTENT / "library" / slug / "index.md",
            title,
            summary(text),
            int(number.group(0)) if number else 99,
            source,
            body,
            "library",
        )

    projects = sorted(
        (path.parent for path in ROOT.glob("*/QUICK-START.md") if path.parent.parent == ROOT),
        key=lambda path: path.name.lower(),
    )
    for weight, project in enumerate(projects, start=1):
        quick = project / "QUICK-START.md"
        deep = project / "DEEP-ANALYSIS.md"
        quick_text = quick.read_text(encoding="utf-8")
        slug = project_slug(project.name)
        category = project_groups.get(slug, default_group)
        title = first_heading(quick_text, project.name)
        description = summary(quick_text)
        url = upstream_url(quick_text)
        index_body = (
            f"{description}\n\n"
            + (f"上游项目：[GitHub]({url})\n\n" if url else "")
            + "本页包含快速概览和深度分析；来源 commit、分析日期与限制以项目文档中的来源块为准。\n"
        )
        project_dir = CONTENT / "projects" / slug
        write_page(project_dir / "_index.md", title, description, weight, quick, index_body, "project", category)
        write_page(
            project_dir / "quick-start.md",
            f"{title} · 快速概览",
            description,
            1,
            quick,
            rewrite_links(strip_first_heading(quick_text), core_lookup, slug),
            "quick-start",
            category,
        )
        if deep.exists():
            deep_text = deep.read_text(encoding="utf-8")
            write_page(
                project_dir / "deep-analysis.md",
                f"{title} · 深度分析",
                description,
                2,
                deep,
                rewrite_links(strip_first_heading(deep_text), core_lookup, slug),
                "deep-analysis",
                category,
            )

    print(f"Generated {len(root_docs)} library documents and {len(projects)} project sections.")


if __name__ == "__main__":
    main()
