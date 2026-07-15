---
layout: post
title: "Rust clap CLI：用子命令组织用户可复用的入口"
date: 2026-05-13 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [rust, clap, cli, teaching]
---

## 学习目标

这一篇把核心库包装成用户能复用的 CLI。读完以后，你应该能说明：

1. 为什么 `summarize` 和 `serve` 要做成子命令；
2. `clap` derive 如何把结构体变成命令行接口；
3. 用户可见错误应该在入口层带上上下文，而核心库保持可测试。

## 先修知识

需要知道 CLI 参数都是字符串，程序要把它们解析成路径、地址、数字或枚举。一个稳定 CLI 应该能通过 `--help` 解释自己。

## 核心模型

CLI 是用户和核心库之间的协议层。

![Rust clap CLI 子命令](/assets/diagrams/rust-clap-cli-subcommands-errors.svg)

`main.rs` 不负责解析日志细节，它只负责把用户输入转换成核心函数调用。这样同一套核心逻辑可以被 CLI、测试和 HTTP API 复用。

## 为什么需要 clap 子命令

日志工具有两种用户任务：一次性生成报告，或启动本地 API。把它们挤在同一个命令里，会出现大量互斥参数；使用 `summarize` 和 `serve` 子命令能把行为边界写进 CLI 结构。

`clap derive` 解决的是字符串参数到类型的转换。路径变成 `PathBuf`，监听地址变成 `SocketAddr`，子命令变成 enum 分支。入口层拿到的已经是较清楚的数据结构，而不是到处手写字符串解析。

CLI 错误也应该停在入口层。核心库负责可测试逻辑，入口层给用户提供 `--help`、版本、参数默认值和错误上下文。这样同一套核心逻辑才能被 tests 和 API 复用。

## 逐步实现

先定义顶层 CLI：

```rust
#[derive(Debug, Parser)]
#[command(name = "rust-log-insight", version, about = "Summarize local structured logs")]
struct Cli {
    #[arg(long, default_value = "sample_config/log-insight.toml", global = true)]
    config: PathBuf,
    #[command(subcommand)]
    command: Command,
}
```

`global = true` 表示 `--config` 可以放在子命令前面。用户不需要为每个子命令重复配置字段。

子命令表达两个用户任务：

```rust
enum Command {
    Summarize { input: PathBuf, json: PathBuf, csv: PathBuf },
    Serve { input: PathBuf, addr: SocketAddr },
}
```

实验里的 CLI 命令是：

```bash
./target/debug/rust-log-insight-cli   --config sample_config/log-insight.toml   summarize   --input sample_logs/app.log   --json reports/summary.json   --csv reports/events.csv
```

输出摘要进入结构化日志：

```text
summary written total=6 errors=2 warnings=1 slow_events=1 json=reports/summary.json csv=reports/events.csv
```

`--help` 也被放进 transcript：

```text
Commands:
  summarize  Parse a log file and write summary JSON plus event CSV
  serve      Serve the same summary through a local HTTP API
```

这说明 CLI 已经具备清楚的用户入口，可以作为工具被复用。

## 输出怎么读

`--help` 是 CLI 合同的一部分，lab 会把它保存进 transcript：

```text
Commands:
  summarize  Parse a log file and write summary JSON plus event CSV
  serve      Serve the same summary through a local HTTP API
```

这两行说明用户入口已经分成两个明确任务。`summarize` 需要输入日志、JSON 输出和 CSV 输出；`serve` 需要输入日志和监听地址。

CLI summary 的日志是：

```text
summary written total=6 errors=2 warnings=1 slow_events=1 json=reports/summary.json csv=reports/events.csv
```

如果命令失败，先看是 clap 参数解析失败，还是配置/日志/输出文件失败。子命令边界能帮助你把错误定位到用户输入还是核心处理。

## 常见错误

1. **把所有选项放在一个命令里**：`--serve --summary --json` 这种组合会让行为边界混乱。子命令更清楚。
2. **手写参数解析**：短脚本可以，教学项目要展示主流库的稳定用法。
3. **错误消息只打印底层失败**：入口层要补充当前正在读哪个配置、写哪个报告。

## 练习或延伸

- 增加 `validate` 子命令，只检查配置和日志格式，不写报告。
- 给 `summarize` 增加 `--min-level ERROR`，观察枚举参数应如何解析。

## 参考资料

- [clap crate documentation](https://docs.rs/clap/)
- [clap derive tutorial](https://docs.rs/clap/latest/clap/_derive/_tutorial/index.html)
- [std::path::PathBuf](https://doc.rust-lang.org/std/path/struct.PathBuf.html)
