---
layout: post
title: "Python HTTP client：用 httpx 把外部服务接进项目"
date: 2026-05-04 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "通过 httpx、timeout、raise_for_status 和项目级错误类型，讲清 HTTP 调用如何进入 Python 项目边界。"
tags: [python, httpx, http-client, timeout, error-handling]
---
{% raw %}


> 主题：Python 从0到可运行项目 / HTTP client / timeout / error surface  
> 本文 lab 使用 `httpx.MockTransport` 做本地 smoke test，不访问外部网络。

很多项目最终都会调用 HTTP 服务：拉取 JSON、请求内部 API、发送 webhook、访问模型服务。直接在业务函数里写 `requests.get(...).json()` 很快，但错误边界会变得模糊：超时、500、非 JSON 响应和字段缺失混在一起。一个小项目也应该把 HTTP 调用包成清楚的边界。

## 学习目标

1. 用 `httpx.Client` 发送 GET 请求。
2. 给 HTTP 请求设置显式 timeout。
3. 用 `raise_for_status()` 把 4xx/5xx 转成异常。
4. 把第三方库异常转换成项目级错误类型。
5. 用 mock transport 做本地可复现测试。

## 先修知识

需要理解 HTTP 状态码和 JSON 对象的基本概念。本文不要求你启动真实服务，测试会在进程内模拟响应。

## 为什么需要 HTTP client 边界

调用外部 HTTP 服务时，失败形式很多：网络连不上、连接很慢、返回 500、返回 HTML 错误页、JSON 结构变化、字段缺失。把这些情况直接暴露给业务函数，会让调用者同时理解 httpx、状态码、JSON 解析和项目语义。

HTTP client 边界把这些复杂情况压缩成一种项目可以处理的契约：成功时返回字典，失败时抛出 `ServiceRequestError`。内部可以使用 httpx 的 timeout、状态码检查和 JSON 解析；外层只面对项目级错误。

显式 timeout 是这个边界的核心。没有 timeout 的请求可能让 CLI 或服务一直等待，表现得像程序卡死。教学 lab 使用 `MockTransport`，让网络边界在进程内可复现；真实网络测试应另设一层，并明确地址、超时、重试和失败告警。


## 核心模型

HTTP client 的目标是把不稳定的网络边界压缩成项目能处理的结果或错误。

![HTTP client 边界](/assets/diagrams/python-http-client-timeout.svg)

调用者不需要知道 httpx 的所有异常类型，只需要知道：成功时得到 JSON 对象；失败时得到 `ServiceRequestError`。

## 封装 fetch_json

示例项目的 HTTP client 很小：

```python
import httpx

class ServiceRequestError(RuntimeError):
    """Boundary error raised when a service request fails."""


def fetch_json(url: str, *, timeout: float = 2.0, client: httpx.Client | None = None) -> dict[str, Any]:
    try:
        if client is not None:
            response = client.get(url)
        else:
            with httpx.Client(timeout=timeout) as owned_client:
                response = owned_client.get(url)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ServiceRequestError(f"GET {url} failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ServiceRequestError(f"GET {url} did not return a JSON object")
    return payload
```

这里有两个工程决策。

第一，timeout 是显式参数。HTTP 调用默认无界等待会让 CLI 或服务卡住，读者很难判断问题来自网络还是程序。

第二，函数允许注入 `client`。真实运行时可以让函数自己创建 client；测试时可以传入 mock client，不需要启动服务器或访问互联网。

## 处理返回结构

客户端拿到 JSON 后，还应在项目边界验证结构：

```python
def summarize_manifest_payload(payload: dict[str, Any]) -> str:
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ServiceRequestError("manifest payload has no summary object")
    return f"files={summary.get('file_count')} bytes={summary.get('total_bytes')}"
```

这个函数不验证整个 OpenAPI schema，但它检查了当前项目真正依赖的字段。小项目先把关键字段守住，比假设远端永远返回正确结构更可靠。

## 本地 smoke test

lab 使用 `httpx.MockTransport` 模拟服务：

```python
def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"summary": {"file_count": 3, "total_bytes": 42}})

with httpx.Client(transport=httpx.MockTransport(handler), base_url="http://local") as client:
    payload = fetch_json("http://local/manifest", client=client)
print("http client mock ->", summarize_manifest_payload(payload))
```

执行结果：

```text
http client mock -> files=3 bytes=42
```

这个 smoke test 验证的是 client 边界，不验证真实网络。真实网络测试应单独做，并明确服务地址、超时和失败重试策略。

## 输出怎么读

本地 mock 输出是：

```text
http client mock -> files=3 bytes=42
```

这行不表示真的访问了外部网站。它表示 `httpx.MockTransport` 返回了一段模拟 JSON，`fetch_json()` 正确处理状态码和 JSON，`summarize_manifest_payload()` 正确读取了 `summary.file_count` 和 `summary.total_bytes`。

如果把 mock 响应改成 HTTP 500，预期行为是抛出 `ServiceRequestError`。如果把响应 JSON 改成数组，也应被结构检查拒绝。

读 HTTP client 测试时要分清三层边界。

1. httpx 边界：连接、状态码、JSON 解析。
2. 项目边界：把第三方异常转成 `ServiceRequestError`。
3. 业务边界：只读取当前项目真正依赖的字段。

这三层分开后，后续要增加重试、认证 header 或 tracing，都可以集中改 client 模块。


## 常见错误

1. **不设置 timeout。** 网络边界必须有等待上限。
2. **只检查 `response.json()`。** 4xx/5xx 也可能返回 JSON 错误体，需要先处理状态码。
3. **把第三方异常泄漏到业务层。** 业务层应该处理项目语义，减少对 httpx 细节异常的依赖。
4. **测试依赖外部网站。** 教学 lab 优先使用 mock 或本地服务，减少不可控因素。

## 练习

1. 增加 `fetch_manifest_summary(base_url: str)`，拼接 `/manifest` 并返回摘要字符串。
2. 模拟 HTTP 500，验证函数抛出 `ServiceRequestError`。
3. 模拟返回数组，观察结构检查如何拒绝非对象响应。

## 参考资料

- HTTPX 文档：[QuickStart](https://www.python-httpx.org/quickstart/)
- HTTPX 文档：[Timeouts](https://www.python-httpx.org/advanced/timeouts/)
- Python 文档：[Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)


{% endraw %}
