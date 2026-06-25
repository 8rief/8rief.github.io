---
layout: post
title: "Rust serde 文件边界：TOML 配置、JSON 汇总和 CSV 明细"
date: 2026-06-25 20:13:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [rust, serde, json, csv, toml, teaching]
---

## 学习目标

这一篇把 Rust 项目的文件输入输出讲清楚。读完以后，你应该能完成：

1. 用 `serde` 派生序列化和反序列化；
2. 用 TOML 保存配置，用 JSON 保存汇总，用 CSV 保存明细；
3. 理解每种文件格式适合放在哪个边界。

## 先修知识

需要知道配置、汇总和明细是三类不同文件。配置影响程序行为，汇总适合机器继续处理，明细适合表格工具或人工抽查。

## 核心模型

这个项目有三条文件路径：TOML 读入、JSON 写出、CSV 写出。

![Rust serde 文件边界](/assets/diagrams/rust-serde-json-csv-toml-files.svg)

TOML 面向人编辑；JSON 保留嵌套结构；CSV 是扁平表格。把三者混用会让后续维护变难。

## 逐步实现

配置结构体使用 `Deserialize`：

```rust
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AppConfig {
    pub error_rate_warning: f64,
    pub slow_latency_ms: u64,
}
```

样例配置很短：

```toml
error_rate_warning = 0.25
slow_latency_ms = 50
```

读取配置后立即校验：

```rust
anyhow::ensure!(
    (0.0..=1.0).contains(&self.error_rate_warning),
    "error_rate_warning must be between 0 and 1"
);
anyhow::ensure!(self.slow_latency_ms > 0, "slow_latency_ms must be positive");
```

汇总写成 JSON：

```rust
let text = serde_json::to_string_pretty(summary).context("encode summary JSON")?;
fs::write(path, format!("{text}
"))?;
```

实验输出证明 JSON 保留了层级：

```json
{
  "total": 6,
  "errors": 2,
  "warnings": 1,
  "slow_events": 1,
  "error_rate": 0.3333333333333333
}
```

明细写成 CSV：

```text
timestamp,level,service,message,latency_ms
2026-06-25T12:00:00Z,INFO,auth,login_ok,12
2026-06-25T12:00:01Z,WARN,billing,retry_scheduled,83
```

CSV 列固定后，读者可以直接用表格工具排序、筛选或导入后续分析脚本。

## 常见错误

1. **把配置写成 JSON**：机器当然能读，但手工编辑时 TOML 更直观。
2. **把汇总压成 CSV**：嵌套的 level/service 统计放进 CSV 会变成多张表或重复列，JSON 更自然。
3. **写文件前不创建目录**：报告路径里常有 `reports/` 子目录，输出函数要处理父目录。

## 练习或延伸

- 给配置增加 `ignored_services = ["worker"]`，让汇总跳过心跳日志。
- 把 `events.csv` 增加 `fields_json` 列，保存额外键值字段。

## 参考资料

- [serde crate](https://serde.rs/)
- [serde_json crate](https://docs.rs/serde_json/)
- [csv crate](https://docs.rs/csv/)
- [toml crate](https://docs.rs/toml/)
