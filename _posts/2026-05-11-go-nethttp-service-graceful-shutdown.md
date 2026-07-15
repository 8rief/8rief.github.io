---
layout: post
title: "Go net/http 服务：路由、API 和优雅关闭"
date: 2026-05-11 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [go, net-http, api, service, teaching]
---

## 学习目标

这一篇把检查逻辑发布成本地 HTTP API。读完以后，你应该能完成：

1. 用 `http.NewServeMux` 定义 `/health` 和 `/api/checks`；
2. 让 API handler 调用同一套检查逻辑；
3. 用信号和 `Server.Shutdown` 做优雅关闭。

## 先修知识

需要知道 HTTP server 是一个长时间运行的进程。它要监听地址、处理请求，并在收到关闭信号时停止接收新请求、等待已有请求结束。

## 核心模型

服务层不应该复制 CLI 的业务逻辑。CLI 和 API 都调用 `checker.CheckAll`，只是触发方式不同。

![Go net/http 服务路径](/assets/diagrams/go-nethttp-service-graceful-shutdown.svg)

`/health` 用来证明监控服务本身活着；`/api/checks` 执行一次目标检查并返回 JSON 数组。

## 为什么需要 HTTP API 和优雅关闭

CLI 适合脚本触发一次检查，但很多项目还需要一个长期运行的服务，让浏览器、前端页面或其他本地工具按需请求检查结果。HTTP API 解决的是交互入口问题：同一套 `checker.CheckAll` 逻辑可以通过 `/api/checks` 暴露出来。

优雅关闭解决的是进程生命周期问题。服务正在处理请求时直接杀进程，客户端可能拿到半截响应，日志也可能丢失。`Server.Shutdown` 在收到信号后停止接收新连接，并给已有请求一个限定时间完成。

本 lab 默认监听 `127.0.0.1`，因为它是教学和本地实践，不需要暴露到局域网。先保证本机 API 可复现，再讨论反向代理、TLS 和公开部署。

## 逐步实现

handler 构造函数接收目标、client、worker 数、超时和 logger：

```go
func NewMonitorHandler(targets []config.Target, client checker.HTTPClient, workers int, timeout time.Duration, logger *slog.Logger) http.Handler
```

健康检查接口很小：

```go
mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
    writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
})
```

检查接口给每个请求设置上下文超时：

```go
mux.HandleFunc("GET /api/checks", func(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), timeout)
    defer cancel()
    results := checker.CheckAll(ctx, client, targets, workers)
    writeJSON(w, http.StatusOK, results)
})
```

服务启动和关闭由统一函数处理：

```go
server := &http.Server{
    Addr:              addr,
    Handler:           handler,
    ReadHeaderTimeout: 2 * time.Second,
}
```

`ReadHeaderTimeout` 是一个基本防护：如果客户端连上后迟迟不发完请求头，server 不会无限等待。

实验中 API smoke 的输出是：

```text
http://127.0.0.1:18190/health 200
{
  "status": "ok"
}
http://127.0.0.1:18190/api/checks 200
[
  {"name":"demo-ok","ok":true,"status_code":200},
  {"name":"demo-fail","ok":false,"status_code":500},
  {"name":"demo-slow","ok":true,"status_code":200}
]
```

## 输出怎么读

API smoke 有两段：

```text
http://127.0.0.1:18190/health 200
{
  "status": "ok"
}
```

这说明监控服务本身可用。第二段访问检查接口：

```text
http://127.0.0.1:18190/api/checks 200
[
  {"name":"demo-ok","ok":true,"status_code":200},
  {"name":"demo-fail","ok":false,"status_code":500},
  {"name":"demo-slow","ok":true,"status_code":200}
]
```

`/api/checks` 返回的是实时执行的检查结果，不是直接读取 CLI 生成的 `results.json`。这证明 CLI 和 API 复用了同一套业务逻辑，但触发入口不同。若 `/health` 正常而 `/api/checks` 失败，优先检查配置读取、目标服务和 timeout。

## 常见错误

1. **API handler 里重新解析文件**：如果每次请求都读配置，性能和错误边界会变复杂。入门项目先在启动时读取配置。
2. **关闭时直接杀进程**：`Server.Shutdown` 能让已有请求在限定时间内完成。
3. **把服务监听到 `0.0.0.0` 当默认值**：教学实验默认监听 `127.0.0.1`，先保持本机可见。

## 练习或延伸

- 给 `/api/checks` 增加 `?workers=1` 查询参数，并限制最大值。
- 增加 `/api/targets`，只返回配置中的目标名和 URL，便于调试。

## 参考资料

- [net/http package](https://pkg.go.dev/net/http)
- [os/signal package](https://pkg.go.dev/os/signal)
- [http.Server.Shutdown](https://pkg.go.dev/net/http#Server.Shutdown)
