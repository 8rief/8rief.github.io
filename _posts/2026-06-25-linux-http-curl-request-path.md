---
layout: post
title: "HTTP 请求从 curl 到字节：看见请求行、头部和响应边界"
date: 2026-06-25 04:20:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 curl -v、nc 和本地 byte-logging 服务观察 HTTP/1.1 请求行、头部、CRLF 分隔和响应结构。"
tags: [linux, http, curl, networking, tcp]
---
{% raw %}

> 主题：Linux 网络基础 / HTTP/1.1 / curl / 原始请求字节  
> 本文命令已在 Ubuntu 24.04、Python 3.12.3、curl 8.5.0、OpenBSD netcat 环境下本地执行验证。实验只访问 `127.0.0.1` 上的本地服务。

上一讲把 socket、端口和 loopback 跑通了。这一讲继续向上走一层：当你执行 `curl http://127.0.0.1:18181/alpha?x=1` 时，HTTP 请求到底长什么样？服务端收到的是函数调用、JSON 对象，还是一段普通字节？

答案是：在 HTTP/1.1 中，服务端首先收到一段文本格式的请求字节。它由请求行、若干头部字段和一个空行组成；如果有请求体，空行后面才是 body。理解这个结构，是后续学习 Web 服务、反向代理、日志、安全过滤和请求走查的基础。

## 安全边界

本文只启动本机服务并向 `127.0.0.1` 发送请求。`curl -v` 和 `nc` 用来观察协议字节，不用来探测外部站点。所有输出都来自本地实验。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释 HTTP 请求行、请求头、空行和响应状态行的边界。
2. 用 `curl -v` 观察客户端发出的请求和服务端返回的响应。
3. 用 `nc` 手写一个最小 HTTP/1.1 请求。
4. 从服务端原始日志中识别 CRLF、`Host`、`User-Agent` 和自定义头部。
5. 区分 TCP 连接成功和 HTTP 协议语义成功。

## 核心模型

HTTP/1.1 的请求可以先看成一段按规则组织的字节流：

![HTTP 请求从命令到字节](/assets/diagrams/linux-http-request-path.svg)

一次简单 GET 请求大致长这样。为了让不可见的换行边界可见，下面用 `\r\n` 表示 CRLF：

```text
GET /alpha?x=1 HTTP/1.1\r\n
Host: 127.0.0.1:18181\r\n
User-Agent: curl/8.5.0\r\n
Accept: */*\r\n
X-Lab: curl-path\r\n
\r\n
```

第一行是请求行，包含方法、路径和协议版本。后面是请求头。最后的空行，也就是连续的 `\r\n\r\n`，表示请求头结束。这个边界很重要：服务端通常先读到空行，再决定是否继续读取请求体。

响应也有类似结构：状态行、响应头、空行、响应体。这里同样用 `\r\n` 显示协议换行：

```text
HTTP/1.1 200 OK\r\n
Content-Length: 48\r\n
Content-Type: text/plain; charset=utf-8\r\n
Connection: close\r\n
\r\n
ok request=1
```

## 写一个 byte-logging 服务

这个服务不做框架解析，只读取 socket 字节并把文本和十六进制都写进日志。核心代码：

```python
def render_hex(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        text_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        lines.append(f'{offset:04x}  {hex_part:<{width*3}}  {text_part}')
    return '\n'.join(lines)
```

读取请求时，服务一直读到 `\r\n\r\n`：

```python
chunks = []
while True:
    part = conn.recv(4096)
    if not part:
        break
    chunks.append(part)
    if b'\r\n\r\n' in b''.join(chunks):
        break
```

这段逻辑只适合教学。真实 HTTP 服务器还要处理 body 长度、分块传输、连接复用、超时、最大头部大小和协议错误。本文刻意保留最小模型，是为了让请求边界可见。

## 用 curl -v 观察请求响应

启动本地服务后执行：

```bash
curl --noproxy '*' -v -H 'X-Lab: curl-path' 'http://127.0.0.1:18181/alpha?x=1'
```

输出节选：

