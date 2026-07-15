---
layout: post
title: "HTTP 加固基础：方法、响应头、超时和绑定地址"
date: 2026-05-23 18:00:00 +0800
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

## 为什么需要最小清单

“服务能返回 200”只覆盖了可用性的一小部分。监听地址过宽会改变谁能连接，未设计的方法会扩大处理分支，缺少缓存与内容解释约束会让客户端采用服务端未预期的行为。把这些状态拆成清单，才能在每次修改后重新检查，而不是依赖上线前的一次人工浏览。

这份清单只覆盖可被当前本地 lab 观察的控制项。它没有身份系统、TLS 终止层或反向代理，因此不会给这些项目虚构通过状态。

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

在 lab 根目录保持前文的 loopback server 运行，再执行：

```bash
PYTHONPATH=src python3 -m local_netsec_lab.cli hardening \
  --base-url http://127.0.0.1:18480 \
  --bind-host 127.0.0.1 \
  --output reports/hardening_report.json
```

本次报告中所有静态检查为 pass，响应头检查包括：

```text
X-Content-Type-Options: nosniff
Cache-Control: no-store
Content-Security-Policy: default-src 'none'
```

这些 headers 不能替代认证、授权、输入验证和日志审计，但它们能降低常见客户端解释风险，也能作为服务设计意识的体现。

### 三个响应头分别约束什么

- `X-Content-Type-Options: nosniff` 要求浏览器遵守声明的 `Content-Type`，避免自行猜测另一种媒体类型。
- `Cache-Control: no-store` 告诉缓存不要存储这份响应；敏感响应仍需结合认证、代理配置和具体缓存模型审查。
- `Content-Security-Policy: default-src 'none'` 为浏览器资源加载设置拒绝式默认值。当前响应是 JSON，因此它主要展示默认拒绝思路，不能直接复制成完整 Web 应用的策略。

响应头由 handler 的统一出口加入：

```python
def end_headers(self) -> None:
    self.send_header("X-Content-Type-Options", "nosniff")
    self.send_header("Cache-Control", "no-store")
    self.send_header("Content-Security-Policy", "default-src 'none'")
    super().end_headers()
```

统一出口避免某个正常路径有 headers、错误路径却遗漏。生产框架通常用中间件承担同一职责。

## 方法边界

lab 允许 GET 和 HEAD，POST 返回 405。405 响应同时给出 `Allow`，让客户端知道当前资源接受的方法：

```bash
curl -sS -i -X POST http://127.0.0.1:18480/health
```

关键输出：

```text
HTTP/1.0 405 Method Not Allowed
Allow: GET, HEAD
{"error": "method not allowed"}
```

方法边界让 API 表面可预测。它不能代替授权：即使某个用户可以发送 GET，也不代表他有权读取所有 GET 资源。真实服务还需要认证、对象级鉴权、CSRF/跨域策略、速率限制和日志。

## 报告里的证据层级

`runtime_headers` 来自对 `/health` 的真实请求；`bind-address` 等 `items` 是本地设计清单。405、路径边界和命令边界由单元测试及各自报告验证。阅读总报告时要保留这一区分：配置声明、运行观察和回归测试是三种证据，不能因为都写成 `pass` 就认为强度相同。

本次完整 lab 运行了 12 个测试，包含 POST→405、`Allow` header、路径越界拒绝、loopback 范围和 IPv6 loopback 探测：

```text
Ran 12 tests
OK
```

Python 官方文档也明确指出 `http.server` 只实现基础安全检查，不建议用于生产。这里选择它是为了让 socket、handler 和 header 行为可见，不是为了搭建生产服务器。

## 常见错误

1. **绑定 `0.0.0.0` 后忘记暴露范围。** 本地教学服务应绑定 loopback。
2. **headers 写了就以为安全。** headers 是防护的一部分，核心仍是服务端边界。
3. **方法未限制。** 未设计的 method 应返回明确错误。
4. **报告不可复跑。** 口头清单应转成脚本和 JSON 证据。

## 练习或延伸

1. 给报告增加 `server-banner` 检查，观察 Python stdlib 默认输出。
2. 增加 OPTIONS 请求处理，明确返回允许的方法。
3. 把 hardening report 转成 Markdown 表格。
4. 给测试增加一个不存在的 header，确认报告返回 `review`，而不是静默通过。

## 参考资料

- Python 文档：[http.server 及安全说明](https://docs.python.org/3/library/http.server.html#security-considerations)
- RFC 9110：[405 Method Not Allowed](https://www.rfc-editor.org/rfc/rfc9110.html#name-405-method-not-allowed)
- OWASP Cheat Sheet Series：[项目首页](https://owasp.org/www-project-cheat-sheets/)
- MDN Web Docs：[X-Content-Type-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options)
- MDN Web Docs：[Content-Security-Policy: default-src](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/default-src)


{% endraw %}
