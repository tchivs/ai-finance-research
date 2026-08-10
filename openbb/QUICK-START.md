# openbb

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/OpenBB-finance/OpenBB
> 分析基线：
> - `openbb`：commit `3e071fcc2cd9f891cac6040ae60296dba76dab46`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/openbb`
<!-- source-sync:end -->


## 一句话定位

以 Provider/Extension 为核心的开放金融数据平台，把多源数据统一暴露给 Python、REST API、Workspace、Excel 和 MCP/Agent 客户端。

## 核心流程

用户通过 `obb.equity.price.historical` 等路由调用 `Query`；`Router`/`CommandRunner` 解析命令并选择 provider，provider 的 `Fetcher` 负责参数、认证、请求和结果转换，统一包装为 `OBBject`，再通过 DataFrame、REST 或 Agent 接口输出。

## 最值得借鉴的设计

1. Provider 插件化：`openbb_core/provider/abstract/provider.py`、`fetcher.py` 与 `provider_interface.py` 把数据源扩展和核心路由分开。
2. 统一结果容器：`openbb_core/app/model/obbject.py` 保留结果、错误、警告和元数据，适合映射到本项目的 `ProviderResult`。
3. 多表面复用：同一 provider 能服务 Python、FastAPI REST、MCP 和工作台，降低重复数据适配成本。

## 限制

仓库 README 声明平台为 AGPLv3；各 provider 还受上游数据源许可证、API key、限流和商用条款约束。OpenBB 更适合借鉴 provider registry、结果契约和扩展机制，不应直接把全部 provider 依赖纳入工作台。

## 深度分析

[阅读 DEEP-ANALYSIS.md](DEEP-ANALYSIS.md)
