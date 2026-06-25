---
layout: post
title: "迹、范数与对偶基：把扩域元素压回小域"
date: 2026-06-25 15:08:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "解释迹和范数为什么落回底域，并用 GF(16) 推导任意元素的迹坐标公式。"
tags: [math, finite-field, trace, linear-algebra]
---
{% raw %}

> 主题：迹 / 范数 / 对偶基 / 坐标提取

有限域扩张 \(K=\mathbb F_{q^n}\) 相对于小域 \(F=\mathbb F_q\) 时，迹和范数把大域元素变回小域元素。它们是有限域线性代数和乘法结构的基本工具，而不是某个单一应用的专用技巧。

![迹、范数与对偶基](/assets/diagrams/finite-field-trace-dual-basis.svg)

## 迹的定义

对 \(a\in\mathbb F_{q^n}\)，它相对于 \(\mathbb F_q\) 的迹定义为

\[
\operatorname{Tr}_{\mathbb F_q}^{\mathbb F_{q^n}}(a)
=a+a^q+a^{q^2}+\cdots+a^{q^{n-1}}.
\]

这是 Frobenius 共轭元之和。

迹一定落回 \(\mathbb F_q\)，因为对它再做一次 Frobenius，只是循环移动求和项：

\[
\operatorname{Tr}(a)^q=\operatorname{Tr}(a).
\]

被 \(x\mapsto x^q\) 固定的元素正是 \(\mathbb F_q\) 中的元素。

## 范数的定义

范数是共轭元之积：

\[
N_{\mathbb F_q}^{\mathbb F_{q^n}}(a)
=a\cdot a^q\cdot a^{q^2}\cdots a^{q^{n-1}}.
\]

它也落回 \(\mathbb F_q\)。迹是加法型的，范数是乘法型的：

\[
\operatorname{Tr}(a+b)=\operatorname{Tr}(a)+\operatorname{Tr}(b),
\]

\[
N(ab)=N(a)N(b).
\]

## 和极小多项式的关系

如果 \(a\) 的极小多项式是

\[
m_a(x)=x^d+c_1x^{d-1}+\cdots+c_d,
\]

而它的共轭元是 \(a,a^q,\ldots,a^{q^{d-1}}\)，那么最高次项下一项系数和常数项与迹、范数有关。

在一般符号下会有符号；在特征 2 中减号等于加号，因此经常可以直接读出。

## \(\mathbb F_{16}\) 中的迹例子

设

\[
K=\mathbb F_{16}=\mathbb F_2[x]/(x^4+x^3+x^2+x+1).
\]

令

\[
\alpha=x\bmod(x^4+x^3+x^2+x+1).
\]

于是

\[
\alpha^4+\alpha^3+\alpha^2+\alpha+1=0.
\]

任意元素 \(\beta\in\mathbb F_{16}\) 都可以唯一写成

\[
\beta=\beta_0+\beta_1\alpha+\beta_2\alpha^2+\beta_3\alpha^3,
\qquad \beta_i\in\mathbb F_2.
\]

目标是求

\[
\operatorname{Tr}_{\mathbb F_2}^{\mathbb F_{16}}(\beta).
\]

因为这里 \(q=2\)、\(n=4\)，所以

\[
\operatorname{Tr}(a)=a+a^2+a^4+a^8.
\]

## 先求基元素的迹

首先，

\[
\operatorname{Tr}(1)=1+1+1+1=0
\]

因为在 \(\mathbb F_2\) 中四个 1 相加为 0。

接着求 \(\operatorname{Tr}(\alpha)\)。\(\alpha\) 的极小多项式就是构造多项式

\[
x^4+x^3+x^2+x+1.
\]

它的 Frobenius 共轭元是

\[
\alpha,
\alpha^2,
\alpha^4,
\alpha^8.
\]

这些共轭元之和就是 \(\operatorname{Tr}(\alpha)\)。由极小多项式的 \(x^3\) 项系数可知

\[
\operatorname{Tr}(\alpha)=1.
\]

由于迹在 Frobenius 下不变，

\[
\operatorname{Tr}(\alpha^2)=\operatorname{Tr}(\alpha)=1.
\]

