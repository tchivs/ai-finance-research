# AI + 金融开源项目研究库

[![最新 TAG](https://img.shields.io/github/v/tag/tchivs/ai-finance-research?label=%E6%9C%80%E6%96%B0%20TAG)](https://github.com/tchivs/ai-finance-research/tags)
[![文档发布](https://img.shields.io/github/actions/workflow/status/tchivs/ai-finance-research/hugo-pages.yml?branch=main&label=%E6%96%87%E6%A1%A3%E5%8F%91%E5%B8%83&logo=github)](https://github.com/tchivs/ai-finance-research/actions/workflows/hugo-pages.yml)
[![在线文档](https://img.shields.io/website?url=https%3A%2F%2Ftchivs.github.io%2Fai-finance-research%2F&label=%E5%9C%A8%E7%BA%BF%E6%96%87%E6%A1%A3)](https://tchivs.github.io/ai-finance-research/)
[![项目数量](https://img.shields.io/badge/%E9%A1%B9%E7%9B%AE-71-2ea44f)](docs/00-INDEX.md)
[![许可证](https://img.shields.io/github/license/tchivs/ai-finance-research?label=%E8%AE%B8%E5%8F%AF%E8%AF%81)](LICENSE)

这是一个面向金融 AI 系统设计的开源研究资料库，收录 71 个开源项目的快速概览、深度分析、跨项目专题、落地路线和架构决策参考。

在线阅读：[Hugo 文档站](https://tchivs.github.io/ai-finance-research/)

## 内容入口

- [总索引与阅读路线](docs/00-INDEX.md)
- [知识库使用与维护指南](docs/01-知识库使用与维护指南.md)
- [跨项目综合提炼](docs/10-SYNTHESIS.md)
- [量化工作台设计 PRD](docs/16-量化工作台设计PRD.md)
- [落地路线图](docs/17-落地路线图.md)
- [模式决策矩阵](docs/18-模式决策矩阵.md)
- [首批源码落地验证](docs/19-首批源码落地验证.md)
- [开发实施 TODO](docs/20-开发实施TODO.md)
- [项目价值评估与方法论](docs/21-项目价值评估与方法论.md)

## 推荐阅读顺序

1. 从 `docs/00-INDEX.md` 了解项目分类和阅读路线。
2. 阅读 `docs/10-SYNTHESIS.md`，建立跨项目的整体认识。
3. 使用 `docs/17-落地路线图.md`、`docs/18-模式决策矩阵.md` 确定实施顺序和技术分叉。
4. 回到专题文档及各项目的 `QUICK-START.md`、`DEEP-ANALYSIS.md` 核对代码证据、风险与限制。
5. 开始实现前，结合 `docs/19-首批源码落地验证.md` 和 `docs/20-开发实施TODO.md` 检查代码边界、阶段门禁和验收证据。

## 本地预览

需要安装 Hugo Extended：

```bash
hugo server --source docs-site --buildDrafts
```

然后访问 <http://localhost:1313/>。重新生成文档内容并构建发布版本：

```bash
python3 docs-site/scripts/sync_content.py
hugo --source docs-site --minify
```

## 源码与文档同步

上游项目源码快照位于 `src/`，项目研究文档位于 `docs/projects/`。新增或更新项目时使用统一技能脚本：

```bash
python3 agents/skills/github-project-docs/scripts/sync_research.py --all --pull --update-doc-metadata
python3 agents/skills/github-project-docs/scripts/sync_research.py --add OWNER/REPO --pull --update-doc-metadata
```

同步后只根据源码证据更新分析结论；不要运行上游项目的测试或编译流程。Codex 和 OpenCode 共用 `agents/skills/github-project-docs/` 技能入口。

## 目录结构

- `docs/`：研究索引、专题分析、设计 PRD 和实施文档。
- `docs/projects/`：各开源项目的快速入门与深度分析。
- `src/`：上游仓库源码快照及同步元数据。
- `docs-site/`：Hugo 文档站源码与 GitHub Pages 发布配置。
- `agents/skills/`：跨工具复用的项目研究与同步技能。

## 许可证与来源

本仓库原创文档、脚本和站点配置采用 MIT 许可证。`src/` 中的第三方源码、项目名称、引用内容和各项目文档仍以对应上游仓库的许可证和声明为准。研究结论仅作设计参考，不替代生产环境中的安全评审、数据验证、合规检查和性能测试。
