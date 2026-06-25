---
layout: post
title: "Rust 工具链和 Cargo 项目结构：先把可靠 CLI 跑起来"
date: 2026-06-25 20:10:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [rust, cargo, cli, teaching]
---

## 学习目标

这一篇先解决 Rust 项目的落地入口：怎样从工具链、Cargo 包和目录结构开始，把一个可靠 CLI 项目跑起来。读完以后，你应该能完成三件事：

1. 用 `rustc --version`、`cargo --version`、`cargo test` 检查环境；
2. 理解 `Cargo.toml`、`src/lib.rs`、`src/main.rs`、`tests/` 的职责；
3. 把后续的日志分析项目放进一个可以测试、构建、演示的结构里。

## 先修知识

需要知道命令行当前目录、相对路径、文本文件和 JSON/CSV 的用途。暂时不要求理解所有权细节，下一篇会把数据流和借用边界放回项目里讲。

## 核心模型

Rust 项目可以先分成四层：包元数据、库代码、入口程序、外部测试。

![Rust Cargo 项目结构](/assets/diagrams/rust-toolchain-cargo-project-layout.svg)

`src/lib.rs` 暴露可测试的核心模块，`src/main.rs` 只负责 CLI 参数、日志初始化和调用核心逻辑。这样做的直接好处是：解析、汇总、文件输出和 HTTP API 都能在不启动完整命令行进程的情况下测试。

## 逐步实现

项目的 `Cargo.toml` 先声明包和依赖：

```toml
[package]
name = "rust-log-insight-cli"
version = "0.1.0"
edition = "2024"

[dependencies]
anyhow = "1.0"
clap = { version = "4.5", features = ["derive"] }
serde = { version = "1.0", features = ["derive"] }
```

这里按项目边界选择依赖：`clap` 解决 CLI 参数解析，`serde` 解决数据结构和 JSON/CSV/TOML 的转换，`anyhow` 负责入口层的错误传播。每个依赖都对应一个明确职责。

目录结构保持清楚：

```text
rust-log-insight-cli/
  Cargo.toml
  src/lib.rs
  src/main.rs
  src/parser.rs
  src/analyzer.rs
  src/io.rs
  src/server.rs
  tests/cli_smoke.rs
  sample_logs/app.log
  sample_config/log-insight.toml
  run_lab.sh
```

`src/lib.rs` 只声明模块：

```rust
pub mod analyzer;
pub mod config;
pub mod io;
pub mod models;
pub mod parser;
pub mod server;
```

第一次验收先跑工具链和基础命令：

```bash
rustc --version
cargo --version
cargo fmt -- --check
cargo test
cargo build
```

实验 transcript 中的关键结果是：

```text
rustc 1.95.0
cargo 1.95.0
running 5 tests
5 passed
running 1 test
summarize_command_writes_reports ... ok
```

这证明项目不只是能启动，核心库测试和 CLI smoke 测试也能复跑。

## 常见错误

1. **把所有逻辑写在 `main.rs`**：命令能跑，但解析和汇总逻辑难以单独测试。
2. **把 `Cargo.lock` 当成无关文件**：应用项目应该保留 lockfile，这样依赖解析更可复现。
3. **只跑 `cargo run`**：能运行一个样例，不能证明解析错误、报告输出和 API 路径都可靠。

## 练习或延伸

- 新增一个 `src/version.rs`，让 CLI 的 `--version` 输出同时包含构建目标平台。
- 把 `tests/cli_smoke.rs` 改成检查 CSV 首行，观察外部测试如何验证用户可见行为。

## 参考资料

- [The Cargo Book](https://doc.rust-lang.org/cargo/)
- [Rust package layout](https://doc.rust-lang.org/cargo/guide/project-layout.html)
- [Rust edition guide](https://doc.rust-lang.org/edition-guide/)
