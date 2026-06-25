---
layout: post
title: "Python HTTP client：用 httpx 把外部服务接进项目"
date: 2026-06-25 16:33:00 +0800
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
