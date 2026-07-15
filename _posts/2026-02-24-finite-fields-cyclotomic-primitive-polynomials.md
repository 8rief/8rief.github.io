---
layout: post
title: "分圆多项式与本原多项式：从阶看不可约因子"
date: 2026-02-24 09:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "解释 Φ_n(x) 如何收集阶为 n 的根，以及本原多项式为什么来自 Φ_{q^m-1}(x)。"
tags: [math, finite-field, cyclotomic, primitive-polynomial]
---
{% raw %}

> 主题：分圆多项式 / 元素阶 / 本原多项式

Möbius反演按“次数”组织不可约多项式。分圆多项式按“根的阶”组织多项式。有限域里这两个视角会合在一起：不可约因子对应 Frobenius 共轭类，分圆多项式对应固定阶的根。

![分圆多项式与本原多项式](/assets/diagrams/finite-field-advanced-cyclotomic-primitive.svg)

## 分圆多项式解决什么问题

\(x^n-1\) 的根是所有满足

\[
\alpha^n=1
\]

的元素。这些根的阶可能是 \(n\)，也可能是 \(n\) 的真因子。

分圆多项式 \(\Phi_n(x)\) 专门收集“阶正好等于 \(n\)”的根：

\[
\Phi_n(x)=\prod_{\operatorname{ord}(\alpha)=n}(x-\alpha).
\]

因此

\[
x^n-1=\prod_{d\mid n}\Phi_d(x).
\]

这和前面的

\[
x^{q^n}-x=\prod_{d\mid n}V_d(x)
\]

结构很像：前者按根的阶分层，后者按极小多项式次数分层。

## 例子：\(\Phi_7(x)\)

因为 7 是素数，

\[
\Phi_7(x)=x^6+x^5+x^4+x^3+x^2+x+1.
\]

在 \(\mathbb F_2[x]\) 中，它分解为

\[
\Phi_7(x)=(x^3+x+1)(x^3+x^2+1).
\]

这两个三次不可约多项式的根都在 \(\mathbb F_8\) 中。由于 \(\mathbb F_8^\times\) 的大小是 7，任何非1的非零元素阶都是 7，所以这些根都是本原元。

于是这两个三次不可约多项式也是三次本原多项式。

## 和本原多项式的关系

设 \(f(x)\in\mathbb F_q[x]\) 是 \(m\) 次不可约多项式，\(\alpha\) 是它的根。若

\[
\operatorname{ord}(\alpha)=q^m-1,
\]

那么 \(f(x)\) 是本原多项式。

也就是说，本原多项式的根是 \(\mathbb F_{q^m}^\times\) 的生成元。这样的根阶正好是 \(q^m-1\)，所以本原多项式一定出现在

\[
\Phi_{q^m-1}(x)
\]

在 \(\mathbb F_q[x]\) 上的分解中。

## 为什么还要检查次数

\(\Phi_{q^m-1}(x)\) 收集阶为 \(q^m-1\) 的根。这样的根一定落在 \(\mathbb F_{q^m}\) 中，并且不会落在任何真子域里。因此它在 \(\mathbb F_q\) 上的极小多项式次数是 \(m\)。

所以本原多项式可以看成：\(\Phi_{q^m-1}(x)\) 在 \(\mathbb F_q[x]\) 上分解出来的 \(m\) 次不可约因子。

## 四次例子：阶决定是否本原

在 \(\mathbb F_2[x]\) 中，四次不可约多项式的根落在 \(\mathbb F_{16}\)。非零乘法群大小是

\[
2^4-1=15.
\]

本原根必须阶为 15，因此本原四次多项式来自

\[
\Phi_{15}(x)
\]

的四次不可约因子。

如果某个四次不可约多项式的根阶只有 5，它仍然能构造 \(\mathbb F_{16}\)，但它不是本原多项式。

## 这和Möbius反演的关系

Möbius反演回答“有多少个 \(m\) 次不可约多项式”。分圆多项式进一步回答“哪些不可约多项式的根有指定阶”。

因此：

- \(V_m(x)\)：按极小多项式次数打包；
- \(\Phi_n(x)\)：按根的乘法阶打包；
- 本原多项式：同时满足“次数是 \(m\)”和“根的阶是 \(q^m-1\)”。

## 常见误区

**误区一：分圆多项式只属于复数。** 它最初可以在复数根中理解，但作为整数系数多项式，也可以模 \(p\) 后在有限域上分解。

**误区二：不可约多项式自动来自最大阶根。** 不可约只控制极小多项式次数；本原性还要检查根的阶。

**误区三：\(\Phi_n(x)\) 在 \(\mathbb F_q\) 上一定不可约。** 一般会分解成多个不可约因子，因子次数由 \(q\) 模 \(n\) 的阶控制。

## 检查点

为什么 \(\Phi_7(x)\) 在 \(\mathbb F_2\) 上分成两个三次因子，而不是一个六次因子？提示：看 \(2\) 模 \(7\) 的阶。



## 为什么要引入这个概念

分圆多项式按根的阶分组；不可约多项式按 Frobenius 轨道分组。本原多项式需要同时满足次数和最大阶，这就是两种分组交汇的地方。

## 可复现实验

把本文结论变成可检查对象，可以用一个最小 Python 检查脚本。运行方式是：

```bash
python3 finite_field_depth_checks.py
```

和本文直接相关的核心断言是：

```python
f3a = 0b1011  # x^3+x+1
f3b = 0b1101  # x^3+x^2+1
phi7 = sum(1 << i for i in range(7))
assert poly_mul(f3a, f3b) == phi7
```

本次实验输出摘录：

```text
cyclotomic_phi7_factor_check=True
cyclotomic_phi7_factors=['x^3+x+1', 'x^3+x^2+1']
```

## 输出怎么读

`True` 表示 `Phi_7(x)` 在 `F_2[x]` 上分成两个三次因子。两个因子的根都具有阶 7，因此都是三次本原多项式。

## 状态变化

状态变化是：先用 `Phi_7` 收集阶为 7 的根；再在 `F_2[x]` 上分解；每个三次因子对应一个 Frobenius 轨道；轨道中的根都是 `F_8^×` 的生成元。

## 练习或延伸

计算 2 模 7 的阶，并用它解释为什么因子次数是 3。

## 参考资料

- SageMath 文档：[Finite Fields](https://doc.sagemath.org/html/en/reference/finite_rings/index.html)
- MIT OpenCourseWare：[18.703 Modern Algebra](https://ocw.mit.edu/courses/18-703-modern-algebra-spring-2013/)
- Encyclopedia of Mathematics：[Finite field](https://en.wikipedia.org/wiki/Finite_field)

{% endraw %}
