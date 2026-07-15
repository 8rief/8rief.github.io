---
layout: post
title: "Go 项目收尾：测试、README、demo transcript 和发布检查"
date: 2026-04-06 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [go, tests, readme, demo, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/go-health-monitor-service/README.md`](/assets/labs/go-health-monitor-service/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

## 学习目标

这一篇做项目收尾。读完以后，你应该能判断一个 Go 教学项目是否已经达到“可以展示”的最低标准：

1. 有可重复运行的测试；
2. 有一条从构建到 CLI 再到 API 的 demo transcript；
3. README 能说明运行方式、预期产物和实验边界。

## 先修知识

需要把测试、README 和 transcript 当成复现证据。它们共同回答“这个项目能否被别人复现”。

## 核心模型

项目收尾的重点是把证据链补齐。

![Go 项目收尾证据链](/assets/diagrams/go-project-tests-readme-demo.svg)

这条证据链从源码开始，经过格式化、测试、构建、CLI、报告、API smoke，最后形成 README 和 transcript。任何一环断掉，文章里的命令就只是描述，不能算已验证教程。

## 为什么需要收尾证据链

一个教学项目能运行一次，还不能说明它可以展示。读者需要知道如何复现，维护者需要知道改动后怎样判断没有破坏功能。测试、README、demo transcript 和报告文件共同解决的是可交付性问题。

测试负责断言稳定行为：配置校验、请求检查、报告写入和 API handler。README 负责告诉读者从哪里开始。transcript 负责保存实际运行过程，避免文章只停留在描述。JSON/CSV 报告和 API smoke 则给出可见结果。

这条证据链也能防止教程变浅。每个命令都要有输出，每个输出都要能解释，失败路径也要有边界。这样项目才是一个可以学习、可以复跑、可以继续扩展的基础包。

## 逐步实现

实验脚本按固定顺序执行：

```bash
./run_lab.sh
```

它做了这些事情：

```text
== environment ==
go version go1.26.4 linux/amd64
== tests ==
ok  example.com/go-health-monitor-service/internal/checker
ok  example.com/go-health-monitor-service/internal/config
ok  example.com/go-health-monitor-service/internal/monitorserver
ok  example.com/go-health-monitor-service/internal/report
== build ==
== start demo target server ==
ready http://127.0.0.1:18191/ok status=200
== CLI check ==
level=INFO msg="checks finished" ok=2 total=3
== start monitor API ==
ready http://127.0.0.1:18190/health status=200
== API smoke ==
http://127.0.0.1:18190/health 200
http://127.0.0.1:18190/api/checks 200
== done ==
```

测试层覆盖：

- `config`：接受 loopback，拒绝外部 host，拒绝重复名字；
- `checker`：记录非 2xx/3xx 状态，响应 context 超时，保持结果顺序；
- `report`：JSON 和 CSV 可以被读取；
- `monitorserver`：API 能执行检查，demo target 能返回稳定状态。

README 至少要说明三件事：

```text
1. 如何运行：./run_lab.sh
2. 会产生什么：bin/healthmon、reports/results.json、reports/results.csv、reports/transcript.txt
3. 实验边界：配置只接受 loopback host，默认不会访问第三方目标
```

最后再检查公开文章本身：文章不应该包含本机绝对路径、内部任务笔记、凭据、临时仓库名或生成痕迹。命令输出只保留读者理解所需的片段。

## 输出怎么读

`run_lab.sh` 的顺序就是验收顺序：

```text
== format ==
== tests ==
== build ==
== start demo target server ==
== CLI check ==
== start monitor API ==
== API smoke ==
== done ==
```

`format` 阶段确保源码格式一致，`tests` 固定包级行为，`build` 生成 `bin/healthmon`，demo server 提供稳定本地目标，CLI check 生成 `reports/results.json` 和 `reports/results.csv`，API smoke 证明 HTTP 服务入口可用。

最终可展示产物是报告文件和 transcript：`reports/results.json` 适合程序读取，`reports/results.csv` 适合表格查看，`reports/transcript.txt` 说明命令确实跑过。若只保留 README 而没有 transcript，读者仍然不知道当前版本是否真的复现过。

## 常见错误

1. **只写 README，不保存 transcript**：README 是说明，transcript 是执行证据，两者不能互相替代。
2. **只测试成功路径**：这个项目专门保留 `/fail` 和超时测试，用来证明失败也被记录。
3. **把本机路径写进公开文章**：公开文章应该使用相对路径和可复现命令，不暴露个人工作目录。

## 练习或延伸

- 给项目加一个 `make test` 或 `just test` 入口，比较它和 `run_lab.sh` 的职责差异。
- 把结果 JSON 转成一个简单 HTML 表格页面，作为下一阶段 showcase 的静态产物。

## 参考资料

- [testing package](https://pkg.go.dev/testing)
- [net/http/httptest package](https://pkg.go.dev/net/http/httptest)
- [Go command documentation](https://pkg.go.dev/cmd/go)
