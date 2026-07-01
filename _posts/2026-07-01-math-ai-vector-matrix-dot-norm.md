---
layout: post
title: "向量和矩阵第一课：dot、norm 和 projection"
date: 2026-07-01 20:40:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "从相似度、长度和投影三个需求出发，建立后续线性模型和神经网络会反复使用的向量语言。"
tags: [math, linear-algebra, vector, teaching]
---
{% raw %}
> 主题：数学基础 / 线性代数 / 向量空间
> 本文 lab 已验证：向量长度、点积、投影和矩阵乘向量都由同一段 NumPy 代码计算，输出 `vector_norm=5.000`。

后续学习算法、数据分析和深度学习时，很多对象都会被写成向量：一条样本的特征、一段文本的 embedding、一张图片展平成的像素数组、模型的一组参数。向量语言的价值在于把“相似不相似”“离得远不远”“沿某个方向有多少成分”变成可以计算的数。

## 问题从哪里来

假设有一个样本向量 `a=(3,4)`，另一个方向向量 `b=(2,-1)`。如果只盯着坐标，很难直接回答三个问题：第一个样本有多大，两个方向是否相近，第一个样本落在第二个方向上有多少。机器学习里的线性分类、推荐系统里的相似度、优化里的梯度方向，都要反复回答这些问题。

## 正式定义

向量 `a=(a_1,...,a_n)` 的欧几里得长度是 `||a|| = sqrt(a_1^2+...+a_n^2)`。两个同维向量的点积是 `a·b = a_1 b_1 + ... + a_n b_n`。如果 `b` 不是零向量，`a` 在 `b` 方向上的投影为 `proj_b(a) = ((a·b)/(b·b)) b`。矩阵乘向量 `A a` 可以理解为把输入向量变换到新的坐标或新的特征空间。

## 直观模型

![向量和矩阵第一课：dot、norm 和 projection](/assets/diagrams/math-ai-vector-matrix-dot-norm.svg)

长度衡量向量本身的规模，点积同时受长度和夹角影响，投影把一个向量拆出“沿某方向的那一部分”。矩阵可以看成一组输出坐标的计算规则：每一行和输入向量做一次点积，得到一个输出分量。

## 怎么算

最小代码如下：

```python
import numpy as np

a = np.array([3.0, 4.0])
b = np.array([2.0, -1.0])
A = np.array([[2.0, 1.0], [-1.0, 3.0]])

norm_a = np.linalg.norm(a)
dot_ab = a @ b
projection = (dot_ab / (b @ b)) * b
mapped = A @ a
```

本次 lab 输出：

```text
vector_norm=5.000
dot=2.000
projection_on_b=(0.800, -0.400)
matrix_times_a=(10.000, 15.000)
```

这些数字都可手算验证：`sqrt(3^2+4^2)=5`，`3*2+4*(-1)=2`，投影系数是 `2/(2^2+(-1)^2)=0.4`，投影为 `(0.8,-0.4)`。这类手算检查能及时发现代码、公式和讲解是否使用了同一组输入。

## 有什么用

1. 线性模型把预测写成 `w·x+b`，本质是用参数方向衡量输入在该方向上的投影。
2. 距离、归一化、cosine similarity 都建立在 norm 和 dot 上。
3. 神经网络的全连接层就是矩阵乘向量再加偏置。
4. PCA、最小二乘、梯度下降都需要把数据、参数和方向写成向量或矩阵。

## 常见误区

1. **把向量当成坐标列表。** 坐标是表示方式，向量运算真正描述的是方向、长度和线性组合。
2. **把点积只理解成相乘求和。** 相乘求和是计算方式，几何意义是长度和夹角共同决定的对齐程度。
3. **投影公式忘记除以 `b·b`。** 只有方向向量长度为 1 时，`(a·b)b` 才直接是投影。
4. **矩阵乘法顺序随便写。** `A @ x` 和 `x @ A` 的含义、维度和结果都不同。

## 检查点

给定 `a=(1,2)`、`b=(2,0)`，手算 `||a||`、`a·b` 和 `proj_b(a)`。再写一行 NumPy 代码确认结果。

## 参考资料
- MIT OpenCourseWare：[18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- NumPy 文档：[Linear algebra](https://numpy.org/doc/stable/reference/routines.linalg.html)
- NumPy 文档：[numpy.linalg.norm](https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html)

{% endraw %}
