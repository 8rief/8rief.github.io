---
layout: page
title: 项目展示
permalink: /project-showcase/
---

这个栏目只放已经有具体输入、输出、报告或静态展示页的项目。文章从真实痛点开始，讲清为什么值得做、为什么这样设计、用了什么技术，以及如何复现。

## 写作结构

每篇项目展示文章默认包含：

1. **痛点**：真实失败场景或使用场景是什么，为什么 checklist 或口头约定不够。
2. **设计目标**：输入、输出、边界、非目标，以及为什么不做成更大的平台。
3. **详细设计**：数据结构、规则、流水线、模块拆分和关键取舍。
4. **技术实现**：CLI、文件格式、报告渲染、测试、静态页、hygiene 或其他用到的技术。
5. **复现方式**：最小命令、样例输入、预期输出。
6. **边界**：工具覆盖哪些判断，哪些判断必须交给人工或外部审查。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "project-showcase" %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}{% if post.categories %} · {{ post.categories | join: ", " }}{% endif %}
{% endfor %}
