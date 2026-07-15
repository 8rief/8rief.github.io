---
layout: post
title: "从不可约多项式构造有限域"
date: 2026-02-20 09:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "解释为什么模掉不可约多项式能把多项式环变成有限域，并用 GF(8) 演示乘法降次。"
tags: [math, finite-field, polynomial]
---
{% raw %}

> 主题：有限域构造 / 多项式商环 / 不可约多项式

上一篇说明有限域大小只能是 \(p^m\)。这篇回答反方向的具体构造问题：给定素数 \(p\) 和正整数 \(m\)，怎样真的造出一个有 \(p^m\) 个元素的域？

最常用的方法是选一个 \(\mathbb F_p[x]\) 中的 \(m\) 次不可约多项式 \(f(x)\)，然后构造商环

\[
\mathbb F_p[x]/(f(x)).
\]

![用不可约多项式构造有限域](/assets/diagrams/finite-field-quotient-construction.svg)

## 为什么从多项式开始

\(\mathbb F_p[x]\) 是系数在 \(\mathbb F_p\) 中的一元多项式环。它可以加、减、乘，也没有零因子，但它不是域。例如 \(x\) 没有多项式逆元，因为不存在多项式 \(g(x)\) 让

\[
xg(x)=1.
\]

如果想得到更大的有限域，就要把多项式“按某个规则降次”。这个规则由不可约多项式 \(f(x)\) 提供。

## 商环里的元素长什么样

设 \(f(x)\) 是 \(m\) 次多项式。模掉 \(f(x)\) 后，每个多项式都可以除以 \(f(x)\)，只保留次数小于 \(m\) 的余式。因此商环中的元素可以唯一写成

\[
a_0+a_1\alpha+a_2\alpha^2+\cdots+a_{m-1}\alpha^{m-1},
\qquad a_i\in\mathbb F_p,
\]

其中

\[
\alpha=x\bmod f(x).
\]

这里的 \(\alpha\) 不是实数，也不是复数。它是商环里 \(x\) 的剩余类。它的作用是作为一个形式元素，满足

\[
f(\alpha)=0.
\]

## 为什么要求 \(f(x)\) 不可约

如果 \(f(x)\) 可约，比如 \(f(x)=g(x)h(x)\)，其中 \(g,h\) 都不是常数，那么在商环中

\[
g(x)h(x)\equiv0\pmod{f(x)}.
\]

但 \(g(x)\) 和 \(h(x)\) 本身不一定为零，这就产生了零因子。有零因子的环不可能是域。

如果 \(f(x)\) 不可约，那么 \((f(x))\) 是极大理想，商环就是域。直观地说，不可约性保证了这个降次规则不会把非零元素错误地乘成 0。

## 例子：构造 \(\mathbb F_8\)

在 \(\mathbb F_2[x]\) 中取

\[
f(x)=x^3+x+1.
\]

它没有 \(0\) 或 \(1\) 作为根，因此作为三次多项式不可约。构造

\[
\mathbb F_8=\mathbb F_2[x]/(x^3+x+1).
\]

令

\[
\alpha=x\bmod f(x).
\]

因为 \(f(\alpha)=0\)，所以

\[
\alpha^3+\alpha+1=0.
\]

在特征 2 中加法和减法一样，因此

\[
\alpha^3=\alpha+1.
\]

这就是乘法后的降次规则。

## 一次完整乘法

计算

\[
(\alpha^2+1)(\alpha+1).
\]

先按普通多项式乘法展开：

\[
(\alpha^2+1)(\alpha+1)=\alpha^3+\alpha^2+\alpha+1.
\]

用 \(\alpha^3=\alpha+1\) 降次：

\[
\alpha^3+\alpha^2+\alpha+1=(\alpha+1)+\alpha^2+\alpha+1.
\]

在 \(\mathbb F_2\) 中相同项相加为 0，所以

\[
(\alpha+\alpha)+(1+1)+\alpha^2=\alpha^2.
\]

因此

\[
(\alpha^2+1)(\alpha+1)=\alpha^2.
\]

## 三种表示方式

同一个元素可以有不同表示：

- 多项式表示：\(\alpha^2+\alpha+1\)；
- 向量表示：\((1,1,1)\)，对应基 \(1,\alpha,\alpha^2\)；
- 幂表示：若选到本原元，非零元素还可以写成 \(\alpha^i\)。

多项式表示适合加法和降次；向量表示适合实现；幂表示适合乘法群和阶的分析。

## 这个构造有什么用

这个构造提供了一套统一的有限计算规则。它可以用于编码理论中的校验符号，通信中的序列设计，计算机代数中的多项式分解，也可以用于密码学里的有限域运算。关键不在某个应用，而在于它把“有限集合”做成了一个能稳定加减乘除的代数结构。

## 常见误区

**误区一：\(\alpha\) 是某个普通数。** 更准确地说，\(\alpha\) 是 \(x\) 在商环中的剩余类。它只需要满足构造多项式给出的关系。

**误区二：乘法后可以保留高次幂。** 在 \(\mathbb F_p[x]/(f)\) 中，每个元素都应该降成次数小于 \(\deg f\) 的形式。

**误区三：任意多项式都能构造域。** 必须用不可约多项式；可约多项式会带来零因子。

## 检查点

在 \(\mathbb F_2[x]/(x^3+x+1)\) 中，试着计算：

\[
\alpha(\alpha^2+\alpha+1).
\]

提示：先展开，再用 \(\alpha^3=\alpha+1\) 降次。



## 为什么要引入这个概念

商环构造把“抽象存在的有限域”变成可计算的表示。引入不可约多项式的原因是给高次幂一个稳定降次规则，同时避免零因子。

## 可复现实验

把本文结论变成可检查对象，可以用一个最小 Python 检查脚本。运行方式是：

```bash
python3 finite_field_depth_checks.py
```

和本文直接相关的核心断言是：

```python
mod8 = 0b1011  # x^3+x+1
lhs = gf_mul(0b101, 0b011, mod8)  # (alpha^2+1)(alpha+1)
assert poly_str(lhs) == 'x^2'
```

本次实验输出摘录：

```text
gf8_product_alpha2_plus_1_times_alpha_plus_1=x^2
```

## 输出怎么读

输出 `x^2` 对应正文推导的结果：普通展开先得到三次项，再用 `alpha^3=alpha+1` 降次，最后同类项在 `F_2` 中抵消。

## 状态变化

状态变化是：两个低次多项式先按普通乘法变成高次多项式；随后对构造多项式取模；最终回到次数小于 3 的标准代表元。

## 练习或延伸

把 `(alpha^2+alpha)(alpha^2+1)` 写成 bitmask 乘法，先手算再运行脚本，检查结果是否一致。

## 参考资料

- SageMath 文档：[Finite Fields](https://doc.sagemath.org/html/en/reference/finite_rings/index.html)
- MIT OpenCourseWare：[18.703 Modern Algebra](https://ocw.mit.edu/courses/18-703-modern-algebra-spring-2013/)
- Encyclopedia of Mathematics：[Finite field](https://en.wikipedia.org/wiki/Finite_field)

{% endraw %}
