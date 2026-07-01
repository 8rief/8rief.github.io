---
layout: post
title: "结课项目：从空目录跑起一个最小任务面板"
date: 2026-07-01 10:49:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把页面、fetch、Node HTTP、JSON 持久化、输入校验和测试合成一个可展示小项目。"
tags: [web, fullstack, capstone, project, teaching]
---
{% raw %}
> 主题：最小 Web 前后端项目 / capstone / task board
> 本文 lab 已验证：任务面板能跑通页面、API、持久化、错误路径和可复查报告。

这个结课项目的目标很明确：不用框架，先做出一个能展示、能测试、能解释边界的本地任务面板。它足够小，适合 0 基础读者逐步理解；它也足够完整，已经包含真实 Web 项目的核心结构。

## 学习目标

1. 从命令行启动一个本地 Web 全栈项目。
2. 看懂前端、API、数据文件、测试脚本分别在哪里。
3. 用浏览器和命令行同时验证项目效果。
4. 知道下一步如何引入框架、数据库或部署。

## 先修知识

建议按顺序读完本包前七篇，并确认 Node.js 可用。

## 核心模型

![最小任务面板结课项目](/assets/diagrams/web-fullstack-capstone-task-board.svg)

结课项目的闭环是：页面接收用户输入，前端用 fetch 调 API，服务器修改 JSON 文件，测试脚本重新读 API 验证状态，transcript 保存证据。

## 可信资料的关键结论

- MDN 的 Fetch、DOM 和表单文档覆盖了浏览器侧最小交互链路：收集输入、发起请求、根据响应更新页面。
- Node.js 的 HTTP、File system 和 Test runner 文档覆盖了本地后端最小闭环：接收请求、读写文件、用测试验证行为。
- 这个结课项目不追求框架完整性，重点是把浏览器、API、持久化和测试证据串成一个能解释的工作系统。

## 逐步实现

完整验证：

```bash
bash run_lab.sh
```

核心输出：

```text
# tests 2
# pass 2
initial_count=2
created_id=3
invalid_title_status=400
final_total=2
smoke_status=ok
health_ok=true
```

手动启动：

```bash
node scripts/reset-data.mjs data/tasks.json
node server.mjs
```

浏览器打开：

```text
http://127.0.0.1:3000
```

你可以完成三个动作：新增任务、标记完成、删除任务。每个动作都对应一个 API 请求，并最终写入 JSON 文件。

项目结构：

```text
minimal-web-fullstack/
  public/
    index.html
    styles.css
    app.js
  scripts/
    reset-data.mjs
    smoke.mjs
  test/
    api.test.mjs
  data/
    tasks.json
  server.mjs
  package.json
  run_lab.sh
```

可展示产物：

```text
reports/transcript.txt
reports/smoke-report.json
reports/api-transcript.ndjson
reports/health.json
reports/tasks.json
```

这些文件回答了展示时最常见的追问：怎么运行，跑了哪些请求，返回了什么，测试是否通过。

## 常见错误

1. **结课项目只写页面。** 没有 API 和持久化，就还没有进入全栈边界。
2. **结课项目一开始就上复杂框架。** 先看清请求、响应和文件状态，后续迁移框架更稳。
3. **没有失败路径。** 空标题返回 400 是项目可靠性的组成部分。
4. **没有发布证据。** README、测试输出和 transcript 能证明项目可以复查。

## 练习或延伸

1. 给任务增加优先级字段，并在页面中显示。
2. 把 JSON 文件替换成 SQLite，保持 API 响应格式不变。
3. 用 Express 重写服务器，比较框架帮你省掉了哪些样板代码。
4. 把前端换成一个 Vite 项目，保留同一组 API。

## 参考资料

- MDN：[Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- MDN：[Document Object Model](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model)
- Node.js：[HTTP](https://nodejs.org/api/http.html)
- Node.js：[File system](https://nodejs.org/api/fs.html)
- Node.js：[Test runner](https://nodejs.org/api/test.html)

{% endraw %}
