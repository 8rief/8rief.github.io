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


## 建议学习路径

当前数学基础主要围绕有限域和有限域序列展开。默认列表按发布时间倒序展示，学习时建议按下面顺序：

| 阶段 | 先读 | 目的 |
| --- | --- | --- |
| 1 | [有限域为什么只能有素数幂个元素](/mathematical-foundations/2026/06/25/finite-fields-prime-power-size.html) | 先建立特征、素域和向量空间视角 |
| 2 | [从不可约多项式构造有限域](/mathematical-foundations/2026/06/25/finite-fields-quotient-construction.html) | 知道有限域元素如何被具体表示和计算 |
| 3 | [非零乘法群、元素阶与本原元](/mathematical-foundations/2026/06/25/finite-fields-multiplicative-group.html) 与 [本原多项式](/mathematical-foundations/2026/06/25/finite-fields-primitive-polynomial.html) | 理解周期、生成元和本原性的关系 |
| 4 | [Frobenius共轭元与极小多项式](/mathematical-foundations/2026/06/25/finite-fields-frobenius-minimal-polynomial.html)、[有限域的存在性与唯一性](/mathematical-foundations/2026/06/25/finite-fields-existence-uniqueness.html)、[子域格图](/mathematical-foundations/2026/06/25/finite-fields-subfield-lattice-p12.html) | 进入结构层面的理解 |
| 5 | [迹、范数与对偶基](/mathematical-foundations/2026/06/25/finite-fields-trace-norm-dual-basis.html) | 连接扩域元素、线性代数和后续编码/密码应用 |
| 6 | [Möbius反演](/mathematical-foundations/2026/06/25/finite-fields-mobius-irreducible-counts.html)、[分圆多项式与本原多项式](/mathematical-foundations/2026/06/25/finite-fields-cyclotomic-primitive-polynomials.html)、[Berlekamp算法](/mathematical-foundations/2026/06/25/finite-fields-berlekamp-factorization.html) | 学会数不可约、多项式分解和构造工具 |
| 7 | [有限域上的线性递推](/mathematical-foundations/2026/06/25/finite-fields-linear-recurrence.html)、[m序列](/mathematical-foundations/2026/06/25/finite-fields-m-sequence.html)、[互相关特性](/mathematical-foundations/2026/06/25/finite-fields-sequence-correlation.html) | 连接到序列、周期和相关性 |

后续如果扩展数学基础，应优先补线性代数、概率统计和数论中直接服务于算法、系统或深度学习的部分，避免脱离需求的大而全理论铺陈。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "mathematical-foundations" %}
{% if posts.size == 0 %}
暂时没有文章。后续会从有限域、数论、线性代数和概率基础开始。
{% else %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}
