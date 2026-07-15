---
layout: post
title: "HTTP 请求和响应：curl 看到的 method、path、status 和 headers"
date: 2026-06-08 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地 HTTP 服务和 curl -i 解释请求行、响应状态、header、body 与服务器 handler 的关系。"
tags: [networking, http, curl, python, teaching]
---
{% raw %}
> 主题：非安全向计算机网络基础 / HTTP / curl
> 本文 lab 已验证：本地 HTTP 服务返回 200，`Content-Type` 为 `application/json; charset=utf-8`，响应体包含 `hello network`。

HTTP 是应用层协议。TCP 负责把字节送到服务端进程，HTTP 负责解释这些字节：请求方法是什么，路径是什么，header 里有什么，服务端返回哪个状态码、哪些 header 和什么 body。

## 学习目标

1. 区分 TCP 连接和 HTTP 请求语义。
2. 读懂 `curl -i` 输出里的 status line、headers 和 body。
3. 理解服务端 handler 如何从 path 生成响应。
4. 知道 HTTP 状态码是应用协议结果，不等于底层网络连通性本身。

## 先修知识

需要理解 TCP socket 和端口。本文只使用本地 HTTP 服务，避免外部站点差异影响观察。

## 核心模型

![HTTP 请求响应结构](/assets/diagrams/network-http-request-response-curl.svg)

`curl` 构造 HTTP 请求；请求行包含 method 和 path；headers 描述客户端能力或元数据；服务端 handler 根据 path 返回 status、headers 和 body；客户端再解析这些响应字段。

## 逐步实现

lab 的服务端返回 JSON：

```python
body = {"method": "GET", "path": self.path, "message": "hello network"}
```

本地请求：

```bash
curl -sS -i --max-time 2 http://127.0.0.1:PORT/hello?name=network
```

lab 摘要：

```text
http_status=200 body_contains=True
content_type: application/json; charset=utf-8
```

`-i` 让 curl 输出响应 header。看到 `HTTP/1.0 200 OK` 或类似状态行时，只能说明 HTTP 层给出了成功响应；若 body 内容不符合业务预期，应用仍然要判定失败。

## 为什么要引入 HTTP 语义层

HTTP 语义层要解决的核心问题是“连接成功之后，应用还要表达意图”。TCP 只传字节，不知道 `GET /hello` 是什么含义，也不知道 `200`、`404`、`Content-Type` 如何解释。HTTP 把这些字节组织成请求、响应和缓存/内容协商等语义。

最小请求可以拆成：

```text
GET /hello?name=network HTTP/1.1
Host: 127.0.0.1:PORT
User-Agent: curl/...
```

最小响应可以拆成：

```text
HTTP/1.0 200 OK
Content-Type: application/json; charset=utf-8

{"message":"hello network"}
```

这些字段都发生在应用层。

## curl 输出怎么读

`curl -i` 把响应 header 和 body 一起打印。阅读顺序：

```text
status line     -> HTTP 版本、状态码、原因短语
headers         -> 内容类型、长度、缓存、服务端元数据
blank line      -> header 和 body 的分界
body            -> 应用真正返回的数据
```

如果 status 是 200，但 body 缺少业务字段，应用仍应判定失败。若 status 是 500，底层 TCP 连接可能完全正常，失败发生在服务端应用逻辑。

## path 如何进入 handler

本地服务端把 path 放进 JSON：

```python
body = {"method": "GET", "path": self.path, "message": "hello network"}
```

请求 `/hello?name=network` 后，body 中的 `path` 应包含查询字符串。这个例子说明 handler 看到的是 HTTP 请求目标，而不是裸 TCP 字节。

## 输出怎么读

lab 摘要：

```text
http_status=200 body_contains=True
content_type: application/json; charset=utf-8
```

`http_status=200` 说明服务端按 HTTP 返回成功状态；`body_contains=True` 说明 body 中出现了预期业务文本；`content_type` 说明客户端应按 JSON 文本解释响应体。三项一起看，才比单独看 200 更可靠。

## 常见排查顺序

HTTP 请求失败时可以这样问：

```text
URL 是否解析到预期 host/port/path？
TCP 是否能连接？
请求 method 是否被 handler 支持？
status code 是否符合预期？
Content-Type 是否符合 body？
body 字段是否满足业务断言？
```

这条顺序把网络连通性和应用语义分开。

## 常见错误

1. **把 200 当作业务成功的全部证据。** 还要检查 body、字段和业务规则。
2. **忽略超时。** 网络或服务端卡住时，客户端应该有明确 timeout。
3. **把 header 当正文。** header 描述元数据，body 承载主要内容。
4. **忽略 path 和 query。** 服务端 handler 常常依赖 path 和 query 决定行为。

## 练习或延伸

1. 用 `curl -v` 再请求一次，比较 `-i` 和 `-v` 的输出差异。
2. 把 path 改成 `/status`，让服务端返回不同 JSON。
3. 给响应加一个 `X-Lab-Name` header，并在 curl 输出中找到它。

## 参考资料

- IETF RFC 9110：[HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- Everything curl：[HTTP with curl](https://everything.curl.dev/http/)
- Python 文档：[http.server](https://docs.python.org/3/library/http.server.html)

{% endraw %}
