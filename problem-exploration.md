---
layout: page
title: 问题探究
permalink: /problem-exploration/
---

这里学习怎样判断一个答案是否被证据支持。文章会把源码事实、公式、实测结果、合理推断和待验证假设分开。

## 阅读方法

1. 先复述待判断的问题，确认性能、安全性或正确性指的是什么量。
2. 标出每条证据的来源：源码、论文定义、实验、成本模型或反例。
3. 检查输入规模、威胁模型、baseline 和测量口径是否一致。
4. 找一个能推翻当前结论的反例或新实验。
5. 最后再写结论，并明确它不能外推到哪里。

## 按问题线索阅读

| 问题线索 | 文章方向 | 学习结果 |
| --- | --- | --- |
| Secure query 与 baseline | Waldo baseline、Secure Selective-Scan、DPF/PIR 更新成本 | 区分源码事实、成本模型与尚未完成的性能比较 |
| PCG 与 selector 负结果 | 三阶 selector、Trace-F2、outer product triples | 理解一个构造直觉为什么可能不足，以及证明或实验还缺什么 |
| 时间与参与元数据泄漏 | participation metadata、TimeLeaks、timing shaper | 建立内容之外的时间、参与集合和事件侧信道模型 |
| 密码学主张的证明边界 | Proof Boundaries before Crypto Claims | 在讨论方案前先固定证明对象、泄漏函数和攻击者能力 |

这部分更适合已经学过基础算法、概率和系统模型的读者。相关先修可从[数学基础](/mathematical-foundations/)和[计算机技术教学](/computer-science-teaching/)补齐。

## 当前探究地图

这组文章的价值在于展示怎样把一个技术判断拆成证据、反例和边界。

| 问题 | 代表文章 | 当前结论类型 |
| --- | --- | --- |
| 短查询 key 是否意味着低成本更新 | [DPF/PIR 笔记](/secure-query/2026/07/11/dpf-pir-short-key-does-not-imply-easy-update.html) | 源码/协议接口边界提醒 |
| selector/PCG 直觉为什么不够 | [三阶 selector](/secure-query/2026/07/11/mult3-continuation-wire.html)、[outer product triples](/secure-query/2026/07/12/pcg-outer-product-is-not-independent-triples.html)、[Trace-F2 PCG](/secure-query/2026/07/12/trace-f2-rho-he-is-not-qa-sd.html) | 负结果和证明缺口 |
| baseline 的协议边界怎样确定 | [Waldo 源码笔记](/secure-query/2026/07/13/waldo-baseline-source-reading.html)、[Secure Selective-Scan Bench](/research-notes/2026/07/13/secure-selective-scan-negative-result.html) | 成本模型和暂不声称性能优势 |
| 时间和参与元数据会泄漏什么 | [参与者集合也是数据](/research-notes/2026/07/14/participation-metadata-leakage.html)、[TimeLeaks Lab](/research-notes/2026/07/14/timeleaks-temporal-metadata.html)、[timing shaper frontier](/research-notes/2026/07/15/timing-shaper-frontier.html) | 侧信道模型和仍需验证的防护边界 |
| 证明边界应该先写什么 | [Proof Boundaries before Crypto Claims](/research-notes/2026/07/15/proof-boundaries-before-crypto-claims.html) | 证明对象、泄漏函数和攻击者能力清单 |

## 全部问题探究

{% assign posts = site.posts | where: "column", "problem-exploration" %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}{% if post.categories %} · {{ post.categories | join: ", " }}{% endif %}
{% endfor %}
