---
layout: post
title: "Möbius反演：从所有根里数出不可约多项式"
date: 2026-02-23 18:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "用 Möbius 反演解释 V_n(x)、不可约多项式个数公式，以及 F_2 上三次和六次例子。"
tags: [math, finite-field, mobius, irreducible-polynomial]
---
{% raw %}

> 主题：Möbius反演 / 不可约多项式计数 / \(V_n(x)\)

前面已经知道

\[
x^{q^n}-x=\prod_{d\mid n}V_d(x),
\]

其中 \(V_d(x)\) 是 \(\mathbb F_q[x]\) 中所有 \(d\) 次首一不可约多项式的乘积。这个式子给的是“总量”：\(x^{q^n}-x\) 会把所有次数整除 \(n\) 的不可约因子都收进来。

第七章开始要解决的问题是：如果我只想要“恰好 \(n\) 次”的不可约多项式，怎么从这个总量里扣出来？Möbius反演就是这个扣除工具。

![Möbius 反演：从总量扣出精确层](/assets/diagrams/finite-field-advanced-mobius-irreducibles.svg)

## 先看普通加法版反演

设

\[
A(n)=\sum_{d\mid n}B(d).
\]

意思是 \(A(n)\) 是所有低层 \(B(d)\) 的总和，其中 \(d\mid n\)。如果要从总量 \(A(n)\) 恢复精确层 \(B(n)\)，就用

\[
B(n)=\sum_{d\mid n}\mu(d)A(n/d).
\]

这里 \(\mu(d)\) 是 Möbius函数。

## Möbius函数怎么取值

\[
\mu(1)=1.
\]

如果 \(n\) 含有平方因子，例如 \(4\mid n\) 或 \(9\mid n\)，则

\[
\mu(n)=0.
\]

如果 \(n\) 是 \(r\) 个不同素数的乘积，则

\[
\mu(n)=(-1)^r.
\]

例如：

\[
\mu(2)=-1,
\quad
\mu(6)=1,
\quad
\mu(12)=0.
\]

它的作用就是“按包含层级加减抵消”。有平方因子的项会被完全丢掉。

## 为什么第七章需要它

对有限域，有一个总量关系：

\[
x^{q^n}-x=\prod_{d\mid n}V_d(x).
\]

如果只想提取 \(V_n(x)\)，就要把所有 \(d\mid n\) 的低层因子扣掉。乘法版Möbius反演可以形式化地写成

\[
V_n(x)=\prod_{d\mid n}\left(x^{q^d}-x\right)^{\mu(n/d)}.
\]

这里指数 \(-1\) 表示在多项式乘积分解意义下做除法。初学时不必把它当成普通高次幂，只要理解为：\(\mu\) 决定哪些总量项乘上来，哪些总量项除下去。

## 例子：\(\mathbb F_2\) 中的三次不可约多项式

当 \(q=2,n=3\) 时，次数整除 3 的层只有 1 和 3：

\[
x^8-x=V_1(x)V_3(x).
\]

其中

\[
V_1(x)=x^2-x=x(x+1).
\]

所以

\[
V_3(x)=\frac{x^8-x}{x^2-x}.
\]

在 \(\mathbb F_2[x]\) 中它分解为

\[
V_3(x)=(x^3+x+1)(x^3+x^2+1).
\]

因此 \(\mathbb F_2\) 上三次首一不可约多项式正好有两个。

用数量公式也能得到同样结果：

\[
N_q(n)=\frac{1}{n}\sum_{d\mid n}\mu(d)q^{n/d}.
\]

代入 \(q=2,n=3\)：

\[
N_2(3)=\frac{1}{3}\left(2^3-2\right)=2.
\]

## 例子：为什么六次不可约有9个

对 \(\mathbb F_2\)，六次首一不可约多项式个数是

\[
N_2(6)=\frac{1}{6}\sum_{d\mid 6}\mu(d)2^{6/d}.
\]

\(6\) 的因子是 \(1,2,3,6\)，对应

\[
\mu(1)=1,
\quad
\mu(2)=-1,
\quad
\mu(3)=-1,
\quad
\mu(6)=1.
\]

所以

\[
N_2(6)=\frac{1}{6}(64-8-4+2)=9.
\]

这也解释了为什么 \(V_6(x)\) 的次数是

\[
6\cdot9=54.
\]

## 到底应该怎么理解 \(V_n(x)\)

\(V_n(x)\) 表示所有 \(n\) 次首一不可约多项式的乘积。它把“恰好 \(n\) 次”这一层打包起来。

为什么要打包？因为单个不可约多项式可能很难直接找，但总乘积可以通过 \(x^{q^n}-x\) 和Möbius反演系统地得到。

## 常见误区

**误区一：\(x^{q^n}-x\) 只含 \(n\) 次不可约多项式。** 它包含所有次数整除 \(n\) 的不可约多项式。

**误区二：\(V_n(x)\) 是某一个多项式的名字。** 它是所有 \(n\) 次首一不可约多项式的乘积。

**误区三：Möbius函数只是数论技巧。** 在这里它的作用是层级扣除：从所有 \(d\mid n\) 的总量中恢复恰好 \(n\) 的层。

## 检查点

用公式计算 \(\mathbb F_2\) 上四次首一不可约多项式的个数：

\[
N_2(4)=\frac{1}{4}\sum_{d\mid4}\mu(d)2^{4/d}.
\]



## 为什么要引入这个概念

Möbius 反演解决的是“从所有落在扩域里的根中扣出恰好属于某个次数的不可约多项式”。它把包含关系上的重复计数变成精确计数。

## 可复现实验

把本文结论变成可检查对象，可以用一个最小 Python 检查脚本。运行方式是：

```bash
python3 finite_field_depth_checks.py
```

和本文直接相关的核心断言是：

```python
def irreducible_count(q, n):
    return sum(mu(d) * q ** (n // d) for d in divisors(n)) // n
assert irreducible_count(2, 3) == 2
assert irreducible_count(2, 4) == 3
assert irreducible_count(2, 6) == 9
```

本次实验输出摘录：

```text
irreducible_counts_F2={'N2_3': 2, 'N2_4': 3, 'N2_6': 9}
```

## 输出怎么读

`N2_3=2` 表示 `F_2[x]` 中有 2 个三次首一不可约多项式；`N2_6=9` 表示六次有 9 个。除以 `n` 是因为每个 n 次不可约多项式贡献 n 个共轭根。

## 状态变化

状态变化是：`x^{q^n}-x` 先收集所有次数整除 n 的根；Möbius 系数按除数关系加减抵消；最后剩下恰好次数为 n 的根数，再除以每个多项式的根数。

## 练习或延伸

计算 `N_3(2)` 和 `N_2(5)`，并解释每个公式项来自哪个除数。

## 参考资料

- SageMath 文档：[Finite Fields](https://doc.sagemath.org/html/en/reference/finite_rings/index.html)
- MIT OpenCourseWare：[18.703 Modern Algebra](https://ocw.mit.edu/courses/18-703-modern-algebra-spring-2013/)
- Encyclopedia of Mathematics：[Finite field](https://en.wikipedia.org/wiki/Finite_field)

{% endraw %}
