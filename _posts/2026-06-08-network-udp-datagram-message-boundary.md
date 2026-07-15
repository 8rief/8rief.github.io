---
layout: post
title: "UDP 数据报：保留消息边界，但要自己处理超时"
date: 2026-06-08 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地 UDP echo 服务解释 datagram、message boundary、timeout/retry 和应用自定义可靠性。"
tags: [networking, udp, datagram, socket, teaching]
---
{% raw %}
> 主题：非安全向计算机网络基础 / UDP / datagram
> 本文 lab 已验证：本地 UDP echo 返回 `UDP DATAGRAM`，并记录一次 loopback RTT。

UDP 给应用提供的是数据报。每次 `sendto` 发送一个 datagram，接收端用 `recvfrom` 收到一个 datagram 和来源地址。UDP 本身不建立连接，不保证到达、不保证重传，也不提供 TCP 那样的有序字节流。

## 学习目标

1. 理解 UDP 的消息边界和 TCP 字节流的差异。
2. 会用 `sendto`、`recvfrom` 和 timeout 写一个最小 UDP demo。
3. 知道可靠性、重试、去重和顺序通常由应用协议补充。
4. 知道 UDP 适合短消息、实时性或自定义传输语义的场景。

## 先修知识

需要理解 IP 地址、端口和 socket。建议先读 TCP 一篇，再比较两者差异。

## 核心模型

![UDP 数据报收发模型](/assets/diagrams/network-udp-datagram-message-boundary.svg)

客户端向服务端地址发送一个 datagram；服务端收到数据和来源地址；服务端把响应 datagram 发回来源地址；客户端等待响应。如果超时，应用需要决定是否重试、放弃或标记失败。

## 逐步实现

lab 的服务端逻辑：

```python
data, addr = sock.recvfrom(65535)
sock.sendto(data.upper(), addr)
```

输出：

```text
udp_echo=UDP DATAGRAM
```

这里能看到 UDP 保留了“这一条 datagram”的边界。若消息比接收缓冲更大，应用会遇到截断问题；若网络丢包，应用需要 timeout 和重试策略。本地 loopback 通常很稳定，所以教学 lab 主要展示 API 和边界。

## 为什么要引入数据报模型

数据报模型要解决的核心问题是“应用有时需要一条一条的独立消息”。TCP 把数据变成连续字节流，适合需要可靠有序传输的场景；UDP 保留每次 `sendto` 的消息边界，适合短消息、低延迟探测、自定义可靠性或上层协议已经处理重传的场景。

UDP 的简化也带来责任转移：

```text
到达保证 -> 应用自己决定重试
顺序保证 -> 应用自己加 sequence number
去重      -> 应用自己记录 request_id
拥塞控制  -> 应用协议或运行环境需要考虑
```

## timeout 是 UDP 客户端的基本边界

最小客户端应该设置超时：

```python
sock.settimeout(1.0)
sock.sendto(b"udp datagram", server_addr)
try:
    data, addr = sock.recvfrom(65535)
except TimeoutError:
    print("no response before timeout")
```

没有 timeout，客户端会在 `recvfrom` 上无限等待，程序看起来像“卡死”。教学 lab 在 loopback 上通常不会丢包，但真实网络会出现丢包、抖动、乱序和重复。

## 输出怎么读

lab 输出：

```text
udp_echo=UDP DATAGRAM
```

这说明服务端收到一个 datagram，把 payload 转成大写后发回，客户端收到的是一条完整响应。这个输出证明了消息边界的基本行为，但不证明网络可靠性；loopback 环境下看不到公网中的丢包和路径 MTU 问题。

## 一个简单重试状态机

可靠一点的 UDP 应用可以按下面状态机写：

```text
send request_id=42
wait response until timeout
if matching response arrives -> success
if timeout and retries left -> resend same request_id
if timeout too many times -> fail
ignore duplicated old response
```

`request_id` 的作用是让客户端区分新响应、重传响应和迟到响应。

## 与 TCP 的直接对比

| 问题 | TCP | UDP |
|---|---|---|
| 连接状态 | 有连接 | 无连接或弱连接语义 |
| 消息边界 | 应用自定义 | 每个 datagram 是一条消息 |
| 到达/顺序 | 协议提供 | 应用需要处理 |
| 常见风险 | 忘记处理部分读写 | 忘记 timeout 和重试 |

选择 TCP 或 UDP 时，先看应用需要的语义，再看性能和实现复杂度。

## 常见错误

1. **用 TCP 的思维处理 UDP。** UDP 没有连接字节流，也没有内置重传。
2. **不设置 timeout。** 客户端可能永远等响应。
3. **忽略 datagram 大小。** 太大的 UDP 数据报更容易遇到分片或丢弃风险。
4. **把本地成功当成公网可靠。** loopback 不会暴露真实链路中的丢包和抖动。

## 练习或延伸

1. 把客户端 timeout 改成很小的值，观察是否会触发超时。
2. 给每个 datagram 加上 `request_id`，实现简单去重。
3. 比较 TCP echo 和 UDP echo 的代码结构，说明哪里体现了连接状态差异。

## 参考资料

- IETF RFC 768：[User Datagram Protocol](https://www.rfc-editor.org/rfc/rfc768)
- Linux man-pages：[udp(7)](https://man7.org/linux/man-pages/man7/udp.7.html)
- Python 文档：[socket.sendto](https://docs.python.org/3/library/socket.html#socket.socket.sendto)

{% endraw %}
