---
layout: post
title: "DNS 和 resolver：应用拿到地址之前发生了什么"
date: 2026-06-07 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 localhost、/etc/resolv.conf、getaddrinfo 和地址族结果解释名字解析在应用边界的位置。"
tags: [networking, dns, resolver, linux, teaching]
---
{% raw %}
> 主题：非安全向计算机网络基础 / DNS / resolver
> 本文 lab 已验证：`localhost` 通过 resolver 返回 3 条地址相关结果，并保存 `/etc/resolv.conf` 与 `getent hosts localhost` 输出。

应用通常不直接写死 IP，而是连接一个 hostname。名字解析发生在 socket 连接之前：应用把 hostname 交给 resolver，resolver 根据系统配置、hosts 文件和 DNS 等来源返回一组地址。之后应用或系统库再选择其中一个地址去创建 socket。

## 学习目标

1. 理解 DNS/resolver 位于应用和 socket connect 之间。
2. 区分 hostname、IP 地址、地址族和端口。
3. 会用 `getent hosts` 和 Python `getaddrinfo` 观察本机解析结果。
4. 知道解析成功不等于连接成功。

## 先修知识

需要知道 IP 地址和端口的基本含义。本文使用 `localhost`，避免依赖外部 DNS 服务。

## 核心模型

![名字解析到地址列表](/assets/diagrams/network-dns-resolver-getaddrinfo.svg)

应用输入 hostname 后，resolver 读取系统配置并返回候选地址。结果可能包含 IPv4、IPv6、stream socket、datagram socket等多种组合。网络连接的下一步才是根据地址族、socket 类型和端口创建具体连接。

## 逐步实现

命令行观察：

```bash
getent hosts localhost
```

Python 观察：

```python
import socket
for item in socket.getaddrinfo("localhost", 0):
    print(item)
```

lab 摘要：

```text
localhost_dns_answers=3
```

这个数量是本地环境的观测结果，不应该写成跨机器常量。不同系统的 `/etc/hosts`、IPv6 配置和 resolver 行为可能不同。学习重点是理解应用拿到的是一组“地址候选集合”。

## 为什么要引入 resolver 边界

resolver 边界要解决的核心问题是“应用输入的是名字，socket 需要的是地址”。用户和配置文件通常写 hostname，例如 `localhost`、`example.com` 或服务名；内核创建连接时需要地址族、IP 地址、端口和 socket 类型。resolver 负责把名字转换成候选地址集合。

这一步独立出来后，排查思路更清楚：

```text
hostname 写错 -> resolver 找不到地址
地址可解析 -> 端口未监听仍会连接失败
解析出 IPv6 -> 应用或服务只支持 IPv4 时可能失败
```

## getaddrinfo 结果怎么读

Python 返回的每一项大致包含：

```text
(family, socktype, proto, canonname, sockaddr)
```

示例形状：

```text
(<AddressFamily.AF_INET: 2>, <SocketKind.SOCK_STREAM: 1>, 6, '', ('127.0.0.1', 0))
```

可以读成：IPv4、stream socket、TCP 协议、目标地址为 `127.0.0.1`，端口使用调用者传入的值。若同一个 hostname 同时返回 IPv4 和 IPv6，应用要么按系统库策略尝试，要么显式选择地址族。

## 状态变化

一次连接前的状态变化是：

```text
hostname + service/port -> resolver 查询 -> 地址候选列表 -> socket connect 尝试
```

`getent hosts localhost` 观察的是系统 resolver 视角；`socket.getaddrinfo()` 观察的是应用能拿到的结构化结果。两者结合，可以判断问题是在系统解析配置，还是在应用调用方式。

## 输出怎么读

lab 摘要：

```text
localhost_dns_answers=3
```

这个数字只代表当前环境里 `localhost` 的候选结果数量。真正需要关注的是结果中有哪些地址族、地址和 socket 类型，而不是死记数量。不同 Linux 发行版、容器、WSL、IPv6 配置都可能改变数量。

## 解析成功后的下一步

解析完成后还要继续验证：

```text
地址候选是否符合预期？
目标端口是否监听？
应用是否选择了正确地址族？
连接是否超时或被拒绝？
HTTP/TLS/业务层是否成功？
```

把 DNS 和连接分开，能避免把所有错误都归因到“域名问题”。

## 常见错误

1. **把 DNS 当成 HTTP 的一部分。** DNS 在 HTTP 请求之前完成，HTTP 看到的是已经选定的连接。
2. **解析成功后直接断言服务可用。** 服务端口可能没监听，路由可能不通，TLS 或 HTTP 层也可能失败。
3. **忽略 IPv6。** `localhost` 可能同时返回 `::1` 和 `127.0.0.1`。
4. **把 resolver 配置写死进代码。** 普通应用优先使用系统 resolver，特殊需求再显式配置。

## 练习或延伸

1. 比较 `getent hosts localhost` 和 `python3 -c 'import socket; print(socket.getaddrinfo("localhost", 80))'`。
2. 打开 `/etc/resolv.conf`，只观察配置项，不修改。
3. 解释为什么 DNS 解析耗时会影响应用启动请求的总延迟。

## 参考资料

- Linux man-pages：[getaddrinfo(3)](https://man7.org/linux/man-pages/man3/getaddrinfo.3.html)
- Linux man-pages：[resolv.conf(5)](https://man7.org/linux/man-pages/man5/resolv.conf.5.html)
- Python 文档：[socket.getaddrinfo](https://docs.python.org/3/library/socket.html#socket.getaddrinfo)

{% endraw %}
