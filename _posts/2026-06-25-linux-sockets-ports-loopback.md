---
layout: post
title: "Linux socket、端口和 loopback：先把本机网络模型跑通"
date: 2026-06-25 04:10:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个本地 Python TCP 服务、ss、lsof、curl 和 nc 观察 Linux socket、端口、监听状态和 loopback 边界。"
tags: [linux, networking, socket, tcp, loopback]
---
{% raw %}

> 主题：Linux 网络基础 / socket / TCP / loopback  
> 本文命令已在 Ubuntu 24.04、Python 3.12.3、iproute2 `ss` 6.1.0、curl 8.5.0、OpenBSD netcat 环境下本地执行验证。实验只使用 `127.0.0.1` 和本机临时端口，不扫描公网，不连接第三方目标。

很多网络问题表面上是“服务访问不了”，实际要拆成几个更小的问题：进程有没有创建 socket？它绑定到了哪个地址和端口？内核有没有把这个 socket 放进监听表？客户端连的是不是同一个地址和端口？请求到达后，服务端有没有读到字节并返回响应？

这篇文章先不引入 DNS、TLS、反向代理或容器网络，只用一个本地 Python 服务建立最小模型。目标是让你能看懂 `127.0.0.1:18180` 这样的地址到底指向什么，并用 `ss`、`lsof`、`curl`、`nc` 把连接路径逐步验证出来。

## 安全边界

本文所有命令只访问本机 loopback 地址 `127.0.0.1`。`nc` 在这里用于向本地测试服务发送手写 HTTP 请求，不用于端口扫描。后续讲安全实验时也沿用这个原则：默认只打本地靶场或明确授权目标。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释 IP、端口、socket、listen backlog 和 loopback 的关系。
2. 用 `ss -ltnp` 判断一个 TCP 服务是否正在监听。
3. 用 `lsof -iTCP` 找到监听端口对应的进程。
4. 用 `curl` 和 `nc` 分别发送 HTTP 请求和原始 TCP 字节。
5. 根据服务端日志把客户端源端口、请求行和监听端口对应起来。

## 核心模型

Linux 网络服务的最小路径如下：

![Linux socket、端口和 loopback 模型](/assets/diagrams/linux-sockets-ports-loopback.svg)

服务端进程调用 `socket()` 创建一个内核 socket 对象，再调用 `bind()` 把它绑定到本地地址和端口，最后调用 `listen()` 让它进入监听状态。监听状态不是应用自己维护的列表，而是内核 TCP 栈的一部分，所以 `ss` 可以看到它。

客户端连接时也会得到一个 socket。客户端通常不手动指定源端口，内核会分配一个临时端口。服务端日志中的 `peer=127.0.0.1:45902` 表示连接来自本机地址和某个临时源端口；服务端自己的监听地址仍然是 `127.0.0.1:18180`。

`127.0.0.1` 是 loopback 地址。数据不会离开本机网卡，适合开发、调试和安全教学。它能帮助我们把“网络协议本身”和“外部网络环境”分开。

## 建立本地服务

创建实验目录：

```bash
mkdir -p linux-sockets-ports-loopback/reports
cd linux-sockets-ports-loopback
```

写一个最小 HTTP-like TCP 服务 `server.py`：

```python
import socket
import threading

HOST = "127.0.0.1"
PORT = 18180


def handle_client(conn, peer):
    with conn:
        data = conn.recv(4096)
        first_line = data.split(b"\r\n", 1)[0].decode("utf-8", errors="replace")
        body = (
            "socket lab response\n"
            f"peer={peer[0]}:{peer[1]}\n"
            f"first_line={first_line}\n"
        ).encode("utf-8")
        response = (
            b"HTTP/1.1 200 OK\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Content-Type: text/plain; charset=utf-8\r\n"
            + b"Connection: close\r\n\r\n"
            + body
        )
        conn.sendall(response)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(16)
    while True:
        conn, peer = server.accept()
        threading.Thread(target=handle_client, args=(conn, peer), daemon=True).start()
```

这段代码对应四个关键动作：

- `AF_INET` 表示 IPv4；`SOCK_STREAM` 表示 TCP 字节流。
- `bind((HOST, PORT))` 把服务固定到 `127.0.0.1:18180`。
- `listen(16)` 让内核开始接受 TCP 连接，`16` 是等待队列的一个上限提示。
- `accept()` 取出一个已经建立的连接，返回连接 socket 和对端地址。

启动服务：

```bash
python3 server.py
```

下面的验证命令可以在另一个终端执行；实验脚本会自动后台启动并清理这个服务。

## 观察监听状态

查看监听中的 TCP socket：

```bash
ss -ltnp | grep ':18180'
```

本地输出：

