---
layout: post
title: "DNS 到 HTTP：用 getent 和 curl -v 读懂一次请求"
date: 2026-06-27 23:02:00 +0800
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
grep -E '^(nameserver|search|options)' /etc/resolv.conf
```

对本地服务执行 verbose 请求：

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

## 读响应头的顺序

1. status line：请求是否成功进入目标路径。
2. content type：客户端如何解释 body。
3. cache control：响应是否可以被缓存。
4. security headers：浏览器或客户端能获得哪些防护提示。
5. server banner：是否暴露过多实现信息，教学 lab 使用 Python stdlib，会显示基础 banner。

## 常见错误

1. **把 DNS 和 HTTP 混为一谈。** DNS 只负责名字到地址。
2. **只保存 body。** headers 经常包含排障关键线索。
3. **用静默 curl 做排障。** 自动化可以静默，定位问题时应保留 verbose trace。
4. **把本地 200 当全局可达。** loopback 成功只说明本机路径可达。

## 练习或延伸

1. 把 URL 改成 `http://localhost:18480/health`，观察 `curl -v` 是否显示 IPv6 或 IPv4 尝试。
2. 访问 `/headers`，查看服务端看到的请求头。
3. 用 `curl -w '%{http_code}
'` 只输出状态码，比较它和 `-v` 的用途差异。

## 参考资料

- Linux man-pages：[resolv.conf(5)](https://man7.org/linux/man-pages/man5/resolv.conf.5.html)
- Everything curl：[Verbose](https://ec.haxx.se/usingcurl/verbose/index.html)
- curl 文档：[Write out](https://everything.curl.dev/usingcurl/verbose/writeout.html)


{% endraw %}
