---
layout: post
title: "Frobenius共轭元与极小多项式"
date: 2026-06-25 14:56:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "用 Frobenius 映射解释有限域共轭元、元素的度以及极小多项式为什么落回小域。"
tags: [math, finite-field, minimal-polynomial]
---
{% raw %}

> 主题：Frobenius映射 / 共轭元 / 极小多项式

有限域里最重要的自同构是 Frobenius 映射。它把一个元素变成它的 \(q\) 次幂：

\[
\varphi(a)=a^q.
\]

如果我们研究扩域 \(\mathbb F_{q^n}/\mathbb F_q\)，这个映射会固定小域 \(\mathbb F_q\)，并在大域里把同一个元素的“共轭元”串起来。

![Frobenius 共轭元与极小多项式](/assets/diagrams/finite-field-frobenius-minimal-polynomial.svg)

## 为什么定义成 \(a\mapsto a^q\)

对小域元素 \(c\in\mathbb F_q\)，总有

\[
c^q=c.
\]

因此 Frobenius 映射对 \(\mathbb F_q\) 中的元素不起作用。它固定小域，只移动扩域中真正新增的元素。

同时，Frobenius 保持加法和乘法：

\[
(a+b)^q=a^q+b^q,
\qquad
(ab)^q=a^qb^q.
\]

所以它是有限域上的结构保持映射。

## 共轭元是什么

设 \(\alpha\in\mathbb F_{q^n}\)。从 \(\alpha\) 开始反复做 Frobenius：

\[
\alpha,
\alpha^q,
\alpha^{q^2},
\alpha^{q^3},\ldots
\]

由于域是有限的，这个序列最终会回到 \(\alpha\)。第一次回到 \(\alpha\) 前出现的不同元素，就是 \(\alpha\) 在 \(\mathbb F_q\) 上的 Frobenius 共轭元。

这些共轭元从小域 \(\mathbb F_q\) 的角度看“不可区分”：它们满足同一个 \(\mathbb F_q\) 系数不可约多项式。

## 元素的度

\(\alpha\) 的度可以理解为三件等价的事：

1. Frobenius 轨道中不同共轭元的个数；
2. \(\alpha\) 在 \(\mathbb F_q\) 上的极小多项式次数；
3. 扩张 \(\mathbb F_q(\alpha)/\mathbb F_q\) 的维数。

如果 \(\alpha\) 的共轭元有 \(d\) 个，那么它的极小多项式就是 \(d\) 次的。

## 极小多项式怎么写

设 \(\alpha\) 的共轭元是

\[
\alpha,
\alpha^q,
\ldots,
\alpha^{q^{d-1}}.
\]

那么 \(\alpha\) 的极小多项式是

\[
m_\alpha(x)=\prod_{i=0}^{d-1}\left(x-\alpha^{q^i}\right).
\]

关键问题是：这个乘积里明明有扩域元素，为什么最后系数会落回 \(\mathbb F_q\)？

原因是 Frobenius 只是在循环置换这些根。整个乘积作为一个集合不变，所以乘积的系数被 Frobenius 固定。有限域里被 \(a\mapsto a^q\) 固定的元素正是 \(\mathbb F_q\) 中的元素，因此系数落回小域。

## 例子：\(\mathbb F_4/\mathbb F_2\)

构造

\[
\mathbb F_4=\mathbb F_2[\omega]/(\omega^2+\omega+1).
\]

由

\[
\omega^2+\omega+1=0
\]

可得

\[
\omega^2=\omega+1.
\]

在 \(\mathbb F_4/\mathbb F_2\) 中，Frobenius 映射是平方：

\[
a\mapsto a^2.
\]

于是

\[
\omega\mapsto\omega^2=\omega+1,
\]

再平方：

\[
(\omega+1)^2=\omega^2+1=(\omega+1)+1=\omega.
\]

所以 \(\omega\) 的共轭元是

\[
\omega,
\omega^2.
\]

极小多项式是

\[
(x-\omega)(x-\omega^2)=x^2+x+1.
\]

在特征 2 中，减号和加号一样。

## 例子：\(\mathbb F_8\) 中的展开

在

\[
\mathbb F_8=\mathbb F_2[\alpha]/(\alpha^3+\alpha+1)
\]

中，有

\[
\alpha^3=\alpha+1.
\]

\(\alpha\) 的 Frobenius 共轭元是

\[
\alpha,
\alpha^2,
\alpha^4.
\]

因为

\[
\alpha^4=\alpha\alpha^3=\alpha(\alpha+1)=\alpha^2+\alpha.
\]

极小多项式应为

\[
(x+\alpha)(x+\alpha^2)(x+\alpha^4).
\]

展开时，\(x^2\) 项系数是

\[
\alpha+\alpha^2+\alpha^4
=\alpha+\alpha^2+(\alpha^2+\alpha)=0.
\]

\(x\) 项系数是

\[
\alpha\alpha^2+\alpha\alpha^4+\alpha^2\alpha^4
=\alpha^3+\alpha^5+\alpha^6=1.
\]

常数项是

\[
\alpha\alpha^2\alpha^4=\alpha^7=1.
\]

所以

\[
(x+\alpha)(x+\alpha^2)(x+\alpha^4)=x^3+x+1.
\]

这回答了一个常见疑问：展开过程中会出现 \(\alpha\)，但最后它们会相互抵消，系数回到 \(\mathbb F_2\)。

## 极小多项式有什么用

第一，它给出元素满足的最短代数关系。例如 \(\alpha^3+\alpha+1=0\) 让我们能把 \(\alpha^3\) 降为 \(\alpha+1\)。

第二，它告诉我们 \(\alpha\) 生成了多大的子域。如果极小多项式次数是 \(d\)，那么

\[
\mathbb F_q(\alpha)\cong\mathbb F_{q^d}.
\]

第三，它用于分解多项式。一个不可约多项式的根会连同它的 Frobenius 共轭元一起出现。

第四，迹和范数可以从极小多项式系数中读出来。

## 常见误区

**误区一：共轭元是复数共轭。** 不是。有限域里的共轭由 Frobenius 映射给出。

**误区二：极小多项式只和构造多项式有关。** 如果元素就是构造时的 \(x\bmod f(x)\)，极小多项式就是 \(f(x)\)。但同一个域里其他元素可能有不同极小多项式。

**误区三：展开时出现 \(\alpha\)，所以结果不在小域。** 整个共轭根乘积被 Frobenius 固定，最终系数会落回小域。

## 检查点

在 \(\mathbb F_4\) 中，试着直接展开

\[
(x+\omega)(x+\omega^2)
\]

并验证结果是 \(x^2+x+1\)。

{% endraw %}
