---
layout: post
title: "API 输入校验：让失败路径也能被前端解释"
date: 2026-06-17 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用空标题、非法 JSON、找不到任务等情况解释 400、404、413 和错误响应体。"
tags: [web, api, validation, http-status, teaching]
---
{% raw %}
> 主题：最小 Web 前后端项目 / validation / error boundary
> 本文 lab 已验证：空标题新增会返回 400，并得到 `invalid_title` 错误码。

一个 API 只处理成功路径，很快会让前端和用户陷入猜测。输入为空、JSON 格式错误、任务不存在、请求体过大，都应该有明确状态码和错误响应体。失败路径可解释，前端才能给出准确提示。

## 学习目标

1. 区分输入校验错误、资源不存在和服务器内部错误。
2. 设计统一的 JSON 错误响应格式。
3. 用测试覆盖失败路径，而不只测试成功路径。

## 先修知识

知道前端通过 `fetchJson()` 调 API，并会根据 `response.ok` 判断成功或失败。

## 核心模型

![API 输入校验和错误边界](/assets/diagrams/web-api-validation-error-boundary.svg)

错误处理也属于接口契约。服务器负责指出错误类型和可读信息；前端负责展示这条信息，而不是猜测失败原因。

## 为什么需要把失败路径当作主线

真实用户不会只提交正确输入。空标题、格式错误、重复请求、找不到资源都很常见。API 如果只在成功路径上设计清楚，前端就只能显示“出错了”这类模糊提示，测试也无法确认错误属于哪一类。

本项目把错误响应统一成：

```json
{
  "error": "invalid_title",
  "message": "Title length must be between 1 and 80 characters."
}
```

`error` 给程序和测试使用，`message` 给用户界面使用。状态码给 HTTP 层使用。三者合起来，失败路径才可以被前端解释、被测试固定、被读者复查。

## 可信资料的关键结论

- MDN 状态码文档把 400 段归为客户端错误，适合表达请求内容不符合要求。
- `Response.ok` 只在 200 到 299 状态码为 true；前端不能把 400 的 JSON 当成功数据。
- 413 表示请求内容过大；即使本地项目，也应限制请求体大小，避免脚本误传大文件。

## 逐步实现

标题校验：

```js
const title = normalizeTitle(payload.title);
if (title.length < 1 || title.length > 80) {
  sendJson(res, 400, {
    error: 'invalid_title',
    message: 'Title length must be between 1 and 80 characters.'
  });
  return;
}
```

找不到任务：

```js
if (!task) {
  sendJson(res, 404, {
    error: 'not_found',
    message: `Task ${id} does not exist.`
  });
  return;
}
```

请求体大小限制：

```js
if (size > JSON_LIMIT_BYTES) {
  const error = new Error('request body too large');
  error.status = 413;
  throw error;
}
```

smoke 脚本故意发送空标题：

```text
POST /api/tasks -> 400
invalid_title_status=400
```

这条验证很重要：它说明前端错误提示来自后端明确响应，可以随接口规则一起被测试。

## 输出怎么读

smoke 报告里的关键字段是：

```json
{
  "invalid_title_status": 400
}
```

它表示空标题请求被服务器按客户端输入错误处理。测试里还会断言错误码是 `invalid_title`，因此如果后端以后误把空标题当成功创建，或者改成 500，测试都会失败。

其他边界也有明确状态：

- JSON 解析失败：400，错误类型 `invalid_json`。
- PATCH 的 `done` 不是布尔值：400，错误类型 `invalid_done`。
- 任务 id 不存在：404，错误类型 `not_found`。
- 请求体超过限制：413，由服务器错误边界转换为 JSON 响应。

## 前后端如何分工

前端可以先做空标题检查，给用户更快反馈；后端仍必须重复校验，因为任何人都可以绕过页面直接发送 HTTP 请求。后端是可信边界，前端是交互体验层。这个分工在小项目里也应保持。

## 常见错误

1. **后端只返回 `error` 字符串。** 前端无法区分错误类型，也不方便测试。
2. **所有失败都返回 500。** 输入错误和服务器故障应区分。
3. **校验只放在前端。** 用户可以绕过页面直接调用 API，后端仍要校验。
4. **测试只覆盖成功路径。** 失败路径没有测试时，错误提示很容易悄悄坏掉。

## 练习或延伸

1. 把标题最大长度从 80 改成 40，并补充测试。
2. 给 PATCH 增加非法 `done` 值测试，例如 `{ "done": "yes" }`。
3. 为所有错误响应增加 `requestId` 字段，方便日志定位。

## 参考资料

- MDN：[HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)
- MDN：[Response.ok](https://developer.mozilla.org/en-US/docs/Web/API/Response/ok)
- MDN：[Response.status](https://developer.mozilla.org/en-US/docs/Web/API/Response/status)

{% endraw %}
