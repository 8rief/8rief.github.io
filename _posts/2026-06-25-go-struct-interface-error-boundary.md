---
layout: post
title: "Go 的 struct、interface 和 error：把监控结果写成清楚的边界"
date: 2026-06-25 19:31:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [go, struct, interface, error, teaching]
---

## 学习目标

这一篇把服务项目里的数据形状和错误边界写清楚。读完以后，你应该能解释：

1. 为什么 `Target` 和 `Result` 要用结构体表达；
2. 为什么检查器只依赖一个很小的 `HTTPClient` interface；
3. 为什么错误应该在边界处包上上下文，而不在底层直接退出程序。

## 先修知识

需要知道 Go 函数可以返回多个值，常见写法是 `(value, error)`。还需要知道 HTTP 请求可能成功返回非 2xx 状态码，也可能因为超时或连接失败没有拿到响应。

## 核心模型

项目里有三类边界：输入配置、一次检查结果、可替换的 HTTP 执行器。

![Go struct interface error 边界](/assets/diagrams/go-struct-interface-error-boundary.svg)

结构体负责把字段固定下来，interface 负责让检查器只依赖必要能力，error 负责把失败路径往调用层传递。三者合起来，才能让测试不用启动真实外部网络，也能覆盖请求失败、状态码失败和超时。

## 逐步实现

配置目标是一个结构体：

```go
type Target struct {
    Name string `json:"name"`
    URL  string `json:"url"`
}
```

检查结果也应该是结构体，因为它会同时被 JSON API、CSV 报告和测试使用：

```go
type Result struct {
    Name       string `json:"name"`
    URL        string `json:"url"`
    OK         bool   `json:"ok"`
    StatusCode int    `json:"status_code"`
    LatencyMS  int64  `json:"latency_ms"`
    Error      string `json:"error,omitempty"`
    CheckedAt  string `json:"checked_at"`
}
```

`OK` 不直接等同于“请求没有错误”。HTTP 500 能拿到响应，但业务上是不健康；超时拿不到响应，`StatusCode` 留在零值，错误写入 `Error` 字段。

检查器依赖的 interface 很小：

```go
type HTTPClient interface {
    Do(req *http.Request) (*http.Response, error)
}
```

这让生产代码可以传入 `*http.Client`，测试可以传入 `httptest` 的 client 或自定义 client。interface 没有暴露不需要的方法，调用者只承诺“能执行请求”。

错误处理放在可以补充上下文的位置：

```go
resp, err := client.Do(req)
if err != nil {
    result.Error = fmt.Sprintf("request failed: %v", err)
    result.LatencyMS = elapsedMillis(start)
    return result
}
```

底层检查函数返回 `Result`，命令入口再决定是否写文件、打日志或设置退出码。这样一个目标失败不会破坏整批检查。

本地测试覆盖了三个行为：HTTP 状态码、context 超时、并发结果顺序。实验 transcript 中可以看到：

```text
ok  example.com/go-health-monitor-service/internal/checker
ok  example.com/go-health-monitor-service/internal/config
ok  example.com/go-health-monitor-service/internal/monitorserver
ok  example.com/go-health-monitor-service/internal/report
```

## 常见错误

1. **用 `map[string]any` 传结果**：字段拼写错误要到运行时才暴露，CSV 和 API 也难以保持一致。
2. **interface 设计过大**：如果把整个服务对象塞进 interface，测试会为了满足无关方法而变复杂。
3. **遇到单个目标失败就 `os.Exit(1)`**：批量监控要保留所有目标的结果，退出码应该由入口层根据需求决定。

## 练习或延伸

- 给 `Result` 增加 `Category` 字段，把错误分成 `status`、`network`、`timeout` 三类。
- 写一个 fake client，让它不启动 HTTP server 也能返回固定响应，比较它和 `httptest` 的适用场景。

## 参考资料

- [The Go Programming Language Specification](https://go.dev/ref/spec)
- [Effective Go](https://go.dev/doc/effective_go)
- [Error handling and Go](https://go.dev/blog/error-handling-and-go)
