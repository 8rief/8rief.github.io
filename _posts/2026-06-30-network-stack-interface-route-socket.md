---
layout: post
title: "网络栈基础：interface、route、socket 和 loopback 如何连起来"
date: 2026-06-30 03:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从本地 loopback lab 出发，把应用、socket、TCP/UDP、IP、路由和网卡接口放进同一个可操作模型。"
tags: [networking, linux, socket, route, teaching]
---
{% raw %}
> 主题：非安全向计算机网络基础 / 网络栈模型
> 本文 lab 已验证：本地观测到 6 个 interface、4 条 route，TCP/UDP/HTTP demo 全部只走 `127.0.0.1`。

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
interfaces=6 routes=4
localhost_dns_answers=3
tcp_echo=NETWORK-FOUNDATIONS tcp_bytes=1048576
udp_echo=UDP DATAGRAM
http_status=200 body_contains=True
```

这些输出分别对应网络栈里的不同层次。`interfaces` 和 `routes` 来自本机内核视图；`localhost_dns_answers` 来自 resolver；TCP/UDP/HTTP 的输出来自 loopback 上实际收发的数据。这个设计让我们能在一台机器上解释网络机制，不依赖外部站点的可用性。

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
