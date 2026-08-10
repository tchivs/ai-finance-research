# Hugo 文档站

该目录是研究库的 Hugo 发布站点。仓库根目录的 `docs/` 保存核心 Markdown，项目目录保存每个项目的 `QUICK-START.md` 和 `DEEP-ANALYSIS.md`；`scripts/sync_content.py` 生成 Hugo 内容树，不修改源文档。

## 本地预览

```bash
python3 docs-site/scripts/sync_content.py
hugo server --source docs-site --buildDrafts --disableFastRender
```

打开 `http://localhost:1313/`。

## 构建发布

```bash
python3 docs-site/scripts/sync_content.py
hugo --source docs-site --minify
```

`.github/workflows/hugo-pages.yml` 会在 `main` 分支更新时生成并部署 GitHub Pages。首次启用时，在仓库 Settings → Pages 中将 Source 设置为 GitHub Actions。