又因为

\[
x^5-1=(x-1)(x^4+x^3+x^2+x+1),
\]

所以 \(\alpha^5=1\)。于是

\[
\alpha^8=\alpha^3.
\]

这说明 \(\alpha^3\) 也在同一个 Frobenius 共轭类里，因此

\[
\operatorname{Tr}(\alpha^3)=1.
\]

综上：

\[
\operatorname{Tr}(1)=0,
\quad
\operatorname{Tr}(\alpha)=1,
\quad
\operatorname{Tr}(\alpha^2)=1,
\quad
\operatorname{Tr}(\alpha^3)=1.
\]

## 任意元素的迹公式

由迹的 \(\mathbb F_2\)-线性性：

\[
\operatorname{Tr}(\beta)
=\beta_0\operatorname{Tr}(1)
+\beta_1\operatorname{Tr}(\alpha)
+\beta_2\operatorname{Tr}(\alpha^2)
+\beta_3\operatorname{Tr}(\alpha^3).
\]

代入刚才结果：

\[
\operatorname{Tr}(\beta)=\beta_1+\beta_2+\beta_3.
\]

所以这个例子最终得到一个坐标公式：

\[
\boxed{\operatorname{Tr}_{\mathbb F_2}^{\mathbb F_{16}}(\beta)=\beta_1+\beta_2+\beta_3.}
\]

这里的加法是在 \(\mathbb F_2\) 中，也就是异或。

## \(\alpha\) 和 \(\beta\) 的关系

\(\alpha\) 是构造 \(\mathbb F_{16}\) 时引入的基元素。它满足构造多项式给出的关系。

\(\beta\) 是任意元素。它可以等于 \(0\)、\(1\)、\(\alpha\)，也可以等于 \(\alpha^3+\alpha^2+1\)。写成

\[
\beta=\beta_0+\beta_1\alpha+\beta_2\alpha^2+\beta_3\alpha^3
\]

只是为了统一表示所有元素。

例如

\[
\beta=\alpha^2+\alpha+1
\]

时，坐标是 \((1,1,1,0)\)，所以

\[
\operatorname{Tr}(\beta)=1+1+0=0.
\]

## 对偶基为什么出现

设 \(K/F\) 是 \(n\) 维扩张，取一组基

\[
b_1,b_2,\ldots,b_n.
\]

如果另一组元素

\[
c_1,c_2,\ldots,c_n
\]

满足

\[
\operatorname{Tr}(b_i c_j)=\delta_{ij},
\]

那么 \(c_1,
\ldots,c_n\) 叫做 \(b_1,
\ldots,b_n\) 的对偶基。

对偶基的作用是提取坐标。若

\[
x=x_1b_1+x_2b_2+\cdots+x_nb_n,
\]

那么

\[
\operatorname{Tr}(x c_j)=x_j.
\]

因为展开后

\[
\operatorname{Tr}(x c_j)
=\sum_i x_i\operatorname{Tr}(b_i c_j)
=\sum_i x_i\delta_{ij}=x_j.
\]

这把“取第 \(j\) 个坐标”变成了一个迹计算。

## 这个工具有什么用

迹把扩域元素压回小域，并且保持线性；范数把乘法结构压回小域；对偶基用迹提取坐标。它们可以用于有限域乘法实现、编码理论、序列分析、有限域上的线性代数和各种需要从扩域回到底域的计算。

## 常见误区

**误区一：迹是普通矩阵迹。** 有联系但不是同一个定义。有限域迹是 Frobenius 共轭元之和，也等于乘法线性变换的迹。

**误区二：\(\beta\) 是另一个生成元。** 在这个例子里，\(\beta\) 只是任意元素的名字。

**误区三：迹公式不依赖基。** 坐标公式依赖构造多项式和所选基。换一个构造多项式或换基，坐标表达式会变。

## 检查点

若

\[
\beta=\alpha^3+\alpha^2+\alpha,
\]

根据公式 \(\operatorname{Tr}(\beta)=\beta_1+\beta_2+\beta_3\)，它的迹是多少？

{% endraw %}
