---
layout: post
title: "fetch 调 API：请求方法、JSON、状态码和错误处理"
date: 2026-07-01 10:14:00 +0800
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
