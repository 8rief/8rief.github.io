---
layout: post
title: "Go 工具链和 module：先把服务项目跑起来"
date: 2026-06-25 19:30:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [go, backend, module, teaching]
---

## 学习目标

这一篇先解决一个现实问题：刚开始写 Go 服务项目时，怎样确认工具链、模块边界和目录结构都能被别人复现。读完以后，你应该能完成三件事：

1. 用 `go version`、`go env` 和 `go test ./...` 检查项目环境；
2. 理解 `go.mod`、`cmd/`、`internal/` 在服务项目里的分工；
3. 把一个本地 HTTP 健康检查器构造成可以测试、构建和演示的最小项目。

## 先修知识

需要知道命令行的当前目录、相对路径、HTTP URL 的基本形式。暂时不需要掌握 Go 的并发，后面的文章会单独讲。

## 核心模型

Go 项目可以先按三个边界拆开：

![Go module 项目边界](/assets/diagrams/go-toolchain-module-project-layout.svg)

- `go.mod` 定义模块名和语言版本，是依赖解析和包导入的根；
- `cmd/healthmon` 放可执行程序入口，负责解析命令、打印日志和退出码；
- `internal/` 放只能被本模块使用的业务包，避免外部项目把教学内部结构当成公共 API。

这个拆法的价值在于让入口层和业务层分离。入口层处理命令行、文件路径和网络监听；业务层处理配置、检查逻辑、报告和 HTTP handler。测试应该尽量打在业务层，因为这里的状态变化最清楚。

## 逐步实现

先看模块文件：

```go
module example.com/go-health-monitor-service

go 1.22
```

模块名使用 `example.com/...`，这是教学项目的占位路径，不依赖真实远端仓库。`go 1.22` 表示源码按 Go 1.22 语言语义编译。实际实验环境用更新的 Go 工具链执行，工具链向后支持这个模块声明。

目录结构保持短而清楚：

```text
go-health-monitor-service/
  go.mod
  cmd/healthmon/main.go
  internal/config/config.go
  internal/checker/checker.go
  internal/report/report.go
  internal/monitorserver/server.go
  sample_config/targets.json
  run_lab.sh
  README.md
```

第一轮验证不看功能，只看项目是否能被工具链理解：

```bash
go version
go env GOOS GOARCH GOVERSION
go test ./...
go build -buildvcs=false -o bin/healthmon ./cmd/healthmon
```

`go test ./...` 会递归测试当前模块里的所有包；`go build` 指向入口包 `./cmd/healthmon`，输出一个可执行文件。实验脚本里加了 `-buildvcs=false`，原因是教学 lab 不一定在 Git 仓库内部，禁用 VCS stamping 可以让构建不依赖仓库元数据。

本地实验的关键输出是：

```text
== environment ==
go version go1.26.4 linux/amd64
linux
amd64
go1.26.4
== tests ==
ok  example.com/go-health-monitor-service/internal/checker
ok  example.com/go-health-monitor-service/internal/config
ok  example.com/go-health-monitor-service/internal/monitorserver
ok  example.com/go-health-monitor-service/internal/report
== build ==
```

这段输出证明四个业务包都通过测试，可执行程序也完成构建。

## 常见错误

1. **把所有代码写进 `main.go`**：短期省事，后面测试配置解析、HTTP 检查、报告输出时会被入口逻辑绑住。
2. **把教学内部包暴露成普通顶层包**：如果没有公共 API 需求，`internal/` 能明确告诉读者这些包只服务本项目。
3. **只运行 `go run`，不运行 `go test ./...`**：能启动不代表边界条件被验证。配置错误、超时、报告格式都需要单独测试。

## 练习或延伸

- 新增一个 `internal/version` 包，让 `healthmon help` 打印版本号，并为版本字符串写一个最小测试。
- 把 `go build` 输出路径改成 `dist/healthmon`，观察 README、脚本和忽略规则是否需要一起调整。

## 参考资料

- [Go installation documentation](https://go.dev/doc/install)
- [Go Modules Reference](https://go.dev/ref/mod)
- [go command documentation](https://pkg.go.dev/cmd/go)
