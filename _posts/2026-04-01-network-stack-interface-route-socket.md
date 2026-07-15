---
layout: post
title: "网络栈基础：interface、route、socket 和 loopback 如何连起来"
date: 2026-04-01 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从本地 loopback lab 出发，把应用、socket、TCP/UDP、IP、路由和网卡接口放进同一个可操作模型。"
tags: [networking, linux, socket, route, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/network-foundations-nonsecurity/README.md`](/assets/labs/network-foundations-nonsecurity/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：非安全向计算机网络基础 / 网络栈模型
> 本文 lab 已验证：本地观测到 5 个 interface、4 条 route，TCP/UDP/HTTP demo 全部只走 `127.0.0.1`。

写网络程序时，很多错误来自一个模糊说法：“请求发到网络上了”。实际路径更具体：应用调用 socket API，选择 TCP 或 UDP，交给 IP 层做路由选择，最后从某个 interface 发出；如果目标是 `127.0.0.1`，数据会留在 loopback 路径内，不经过外部网络。

## 学习目标

1. 把应用代码、socket、传输层、IP、route 和 interface 放进同一个模型。
2. 理解 loopback 的用途：在本机复现网络行为，同时避免触碰外部主机。
3. 能读懂最小网络观测报告中的 interface、route、TCP、UDP 和 HTTP 字段。
4. 建立后续学习 IP、DNS、TCP、UDP 和 HTTP 的主线。

## 先修知识

需要会运行 Linux 命令，知道进程可以通过文件描述符读写数据。前置的 OS/Linux 文件与进程基础会帮助理解 socket 也是一种内核对象。

## 核心模型

![网络栈从应用到接口的路径](/assets/diagrams/network-stack-interface-route-socket.svg)

一次本地 HTTP 请求可以拆成六步：应用构造请求；socket API 创建连接；TCP 负责有序字节流；IP 层选择路由；loopback interface 承载本机到本机的数据；观测报告记录端口、状态、耗时和输出。

## 逐步实现

本文 package 的 lab 使用 Python 标准库创建本地 TCP echo、UDP echo 和 HTTP 服务，所有服务都绑定在 `127.0.0.1`。运行命令：

```bash
bash run_lab.sh
```

关键输出：

```text
interfaces=5 routes=4
localhost_dns_answers=3
tcp_echo=NETWORK-FOUNDATIONS tcp_bytes=1048576
udp_echo=UDP DATAGRAM
http_status=200 body_contains=True
```

这些输出分别对应网络栈里的不同层次。`interfaces` 和 `routes` 来自本机内核视图；`localhost_dns_answers` 来自 resolver；TCP/UDP/HTTP 的输出来自 loopback 上实际收发的数据。这个设计让我们能在一台机器上解释网络机制，不依赖外部站点的可用性。

## 为什么要引入分层网络模型

分层模型要解决的核心问题是“排查时不知道哪一层坏了”。同样是 `curl` 失败，可能是 hostname 没解析出地址，也可能是 route 没选对，可能是 TCP 连接被拒绝，也可能是 HTTP handler 返回了错误状态。把所有现象都叫“网络不通”，会让排查失去方向。

可以先按下面顺序拆：

```text
应用输入 -> resolver -> socket -> TCP/UDP -> IP route -> interface -> 对端服务 -> 应用协议输出
```

每一层都有自己的观测命令和失败形态。本文的 loopback lab 把变量固定在本机，让初学者先看清这些边界。

## 一次本地 HTTP 请求的状态变化

对 `http://127.0.0.1:PORT/hello?name=network` 发起请求时，状态变化可以拆成：

```text
1. Python HTTP server 绑定 127.0.0.1:PORT 并 listen
2. curl 解析 URL，得到 host=127.0.0.1、port=PORT、path=/hello?name=network
3. 客户端 socket connect 到 loopback 地址
4. TCP 建立连接并传输 HTTP 请求字节
5. server handler 读取 path，生成 JSON body
6. curl 接收 status line、headers 和 body
```

`127.0.0.1` 的关键作用是让第 3 步之后的数据留在本机网络栈内。这样能学习 socket、TCP 和 HTTP 行为，同时避免外部 DNS、NAT、链路质量和远端服务状态干扰。

## 输出怎么读

lab 的核心输出可以逐行对应到模型：

```text
interfaces=5 routes=4
localhost_dns_answers=3
tcp_echo=NETWORK-FOUNDATIONS tcp_bytes=1048576
udp_echo=UDP DATAGRAM
http_status=200 body_contains=True
```

`interfaces` 和 `routes` 说明内核中存在可观察的接口和路由决策表；`localhost_dns_answers` 说明 resolver 给应用返回的是地址候选集合；TCP 和 UDP 输出证明本机服务确实收发了数据；HTTP 输出证明应用层 handler 返回了可解析的状态和 body。

## 排查路径

以后遇到网络问题，可以按层提问：

```text
名字是否解析？         getent hosts / getaddrinfo
目标地址属于哪个前缀？ ip route get 或本地 route 选择模型
端口是否监听？         ss -ltnup
TCP 是否建立？         curl -v / nc / 应用日志
HTTP 是否成功？        status、headers、body、业务字段
```

这个顺序能把“请求失败”拆成可验证的小问题。

## 常见错误

1. **把网络理解成一个黑盒。** 排查时要分层：名字解析、路由选择、连接建立、协议语义、应用输出。
2. **混淆地址和接口。** IP 地址标识一个网络端点或接口配置，interface 是内核发送和接收帧/包的路径。
3. **把 loopback 当成假网络。** loopback 不经过物理网卡，但仍然经过 socket、TCP/UDP、IP 等关键软件路径。
4. **一开始就访问外网。** 初学阶段先用本地服务固定变量，再讨论外部 DNS、NAT、防火墙和链路质量。

## 练习或延伸

1. 运行 `ip addr show`，找到 `lo` 和一个非 loopback interface。
2. 把 HTTP demo 的路径从 `/hello?name=network` 改成 `/metrics`，观察服务端记录的 path。
3. 画出一次 `curl http://127.0.0.1:PORT/hello` 从命令行到 handler 的路径。

## 参考资料

- Linux man-pages：[socket(7)](https://man7.org/linux/man-pages/man7/socket.7.html)
- Linux man-pages：[ip-address(8)](https://man7.org/linux/man-pages/man8/ip-address.8.html)
- Linux man-pages：[proc_net(5)](https://man7.org/linux/man-pages/man5/proc_net.5.html)

{% endraw %}
