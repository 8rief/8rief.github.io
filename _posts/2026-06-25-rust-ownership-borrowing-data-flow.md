---
layout: post
title: "Rust 所有权和借用：从日志记录的数据流理解安全边界"
date: 2026-06-25 20:11:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [rust, ownership, borrowing, teaching]
---

## 学习目标

这一篇用日志分析项目解释 Rust 的所有权和借用。读完以后，你应该能说明：

1. 哪些数据由函数拥有，哪些数据只是被借用；
2. 为什么 `&[LogRecord]` 比复制整个 `Vec<LogRecord>` 更适合汇总；
3. 为什么 HTTP API 需要共享只读数据时要使用 `Arc`。

## 先修知识

需要知道 `Vec<T>` 是一组同类型元素，结构体把多个字段组合成一个值。Rust 的所有权规则可以先理解为“每个值都有明确的负责人”。

## 核心模型

日志项目的数据流是：文件文本进入解析器，解析器产生记录列表，分析器借用记录列表生成汇总，CLI 或 API 再把结果输出。

![Rust 所有权数据流](/assets/diagrams/rust-ownership-borrowing-data-flow.svg)

数据流里最重要的设计是减少无意义复制。解析器拥有新建的 `Vec<LogRecord>`；分析器只读它；报告输出和 API 返回需要序列化时再按边界生成目标格式。

## 逐步实现

日志记录结构体拥有自己的字段：

```rust
pub struct LogRecord {
    pub timestamp: String,
    pub level: Level,
    pub service: String,
    pub message: String,
    pub latency_ms: Option<u64>,
    pub fields: BTreeMap<String, String>,
}
```

`String` 表示记录拥有文本内容。这样解析函数返回后，记录不再依赖原始文件字符串的生命周期。对入门项目来说，这比让每个字段都借用原始字符串更直接。

汇总函数只需要读记录：

```rust
pub fn summarize(records: &[LogRecord], config: &AppConfig) -> Summary
```

`&[LogRecord]` 是切片借用，表示函数可以遍历记录，但不会拿走记录所有权。调用者之后仍然可以把同一组记录写成 CSV 或交给 HTTP API。

HTTP API 的状态需要被多个 handler 共享：

```rust
pub struct AppState {
    records: Arc<Vec<LogRecord>>,
    config: AppConfig,
}
```

`Arc` 是原子引用计数指针，适合在异步服务里共享只读数据。这里没有让 handler 修改记录，所以不需要 `Mutex`。这是 Rust 工程里很常见的判断：先问数据是否真的需要可变共享，再决定同步原语。

本地 lab 证明同一份解析结果可以被多条路径使用：

```text
== CLI summarize ==
summary written total=6 errors=2 warnings=1 slow_events=1
== API smoke ==
/api/summary 200
/api/events 200
```

CLI 和 API 使用同一组核心模块，数据边界没有分裂成两套实现。

## 常见错误

1. **为了绕过借用错误到处 `.clone()`**：复制能让代码暂时编译，但会隐藏真实的数据所有权设计问题。
2. **把 `Arc<Mutex<Vec<_>>>` 当作默认共享方式**：如果 handler 只读数据，`Arc<Vec<_>>` 更简单。
3. **让记录字段借用临时字符串**：入门项目先让记录拥有字段，生命周期会清楚很多。

## 练习或延伸

- 把 `Summary` 中的 `service_counts` 排序逻辑改成按错误数降序，观察需要拥有还是借用中间数据。
- 尝试让 `LogRecord` 字段改成 `&str`，记录编译器会要求你补充哪些生命周期关系。

## 参考资料

- [Rust Book: Ownership](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html)
- [Rust Book: References and Borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html)
- [std::sync::Arc](https://doc.rust-lang.org/std/sync/struct.Arc.html)
