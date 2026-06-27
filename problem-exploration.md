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


## 阅读分组

问题探究栏目不按入门路线组织，而按问题线索阅读：

| 分组 | 文章方向 | 阅读目的 |
| --- | --- | --- |
| Secure query / baseline 边界 | Waldo baseline、Secure Selective-Scan、DPF/PIR 更新成本 | 区分源码事实、成本模型和不能提前下的性能结论 |
| PCG / selector 负结果 | 三阶 selector、Trace-F2、outer product triples | 记录构造直觉为什么不足，以及还需要什么证明或实验 |
| 时间与参与元数据泄漏 | participation metadata、TimeLeaks、timing shaper | 理解内容保护之外的时间、参与集合和事件侧信道 |
| 证明边界 | Proof Boundaries before Crypto Claims | 把证明对象、泄漏边界和 claim 检查表先固定下来 |

这些文章的栏目归属合理。早期问题探究文章已经围绕具体问题展开，但小标题没有完全统一为“问题、关键难点、分析路径、证据边界、结论与下一步”。如果未来要做公开精选集，可优先统一这些标题。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "problem-exploration" %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}{% if post.categories %} · {{ post.categories | join: ", " }}{% endif %}
{% endfor %}
