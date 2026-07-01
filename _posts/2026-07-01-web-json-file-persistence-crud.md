---
layout: post
title: "先用 JSON 文件持久化：读写任务、生成 id 和保存状态"
date: 2026-07-01 10:28:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 fs/promises 把任务数组保存到本地文件，理解 CRUD 背后的状态边界。"
tags: [nodejs, json, persistence, crud, teaching]
---
{% raw %}
> 主题：最小 Web 前后端项目 / persistence / JSON file / CRUD
> 本文 lab 已验证：初始 2 条任务，新增 id 为 3，删除后最终总数回到 2。

最小全栈项目需要持久化，否则刷新页面或重启服务后数据就丢失。真正的产品通常会用数据库；教学第一步可以先用 JSON 文件，因为它能把状态变化看得很清楚：读数组、改数组、写回文件。

## 学习目标

1. 理解任务列表为什么不能只存在浏览器内存里。
2. 用 `fs/promises` 读写 JSON 文件。
3. 看懂 create、read、update、delete 如何改变同一个任务数组。

## 先修知识

知道 API 请求最终会到达 Node.js 服务器。

## 核心模型

![JSON 文件持久化 CRUD](/assets/diagrams/web-json-file-persistence-crud.svg)

服务器把 JSON 文件读成数组，在内存里做一次明确修改，再把完整数组写回文件。这个模型适合本地学习和单用户 demo，不适合作为高并发生产存储。

## 可信资料的关键结论

- Node.js `fs/promises` 提供基于 Promise 的异步文件系统方法，适合和 `async/await` 配合。
- JSON 是前后端交换和本地保存结构化数据的常见格式；读写时要处理解析失败。
- 对初学项目而言，文件持久化能清楚展示状态边界；数据库留到需要并发、查询和约束时再引入。

## 逐步实现

确保数据文件存在：

```js
async function ensureDataFile(dataFile) {
  await mkdir(path.dirname(dataFile), { recursive: true });
  if (!existsSync(dataFile)) {
    await writeFile(dataFile, '[]\n', 'utf8');
  }
}
```

读取任务：

```js
async function loadTasks(dataFile) {
  await ensureDataFile(dataFile);
  const text = await readFile(dataFile, 'utf8');
  const tasks = JSON.parse(text);
  return tasks;
}
```

保存任务：

```js
async function saveTasks(dataFile, tasks) {
  await mkdir(path.dirname(dataFile), { recursive: true });
  await writeFile(dataFile, `${JSON.stringify(tasks, null, 2)}\n`, 'utf8');
}
```

新增任务时，服务器先生成下一个 id：

```js
function nextId(tasks) {
  return tasks.reduce((max, task) => Math.max(max, Number(task.id) || 0), 0) + 1;
}
```

smoke 输出：

```text
initial_count=2
created_id=3
final_total=2
```

这三个值说明持久化路径真的参与了 API 流程：先读到 2 条，新增生成 id 3，删除后回到 2 条。

## 常见错误

1. **把数据只存在前端变量里。** 刷新页面后数据会丢。
2. **写文件前不创建目录。** 第一次运行时容易因为目录不存在失败。
3. **解析 JSON 失败没有错误边界。** 文件损坏时应返回明确的服务器错误。
4. **把 JSON 文件当生产数据库。** 本包只用于本地学习，后续数据库包会处理约束、事务和并发问题。

## 练习或延伸

1. 在 `tasks.json` 中手动增加一条任务，刷新页面观察列表变化。
2. 给任务增加 `createdAt` 字段，并在页面中显示。
3. 写一个脚本统计 JSON 文件里 done 和 active 的数量。

## 参考资料

- Node.js：[File system](https://nodejs.org/api/fs.html)
- Node.js：[fs/promises](https://nodejs.org/api/fs.html#promises-api)
- MDN：[JSON](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON)

{% endraw %}
