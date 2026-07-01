---
layout: post
title: "数值稳定性：softmax 为什么要减最大值"
date: 2026-07-01 20:48:00 +0800
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

## 问题从哪里来

分类模型常把最后一层输出写成 logits，再通过 softmax 转成概率：`softmax_i(z)=exp(z_i)/sum_j exp(z_j)`。如果 logits 是 `(1000,1001,999)`，`exp(1001)` 会超过普通浮点数能表示的范围，朴素实现可能得到 `inf` 和 `nan`。

## 正式定义

softmax 对所有 logits 加同一个常数不变：`softmax(z)=softmax(z-c)`。因此可以取 `c=max(z)`，把最大 logit 变成 0，其余 logit 变成非正数，避免指数上溢。logsumexp 也使用相同思想：`log(sum exp(z_i)) = m + log(sum exp(z_i-m))`，其中 `m=max(z)`。

## 直观模型

![数值稳定性：softmax 为什么要减最大值](/assets/diagrams/math-ai-numerical-stability-softmax-logsumexp.svg)

softmax 关心相对差距，不关心所有 logits 的共同平移。减最大值不会改变概率，只是把计算搬到浮点数更安全的范围。

## 怎么算

稳定实现：

```python
z = np.array([1000.0, 1001.0, 999.0])
shifted = z - z.max()
exp_shifted = np.exp(shifted)
probs = exp_shifted / exp_shifted.sum()
logsumexp = z.max() + np.log(exp_shifted.sum())
```

lab 输出：

```text
naive_overflows=True
stable_softmax=(0.244728, 0.665241, 0.090031)
stable_softmax_sum=1.000000
logsumexp=1001.407606
```

概率和接近 1，说明稳定实现保留了 softmax 的基本性质。`naive_overflows=True` 说明朴素实现确实触碰了数值边界。

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

## 检查点

把 logits 改成 `(10000,10001,9999)`。比较朴素实现和稳定实现的输出，并解释为什么概率几乎不变。

## 参考资料
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- NumPy 文档：[numpy.exp](https://numpy.org/doc/stable/reference/generated/numpy.exp.html)
- NumPy 文档：[numpy.logaddexp](https://numpy.org/doc/stable/reference/generated/numpy.logaddexp.html)

{% endraw %}