```text
LISTEN 0 16 127.0.0.1:18180 0.0.0.0:* users:(("python3",pid=1912393,fd=3))
```

字段可以这样读：

- `LISTEN`：这个 TCP socket 正在监听。
- `127.0.0.1:18180`：本地监听地址和端口。
- `0.0.0.0:*`：尚未连接到固定远端；监听 socket 接受未来连接。
- `python3`、`pid`、`fd=3`：拥有这个 socket 的进程和文件描述符。

再用 `lsof` 从进程角度看同一件事：

```bash
lsof -nP -iTCP:18180 -sTCP:LISTEN
```

输出：

```text
COMMAND   PID  USER FD  TYPE DEVICE NODE NAME
python3 1912393 user 3u IPv4 ...      TCP 127.0.0.1:18180 (LISTEN)
```

`ss` 更偏内核网络表，`lsof` 更偏“哪个进程打开了哪个文件描述符”。Linux 中 socket 也是文件描述符，所以这两个工具能从不同角度看到同一个监听端口。

## 用 curl 发送请求

执行：

```bash
curl --noproxy '*' -sS http://127.0.0.1:18180/hello?name=lab
```

输出：

```text
socket lab response
peer=127.0.0.1:45902
first_line=GET /hello?name=lab HTTP/1.1
```

这里有两个容易忽略的点。

第一，客户端源端口 `45902` 不是服务端端口。服务端监听 `18180`，客户端由内核临时分配源端口。TCP 连接可以用四元组识别：源 IP、源端口、目标 IP、目标端口。

第二，`curl` 不只是“打开网页”。它把 URL 转成 HTTP 请求行、`Host`、`User-Agent` 等请求头，然后写进 TCP 连接。服务端读到的第一行是 `GET /hello?name=lab HTTP/1.1`。

## 用 nc 手写字节

`nc` 可以直接向 TCP 连接写入字节。下面手写一个最小 HTTP 请求：

```bash
printf 'GET /raw HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n' | nc 127.0.0.1 18180
```

输出：

```text
HTTP/1.1 200 OK
Content-Length: 70
Content-Type: text/plain; charset=utf-8
Connection: close

socket lab response
peer=127.0.0.1:45908
first_line=GET /raw HTTP/1.1
```

这个命令把 HTTP 的文本格式暴露出来：请求行之后是请求头，每一行用 CRLF 结束，空行表示请求头结束。`curl` 自动生成这些字节；`nc` 让我们手动写出来。

## 服务端日志如何对应请求

实验脚本保存的日志节选：

```text
listening host=127.0.0.1 port=18180
peer=127.0.0.1:45902 first_line='GET /hello?name=lab HTTP/1.1' bytes=92
peer=127.0.0.1:45908 first_line='GET /raw HTTP/1.1' bytes=57
```

`curl` 请求字节更多，因为它自动加了若干请求头。`nc` 请求更短，因为我们只写了 `Host` 和 `Connection`。两者都通过同一个监听 socket 到达同一个服务进程。

## 常见错误

**只看端口号，不看绑定地址。** `127.0.0.1:18180` 和 `0.0.0.0:18180` 的暴露范围不同。下一篇会专门讲绑定地址的安全边界。

**把客户端临时端口误认为服务端端口。** 服务端日志里的 `peer` 是客户端地址。服务端监听端口要看 `ss` 或服务启动参数。

**服务启动了但没有进入 LISTEN。** 只有 `bind()` 成功还不够，TCP 服务还需要 `listen()`。`ss -ltnp` 是确认监听状态的直接证据。

**调试本机服务时忘记代理。** 本文命令使用 `curl --noproxy '*'`，避免环境变量中的代理设置影响本地实验。

## 练习

1. 把端口改成 `18190`，观察 `ss` 和 `lsof` 输出如何变化。
2. 把 `HOST` 改成 `0.0.0.0`，先不要对外访问，只观察 `ss` 中本地地址的变化。
3. 给 `server.py` 增加一行日志，记录完整请求头，比较 `curl` 和 `nc` 的差异。
4. 用 `ss -tanp | grep 18180` 在请求进行时观察已建立连接和监听 socket 的区别。

## 参考资料

- [Linux man-pages: socket(2)](https://man7.org/linux/man-pages/man2/socket.2.html)
- [Linux man-pages: bind(2)](https://man7.org/linux/man-pages/man2/bind.2.html)
- [Linux man-pages: listen(2)](https://man7.org/linux/man-pages/man2/listen.2.html)
- [Linux man-pages: ip(7)](https://man7.org/linux/man-pages/man7/ip.7.html)
- [Linux man-pages: ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html)
- [curl man page](https://curl.se/docs/manpage.html)
{% endraw %}
