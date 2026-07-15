---
layout: post
title: "Rust 所有权和借用：从日志记录的数据流理解安全边界"
date: 2026-05-12 09:00:00 +0800
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

## 为什么需要所有权数据流

日志分析项目会把同一份记录交给多个阶段：解析器创建记录，汇总器读取记录，CSV 输出读取记录，HTTP API 也要读取记录。如果每一步都复制整份数据，代码能跑但数据流会变得模糊；如果随意借用临时字符串，又会遇到生命周期问题。所有权设计解决的核心问题是让每份数据的负责人清楚。

本项目让 `LogRecord` 拥有字段值，因此解析完成后记录不依赖原始文本；`summarize(&[LogRecord], &AppConfig)` 只借用记录，不拿走所有权；API 用 `Arc<Vec<LogRecord>>` 共享只读记录。这个组合让 CLI 和 API 能复用同一批数据，又不需要可变共享。

判断是否需要 `clone`、`Arc` 或 `Mutex` 时，先问数据是否要被修改。只读共享用 `Arc` 就足够；需要并发修改时才考虑锁。这个顺序能减少为了绕过编译器而过度复制或过度加锁。

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

## 输出怎么读

lab 证明同一份数据被多个出口使用：

```text
== CLI summarize ==
summary written total=6 errors=2 warnings=1 slow_events=1
== API smoke ==
/api/summary 200
/api/events 200
```

CLI 阶段读取日志并生成 `Summary` 与 CSV；API 阶段读取同一份样例日志，返回 `/api/summary` 和 `/api/events`。如果核心逻辑被复制成两套实现，这两条路径很容易出现统计不一致。

`/api/events` 返回 6 条事件，字段包括 `timestamp`、`level`、`service`、`message`、`latency_ms` 和 `fields`。这说明解析后的 `LogRecord` 已经拥有足够的数据，handler 不需要重新读取原始日志文本。

如果编译器提示 borrowed value does not live long enough，先回到数据流图，确认返回值是否需要拥有数据。日志记录跨越 parser、analyzer、io 和 server 四个模块，选择拥有字段值能让这些边界更直接。

这类设计比事后到处补生命周期标注更适合入门项目。

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
