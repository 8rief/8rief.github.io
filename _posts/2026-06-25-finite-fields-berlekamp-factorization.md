---
layout: post
title: "Berlekamp算法：把有限域多项式分解变成线性代数"
date: 2026-06-25 16:08:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "从 h^q≡h mod f 的固定空间解释 Berlekamp矩阵、因子个数和 gcd 切分流程。"
tags: [math, finite-field, berlekamp, factorization]
---
{% raw %}

> 主题：Berlekamp算法 / 多项式分解 / 线性代数

知道不可约多项式一定存在以后，下一个实际问题是：给定一个有限域上的多项式，怎样把它分解成不可约因子？Berlekamp算法的关键思想是把多项式分解问题变成线性代数问题。

![Berlekamp 算法：分解变成线性代数](/assets/diagrams/finite-field-advanced-berlekamp.svg)

## 算法要解决什么

给定

\[
f(x)\in\mathbb F_q[x],
\]

希望分解为

\[
f(x)=f_1(x)f_2(x)\cdots f_r(x),
\]

其中每个 \(f_i(x)\) 都不可约。初学时先假设 \(f\) 没有重因子，即 \(\gcd(f,f')=1\)。重因子可以先单独处理。

## 固定空间 \(R_f\)

在商环

\[
\mathbb F_q[x]/(f)
\]

中定义

\[
R_f=\{h(x):h(x)^q\equiv h(x)\pmod f\}.
\]

这个条件的意思是：\(h\) 在 Frobenius 映射下固定。

为什么这个空间有用？如果

\[
f=f_1f_2\cdots f_r
\]

且各因子互素，那么中国剩余定理把商环分成 \(r\) 个分量。条件 \(h^q=h\) 会让每个分量落在底域 \(\mathbb F_q\) 中，因此 \(h\) 本质上对应一个 \(r\) 元组：

\[
(a_1,a_2,
\ldots,a_r),
\qquad a_i\in\mathbb F_q.
\]

所以

\[
\dim_{\mathbb F_q}R_f=r.
\]

也就是说，固定空间维数等于不可约因子个数。

## Berlekamp矩阵怎么来

设 \(\deg f=n\)。商环里每个元素都能写成

\[
h(x)=h_0+h_1x+\cdots+h_{n-1}x^{n-1}.
\]

计算

\[
1^q,
\quad x^q,
\quad x^{2q},
\ldots,
\quad x^{(n-1)q}
\]

分别模 \(f(x)\) 的余式，并把它们写成 \(1,x,
\ldots,x^{n-1}\) 的坐标。这些坐标组成矩阵 \(Q\)。

条件

\[
h^q\equiv h\pmod f
\]

就变成

\[
Qh=h,
\]

也就是

\[
(Q-I)h=0.
\]

所以求 \(R_f\) 就是求 \(Q-I\) 的零空间。

## 小例子完整走一遍

在 \(\mathbb F_2[x]\) 中分解

\[
f(x)=x^3+x^2+x.
\]

理论上它等于

\[
x(x^2+x+1),
\]

其中 \(x^2+x+1\) 在 \(\mathbb F_2[x]\) 中不可约。下面用 Berlekamp 的流程算出来。

商环中任意元素写成

\[
h(x)=h_0+h_1x+h_2x^2.
\]

要解

\[
h(x)^2\equiv h(x)\pmod f.
\]

先算基元素的平方：

\[
1^2=1,
\quad x^2=x^2.
\]

还需要

\[
(x^2)^2=x^4.
\]

由

\[
x^3+x^2+x\equiv0
\]

可得

\[
x^3=x^2+x.
\]

因此

\[
x^4=x\cdot x^3=x^3+x^2=(x^2+x)+x^2=x.
\]

所以

\[
h(x)^2=h_0+h_1x^2+h_2x^4
\equiv h_0+h_2x+h_1x^2.
\]

和

\[
h(x)=h_0+h_1x+h_2x^2
\]

比较系数，得到唯一约束

\[
h_1=h_2.
\]

于是

\[
h(x)=h_0+h_1x+h_1x^2.
\]

有两个自由变量，所以

\[
\dim R_f=2.
\]

这说明 \(f(x)\) 有两个不可约因子。

## 用 \(h\) 切出因子

取非平凡元素

\[
h(x)=x+x^2.
\]

在 \(\mathbb F_2\) 中，只需看

\[
\gcd(f,h)
\quad\text{和}\quad
\gcd(f,h+1).
\]

先算

\[
\gcd(x^3+x^2+x,
 x^2+x)=x.
\]

于是切出因子 \(x\)。剩余因子是

\[
\frac{x^3+x^2+x}{x}=x^2+x+1.
\]

最终得到

\[
\boxed{x^3+x^2+x=x(x^2+x+1).}
\]

## 维数为1说明什么

若 \(f\) 无重因子，且

\[
\dim R_f=1,
\]

则 \(f\) 只有一个不可约因子，所以 \(f\) 本身不可约。

这个判断依赖无重因子条件。如果 \(f\) 有重因子，需要先用 \(\gcd(f,f')\) 处理。

## 常见误区

**误区一：Berlekamp矩阵是在猜因子。** Berlekamp矩阵的目标是求 Frobenius 固定空间；真正的因子还要用固定空间元素通过 gcd 切出来。

**误区二：零空间里的每个向量都是一个因子。** 零空间向量对应辅助多项式 \(h\)，真正的因子要通过 \(\gcd(f,h-a)\) 切出来。

**误区三：维数等于次数。** 维数等于不同不可约因子个数，不等于 \(\deg f\)。

## 检查点

对上面的例子，为什么 \(h(x)=1\) 虽然在 \(R_f\) 中，却不能切出非平凡因子？

{% endraw %}
