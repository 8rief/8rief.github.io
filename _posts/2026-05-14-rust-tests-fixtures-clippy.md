---
layout: post
title: "Rust 测试和 clippy：让解析器、报告和 CLI 能回归验证"
date: 2026-05-14 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [rust, testing, clippy, teaching]
---

## 学习目标

这一篇讲 Rust 项目的验证方式。读完以后，你应该能搭出三层检查：

1. 单元测试验证解析器、配置和汇总逻辑；
2. 集成测试验证 CLI 真实二进制会写出报告；
3. `cargo fmt` 和 `cargo clippy` 作为提交前质量门禁。

## 先修知识

测试应该验证用户可见行为。日志项目的可见行为包括：错误分支、统计数值、报告文件和命令退出状态。

## 核心模型

Rust 项目的验证可以分成四个层级。

![Rust 测试与 clippy 门禁](/assets/diagrams/rust-tests-fixtures-clippy.svg)

单元测试覆盖小函数，集成测试覆盖二进制入口，clippy 检查常见代码风险，run script 把这些检查组合成可复现 transcript。

## 为什么需要测试和 clippy 门禁

Rust 编译器能保证很多内存安全性质，但它不能替代业务测试。解析器是否拒绝非法 level，汇总是否算对错误率，CSV 是否包含表头，CLI 是否真的写出报告，都需要测试断言。clippy 则补充检查常见代码质量问题。

本项目把验证分成四层：单元测试覆盖 parser/config/analyzer/io，集成测试调用真实二进制，`cargo fmt --check` 保持格式一致，`cargo clippy --all-targets -- -D warnings` 把 warning 提升为失败。这样 demo 不是只靠人工观察。

fixtures 的价值是稳定。样例日志固定 6 行，包含 INFO/WARN/ERROR/DEBUG、服务名、延迟和额外字段。固定输入让每次改代码后都能对比同一组输出。

## 逐步实现

解析器测试直接断言错误类型：

```rust
let err = parse_line("2026-06-25T12:00:00Z NOTICE api request_ok")
    .expect_err("invalid level should fail");
assert_eq!(err, ParseLogError::InvalidLevel("NOTICE".to_owned()));
```

汇总测试使用小 fixture：

```rust
let records = parse_lines(
    "2026-06-25T12:00:00Z INFO api ok latency_ms=10
     2026-06-25T12:00:01Z ERROR api fail latency_ms=60
",
)?;
```

集成测试启动真实 CLI 二进制：

```rust
let bin = env!("CARGO_BIN_EXE_rust-log-insight-cli");
let output = Command::new(bin)
    .args(["summarize", "--input", "sample_logs/app.log"])
    .output()?;
assert!(output.status.success());
```

本地 lab 的验证命令是：

```bash
cargo fmt -- --check
cargo test
cargo clippy --all-targets -- -D warnings
cargo build
```

对应 transcript 证明了测试规模：

```text
running 5 tests
5 passed
running 1 test
summarize_command_writes_reports ... ok
== clippy ==
Finished dev profile
```

这里的 `-D warnings` 会把 clippy warning 当成失败。教学代码不应该依赖“有 warning 但先不管”的状态。

## 输出怎么读

当前测试输出给出明确规模：

```text
running 5 tests
5 passed
running 1 test
summarize_command_writes_reports ... ok
== clippy ==
Finished dev profile
```

5 个单元测试覆盖配置、解析、汇总和报告写入；1 个集成测试覆盖真实 CLI。`clippy` 后面没有 warning，因为命令使用了 `-D warnings`，任何 warning 都会让 lab 失败。

如果以后新增字段，应该同时更新 parser 测试、summary 测试、CSV/JSON 报告测试和 CLI smoke。只改输出代码而不改测试，通常会让回归风险藏到发布阶段。

## 常见错误

1. **只测 parser 成功路径**：可靠工具必须覆盖非法 level、缺字段、非法数字等失败路径。
2. **集成测试不调用二进制**：库测试通过，不代表 CLI 参数和文件路径都接好了。
3. **把 clippy 当成可选装饰**：clippy 不替代测试，但能提前发现很多常见写法问题。

## 练习或延伸

- 增加一个非法 `latency_ms=fast` 的测试，断言错误分支。
- 给 CLI 集成测试检查 JSON 里的 `error_rate` 数值，避免只检查文件存在。

## 参考资料

- [Rust Book: Writing Automated Tests](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [Cargo tests](https://doc.rust-lang.org/cargo/commands/cargo-test.html)
- [Clippy documentation](https://doc.rust-lang.org/clippy/)
