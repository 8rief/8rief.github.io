---
layout: post
title: "DNS 到 HTTP：用 getent 和 curl -v 读懂一次请求"
date: 2026-05-22 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把名字解析、TCP 连接、HTTP 请求行、响应头和响应体放到同一条排障路径里。"
tags: [linux, dns, http, curl, resolver]
---
{% raw %}

> 主题：Linux 网络与授权安全基础 / DNS / HTTP
> 本文对应 lab 的 resolver 观察、headers 记录和 `curl -v` transcript。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

一次 HTTP 请求可以拆成两个阶段：先把主机名解析成地址，再向地址和端口建立连接并发送 HTTP 消息。`getent` 走系统名字服务，适合检查本机解析路径；`curl -v` 记录客户端请求过程，适合检查 HTTP 细节。

## 为什么需要拆开名字与连接

“访问不了某个 URL”至少可能发生在四个位置：名字没有解析、地址路由不通、端口没有监听、HTTP handler 返回错误。若从一开始就把它们统称为“网络问题”，每次排障都会重复猜测。

还要区分 **系统名字服务** 与 DNS。`getent hosts` 按 NSS 配置查询，结果可能来自 `/etc/hosts`、systemd-resolved、DNS 或其他来源；`/etc/resolv.conf` 只描述 DNS resolver 的一部分配置。`localhost` 通常由本地 hosts 配置提供，不能拿它证明外部 DNS 正常。

## 学习目标

1. 用 `getent hosts` 观察系统 resolver 结果。
2. 读懂 `curl -v` 中的连接、请求和响应片段。
3. 区分 HTTP 状态码、响应头和响应体。
4. 说明响应头为何属于调试和安全证据。

## 先修知识

需要知道域名、IP、端口和 HTTP status code 的基本含义。

## 核心模型

![DNS 到 HTTP 请求路径](/assets/diagrams/linux-dns-http-curl-verbose.svg)

resolver 返回地址，TCP 连接到地址和端口，HTTP 请求行指明路径，服务返回状态、headers 和 body。

## 逐步实现

观察名字解析：

```bash
getent hosts localhost
getent ahosts localhost
grep -E '^(nameserver|search|options)' /etc/resolv.conf
```

本机观测到 `localhost` 可解析为 loopback。具体地址顺序可能因 NSS 和 IPv4/IPv6 配置不同而变化；文章不固定本机 nameserver 地址，因为它既不影响这个 loopback 实验，也不应成为公开教程的环境指纹。

保持前一篇启动的本地服务运行，再执行 verbose 请求：

```bash
curl -v -sS http://127.0.0.1:18480/health -o reports/health_body.json
```

关键片段：

```text
> GET /health HTTP/1.1
< HTTP/1.0 200 OK
< Content-Type: application/json; charset=utf-8
< X-Content-Type-Options: nosniff
< Cache-Control: no-store
```

`>` 表示客户端发出的内容，`<` 表示服务端返回的内容。状态码 200 表示这个路径成功，`Content-Type` 说明响应体格式，其他 headers 表示服务的安全和缓存边界。

## 用同一服务隔离名字解析变量

直接访问 `127.0.0.1` 跳过了主机名解析。为了测试“名字→地址→HTTP”而不修改 `/etc/hosts`，可以让 curl 临时把 `lab.local` 映射到 loopback：

```bash
curl --noproxy '*' \
  --resolve lab.local:18480:127.0.0.1 \
  -sS -o /dev/null \
  -w 'remote_ip=%{remote_ip} http_code=%{http_code}\n' \
  http://lab.local:18480/health
```

当前输出：

```text
remote_ip=127.0.0.1 http_code=200
```

`--resolve` 的键包含 host、port 和 address，只对这次 curl 命令生效。`--noproxy '*'` 防止环境代理把本地教学请求转发出去。这个命令验证 curl 使用指定地址并发送 `Host: lab.local:18480`，它仍然没有测试真实 DNS 服务器。

## 读响应头的顺序

1. status line：请求是否成功进入目标路径。
2. content type：客户端如何解释 body。
3. cache control：响应是否可以被缓存。
4. security headers：浏览器或客户端能获得哪些防护提示。
5. server banner：是否暴露过多实现信息，教学 lab 使用 Python stdlib，会显示基础 banner。

还可以把 verbose trace 按阶段读：

```text
Trying / Connected  -> 地址与 TCP
> GET / Host        -> 客户端请求
< HTTP/1.0 200      -> 应用状态
< Content-Type ...  -> 响应元数据
Closing connection  -> 连接生命周期
```

当前服务使用 `BaseHTTPRequestHandler` 的默认 HTTP/1.0 响应。它适合展示状态变化，不能用来推断 HTTP/2、连接复用或生产代理行为。

## 常见错误

1. **把 DNS 和 HTTP 混为一谈。** DNS 只负责名字到地址。
2. **只保存 body。** headers 经常包含排障关键线索。
3. **用静默 curl 做排障。** 自动化可以静默，定位问题时应保留 verbose trace。
4. **把本地 200 当全局可达。** loopback 成功只说明本机路径可达。

## 练习或延伸

1. 把 URL 改成 `http://localhost:18480/health`，观察 `curl -v` 是否显示 IPv6 或 IPv4 尝试。
2. 访问 `/headers`，查看服务端看到的请求头。
3. 用下面的命令只输出状态码，比较它和 `-v` 的用途差异：

   ```bash
   curl -sS -o /dev/null -w '%{http_code}\n' \
     http://127.0.0.1:18480/health
   ```

## 参考资料

- Linux man-pages：[getent(1)](https://man7.org/linux/man-pages/man1/getent.1.html)
- Linux man-pages：[nsswitch.conf(5)](https://man7.org/linux/man-pages/man5/nsswitch.conf.5.html)
- Linux man-pages：[resolv.conf(5)](https://man7.org/linux/man-pages/man5/resolv.conf.5.html)
- Everything curl：[Verbose](https://ec.haxx.se/usingcurl/verbose/index.html)
- Everything curl：[Name resolve tricks](https://everything.curl.dev/usingcurl/connections/name.html)
- curl 文档：[Write out](https://everything.curl.dev/usingcurl/verbose/writeout.html)


{% endraw %}
