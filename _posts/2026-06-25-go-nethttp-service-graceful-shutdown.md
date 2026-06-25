---
layout: post
title: "Go net/http 服务：路由、API 和优雅关闭"
date: 2026-06-25 19:36:00 +0800
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
