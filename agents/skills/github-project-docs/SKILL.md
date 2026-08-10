---
name: github-project-docs
description: 将 GitHub 开源项目提取为可审计的 Markdown 研究文档，并在用户要求批量拉取、更新源码、同步项目文档、刷新知识库或检查上游变化时触发。适用于当前资料库这种 src/源码快照 + 项目 QUICK-START/DEEP-ANALYSIS + 总索引/专题文档的结构。
compatibility: Python 3.10+, Git, 网络访问；使用 codebase-memory MCP 做源码结构分析。
metadata:
  output: QUICK-START.md, DEEP-ANALYSIS.md, source-sync.json, source-sync.md
  source_root: src/
  doc_root: project directories at repository root
---

# GitHub Project Documentation

把仓库源码、版本基线和研究结论绑定在一起。重点是可复核，不是把 README 改写成宣传稿。

## 一键同步入口

在资料库根目录执行：

```bash
python3 .codex/skills/github-project-docs/scripts/sync_research.py \
  --all --pull --update-doc-metadata
```

只同步一个项目：

```bash
python3 .codex/skills/github-project-docs/scripts/sync_research.py \
  --project qlib --pull --update-doc-metadata
```

预览项目、远程地址、当前 commit 和文档映射，不拉取、不写文件：

```bash
python3 .codex/skills/github-project-docs/scripts/sync_research.py \
  --all --dry-run
```

新增项目并自动放入 `src/`：

```bash
# GitHub URL
python3 .codex/skills/github-project-docs/scripts/sync_research.py \
  --add https://github.com/OWNER/REPO \
  --pull --update-doc-metadata

# OWNER/REPO 简写
python3 .codex/skills/github-project-docs/scripts/sync_research.py \
  --add OWNER/REPO --pull --update-doc-metadata

# 自定义本地目录名
python3 .codex/skills/github-project-docs/scripts/sync_research.py \
  --add local-name=https://github.com/OWNER/REPO \
  --pull --update-doc-metadata
```

`--add` 会 clone 到 `src/<目录名>`，创建缺失的 `QUICK-START.md`、`DEEP-ANALYSIS.md`，并把项目加入 `docs/00-INDEX.md` 的“自动发现项目（待分类）”区。用户只给项目名称时，先用 GitHub 搜索确定官方仓库 URL，再调用同一入口；不要根据一个有歧义的裸名称猜仓库。

脚本行为：

1. 扫描 `src/*/.git`，读取 `origin`、当前分支、upstream、HEAD 和工作区状态。
2. 只对干净且有 upstream 的分支执行 `fetch --prune` + `merge --ff-only`。
3. 脏工作区、detached HEAD、没有 upstream 或快进失败时跳过并记录原因，不覆盖本地修改。
4. 通过文档中的 GitHub URL 优先、目录名其次，将源码目录映射到项目文档目录。
5. 写入 `.planning/source-sync.json` 和 `.planning/source-sync.md`。
6. `--update-doc-metadata` 只维护来源、commit、日期和本地源码目录，不自动改写正文。

新增项目的自动骨架只是占位，必须继续完成源码分析：

1. 读取新项目的 README、依赖清单、入口和测试布局。
2. 用 codebase-memory MCP 建立/刷新索引，定位入口、关键模块、主要调用链和配置契约。
3. 用新仓库的 HEAD 生成 QUICK-START 的定位、核心流程、可借鉴设计和限制。
4. 完成 DEEP-ANALYSIS 的模块、数据流、状态、错误路径、测试、性能、安全和运维分析。
5. 将“待分析”占位替换为有文件/符号依据的结论，并保留未验证项。
6. 把“待分类”索引项移动到合适的项目分类；只有出现跨项目证据时才更新专题和综合文档。

## 源码变更后的文档流程

同步结束后，先阅读 `.planning/source-sync.md`，再处理状态为 `updated` 的项目。每个变更项目都要：

1. 读取 `source-sync.json` 的 `before`、`after` 和 `changed_files`。
2. 把 `after.head` 作为新的分析基线；不要使用当前工作区路径、模糊版本号或未经核对的默认分支描述。
3. 优先用 codebase-memory MCP 的结构查询确认新增、删除、重命名和调用关系；索引尚未更新时等待索引刷新，再读取具体源码。
4. 阅读变更文件及其调用方，区分“源码变化”与“文档理解修正”。
5. 只更新受影响项目的 `QUICK-START.md` 和 `DEEP-ANALYSIS.md`，保留来源块、限制和未验证项。
6. 跨项目结论只有在至少两个项目的证据发生变化时，才更新专题、`10-SYNTHESIS.md`、`18-模式决策矩阵.md` 或 `17-落地路线图.md`。
7. 重新运行覆盖检查，确认没有孤立文档、失效链接或过期 commit。

## QUICK-START.md 模板

```markdown
# <项目名>

> 上游项目：<GitHub URL>
> 分析基线：commit `<full commit>`
> 分析日期：YYYY-MM-DD

## 一句话定位

## 核心流程

## 最值得借鉴的设计

1. <模式>：<源码证据和适用条件>
2. <模式>：<源码证据和适用条件>
3. <模式>：<源码证据和适用条件>

## 限制

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
```

## DEEP-ANALYSIS.md 模板

正文至少覆盖：

- 来源、版本/commit、分析日期和验证范围。
- 系统边界、入口、关键模块和依赖关系。
- 主要控制流、数据流、事件流或任务流。
- 核心契约、状态机、持久化、缓存和错误路径。
- 测试、质量、安全、性能、运维和扩展风险。
- 可迁移模式、适用前提、迁移成本和不应照搬的部分。
- 未验证项和下一次源码更新时应复核的证据。

每个重要结论都应能回到文件、符号、调用关系、配置或上游文档；缺少证据时明确写“待验证”。不要维护行数、文件数量等高频失效数字。

## 证据与版本规则

- 固定 commit 优先于默认分支名称。
- 代码事实、模型推断、Agent 判断和当前项目建议分开写。
- 删除或重命名的实现要在文档中明确标记，不能静默保留旧能力描述。
- 上游限制与可借鉴点同时记录，不只摘录优点。
- 不写 token、Cookie、私钥、认证头、`.env` 内容或真实敏感数据。

## 完成检查

- [ ] `source-sync.json` 中的 `after.head` 已写入文档来源块。
- [ ] 所有 `changed_files` 已判断是否影响正文。
- [ ] QUICK-START 和 DEEP-ANALYSIS 的结论没有互相矛盾。
- [ ] 新增、删除、重命名模块与调用关系已核对。
- [ ] 跨项目文档只在证据足够时更新。
- [ ] 入口索引、相对链接和文档覆盖均通过检查。
