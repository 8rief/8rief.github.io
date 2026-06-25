---
layout: post
title: "Rust Tokio、Axum 和 tracing：把 CLI 核心发布成本地 API"
date: 2026-06-25 20:16:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [rust, tokio, axum, tracing, api, teaching]
---

## 学习目标

这一篇把日志分析核心发布成本地 HTTP API。读完以后，你应该能解释：

1. Tokio runtime 在异步服务里的作用；
2. Axum router 怎样复用核心库逻辑；
3. tracing 日志怎样记录服务启动、请求结果和关闭边界。

## 先修知识

需要知道 HTTP API 是长时间运行的服务进程，默认应该绑定在本机地址。这里的 API 只读取本地样例日志，不连接外部服务。

## 核心模型

API 层只做三件事：启动监听、暴露路由、调用核心汇总函数。

![Rust Axum API 服务路径](/assets/diagrams/rust-axum-tokio-tracing-api.svg)

`/health` 说明服务进程活着，`/api/summary` 返回汇总，`/api/events` 返回解析后的事件。它们都不重新实现解析规则。

## 逐步实现

入口函数使用 Tokio runtime：

```rust
#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt().init();
    run(Cli::parse()).await
}
```

router 组合三个路由：

```rust
Router::new()
    .route("/health", get(health))
    .route("/api/summary", get(summary))
    .route("/api/events", get(events))
    .with_state(AppState::new(records, config))
```

状态对象保存记录和配置：

```rust
pub struct AppState {
    records: Arc<Vec<LogRecord>>,
    config: AppConfig,
}
```

`summary` handler 调用核心函数：

```rust
async fn summary(State(state): State<AppState>) -> Json<Summary> {
    Json(analyzer::summarize(&state.records, &state.config))
}
```

服务启动命令是：

```bash
./target/debug/rust-log-insight-cli   --config sample_config/log-insight.toml   serve   --input sample_logs/app.log   --addr 127.0.0.1:18220
```

实验 smoke 覆盖了三个端点：

```text
http://127.0.0.1:18220/health 200
http://127.0.0.1:18220/api/summary 200
http://127.0.0.1:18220/api/events 200
```

`tracing` 日志记录服务启动和 CLI summary：

```text
summary written total=6 errors=2 warnings=1 slow_events=1
```

这比随手 `println!` 更适合服务项目，因为字段能被过滤、采集和复查。

## 常见错误

1. **API handler 里复制 CLI 逻辑**：这会产生两套统计语义，后期很难保持一致。
2. **默认监听 `0.0.0.0`**：教学服务默认只绑定 `127.0.0.1`，先保持本机边界。
3. **用普通打印替代结构化日志**：服务排错需要字段化上下文，`tracing` 更适合。

## 练习或延伸

- 增加 `/api/services/:name`，只返回某个 service 的事件。
- 给 `serve` 增加 `--reload` 思路说明：每次请求重新读文件还是使用文件 watcher，各有什么代价。

## 参考资料

- [Tokio tutorial](https://tokio.rs/tokio/tutorial)
- [Axum crate documentation](https://docs.rs/axum/)
- [tracing crate documentation](https://docs.rs/tracing/)
