---
layout: post
title: "最小全栈心智模型：浏览器、HTTP、服务器和 JSON 文件怎么连起来"
date: 2026-07-01 10:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从一个任务面板 lab 出发，看清前端页面、API、服务器和持久化文件之间的边界。"
tags: [web, fullstack, http, teaching]
---
{% raw %}
> 主题：最小 Web 前后端项目 / full-stack boundary / request-response
> 本文 lab 已验证：页面、API、JSON 文件和测试脚本串通，`smoke_status=ok`。

很多 0 基础学习者听到“前后端”会先想到框架名。更稳的入口是先看一次完整数据流：浏览器打开页面，页面用 JavaScript 发起 HTTP 请求，本地服务器按 URL 和方法选择处理逻辑，最后把任务列表保存到 JSON 文件。框架可以以后再学，第一步要先知道每一层到底负责什么。

## 学习目标

1. 区分浏览器页面、HTTP 请求、服务器路由、API 响应和本地持久化文件。
2. 运行一个无第三方依赖的本地任务面板，并看到可验证输出。
3. 理解为什么最小全栈项目也需要测试和 transcript。

## 先修知识

需要能运行 `node --version`，并能在终端执行 `bash run_lab.sh`。不要求先会 React、Vue、Express 或数据库。

## 核心模型

![最小全栈请求响应边界](/assets/diagrams/web-fullstack-request-response-boundary.svg)

这个项目只有四个核心部件：静态页面、浏览器脚本、本地 HTTP 服务器、JSON 数据文件。浏览器只通过 HTTP 认识服务器；服务器只通过文件读写保存数据。边界清楚后，调试才有方向。

## 可信资料的关键结论

- MDN 对 HTTP 的说明强调：请求方法表达意图，状态码表达结果。
- Node.js `node:http` 是稳定模块，可以直接创建 HTTP 服务器；本包用它避免一开始被框架封装挡住视线。
- MDN Fetch API 说明浏览器可以通过 `fetch()` 发起网络请求并处理响应；本包前端用它调用本地 API。

## 逐步实现

在 lab 目录运行：

```bash
bash run_lab.sh
```

关键输出：

```text
node_version=v22.22.2
fetch_available=function
# tests 2
# pass 2
initial_count=2
created_id=3
final_total=2
smoke_status=ok
```

这些输出说明：Node 环境可用；内置测试通过；端到端 smoke 脚本确实启动服务器、访问页面、调用 API、创建任务、更新任务、删除任务并验证最终统计。

手动运行应用：

```bash
node scripts/reset-data.mjs data/tasks.json
node server.mjs
```

然后打开：

```text
http://127.0.0.1:3000
```

你会看到一个任务面板。新增任务时，浏览器发出 `POST /api/tasks`；点击完成时，浏览器发出 `PATCH /api/tasks/:id`；删除时，浏览器发出 `DELETE /api/tasks/:id`。

## 常见错误

1. **先学框架名，没看清数据流。** 框架只是组织代码的方式，底层仍是请求和响应。
2. **把页面打开当作项目成功。** 页面能打开只验证了静态文件，不能证明 API 和持久化正确。
3. **不知道错误在哪一层。** 先看浏览器控制台和 Network，再看服务器日志，再看数据文件。
4. **忽略本地边界。** 本包监听 `127.0.0.1`，目标是本机学习，不是公网部署。

## 练习或延伸

1. 打开浏览器开发者工具的 Network 面板，新增一个任务，观察 `POST /api/tasks`。
2. 修改 `data/tasks.json` 中一个任务标题，刷新页面，看前端是否重新读取到变化。
3. 在服务器终端停止进程，再刷新页面，观察页面和 API 的失败表现。

## 参考资料

- MDN：[HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP)
- MDN：[Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- Node.js：[HTTP](https://nodejs.org/api/http.html)

{% endraw %}
