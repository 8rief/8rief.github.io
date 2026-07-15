---
layout: post
title: "最小全栈心智模型：浏览器、HTTP、服务器和 JSON 文件怎么连起来"
date: 2026-04-09 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从一个任务面板 lab 出发，看清前端页面、API、服务器和持久化文件之间的边界。"
tags: [web, fullstack, http, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/minimal-web-fullstack/README.md`](/assets/labs/minimal-web-fullstack/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

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

## 为什么需要先学边界

全栈项目容易让初学者同时面对太多名词：路由、组件、接口、数据库、部署、跨域、状态管理。先把边界画清楚，是为了把问题压缩成可观察的请求链路。页面加载失败、按钮没反应、数据没有保存，分别属于不同层。

本 lab 用一个本地任务面板建立最小边界：

1. 浏览器请求 `/`，服务器返回 HTML。
2. HTML 加载 `app.js`，脚本绑定表单和按钮事件。
3. 前端通过 `fetch('/api/tasks')` 调用 API。
4. 服务器按 URL 和 method 选择处理逻辑。
5. 服务器读写 JSON 文件，返回新的任务列表和 summary。

这个顺序能帮助你定位故障。比如页面能打开但列表为空，先查 `GET /api/tasks`；新增任务返回 400，查 API 输入校验；刷新后数据丢失，查 JSON 文件写入。

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

## 输出怎么读

这些输出分别证明不同层已经接上：

- `fetch_available=function`：当前 Node 环境有全局 `fetch`，smoke 脚本能直接发 HTTP 请求。
- `# tests 2`、`# pass 2`：接口测试覆盖了任务 CRUD、静态页面和缺失 API 路由。
- `initial_count=2`：服务器从 seed JSON 文件读到了 2 条任务。
- `created_id=3`：`POST /api/tasks` 经过服务器逻辑生成了新 id。
- `final_total=2`：新增、更新、删除之后，最终列表又回到 2 条。
- `smoke_status=ok`：端到端请求链路全部完成。

这些输出把页面、API、持久化和测试连成了可复查闭环。

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

## 状态变化跟踪

一次新增任务的状态变化可以写成：

```text
输入框里的标题
-> submit 事件
-> fetch POST /api/tasks
-> server normalizeTitle + nextId
-> tasks.json 写入新数组
-> JSON 响应返回 task 和 summary
-> 前端重新 GET /api/tasks 并渲染列表
```

这个链路中任意一步失败，都应该能找到对应证据：浏览器 Network、服务器状态码、数据文件内容或 smoke transcript。

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
