---
layout: post
title: "全栈本地验证：Node test、smoke 脚本和 transcript 证明什么"
date: 2026-07-01 10:42:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用内置测试和端到端 smoke 证明页面、API、持久化和错误路径真的连通。"
tags: [web, testing, smoke-test, nodejs, teaching]
---
{% raw %}
> 主题：最小 Web 前后端项目 / Node test / smoke / transcript
> 本文 lab 已验证：Node 内置测试 2/2 通过，端到端 smoke 返回 `smoke_status=ok`。

能打开页面只是一种很弱的证据。全栈项目至少要证明四件事：静态页面能返回，API 能成功读写，失败路径有状态码，数据能持久化。测试和 transcript 的价值就在这里：把“看起来能用”变成“有步骤可复查”。

## 学习目标

1. 理解单元/接口测试和端到端 smoke 的区别。
2. 用 Node 内置 test runner 跑 API 测试。
3. 保存 transcript，记录命令、环境和关键输出。

## 先修知识

知道本项目有页面、API 和 JSON 数据文件。

## 核心模型

![全栈验证证据链](/assets/diagrams/web-fullstack-test-smoke-transcript.svg)

测试负责断言行为，smoke 负责跑通真实请求链路，transcript 负责让过程可复查。三者合起来，才能支持“这个最小项目已经能展示”。

## 可信资料的关键结论

- Node.js 内置 test runner 可以直接运行测试，不需要安装第三方测试框架。
- Node.js Learn 文档强调 test runner 会执行测试并反馈通过或失败。
- 对本地教学项目，最小测试应覆盖成功路径、失败路径和静态页面入口。

## 逐步实现

运行测试：

```bash
npm test
```

预期输出包含：

```text
# tests 2
# pass 2
# fail 0
```

测试会启动临时服务器，访问真实 API：

```js
result = await json(base, '/api/tasks', {
  method: 'POST',
  body: JSON.stringify({ title: '  write a smoke test  ' })
});
assert.equal(result.response.status, 201);
assert.equal(result.body.task.title, 'write a smoke test');
```

运行 smoke：

```bash
npm run smoke -- .lab_tmp/data/tasks.json reports
```

它会访问：

```text
GET /api/health
GET /
GET /api/tasks
POST /api/tasks
PATCH /api/tasks/3
POST /api/tasks
DELETE /api/tasks/3
GET /api/tasks
```

最终报告：

```json
{
  "initial_count": 2,
  "created_id": 3,
  "invalid_title_status": 400,
  "final_summary": {
    "total": 2,
    "done": 1,
    "active": 1
  },
  "smoke_status": "ok"
}
```

完整命令记录保存在：

```text
reports/transcript.txt
```

## 常见错误

1. **只手动点页面。** 手动点击没有固定输入，难以复查。
2. **只测试成功路径。** 空标题、找不到任务、未知路由也需要验证。
3. **测试依赖固定端口。** smoke 使用临时端口，减少端口冲突。
4. **不保存 transcript。** 后续文章或项目展示缺少证据来源。

## 练习或延伸

1. 给 `DELETE /api/tasks/:id` 的 404 情况补一个测试。
2. 故意改坏 `invalid_title`，观察测试或 smoke 如何失败。
3. 把 smoke 报告扩展成 Markdown 表格。

## 参考资料

- Node.js：[Test runner](https://nodejs.org/api/test.html)
- Node.js Learn：[Using Node.js's test runner](https://nodejs.org/learn/test-runner/using-test-runner)
- Node.js Learn：[Discovering Node.js's test runner](https://nodejs.org/learn/test-runner/introduction)

{% endraw %}
