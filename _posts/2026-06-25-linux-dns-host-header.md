---
layout: post
title: "DNS 解析和 Host 头：名字如何变成连接目标"
date: 2026-06-25 04:40:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 getent、socket.getaddrinfo、curl --resolve 和本地服务区分名称解析、连接地址与 HTTP Host 头。"
tags: [linux, networking, dns, http, curl]
---
{% raw %}

> 主题：Linux 网络基础 / DNS 解析 / HTTP Host 头 / curl 调试  
> 本文命令已在 Ubuntu 24.04、Python 3.12.3、curl 8.5.0、glibc `getent` 环境下本地执行验证。实验只访问 `127.0.0.1` 上的本地服务，不修改系统 DNS，不连接第三方目标。

很多 Web 排障会把几个层次混在一起：域名能不能解析？解析出来的 IP 是什么？TCP 连接连到了哪个地址？HTTP 请求里的 `Host` 又是什么？这四个问题相关，但不是同一个问题。

这一讲用本地服务把路径拆开。`getent` 和 `socket.getaddrinfo()`观察名称解析，`curl --resolve`把一个临时名字映射到 `127.0.0.1`，服务端打印实际连接地址和 HTTP `Host` 头。这样可以看清：名字解析决定连接目标，`Host` 头决定 HTTP 层把这次请求声明给哪个虚拟主机。

## 安全边界

本文只启动本地服务并访问 `127.0.0.1:18183`。`curl --resolve` 只给本次 curl 命令增加一条临时解析规则，不写 `/etc/hosts`，不影响系统全局配置。示例域名 `lab.local` 和 `virtual.local` 只用于本地实验。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释名称解析、连接目标和 HTTP `Host` 头的区别。
2. 用 `getent` 和 `socket.getaddrinfo()`观察本机解析结果。
3. 用 `curl --resolve` 做一次临时的本地解析映射。
4. 判断服务端日志里的 `local`、`peer`、`first_line` 和 `host` 分别属于哪一层。
5. 避免把 DNS 问题、TCP 连接问题和虚拟主机路由问题混为一谈。

## 核心模型

一次 HTTP 访问至少跨过三层边界：

![DNS 解析、TCP 连接与 HTTP Host 头](/assets/diagrams/linux-dns-host-header.svg)

1. **名称解析层**：客户端把 `lab.local` 变成一个或多个地址，例如 `127.0.0.1`。
2. **连接层**：客户端向解析得到的 IP 和端口建立 TCP 连接，服务端看到本地地址和对端地址。
3. **HTTP 层**：客户端在请求头里发送 `Host: lab.local:18183`。反向代理或应用可以用这个字段选择虚拟主机、租户或路由规则。

这三个状态可以一致，也可以被调试工具临时分离。`curl --resolve lab.local:18183:127.0.0.1` 就是把名字解析固定到本地地址，同时仍然让 HTTP 请求携带 `Host: lab.local:18183`。

## 查看本机解析结果

先看 `localhost` 的系统解析：

```bash
getent hosts localhost
getent ahostsv4 localhost
```

实验输出：

```text
::1             localhost
127.0.0.1       STREAM localhost
127.0.0.1       DGRAM
127.0.0.1       RAW
```

`getent hosts` 展示名称服务返回的主机项，这里先出现 IPv6 loopback `::1`。`getent ahostsv4` 只看 IPv4 地址，所以出现 `127.0.0.1`。不同发行版、容器或 WSL 环境的顺序可能不同；排障时要以本机输出为准。

再从程序角度看同一个问题：

```bash
python3 -c "import socket; [print(item) for item in socket.getaddrinfo('localhost', 18183, type=socket.SOCK_STREAM)]"
```

输出：

```text
(<AddressFamily.AF_INET: 2>, <SocketKind.SOCK_STREAM: 1>, 6, '', ('127.0.0.1', 18183))
```

`getaddrinfo()` 是很多程序实际使用的解析入口。它返回的不只是 IP，还包括地址族、socket 类型、协议号和可连接的地址元组。

## 启动一个打印 Host 的服务

服务端核心逻辑很短：读到 HTTP 头结束边界，取请求行和 `Host` 头，再把本地地址、对端地址一起写回响应。

```python
def parse_headers(text: str) -> dict[str, str]:
    headers = {}
    for line in text.split('\r\n')[1:]:
        if not line:
            break
        if ':' in line:
            k, v = line.split(':', 1)
            headers[k.strip().lower()] = v.strip()
    return headers

local_ip, local_port = conn.getsockname()[:2]
host = parse_headers(text).get('host', '<missing>')
```

