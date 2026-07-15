---
layout: post
title: "数值稳定性：softmax 为什么要减最大值"
date: 2026-02-18 09:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "用大 logits 触发指数溢出，再用稳定 softmax 和 logsumexp 修复同一个计算目标。"
tags: [math, numerical-stability, softmax, teaching]
---
{% raw %}
> 主题：数学基础 / 数值稳定性 / softmax
> 本文 lab 已验证：朴素指数计算会溢出，稳定 softmax 的概率和为 `1.000000`。

数学公式在纸上成立，不代表直接照写成程序就稳定。指数、对数、除法、矩阵分解都可能因为浮点范围和舍入误差产生异常。softmax 是最适合入门的例子：公式很简单，错误也很常见。

数值稳定性关注的是：在有限精度和有限表示范围内，程序能否可靠计算数学上等价的目标。稳定变换不会改变所求概率，却会改变中间值是否溢出、下溢或丢失有效数字。

## 为什么要引入稳定等价变换

分类模型常把最后一层输出写成 logits，再通过 softmax 转成概率：`softmax_i(z)=exp(z_i)/sum_j exp(z_j)`。如果 logits 是 `(1000,1001,999)`，`exp(1001)` 会超过普通浮点数能表示的范围，朴素实现可能得到 `inf` 和 `nan`。

## 正式定义

softmax 对所有 logits 加同一个常数不变：`softmax(z)=softmax(z-c)`。因此可以取 `c=max(z)`，把最大 logit 变成 0，其余 logit 变成非正数，避免指数上溢。logsumexp 也使用相同思想：`log(sum exp(z_i)) = m + log(sum exp(z_i-m))`，其中 `m=max(z)`。

平移不变性可直接推导：

```text
exp(z_i-c) / Σ_j exp(z_j-c)
= [exp(z_i)exp(-c)] / [exp(-c)Σ_j exp(z_j)]
= exp(z_i) / Σ_j exp(z_j)
```

选择最大值作为 `c` 后，所有 `z_i-c<=0`，指数位于 `(0,1]`。

## 直观模型

![数值稳定性：softmax 为什么要减最大值](/assets/diagrams/math-ai-numerical-stability-softmax-logsumexp.svg)

softmax 关心相对差距，不关心所有 logits 的共同平移。减最大值不会改变概率，只是把计算搬到浮点数更安全的范围。

## 怎么算

稳定实现：

```python
import numpy as np

z = np.array([1000.0, 1001.0, 999.0])
shifted = z - z.max()
exp_shifted = np.exp(shifted)
probs = exp_shifted / exp_shifted.sum()
logsumexp = z.max() + np.log(exp_shifted.sum())
```

朴素版本会得到不可用中间值：

```python
with np.errstate(over="ignore", invalid="ignore"):
    naive_exp = np.exp(z)
    naive = naive_exp / naive_exp.sum()
print(naive_exp)
print(naive)
```

```text
[inf inf inf]
[nan nan nan]
```

lab 输出：

```text
naive_overflows=True
stable_softmax=(0.244728, 0.665241, 0.090031)
stable_softmax_sum=1.000000
logsumexp=1001.407606
```

概率和接近 1，说明稳定实现保留了 softmax 的基本性质。`naive_overflows=True` 说明朴素实现确实触碰了数值边界。

三个概率还可由较小的相对 logits `[0,1,-1]` 手算。分母是 `1+e+e^-1≈4.0862`，结果正是 `[0.2447,0.6652,0.0900]`。共同加上 1000 没有改变分布。

## logsumexp 怎样连接交叉熵

对真实类别 `y`，softmax 交叉熵可写成：

```text
-log softmax(z)_y = logsumexp(z) - z_y
```

因此无需先生成可能接近 0 的概率再取对数。当前 logits 若真实类别为 1，loss 为 `1001.407606-1001=0.407606`。

```python
y = 1
loss = logsumexp - z[y]
assert np.isclose(loss, -np.log(probs[y]))
```

这种等价重写同时避免大指数上溢和极小概率取 `log(0)`。

## 稳定不等于没有下溢

若两个 logit 相差上千，较小项的稳定指数仍可能下溢到 0；这通常正确表达了它在当前 dtype 下可忽略。需要保留极小对数概率时，应直接在 log domain 使用 logsumexp，而非先转普通概率。

检查 dtype 也很重要：float32 的指数范围比 float64 更窄。发现 `nan` 时应记录输入范围、dtype 和首次出现异常的算子。

## 有什么用

1. 分类交叉熵、注意力权重和语言模型解码都依赖 softmax 或 logsumexp。
2. 数值稳定性错误常表现为 loss 变成 `nan`，需要从公式实现处排查。
3. 稳定计算通常利用数学等价变换，而不是更换机器或增大精度。
4. 学会这个例子后，更容易理解标准库为什么提供专门的稳定函数。

## 常见误区

1. **认为 Python 大数能解决 NumPy 浮点溢出。** 数组运算遵循固定浮点 dtype。
2. **减均值代替减最大值。** 减均值不一定避免最大指数上溢。
3. **把 logits 当概率。** logits 是未归一化分数，softmax 后才是概率分布。
4. **看到 `nan` 只调学习率。** 还应检查指数、对数、除零和输入范围。

## 练习与检查点

把 logits 改成 `(10000,10001,9999)`。比较朴素实现和稳定实现的输出，并解释为什么概率几乎不变。

## 参考资料
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- NumPy 文档：[numpy.exp](https://numpy.org/doc/stable/reference/generated/numpy.exp.html)
- NumPy 文档：[numpy.logaddexp](https://numpy.org/doc/stable/reference/generated/numpy.logaddexp.html)
- SciPy 文档：[scipy.special.logsumexp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.logsumexp.html)
- SciPy 文档：[scipy.special.softmax](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.softmax.html)

{% endraw %}
