---
layout: post
title: "Node.js HTTP 服务器：路由、静态文件和 API 边界"
date: 2026-06-16 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "不用框架，直接用 node:http 看清 URL、method、静态资源和 JSON API 如何分流。"
tags: [nodejs, http, web-server, teaching]
---
{% raw %}
> 主题：最小 Web 前后端项目 / Node.js / HTTP routing / static files
> 本文 lab 已验证：`/` 返回 HTML，`/api/health` 返回 JSON，未知 API 返回 404。

框架能提高效率，但 0 基础阶段容易让人看不见服务器的基本工作。一个 HTTP 服务器最核心的动作很少：读请求方法和 URL，决定交给静态文件处理还是 API 处理，然后写出状态码、头部和响应体。

## 学习目标

1. 知道 Node.js `node:http` 如何创建本地服务器。
2. 区分静态文件路由和 API 路由。
3. 理解 URL、method 和状态码是后端接口的最小契约。

## 先修知识

已经知道浏览器会请求 `/`，前端会请求 `/api/tasks`。

## 核心模型

![Node HTTP 路由分流](/assets/diagrams/web-node-http-routing-static-api.svg)

服务器先判断路径是否以 `/api/` 开头。API 请求返回 JSON；其他 GET 请求按静态文件处理。这个分流规则简单，但已经覆盖最小全栈项目的关键边界。

## 为什么需要先看无框架服务器

Express、Koa、Fastify 会帮你写掉很多样板代码，但初学阶段如果直接从框架开始，很容易把路由、静态文件、状态码和响应头都当成魔法。先用 `node:http` 写一次最小服务器，可以看清框架到底在封装什么。

本 lab 的服务器只做四件事：

1. 解析 `req.url` 得到 pathname。
2. 按 `/api/` 前缀决定 API 分支或静态文件分支。
3. API 分支按 method 和 path 返回 JSON。
4. 静态分支从 `public/` 目录读取 HTML、CSS、JS。

理解这四件事后，再学习框架路由时会更清楚：框架主要是在帮你组织同样的请求分发逻辑。

## 可信资料的关键结论

- Node.js `node:http` 文档说明该模块包含 HTTP 客户端和服务器能力，可通过 `node:http` 导入。
- Node.js HTTP API 是低层接口，开发者需要自己处理路由、头部和响应体。
- URL 解析应使用标准 `URL` 对象，避免手写字符串切分时漏掉查询参数和编码问题。

## 逐步实现

服务器入口：

```js
import { createServer as createHttpServer } from 'node:http';

export function createApp(options = {}) {
  return createHttpServer(async (req, res) => {
    const url = new URL(req.url || '/', 'http://localhost');
    if (url.pathname.startsWith('/api/')) {
      await handleApi(req, res, url, dataFile);
      return;
    }
    await serveStatic(req, res, url, publicDir);
  });
}
```

静态文件规则：

```js
const rawPath = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
const candidate = path.normalize(path.join(publicDir, rawPath));
```

这里 `/` 会映射到 `public/index.html`。`/styles.css` 和 `/app.js` 会映射到对应文件。代码还检查最终路径仍在 `public` 目录下，避免路径穿越。

API 路由按路径和方法判断：

```js
if (url.pathname === '/api/tasks' && req.method === 'GET') { ... }
if (url.pathname === '/api/tasks' && req.method === 'POST') { ... }
if (id && req.method === 'PATCH') { ... }
if (id && req.method === 'DELETE') { ... }
```

端到端 smoke 同时访问了页面和 API，因此它能证明静态文件分支和 API 分支都能工作。

## 输出怎么读

smoke transcript 中与服务器路由相关的几行是：

```text
GET /api/health -> 200
GET / -> 200
GET /api/tasks -> 200
```

第一行证明 API 分支能返回 JSON；第二行证明静态文件分支能把 `/` 映射到 `index.html`；第三行证明 API 分支能读数据文件并返回任务列表。测试还覆盖了未知 API 路由：

```text
GET /api/missing -> 404
```

这说明路由表里没有的 API 会返回明确 JSON 错误，而不是落到静态文件处理里。

## 静态文件边界

`serveStatic()` 会把请求路径映射到 `public` 目录下的文件，并检查 normalize 后的路径仍在 public 根目录内。这个检查属于基础安全习惯：URL 来自客户端，不能直接让它访问任意磁盘路径。学习阶段不需要展开攻击技巧，只需要记住“路径映射必须有根目录边界”。

## 常见错误

1. **只按 URL，不看 method。** `/api/tasks` 的 GET 和 POST 是两个不同动作。
2. **静态文件路径不做边界检查。** 用户输入的路径不能随意映射到磁盘任意位置。
3. **API 和页面混用响应格式。** 页面返回 HTML，API 返回 JSON，错误也要保持一致。
4. **服务器监听所有网卡。** 学习阶段默认监听 `127.0.0.1`，减少暴露面。

## 练习或延伸

1. 增加一个 `/api/health` 字段，例如当前任务文件路径的 basename。
2. 故意访问 `/api/missing`，观察 JSON 404 响应。
3. 访问一个不存在的静态文件，例如 `/missing.css`，观察文本 404 响应。

## 参考资料

- Node.js：[HTTP](https://nodejs.org/api/http.html)
- Node.js：[URL](https://nodejs.org/api/url.html)
- MDN：[HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP)

{% endraw %}