启动后确认监听：

```bash
ss -ltnp | grep ':18183'
```

输出：

```text
LISTEN 0 16 127.0.0.1:18183 0.0.0.0:* users:(("python3",pid=1914304,fd=3))
```

这说明服务只监听在 `127.0.0.1:18183`。

## 直接访问 IP

执行：

```bash
curl --noproxy '*' -sS http://127.0.0.1:18183/direct
```

输出：

```text
dns-host lab response
local=127.0.0.1:18183
peer=127.0.0.1:32804
first_line=GET /direct HTTP/1.1
host=127.0.0.1:18183
```

这次没有域名解析争议：URL 里就是 IP，连接目标也是 `127.0.0.1:18183`，HTTP `Host` 头也是 `127.0.0.1:18183`。

## 用 curl --resolve 固定一次解析

执行：

```bash
curl --noproxy '*' --resolve 'lab.local:18183:127.0.0.1' -sS http://lab.local:18183/from-resolve
```

输出：

```text
dns-host lab response
local=127.0.0.1:18183
peer=127.0.0.1:32806
first_line=GET /from-resolve HTTP/1.1
host=lab.local:18183
```

这里的关键差异是：TCP 连接仍然进了 `127.0.0.1:18183`，但 HTTP `Host` 变成了 `lab.local:18183`。这正是本地调试反向代理、虚拟主机、TLS SNI/证书域名问题时常用的技巧：让名字指向本地或测试服务，同时保留应用层看到的域名。

## 手动改 Host 头

还可以直接覆盖 HTTP `Host`：

```bash
curl --noproxy '*' -H 'Host: virtual.local' -sS http://127.0.0.1:18183/host-override
```

输出：

```text
dns-host lab response
local=127.0.0.1:18183
peer=127.0.0.1:32820
first_line=GET /host-override HTTP/1.1
host=virtual.local
```

这次连接目标来自 URL 的 IP，`Host` 头来自 `-H` 参数。它说明 HTTP 应用层可以看到的主机名并不必然等于连接层的目标 IP。这个能力对调试很有用，但上线系统不能盲目信任 `Host`；反向代理和应用应显式配置允许的主机名。

## 日志如何读

服务端日志节选：

```text
peer=127.0.0.1:32804 local=127.0.0.1:18183 first_line='GET /direct HTTP/1.1' host='127.0.0.1:18183'
peer=127.0.0.1:32806 local=127.0.0.1:18183 first_line='GET /from-resolve HTTP/1.1' host='lab.local:18183'
peer=127.0.0.1:32820 local=127.0.0.1:18183 first_line='GET /host-override HTTP/1.1' host='virtual.local'
```

- `local`：服务端本地 socket 地址，属于连接层。
- `peer`：客户端源地址和临时源端口，属于连接层。
- `first_line`：HTTP 请求行，属于应用协议层。
- `host`：HTTP 请求头字段，常用于虚拟主机和反向代理路由。

## 常见错误

**DNS 成功不等于服务可访问。** 名字能解析只说明得到候选地址；服务是否监听、路由是否可达、端口是否开放还要继续验证。

**连接成功不等于 Host 路由正确。** TCP 已连接但返回 404、421 或错误租户页面时，问题可能在 HTTP `Host`、反向代理或应用路由。

**把临时解析当成全局配置。** `curl --resolve` 只影响当前 curl 调用。需要系统级配置时再考虑 `/etc/hosts`、DNS 服务或容器网络配置。

**无边界地信任 Host。** `Host` 是客户端发送的请求头。对外系统应该配置允许列表，并在反向代理层处理非法主机名。

## 练习

1. 把 `lab.local` 换成 `api.local`，观察响应中的 `host` 如何变化。
2. 删除 `--resolve`，直接访问 `http://lab.local:18183/`，观察错误属于解析失败还是连接失败。
3. 同时使用 `--resolve` 和 `-H 'Host: other.local'`，判断连接目标和 `Host` 头分别是什么。
4. 在服务端增加一行日志，打印所有请求头。

## 参考资料

- [Linux man-pages: getaddrinfo(3)](https://man7.org/linux/man-pages/man3/getaddrinfo.3.html)
- [curl man page](https://curl.se/docs/manpage.html)
- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [RFC 9112: HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112)
{% endraw %}
