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

本栏目现在分成两条可直接学习的路线：一条服务于 AI、算法和数据工程中的基础数学，一条服务于有限域、序列和计算代数。默认文章列表仍按发布时间倒序展示；学习时建议按下面顺序读。

### 路线 A：AI、算法和数据工程数学基础

| 阶段 | 先读 | 目的 |
| --- | --- | --- |
| 1 | [向量和矩阵第一课：dot、norm 和 projection](/mathematical-foundations/2026/07/01/math-ai-vector-matrix-dot-norm.html) | 建立样本、参数、方向、长度和线性变换的共同语言 |
| 2 | [线性方程和最小二乘：从无解系统到可解释拟合](/mathematical-foundations/2026/07/01/math-ai-linear-system-least-squares.html) | 理解现实数据无法精确满足方程时如何定义最佳近似 |
| 3 | [特征值、协方差和 PCA：找出数据变化最大的方向](/mathematical-foundations/2026/07/01/math-ai-eigen-covariance-pca.html) | 把协方差、特征向量和降维连接起来 |
| 4 | [概率、期望和方差：把随机实验变成可比较数字](/mathematical-foundations/2026/07/01/math-ai-probability-expectation-variance.html) | 区分单次随机结果、长期均值和波动规模 |
| 5 | [Bayes 公式和混淆矩阵：阳性结果为什么还要看先验](/mathematical-foundations/2026/07/01/math-ai-bayes-confusion-metrics.html) | 学会把先验、检测质量和评估指标放在同一张表里解释 |
| 6 | [导数和梯度：用 finite difference 检查方向](/mathematical-foundations/2026/07/01/math-ai-gradient-finite-difference.html) | 用数值检查建立对梯度方向的可信理解 |
| 7 | [链式法则到反向传播：一层 tanh 网络怎么传回梯度](/mathematical-foundations/2026/07/01/math-ai-chain-rule-backprop.html) | 从计算图角度理解反向传播 |
| 8 | [梯度下降和学习率：为什么一步一步能靠近最优点](/mathematical-foundations/2026/07/01/math-ai-gradient-descent-learning-rate.html) | 理解优化循环、学习率和 loss 曲线 |
| 9 | [数值稳定性：softmax 为什么要减最大值](/mathematical-foundations/2026/07/01/math-ai-numerical-stability-softmax-logsumexp.html) | 学会用等价变换避免浮点溢出 |
| 10 | [结课项目：用数学基础做一个可验证 logistic baseline](/mathematical-foundations/2026/07/01/math-ai-capstone-logistic-baseline.html) | 把向量、概率、梯度、优化和评估合成一个可验证 baseline |

### 路线 B：有限域、有限域序列和计算代数

| 阶段 | 先读 | 目的 |
| --- | --- | --- |
| 1 | [有限域为什么只能有素数幂个元素](/mathematical-foundations/2026/06/25/finite-fields-prime-power-size.html) | 先建立特征、素域和向量空间视角 |
| 2 | [从不可约多项式构造有限域](/mathematical-foundations/2026/06/25/finite-fields-quotient-construction.html) | 知道有限域元素如何被具体表示和计算 |
| 3 | [非零乘法群、元素阶与本原元](/mathematical-foundations/2026/06/25/finite-fields-multiplicative-group.html) 与 [本原多项式](/mathematical-foundations/2026/06/25/finite-fields-primitive-polynomial.html) | 理解周期、生成元和本原性的关系 |
| 4 | [Frobenius共轭元与极小多项式](/mathematical-foundations/2026/06/25/finite-fields-frobenius-minimal-polynomial.html)、[有限域的存在性与唯一性](/mathematical-foundations/2026/06/25/finite-fields-existence-uniqueness.html)、[子域格图](/mathematical-foundations/2026/06/25/finite-fields-subfield-lattice-p12.html) | 进入结构层面的理解 |
| 5 | [迹、范数与对偶基](/mathematical-foundations/2026/06/25/finite-fields-trace-norm-dual-basis.html) | 连接扩域元素、线性代数和后续编码/密码应用 |
| 6 | [Möbius反演](/mathematical-foundations/2026/06/25/finite-fields-mobius-irreducible-counts.html)、[分圆多项式与本原多项式](/mathematical-foundations/2026/06/25/finite-fields-cyclotomic-primitive-polynomials.html)、[Berlekamp算法](/mathematical-foundations/2026/06/25/finite-fields-berlekamp-factorization.html) | 学会数不可约、多项式分解和构造工具 |
| 7 | [有限域上的线性递推](/mathematical-foundations/2026/06/25/finite-fields-linear-recurrence.html)、[m序列](/mathematical-foundations/2026/06/25/finite-fields-m-sequence.html)、[互相关特性](/mathematical-foundations/2026/06/25/finite-fields-sequence-correlation.html) | 连接到序列、周期和相关性 |

## 已归入本栏目

{% assign posts = site.posts | where: "column", "mathematical-foundations" %}
{% if posts.size == 0 %}
暂时没有文章。后续会从有限域、数论、线性代数和概率基础开始。
{% else %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}
