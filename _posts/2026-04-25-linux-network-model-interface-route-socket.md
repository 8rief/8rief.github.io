---
layout: post
title: "Linux 网络模型：interface、route、socket 和 resolver 如何连起来"
date: 2026-04-25 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 interface、route、socket、resolver 四个状态解释 Linux 网络排障的第一张图。"
tags: [linux, networking, resolver, socket, teaching]
---
{% raw %}

> 主题：Linux 网络与授权安全基础 / 网络心智模型
> 本文是本地网络安全基础包的第一篇。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

学习网络排障不能先背命令。更稳的入口是把一次连接拆成四个状态：网卡或 loopback 提供地址，路由表决定下一跳，socket 表示进程打开的通信端点，resolver 把名字解析成地址。后续 `ss`、`curl`、服务映射和 HTTP 边界都围绕这四个状态展开。

## 为什么需要分层心智模型

一个 URL 同时包含名字、端口和资源路径，但操作系统不会把它们作为一个整体处理。resolver 先产生候选地址，路由表为目标地址选择接口与源地址，TCP 连接到远端 socket，最后 HTTP handler 才解释 `/health`。每一层都有独立状态和独立错误。

分层的价值在于缩小搜索范围。名字已解析时无需反复改 DNS；端口拒绝连接时无需先检查 JSON；HTTP 返回 404 时也无需怀疑网卡消失。

## 学习目标

1. 解释 interface、route、socket、resolver 的职责。
2. 区分地址、端口、进程和 HTTP 资源路径。
3. 用本机 loopback 建立安全实验边界。
4. 知道遇到连接失败时先检查哪几类状态。

## 先修知识

需要知道命令行、IP 地址、端口号和 HTTP URL 的基本写法。

## 核心模型

![Linux 网络四层观察模型](/assets/diagrams/linux-network-model-interface-route-socket.svg)

`127.0.0.1` 指向本机 loopback。服务监听端口后，客户端连接同一台机器上的 socket。名字解析只负责把 `localhost` 等名字变成地址，HTTP 路径在 TCP 连接建立后才进入应用层。

## 逐步实现

先观察 loopback interface 与路由：

```bash
ip -brief address show lo
ip route get 127.0.0.1
```

当前机器的关键片段是：

```text
lo  ...  127.0.0.1/8  ...  ::1/128
local 127.0.0.1 dev lo src 127.0.0.1
```

第一行说明 `lo` 拥有 IPv4/IPv6 loopback 地址；第二行说明发往 `127.0.0.1` 的流量使用 `lo`，源地址也是 `127.0.0.1`。省略号代表与本课无关、且会因 WSL/发行版而变化的本机地址。

再观察 resolver：

```bash
getent hosts localhost
grep -E '^(nameserver|search|options)' /etc/resolv.conf
```

本地 transcript 中得到：

```text
::1             localhost
```

`getent` 证明系统名字服务能返回 loopback；它不证明结果一定来自 DNS。nameserver 的具体私有地址是环境状态，不写入公开示例。

再观察系统和工具：

```bash
python3 --version
uname -srm
command -v curl
command -v ss
```

本地 lab 记录了 Python 3.12.3、WSL2 Linux 内核、`curl` 和 `ss` 的位置。这里不需要外网目标，因为后续服务由 lab 在 loopback 上启动。

## 四类对象不要混用

| 对象 | 当前例子 | 回答的问题 |
|---|---|---|
| interface | `lo` | 本机有哪些网络端点 |
| route | `local ... dev lo` | 目标地址交给哪个接口 |
| socket | `127.0.0.1:18480` | 哪个传输端点正在监听 |
| resolver result | `localhost → ::1/127.0.0.1` | 名字有哪些候选地址 |
| HTTP path | `/health` | 连接建立后调用哪个资源 |

这里特意多列一行 HTTP path，因为初学者最容易把它和端口混在一起。内核路由表不认识 `/health`；HTTP server 也不会替你选择网卡。

## 从连接失败倒推

一次 `curl http://127.0.0.1:18480/health` 失败时，按这个顺序检查：

1. 地址是否指向预期主机，当前 lab 只允许 loopback。
2. 服务是否监听端口，可用 `ss -ltn` 查。
3. TCP 是否建立，可用 `curl -v` 看连接阶段。
4. HTTP 状态码、响应头和响应体是否符合预期。

可以把命令和失败层对应起来：

```text
getent hosts <name>        -> resolver
ip route get <address>     -> route / source address
ss -ltn 'sport = :<port>'  -> listening socket
curl -v <url>              -> connect + HTTP exchange
```

如果 URL 使用 `localhost`，curl 可能先尝试 `::1`。当前教学服务只绑定 `127.0.0.1`，所以 IPv6 尝试可能失败后再回退到 IPv4。根因是 resolver 给出多个候选地址，而服务只监听其中一个。

## 可观察状态与结论边界

一次本地 200 只能证明当前进程、当前 namespace、当前时刻的 `/health` 可用。容器有自己的 network namespace，防火墙可能区分接口，生产代理还会增加 TLS 和上游转发。先掌握这条最短路径，再逐层增加组件，才能知道新增状态来自哪里。

## 常见错误

1. **把 URL 路径当端口。** `:18480` 是端口，`/health` 是应用层路径。
2. **忽略 bind 地址。** 服务绑定 `127.0.0.1` 只接受本机连接，绑定 `0.0.0.0` 会暴露给更多网络接口。
3. **只看应用日志。** 如果 socket 没有监听，应用日志可能没有请求记录。
4. **把 DNS 问题和 TCP 问题混在一起。** 先确认名字解析，再确认连接。

## 练习或延伸

1. 用 `getent hosts localhost` 和 `getent hosts 127.0.0.1` 比较输出。
2. 在服务启动前运行 `ss -ltn | grep 18480`，再启动服务后重复一次。
3. 画出你机器上 `curl -> socket -> HTTP handler` 的路径。

## 参考资料

- Linux man-pages：[resolv.conf(5)](https://man7.org/linux/man-pages/man5/resolv.conf.5.html)
- Linux man-pages：[ip-address(8)](https://man7.org/linux/man-pages/man8/ip-address.8.html)
- Linux man-pages：[ip-route(8)](https://man7.org/linux/man-pages/man8/ip-route.8.html)
- Linux man-pages：[ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html)
- curl 文档：[curl man page](https://curl.se/docs/manpage.html)


{% endraw %}
