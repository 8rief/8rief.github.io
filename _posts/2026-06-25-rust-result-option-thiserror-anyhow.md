---
layout: post
title: "Rust Result 和 Option：把解析失败写成可定位错误"
date: 2026-06-25 20:12:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [rust, result, error-handling, teaching]
---

## 学习目标

这一篇处理可靠 CLI 的错误边界。读完以后，你应该能解释：

1. `Option<T>` 适合表示字段可能缺失；
2. `Result<T, E>` 适合表示操作可能失败；
3. `thiserror` 和 `anyhow` 分别适合核心库错误和入口层上下文。

## 先修知识

需要知道日志行可能偏离预期：列数不足、level 拼错、延迟字段无法解析成数字。这些失败应该在解析阶段被报告，避免后续步骤得到无意义的空结果。

## 核心模型

错误处理可以分成两层：核心库用具体错误类型表达可测试的失败原因，入口层用上下文把错误和文件路径、命令操作关联起来。

![Rust Result Option 错误边界](/assets/diagrams/rust-result-option-thiserror-anyhow.svg)

这样设计后，单元测试可以断言具体错误，CLI 用户看到的错误也能定位到哪个文件、哪一步失败。

## 逐步实现

日志 level 的解析先用一个具体错误类型：

```rust
#[derive(Debug, Error, Clone, PartialEq, Eq)]
#[error("unknown log level {0:?}")]
pub struct LevelParseError(pub String);
```

解析日志行时，错误枚举表达不同失败原因：

```rust
#[derive(Debug, Error, PartialEq, Eq)]
pub enum ParseLogError {
    #[error("line must contain at least timestamp, level, service, and message")]
    MissingColumns,
    #[error("invalid level: {0}")]
    InvalidLevel(String),
    #[error("latency_ms must be an unsigned integer, got {0:?}")]
    InvalidLatency(String),
}
```

`latency_ms` 字段可能不存在，所以结构体里用 `Option<u64>`：

```rust
pub latency_ms: Option<u64>
```

汇总慢请求时只处理存在的值：

```rust
if record.latency_ms.is_some_and(|latency| latency >= config.slow_latency_ms) {
    slow_events += 1;
}
```

文件读取属于入口边界，错误要加路径上下文：

```rust
let text = fs::read_to_string(path)
    .with_context(|| format!("read log file {}", path.display()))?;
parser::parse_lines(&text)
    .with_context(|| format!("parse log file {}", path.display()))
```

测试中直接验证错误类型：

```rust
let err = parse_line("2026-06-25T12:00:00Z NOTICE api request_ok")
    .expect_err("invalid level should fail");
assert_eq!(err, ParseLogError::InvalidLevel("NOTICE".to_owned()));
```

这比只检查命令退出失败更强，因为它证明失败原因没有被吞掉。

## 常见错误

1. **用空字符串表示缺失字段**：缺失和空值含义不同，`Option` 能把边界写进类型。
2. **核心库直接返回 `anyhow::Error`**：方便但不利于测试具体错误分支。核心库保留具体错误类型更清楚。
3. **入口层不加上下文**：用户只看到“parse failed”时，很难知道是哪一个文件出错。

## 练习或延伸

- 给解析器增加行号，让错误显示 `line 3: invalid level`。
- 增加一个 `InvalidTimestamp` 错误分支，但先不要引入时间库，比较字符串校验和完整时间解析的取舍。

## 参考资料

- [Rust Book: Recoverable Errors with Result](https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html)
- [thiserror crate](https://docs.rs/thiserror/)
- [anyhow crate](https://docs.rs/anyhow/)
