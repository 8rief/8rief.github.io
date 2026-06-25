---
layout: page
title: 数学基础
permalink: /mathematical-foundations/
---

这个栏目整理计算机科学、工程实现和理论学习中反复出现的数学基础。它不只服务于密码学，也服务于编码理论、通信、随机序列、算法分析、计算代数、概率模型、线性代数和后续系统性学习。

## 写作结构

每篇文章默认回答：

1. **问题从哪里来**：为什么需要这个概念。
2. **正式定义**：给出可复用的数学表述。
3. **直观模型**：把符号翻译成可理解的结构。
4. **怎么算**：用小例子完整走一遍。
5. **有什么用**：说明它连接到哪些后续主题。
6. **常见误区**：指出容易混淆的边界。
7. **检查点**：给读者留一个可以自测的小问题。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "mathematical-foundations" %}
{% if posts.size == 0 %}
暂时没有文章。后续会从有限域、数论、线性代数和概率基础开始。
{% else %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}
