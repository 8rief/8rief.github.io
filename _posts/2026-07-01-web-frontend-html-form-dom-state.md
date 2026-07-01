---
layout: post
title: "前端最小页面：HTML 表单、DOM 节点和用户动作如何变成状态变化"
date: 2026-07-01 10:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用任务面板解释表单、输入框、按钮、事件监听和 DOM 渲染的最小闭环。"
tags: [web, frontend, html, dom, teaching]
---
{% raw %}
> 主题：最小 Web 前后端项目 / HTML form / DOM / frontend state
> 本文 lab 已验证：静态首页返回 200，页面包含“任务面板”标记。

前端的第一步不需要组件框架。一个最小页面已经包含真实前端开发的基本问题：用户在哪里输入，代码如何监听动作，页面上的节点如何更新，错误信息显示在哪里。

## 学习目标

1. 知道 `<form>`、`<input>`、`<button>` 在页面里的职责。
2. 用 DOM 选择元素、监听提交事件、更新列表节点。
3. 理解前端状态来自 API 响应，而不是凭空保存在页面里。

## 先修知识

知道浏览器会请求 `/index.html`，服务器会返回 HTML、CSS 和 JS 文件。

## 核心模型

![HTML 表单到 DOM 状态](/assets/diagrams/web-frontend-form-dom-state.svg)

用户动作先发生在表单控件上，JavaScript 监听事件，把输入值转成请求。请求成功后再用响应数据渲染 DOM。这个顺序能避免页面状态和服务器状态互相打架。

## 可信资料的关键结论

- MDN 对 `<form>` 的定义是：表单代表一段用于提交信息的交互控件。
- DOM 是 Web 文档的编程接口，JavaScript 可以通过它改变结构、样式和内容。
- HTMLFormElement 让脚本可以访问表单及其控件；本包只用最基本的提交事件和输入值。

## 逐步实现

页面入口：

```html
<form id="task-form">
  <label for="task-title">任务标题</label>
  <input id="task-title" name="title" maxlength="80" required>
  <button type="submit">保存</button>
</form>
<ul id="task-list"></ul>
```

脚本先拿到 DOM 节点：

```js
const list = document.querySelector('#task-list');
const form = document.querySelector('#task-form');
const input = document.querySelector('#task-title');
const status = document.querySelector('#status');
```

监听提交事件：

```js
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const title = input.value.trim();
  if (!title) {
    setStatus('请输入任务标题。', true);
    return;
  }
  await createTask(title);
});
```

这里有两个关键点。第一，`event.preventDefault()` 阻止浏览器按传统表单方式整页跳转。第二，输入值只作为请求参数，最终列表以服务器返回的数据为准。

渲染列表时，脚本为每个任务创建一个 `<li>`，再给“完成”和“删除”按钮绑定事件。这样页面上的每个按钮都能对应一个明确的 API 调用。

## 常见错误

1. **忘记阻止默认提交。** 页面会刷新，刚写的 JavaScript 状态也会丢失。
2. **只改 DOM，不调 API。** 页面看起来变了，刷新后数据又回去了。
3. **直接拼接不可信 HTML。** 本包用 `textContent` 放标题，避免把用户输入当作 HTML 解释。
4. **没有状态提示。** 初学项目也要告诉用户加载中、成功、失败。

## 练习或延伸

1. 给任务标题旁边增加一个“active/done”计数显示。
2. 把空标题错误提示改得更具体，例如“任务标题不能为空”。
3. 给完成的任务加一个不同背景色，而不只用删除线。

## 参考资料

- MDN：[`<form>` element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/form)
- MDN：[Document Object Model](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model)
- MDN：[HTMLFormElement](https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement)

{% endraw %}