```text
*   Trying 127.0.0.1:18181...
* Connected to 127.0.0.1 (127.0.0.1) port 18181
> GET /alpha?x=1 HTTP/1.1
> Host: 127.0.0.1:18181
> User-Agent: curl/8.5.0
> Accept: */*
> X-Lab: curl-path
>
< HTTP/1.1 200 OK
< Content-Length: 48
< Content-Type: text/plain; charset=utf-8
< Connection: close
<
ok request=1
first_line=GET /alpha?x=1 HTTP/1.1
```

`>` 表示 curl 发出的请求头，`<` 表示服务端返回的响应头。第一行 `Trying` 和 `Connected` 属于 TCP 连接层；`GET ... HTTP/1.1` 之后才是 HTTP 层。

这就是一个常用排障分界：如果卡在 `Trying`，说明 TCP 连接可能没有建立；如果已经 `Connected` 但没有响应，说明请求到达后服务端处理、协议解析或应用逻辑可能有问题；如果返回了 `HTTP/1.1 500`，说明网络通了，但应用层返回错误。

## 用 nc 手写请求

执行：

```bash
printf 'GET /manual HTTP/1.1\r\nHost: lab.local\r\nUser-Agent: raw-netcat\r\nConnection: close\r\n\r\n' | nc 127.0.0.1 18181
```

输出：

```text
HTTP/1.1 200 OK
Content-Length: 45
Content-Type: text/plain; charset=utf-8
Connection: close

ok request=2
first_line=GET /manual HTTP/1.1
```

这说明 curl 没有魔法。它只是替我们生成了符合协议的请求字节，并处理响应显示。`nc` 让我们直接控制这些字节。

## 服务端看到的原始字节

日志中的第一条请求：

```text
first_line: GET /alpha?x=1 HTTP/1.1
raw_text:
GET /alpha?x=1 HTTP/1.1\r\n
Host: 127.0.0.1:18181\r\n
User-Agent: curl/8.5.0\r\n
Accept: */*\r\n
X-Lab: curl-path\r\n
\r\n
```

对应的十六进制开头：

```text
0000  47 45 54 20 2f 61 6c 70 68 61 3f 78 3d 31 20 48   GET /alpha?x=1 H
0010  54 54 50 2f 31 2e 31 0d 0a 48 6f 73 74 3a 20 31   TTP/1.1..Host: 1
```

`0d 0a` 就是 CRLF。十六进制视图的价值在于：当文本显示工具隐藏换行符、编码或不可见字符时，hex dump 仍然能显示真实字节。

第二条手写请求更短：

```text
first_line: GET /manual HTTP/1.1
raw_text:
GET /manual HTTP/1.1\r\n
Host: lab.local\r\n
User-Agent: raw-netcat\r\n
Connection: close\r\n
\r\n
```

它没有 `Accept` 和 `X-Lab`，因为我们没有写。HTTP 服务端不应该假设所有客户端都像浏览器或 curl 一样发送同一组头。

## 常见错误

**把 TCP 连接成功当成 HTTP 成功。** `Connected` 只说明三次握手完成。HTTP 状态码、响应头和响应体还要继续看。

**忘记 `Host`。** HTTP/1.1 请求通常需要 `Host` 头。虚拟主机、反向代理和本地服务路由都可能依赖它。

**看不到 CRLF 边界。** 很多调试输出会把 `\r\n` 显示成换行。需要确认协议边界时，用服务端日志或十六进制视图。

**把 curl 输出方向看反。** `curl -v` 里 `>` 是客户端发出的内容，`<` 是服务端返回的内容。方向看反会导致排障判断完全错误。

## 练习

1. 给 `curl` 增加 `-H 'X-Trace: 123'`，确认服务端 raw log 中出现这个头。
2. 删除手写请求里的空行，观察服务端是否会等待到超时。
3. 把请求方法从 `GET` 改成 `POST`，比较 first line 的变化。
4. 修改服务端响应状态行为 `HTTP/1.1 404 Not Found`，观察 curl 输出和退出码。

## 参考资料

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [RFC 9112: HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112)
- [curl man page](https://curl.se/docs/manpage.html)
- [Linux man-pages: recv(2)](https://man7.org/linux/man-pages/man2/recv.2.html)
- [Linux man-pages: tcp(7)](https://man7.org/linux/man-pages/man7/tcp.7.html)
{% endraw %}
