---
layout: post
title: "Go HTTP client：超时、状态码和本地目标边界"
date: 2026-05-10 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [go, http, timeout, teaching]
---

## 学习目标

这一篇讲健康检查器的网络核心。读完以后，你应该能解释：

1. 一次 HTTP 检查包含哪些可观测结果；
2. 为什么必须设置超时；
3. 为什么状态码失败和请求错误要分开记录。

## 先修知识

需要知道 HTTP 请求由 client 发起，server 返回状态码和响应体。状态码 200 到 399 通常表示请求成功或可接受的重定向；500 表示服务端错误。

## 核心模型

一次检查可以被拆成五个状态：构造请求、发送请求、等待响应、解释状态码、记录延迟。

![Go HTTP client 检查路径](/assets/diagrams/go-http-client-timeout-boundary.svg)

在这个模型里，超时属于网络边界的核心约束。没有超时，单个慢目标就可能拖住整批检查。

## 为什么需要 HTTP timeout 边界

健康检查器面对的是网络和服务状态，最危险的默认行为是无限等待。一个目标迟迟不返回，如果没有超时，会拖住 worker，进而拖住整批报告。timeout 边界解决的是可结束性：每次请求和每轮检查都必须在可解释的时间内完成。

状态码和请求错误也要分开。HTTP 500 表示服务端返回了响应，但业务上不健康；连接失败、DNS 错误、context 超时表示请求没有正常完成。把二者都写成同一种错误，会让后续报告无法判断目标到底是“返回失败状态”还是“无法请求”。

本 lab 使用本地 demo server 保证输出稳定：`/ok`、`/fail`、`/slow` 分别覆盖成功、状态失败和慢响应。初学者先用可控目标理解 client 行为，再把同样模型迁移到授权的真实服务。

## 逐步实现

检查函数接收 `context.Context`、HTTP client 和目标：

```go
func Check(ctx context.Context, client HTTPClient, target config.Target) Result {
    start := time.Now()
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, target.URL, nil)
    // send request and record result
}
```

`NewRequestWithContext` 把取消信号绑定到请求上。上层如果设置了 900ms 超时，请求超过这个时间就会尽快返回错误。

CLI 入口创建 client 时也设置了超时：

```go
client := &http.Client{Timeout: *timeout}
```

context 和 client timeout 的侧重点不同：context 表示这一轮操作的生命周期；client timeout 表示单次 HTTP 操作的硬边界。教学项目里两者都保留，便于读者观察控制流。

实验中的三个本地目标分别返回：

```text
demo-ok   -> status 200, ok=true
demo-fail -> status 500, ok=false
demo-slow -> status 200, ok=true, latency around 200ms
```

JSON 片段显示了这种差异：

```json
{
  "name": "demo-fail",
  "url": "http://127.0.0.1:18191/fail",
  "ok": false,
  "status_code": 500,
  "latency_ms": 1,
  "checked_at": "2026-07-03T14:21:00Z"
}
```

这里没有 `error` 字段，因为请求成功到达 server，只是 server 返回了不健康状态。真正的请求失败会出现在 `error` 字段中。

## 输出怎么读

当前 JSON 报告里三类目标很清楚：

```text
demo-ok   status_code=200 ok=true
demo-fail status_code=500 ok=false
demo-slow status_code=200 ok=true latency_ms≈200
```

`demo-fail` 的关键是 `status_code=500` 且没有 `error` 字段。这说明 Go 的 `client.Do` 完成了请求，调用者需要自己解释状态码。`demo-slow` 仍然 `ok=true`，因为它在 `900ms` timeout 内返回了 200；如果把 `-timeout` 改成 `50ms`，它会更可能进入请求错误路径。

`checked_at` 使用 UTC RFC3339 时间，便于和日志、API 输出比较。`latency_ms` 是本地教学观察值，不应被当成性能基准；它只说明慢目标确实比普通目标等待更久。

排查网络检查器时，可以先只保留一个目标。单目标能稳定返回后，再增加失败目标和慢目标。这样你能分清是配置读取、请求执行、状态码解释还是并发调度出了问题。

对于真实服务，timeout 需要从业务需求出发设置。太短会把偶发慢响应误判为失败，太长会让批量报告迟迟不结束。本 lab 用 `900ms`，只是为了稳定覆盖 `/slow` 的约 200ms 延迟。

可以用下面的判断表定位结果：

```text
status_code=200..399, error empty  -> 目标健康
status_code=500, error empty       -> 请求成功，目标不健康
status_code=0, error non-empty     -> 请求没有正常完成
```

这张表比只看 `ok` 字段更适合排查。

## 常见错误

1. **把 HTTP 500 当作 Go error**：`client.Do` 只负责请求执行，状态码需要调用者解释。
2. **没有设置超时**：网络代码默认可能等待很久，服务监控必须给出明确时间边界。
3. **把公网 URL 放进入门实验**：教学实验默认只访问本地目标，降低误操作风险，也让输出稳定。

## 练习或延伸

- 把成功范围从 `200 <= code < 400` 改成只接受 2xx，观察 `/redirect` 目标应如何处理。
- 增加 `-timeout 50ms` 运行一次，让 `/slow` 进入请求错误路径。

## 参考资料

- [net/http package](https://pkg.go.dev/net/http)
- [context package](https://pkg.go.dev/context)
- [Go blog: Context](https://go.dev/blog/context)
