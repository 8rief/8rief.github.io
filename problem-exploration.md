---
layout: page
title: 问题探究
permalink: /problem-exploration/
---

这个栏目记录研究问题、源码阅读、负结果、实验现象和边界推理。它把猜想、模型值、实测结果和待验证路线分开写，保证每个结论都能追溯到对应证据。

## 写作结构

每篇问题探究文章默认包含：

1. **问题**：要解释或否定的具体问题是什么。
2. **关键难点**：常见直觉、简化模型或错误路径卡在哪里。
3. **分析路径**：源码、公式、实验、反例或成本模型如何支持推理。
4. **证据边界**：哪些是已验证事实，哪些只是合理推断或待测假设。
5. **结论与下一步**：当前能下什么结论，下一步需要什么实验或 baseline。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "problem-exploration" %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}{% if post.categories %} · {{ post.categories | join: ", " }}{% endif %}
{% endfor %}
