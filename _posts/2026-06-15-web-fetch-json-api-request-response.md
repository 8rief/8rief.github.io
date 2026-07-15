---
layout: post
title: "fetch 调 API：请求方法、JSON、状态码和错误处理"
date: 2026-06-15 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 GET、POST、PATCH、DELETE 四个请求看懂浏览器如何和本地 API 说话。"
tags: [web, fetch, json, api, teaching]
---
{% raw %}
> 主题：最小 Web 前后端项目 / fetch / JSON / API response
> 本文 lab 已验证：`GET /api/tasks`、`POST /api/tasks`、`PATCH /api/tasks/3`、`DELETE /api/tasks/3` 都返回预期状态。

前端和后端之间最常见的接口形态是 HTTP + JSON。浏览器通过 `fetch()` 发请求，服务器用状态码说明成功或失败，用 JSON 传回结构化数据。学会读这条边界，比背框架 API 更重要。

## 学习目标

1. 区分 GET、POST、PATCH、DELETE 在这个任务面板里的用途。
2. 会读取 `response.ok`、`response.status` 和 JSON 响应体。
3. 知道错误也应该有可解释的 JSON 结构。

## 先修知识

已经能运行任务面板并看到前端页面。

## 核心模型

![fetch JSON API 流程](/assets/diagrams/web-fetch-json-api-flow.svg)

`fetch()` 返回的是响应对象。代码先看状态，再解析 JSON。成功响应用于渲染页面，失败响应用于提示用户。

## 为什么需要把 HTTP 方法和 JSON 讲清楚

前端调用 API 时，真正传递给后端的信息只有几类：URL、method、headers、body。URL 指向资源，method 表达动作，JSON body 携带结构化输入，状态码表达结果。把这四件事分清楚，才能读懂 Network 面板，也能设计可测试的接口。

在任务面板里，每个动作都有明确语义：

1. `GET /api/tasks`：读取当前任务列表。
2. `POST /api/tasks`：创建一个新任务。
3. `PATCH /api/tasks/:id`：修改某个任务的 `done` 状态。
4. `DELETE /api/tasks/:id`：删除某个任务。

这些方法让 API 行为可以从请求本身读出来。后续换成 Express、Fastify 或其他框架时，底层契约仍然是这一组 HTTP 交互。

## 可信资料的关键结论

- MDN Fetch API 说明 `fetch()` 用于获取资源并处理响应，比旧的 XMLHttpRequest 更灵活。
- MDN Response 文档指出 `response.ok` 表示状态码是否在 200 到 299 范围内。
- MDN HTTP 状态码文档把状态码分为成功、重定向、客户端错误、服务器错误等类别。

## 逐步实现

本包封装了一个小函数：

```js
async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'content-type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.message || `HTTP ${response.status}`);
  }
  return payload;
}
```

读取任务列表：

```js
const payload = await fetchJson('/api/tasks');
render(payload.tasks, payload.summary);
```

新增任务：

```js
await fetchJson('/api/tasks', {
  method: 'POST',
  body: JSON.stringify({ title })
});
```

更新任务：

```js
await fetchJson(`/api/tasks/${id}`, {
  method: 'PATCH',
  body: JSON.stringify({ done })
});
```

删除任务：

```js
await fetchJson(`/api/tasks/${id}`, { method: 'DELETE' });
```

端到端 smoke 记录了实际状态：

```text
GET /api/health -> 200
GET / -> 200
GET /api/tasks -> 200
POST /api/tasks -> 201
PATCH /api/tasks/3 -> 200
POST /api/tasks -> 400
DELETE /api/tasks/3 -> 200
```

注意 `POST /api/tasks -> 400` 是故意测试空标题。失败路径能被验证，API 才更可靠。

## 输出怎么读

端到端 transcript 里的状态码可以逐条解释：

- `GET /api/health -> 200`：服务进程可用。
- `GET / -> 200`：静态首页可用。
- `GET /api/tasks -> 200`：任务列表可读。
- `POST /api/tasks -> 201`：新任务创建成功，201 表示 created。
- `PATCH /api/tasks/3 -> 200`：id 为 3 的任务更新成功。
- `POST /api/tasks -> 400`：空标题被后端拒绝。
- `DELETE /api/tasks/3 -> 200`：刚创建的任务被删除。

这组输出覆盖成功和失败路径。尤其是 400，它证明前端不能只看 JSON 结构，还必须看 `response.ok` 或状态码。

## fetchJson 的边界

`fetchJson()` 统一做三件事：设置 JSON 请求头、解析 JSON 响应、把非 2xx 状态转成异常。它不负责决定业务下一步怎么做。创建、更新、删除函数捕获异常后，把错误 message 写入页面状态区。这样 API 规则变化时，前端错误展示路径仍然集中。

## 常见错误

1. **只解析 JSON，不看状态码。** 失败响应也可能有 JSON，但不能当成功处理。
2. **POST 忘记 `JSON.stringify`。** 请求体必须是字符串或其他可发送格式。
3. **错误响应只返回纯文本。** 前端很难统一展示错误。
4. **把所有操作都写成 GET。** 修改数据的动作应使用能表达意图的方法。

## 练习或延伸

1. 在 Network 面板里查看 `POST /api/tasks` 的请求体。
2. 把新增任务标题设为空，确认前端显示服务器返回的错误信息。
3. 给 API 增加 `GET /api/tasks/:id`，返回单个任务。

## 参考资料

- MDN：[Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- MDN：[Window.fetch()](https://developer.mozilla.org/en-US/docs/Web/API/Window/fetch)
- MDN：[Response](https://developer.mozilla.org/en-US/docs/Web/API/Response)
- MDN：[HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)

{% endraw %}
