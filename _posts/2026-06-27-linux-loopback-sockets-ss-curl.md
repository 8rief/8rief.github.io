---
layout: post
title: "Loopback 服务和 ss：从监听端口看到 TCP 连接"
date: 2026-06-27 23:01:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "启动一个本地 HTTP 服务，用 ss 和 curl 观察监听端口、连接阶段和响应状态。"
tags: [linux, tcp, ss, curl, loopback]
---
{% raw %}

> 主题：Linux 网络与授权安全基础 / loopback / socket
> 本文对应 lab 的本地 HTTP 服务启动与 `ss` 观察。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

TCP 服务要先监听地址和端口，客户端才能连接。把服务绑定在 `127.0.0.1:18480` 后，`ss -ltn` 能看到监听 socket，`curl -v` 能看到连接、请求、响应和关闭四个阶段。

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
python3 -m local_netsec_lab.cli server   --host 127.0.0.1   --port 18480   --public-dir sample_public   --outside-dir outside_area
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

## 连接阶段怎样判断

- `Connection refused` 通常说明端口没有监听，或服务刚停止。
- `Connected` 后出现 404、405、500，说明 TCP 已建立，问题进入 HTTP 或应用层。
- 健康检查 200 只证明 `/health` 正常，不能代表所有路径都安全。

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
- Python 文档：[http.server](https://docs.python.org/3/library/http.server.html)


{% endraw %}
