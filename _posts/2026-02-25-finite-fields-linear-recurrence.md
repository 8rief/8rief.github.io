---
layout: post
title: "有限域上的线性递推：特征多项式如何控制周期"
date: 2026-02-25 09:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "把 m 阶线性递推看成有限状态机，解释本原特征多项式为什么给出最大周期。"
tags: [math, finite-field, linear-recurrence, lfsr]
---
{% raw %}

> 主题：线性递推 / 特征多项式 / 有限状态 / 周期

有限域上的线性递推把前面学过的不可约多项式、本原多项式和有限乘法群连接起来。它的核心问题是：一个递推序列什么时候会进入最长可能周期？

![线性递推：状态在有限域里循环](/assets/diagrams/finite-field-advanced-linear-recurrence.svg)

## 什么是线性递推

在 \(\mathbb F_q\) 上，一个 \(m\) 阶线性递推可以写成

\[
s_{n+m}=c_{m-1}s_{n+m-1}+c_{m-2}s_{n+m-2}+\cdots+c_0s_n.
\]

给定初始状态

\[
(s_0,s_1,\ldots,s_{m-1}),
\]

后面的项都由这个递推唯一决定。

## 状态视角

每一时刻的状态可以写成

\[
(s_n,s_{n+1},
\ldots,s_{n+m-1}).
\]

下一步状态是

\[
(s_{n+1},s_{n+2},
\ldots,s_{n+m}).
\]

由于 \(\mathbb F_q\) 上共有 \(q^m\) 个状态，序列一定最终循环。零状态会永远停在零状态，因此非零状态最多只有

\[
q^m-1
\]

个可循环状态。

## 特征多项式

递推对应的特征多项式是

\[
f(x)=x^m-c_{m-1}x^{m-1}-\cdots-c_1x-c_0.
\]

在特征 2 中，减号和加号相同。

这个多项式控制递推的结构。若 \(f(x)\) 是本原多项式，则非零状态会形成一个长度

\[
q^m-1
\]

的大循环。这是最大可能周期。

## 例子：三阶二元递推

考虑 \(\mathbb F_2\) 上递推

\[
s_{n+3}=s_{n+1}+s_n.
\]

对应特征多项式是

\[
f(x)=x^3+x+1.
\]

这个多项式在 \(\mathbb F_2[x]\) 中是三次本原多项式。取初始状态

\[
(s_0,s_1,s_2)=(0,0,1).
\]

递推得到一个周期为 7 的序列：

\[
0,0,1,0,1,1,1,
\]

然后重复。

状态依次是

\[
001,
010,
101,
011,
111,
110,
100,
\]

正好遍历所有非零三元组。

## 为什么本原多项式给出最大周期

若 \(f(x)\) 是 \(m\) 次本原多项式，设 \(\alpha\) 是它的根，则

\[
\operatorname{ord}(\alpha)=q^m-1.
\]

递推的状态转移在代数上对应“乘以 \(\alpha\)”这样的循环动作。由于 \(\alpha\) 的阶最大，非零状态就会绕完整个 \(q^m-1\) 长度的循环。

所以本原多项式不仅是构造有限域的工具，也是构造最大周期线性递推的工具。

## 特征多项式不可约但非本原会怎样

如果特征多项式不可约但不是本原，那么状态仍然有良好的代数结构，但周期会小于 \(q^m-1\)。

例如四次不可约多项式的根如果阶为 5，那么对应非零状态周期最多围绕长度 5 的循环，而不是 \(15\)。

## 常见误区

**误区一：递推阶数 \(m\) 就是周期。** 阶数只是状态长度；最大周期是 \(q^m-1\)。

**误区二：任意非零初始状态都能避开短周期。** 只有当特征多项式足够强，例如本原时，所有非零状态才落在同一个最大循环中。

**误区三：特征多项式只是形式符号。** 它决定了状态转移的代数结构和周期。

## 检查点

对递推 \(s_{n+3}=s_{n+1}+s_n\)，从初始状态 \(100\) 开始写出7个状态，验证它们也是同一个周期的循环移位。



## 为什么要引入这个概念

线性递推把多项式的本原性转成状态机周期。引入特征多项式后，才能解释为什么同样是三阶递推，有的短周期，有的达到最大周期。

## 可复现实验

把本文结论变成可检查对象，可以用一个最小 Python 检查脚本。运行方式是：

```bash
python3 finite_field_depth_checks.py
```

和本文直接相关的核心断言是：

```python
def lfsr(init, length):
    s = list(init)
    for i in range(3, length):
        s.append(s[i-2] ^ s[i-3])
    return s
period = lfsr([0, 0, 1], 14)[:7]
states = [''.join(map(str, (period[(i + j) % 7] for j in range(3)))) for i in range(7)]
assert ''.join(map(str, period)) == '0010111'
assert len(set(states)) == 7
```

本次实验输出摘录：

```text
linear_recurrence_period=0010111
linear_recurrence_states=['001', '010', '101', '011', '111', '110', '100']
```

## 输出怎么读

周期 `0010111` 长度为 7，状态列表正好覆盖全部非零三比特状态。由于 `2^3-1=7`，这个递推达到了三阶二元递推的最大非零周期。

## 状态变化

状态变化是：每一步丢掉最左边的状态位，追加 `s_{n+1}+s_n`；特征多项式本原时，这个状态转移在非零状态上形成一个大环。

## 练习或延伸

从初始状态 `100` 开始运行同一递推，验证得到的是同一个 7 状态环的循环移位。

## 参考资料

- SageMath 文档：[Finite Fields](https://doc.sagemath.org/html/en/reference/finite_rings/index.html)
- MIT OpenCourseWare：[18.703 Modern Algebra](https://ocw.mit.edu/courses/18-703-modern-algebra-spring-2013/)
- Encyclopedia of Mathematics：[Finite field](https://en.wikipedia.org/wiki/Finite_field)

{% endraw %}
