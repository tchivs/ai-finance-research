# polymarket-cli 深度分析

<!-- source-sync:start -->
> 上游项目：
> - https://github.com/Polymarket/polymarket-cli
> 分析基线：
> - `polymarket-cli`：commit `9b18b5faf5493b945c48ca22efaf9645f0c69ab8`
> 分析日期：2026-08-10
> 本地源码目录：
> - `src/polymarket-cli`
<!-- source-sync:end -->


## 系统边界

Rust CLI 通过 `src/main.rs` 进入，命令、认证、配置、shell 和输出模块分别隔离。它调用官方 API/链上接口，不承载长期任务、数据库或实时 UI 状态。

## 关键模块

- `commands/`：markets、events、CLOB、wallet、CTF 等操作。
- `output/`：人类可读和 JSON 输出，适合保留 raw structured result。
- `auth.rs` / `config.rs`：私钥、chain id、signature type 和本地配置。
- `cli_integration/`：命令组合和脚本化入口。
- `tests/cli_integration.rs`：CLI 集成行为验证。

## 执行流与数据流

```text
argv -> clap command -> public/authenticated client -> output formatter
                                      -> optional wallet sign -> chain/CLOB action
```

市场 list/search/get、order book 等读操作可生成 JSON snapshot；订单、余额、approve、split/merge/redeem 和交易需要 ActionGuard 才能进入执行。

## 契约、状态与持久化

README 定义了 `~/.config/polymarket/config.json`、环境变量和 CLI flag 的优先级。当前状态偏本地文件，不适合直接作为服务端多用户真相；应将 command、params、scope、exit status 和 raw hash 写入 `ToolCallEnvelope`。

## 质量、安全、性能与运维

项目提供 Cargo lock 和 CLI integration test；未在当前环境运行 `cargo test`。私钥 flag 会进入 shell history/process args 风险，生产集成应改成服务端签名或硬件/托管密钥，并默认只读。

## 可迁移模式与限制

可迁移的是 JSON CLI、命令发现和读写边界；不要直接把 CLI 当 execution gateway。更适合把它封装成 provider adapter，所有写操作经过服务端 scope、幂等和人工确认。
