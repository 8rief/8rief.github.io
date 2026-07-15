---
layout: post
title: "Loopback 服务和 ss：从监听端口看到 TCP 连接"
date: 2026-05-22 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "启动一个本地 HTTP 服务，用 ss 和 curl 观察监听端口、连接阶段和响应状态。"
tags: [linux, tcp, ss, curl, loopback]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/linux-network-security-basics/README.md`](/assets/labs/linux-network-security-basics/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：Linux 网络与授权安全基础 / loopback / socket
> 本文对应 lab 的本地 HTTP 服务启动与 `ss` 观察。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

TCP 服务要先监听地址和端口，客户端才能连接。把服务绑定在 `127.0.0.1:18480` 后，`ss -ltn` 能看到监听 socket，`curl -v` 能看到连接、请求、响应和关闭四个阶段。

## 为什么需要同时看服务端和客户端

单看应用日志会漏掉“请求根本没有到达进程”的情况；单看 `curl` 又无法确认哪个进程、哪个地址正在监听。`ss` 提供内核的 socket 视角，`curl -v` 提供客户端的协议视角。两边证据合在一起，才能把连接失败定位到监听、TCP 或 HTTP。

loopback 还提供了可控边界：报文经过本机网络栈，但不需要外部主机。它适合观察 bind、listen、connect 和 HTTP handler 的先后关系。

## 学习目标

1. 启动一个只监听 loopback 的本地服务。
2. 用 `ss -ltn` 确认端口处于 LISTEN 状态。
3. 用 `curl -v` 观察 TCP 连接和 HTTP 响应。
4. 区分连接阶段错误和 HTTP 状态错误。

## 先修知识

需要知道 TCP 端口和 HTTP URL 的基本格式。

## 核心模型

![Loopback 监听与 curl 连接](/assets/diagrams/linux-loopback-sockets-ss-curl.svg)

服务端监听 socket，客户端建立连接，HTTP 请求在连接上发送。`ss` 观察系统 socket，`curl` 观察客户端视角。

## 逐步实现

lab 通过脚本启动服务：

```bash
PYTHONPATH=src python3 -m local_netsec_lab.cli server \
  --host 127.0.0.1 \
  --port 18480 \
  --public-dir sample_public \
  --outside-dir outside_area
```

健康检查返回：

```json
{"bind": "127.0.0.1", "status": "ok"}
```

端口监听证据来自：

```bash
ss -ltn | grep ':18480'
```

transcript 中可以看到 `127.0.0.1:18480` 处于 `LISTEN`。随后运行：

```bash
curl -v -sS http://127.0.0.1:18480/health
```

`curl -v` 记录了 `Trying`、`Connected`、`GET /health`、`HTTP/1.0 200 OK` 和响应头。这个输出比单独看响应体更适合排障。

verbose 信息默认写到 stderr，响应体写到 stdout。lab 用 `-o` 保存 body，并把 stderr 单独重定向到 transcript，避免两类证据混在一起：

```bash
curl -v -sS http://127.0.0.1:18480/health \
  -o reports/health_body.json \
  2> reports/curl_health_verbose.txt
```

## socket 状态如何变化

服务端先执行 bind，再进入 listen；客户端 connect 成功后，双方才有一条已建立连接。对这次请求，可以用四元组理解端点：

```text
client = 127.0.0.1:<临时端口>
server = 127.0.0.1:18480
protocol = TCP
application = HTTP /health
```

`LISTEN` socket 只保存服务端本地端点并等待新连接。每次 accept 会产生新的 connected socket；短请求结束后，connected socket 很快消失，而监听 socket 继续存在。

为了减少 `ss` 输出噪声，可以按源端口过滤：

```bash
ss -ltn 'sport = :18480'
```

`Recv-Q`、`Send-Q` 与 backlog 的含义随 socket 状态而变，初学时先确认 `Local Address:Port` 和 `LISTEN`，不要把队列数字当作业务吞吐量。

## 连接阶段怎样判断

- `Connection refused` 通常说明端口没有监听，或服务刚停止。
- `Connected` 后出现 404、405、500，说明 TCP 已建立，问题进入 HTTP 或应用层。
- 健康检查 200 只证明 `/health` 正常，不能代表所有路径都安全。

脚本不能在启动进程后立刻假设服务可用。当前 `run_lab.sh` 最多轮询 60 次，每次间隔 0.1 秒，直到 `/health` 成功；若始终失败，后续步骤会因缺少健康响应而停止。这个 readiness check 消除了常见的启动竞态。

## 退出状态和 HTTP 状态不是一回事

默认情况下，curl 收到 HTTP 404 仍可能返回进程退出状态 0，因为网络传输本身成功。自动化若要把 4xx/5xx 当失败，可以使用：

```bash
curl --fail-with-body -sS http://127.0.0.1:18480/missing
echo "$?"
```

当前端点会显示错误响应体，并返回非零退出状态。排障时同时记录 curl 退出状态和 HTTP status，才能区分传输失败与应用响应。

## 常见错误

1. **只看端口号。** 端口要和 bind 地址一起看。
2. **把 LISTEN 当作业务成功。** LISTEN 只说明服务在等连接。
3. **隐藏 `curl -v`。** 排障阶段需要看到请求头和响应头。
4. **忽略服务启动时机。** 自动化脚本要等待 `/health` 可达后再测试。

## 练习或延伸

1. 修改服务端口为 `18482`，同时更新 `curl` 和 `ss` 命令。
2. 访问不存在的 `/missing`，比较 TCP 成功和 HTTP 404 的区别。
3. 用 `curl -I` 发送 HEAD 请求，观察响应头。

## 参考资料

- Linux man-pages：[ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html)
- curl 文档：[curl man page](https://curl.se/docs/manpage.html)
- curl 文档：[`--fail-with-body`](https://curl.se/docs/manpage.html#--fail-with-body)
- Python 文档：[socket](https://docs.python.org/3/library/socket.html)
- Python 文档：[http.server](https://docs.python.org/3/library/http.server.html)


{% endraw %}
