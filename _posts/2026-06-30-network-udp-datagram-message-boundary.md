---
layout: post
title: "UDP 数据报：保留消息边界，但要自己处理超时"
date: 2026-06-30 03:05:00 +0800
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
