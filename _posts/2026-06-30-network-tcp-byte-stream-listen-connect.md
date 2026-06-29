---
layout: post
title: "TCP 字节流：listen、connect、accept 到有序数据"
date: 2026-06-30 03:04:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地 TCP echo 服务解释连接建立、字节流、send/recv 和吞吐观察的基本边界。"
tags: [networking, tcp, socket, python, teaching]
---
{% raw %}
> 主题：非安全向计算机网络基础 / TCP / byte stream
> 本文 lab 已验证：本地 TCP echo 返回 `NETWORK-FOUNDATIONS`，传输了 1048576 字节并记录 loopback 吞吐观察。

TCP 给应用提供的是有序、可靠的字节流。它不保留应用层“消息边界”：你发送两次，接收端可能一次读到，也可能分多次读到。应用协议需要自己定义如何分隔请求、响应和记录。

## 学习目标

1. 理解 `listen`、`connect`、`accept` 各自发生在哪一端。
2. 知道 TCP 面向字节流，应用需要自己处理消息边界。
3. 能用本地 echo 服务验证 send/recv 的基本行为。
4. 读懂简单 RTT 和吞吐观察，避免把 loopback 数值当公网性能。

## 先修知识

需要理解 socket 是应用和内核网络栈之间的接口。建议先读网络栈模型和路由表两篇。

## 核心模型

![TCP 从监听到字节流](/assets/diagrams/network-tcp-byte-stream-listen-connect.svg)

服务端先绑定地址和端口并进入 listen 状态；客户端 connect 到该地址端口；服务端 accept 得到一个连接 socket；两端使用 send/recv 读写字节；任一方关闭连接后，资源被释放。

## 逐步实现

lab 使用本地 TCP echo handler：

```python
data = connection.recv(65536)
connection.sendall(data.upper())
```

运行输出：

```text
tcp_echo=NETWORK-FOUNDATIONS
tcp_bytes=1048576
throughput_mib_s=564.706
```

`tcp_echo` 验证字节被服务端处理后返回；`tcp_bytes` 说明吞吐观察的输入规模；`throughput_mib_s` 是本机 loopback 上的一次测量。这个数值可以帮助比较同一机器上的实现变化，不能直接代表跨机网络速度。

## 常见错误

1. **假设一次 `recv` 对应一次 `send`。** TCP 是字节流，应用协议要自己定义长度、分隔符或帧格式。
2. **忘记处理部分读写。** 大数据可能需要循环读到目标字节数。
3. **把 loopback 吞吐当公网吞吐。** loopback 少了真实链路、拥塞、NAT 和远端服务开销。
4. **连接后不关闭资源。** 长期服务需要清楚连接生命周期和超时策略。

## 练习或延伸

1. 把 payload 改成两段发送，观察服务端是否仍然能返回完整大写数据。
2. 给 echo 协议增加 4 字节长度前缀，保证接收端知道一条消息何时结束。
3. 用 `ss -tn` 在连接期间观察 TCP 状态。

## 参考资料

- IETF RFC 9293：[Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293)
- Linux man-pages：[tcp(7)](https://man7.org/linux/man-pages/man7/tcp.7.html)
- Python 文档：[socket](https://docs.python.org/3/library/socket.html)

{% endraw %}
