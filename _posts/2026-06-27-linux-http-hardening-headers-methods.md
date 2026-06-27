---
layout: post
title: "HTTP 加固基础：方法、响应头、超时和绑定地址"
date: 2026-06-27 23:04:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地服务的 headers、405、bind address 和 hardening report 建立 HTTP 服务加固清单。"
tags: [linux, http, hardening, security-headers]
---
{% raw %}

> 主题：Linux 网络与授权安全基础 / HTTP hardening
> 本文用本地服务生成 hardening report，不评价真实生产系统。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

HTTP 加固可以从最小清单开始：服务绑定在哪个地址，允许哪些方法，响应头怎样指导客户端，路径是否被限制，命令执行是否经过验证，工具是否限制了探测范围。lab 把这些检查写成结构化报告。

## 学习目标

1. 解释 bind address 对暴露面的影响。
2. 检查 unsupported method 是否返回 405。
3. 识别几个基础响应头的作用。
4. 把安全检查写成可复跑 JSON 报告。

## 先修知识

需要知道 HTTP method、response header 和 loopback 地址。

## 核心模型

![HTTP 加固检查链](/assets/diagrams/linux-http-hardening-headers-methods.svg)

一个最小检查链从网络暴露面开始，再看方法、headers、路径边界、子进程边界和工具范围。

## 逐步实现

运行：

```bash
python3 -m local_netsec_lab.cli hardening   --base-url http://127.0.0.1:18480   --bind-host 127.0.0.1   --output reports/hardening_report.json
```

本次报告中所有静态检查为 pass，响应头检查包括：

```text
X-Content-Type-Options: nosniff
Cache-Control: no-store
Content-Security-Policy: default-src 'none'
```

这些 headers 不能替代认证、授权、输入验证和日志审计，但它们能降低常见客户端解释风险，也能作为服务设计意识的体现。

## 方法边界

lab 允许 GET 和 HEAD，POST 返回 405。方法边界的意义是让 API 表面可预测。真实服务还需要认证、鉴权、CSRF/跨域策略、速率限制和日志。

## 常见错误

1. **绑定 `0.0.0.0` 后忘记暴露范围。** 本地教学服务应绑定 loopback。
2. **headers 写了就以为安全。** headers 是防护的一部分，核心仍是服务端边界。
3. **方法未限制。** 未设计的 method 应返回明确错误。
4. **报告不可复跑。** 口头清单应转成脚本和 JSON 证据。

## 练习或延伸

1. 给报告增加 `server-banner` 检查，观察 Python stdlib 默认输出。
2. 增加 OPTIONS 请求处理，明确返回允许的方法。
3. 把 hardening report 转成 Markdown 表格。

## 参考资料

- Python 文档：[http.server](https://docs.python.org/3/library/http.server.html)
- OWASP Cheat Sheet Series：[项目首页](https://owasp.org/www-project-cheat-sheets/)
- MDN Web Docs：[X-Content-Type-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options)


{% endraw %}
