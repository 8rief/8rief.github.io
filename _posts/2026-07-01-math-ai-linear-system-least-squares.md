---
layout: post
title: "线性方程和最小二乘：从无解系统到可解释拟合"
date: 2026-07-01 20:41:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "现实数据通常不能被一条直线完全穿过，最小二乘把“尽量贴近”变成可计算目标。"
tags: [math, least-squares, linear-algebra, teaching]
---
{% raw %}
> 主题：数学基础 / 线性系统 / 最小二乘
> 本文 lab 已验证：`numpy.linalg.lstsq` 拟合一条直线，得到斜率 `1.809`、截距 `-0.404`，均方误差约 `0.00943`。

工程数据很少刚好满足一组线性方程。传感器有噪声，用户行为有波动，日志指标也可能被偶然因素影响。线性方程组教我们怎样精确求解，最小二乘教我们在“不能精确求解”时怎样定义最合理的近似。

## 问题从哪里来

如果有 5 个点，大致沿着一条直线上升，但每个点都有噪声，一条直线通常无法同时穿过所有点。此时问题不再是解 `Xw=y`，而是找一个 `w` 让预测 `Xw` 尽量接近 `y`。这就是很多 baseline 模型、趋势拟合和参数估计的基础。

## 正式定义

给定设计矩阵 `X` 和目标向量 `y`，最小二乘问题写成：`min_w ||Xw-y||_2^2`。当 `X` 的列满秩时，正规方程是 `X^T X w = X^T y`。实际计算中更常用数值线性代数库，因为直接求逆可能放大误差。

## 直观模型

![线性方程和最小二乘：从无解系统到可解释拟合](/assets/diagrams/math-ai-linear-system-least-squares.svg)

每个样本点都会给直线参数一个约束。噪声让这些约束互相冲突。最小二乘选择让所有垂直误差平方和最小的参数，平方会让大误差受到更强惩罚。

## 怎么算

拟合 `y = slope * x + intercept` 时，可以把每个样本写成一行 `[x_i, 1]`：

```python
import numpy as np

x = np.linspace(-2, 2, 5)
y = 1.8 * x - 0.4 + np.array([0.05, -0.08, 0.03, 0.10, -0.04])
X = np.column_stack([x, np.ones_like(x)])
coef, *_ = np.linalg.lstsq(X, y, rcond=None)
slope, intercept = coef
```

lab 输出：

```text
least_squares_slope=1.809
least_squares_intercept=-0.404
least_squares_mse=0.00943
rank=2
```

`rank=2` 表示两列特征在这个样本上能提供两个独立方向：一列控制斜率，一列控制截距。如果所有 `x` 都相同，斜率和截距就无法被稳定地区分。

## 有什么用

1. 线性回归是最常见的可解释 baseline。
2. 多项式拟合、特征工程后的线性模型都可以归约到最小二乘。
3. 深度学习训练前，用简单 baseline 能判断任务是否真的需要复杂模型。
4. 数值线性代数库会返回 rank 和奇异值，帮助判断问题是否病态。

## 常见误区

1. **直接使用矩阵求逆。** `inv(X^T X)` 在病态数据上容易放大误差，库函数通常更稳健。
2. **只看斜率不看残差。** 参数可解释不代表拟合足够好，残差和 MSE 才说明误差规模。
3. **把相关性当因果。** 一条拟合线只能说明线性关系强弱，不能自动说明原因。
4. **忘记截距列。** 没有常数列时，模型被迫经过原点，很多数据会被错误约束。

## 检查点

把所有 `x` 改成同一个值，观察 `rank` 和奇异值如何变化。思考为什么此时斜率无法可靠估计。

## 参考资料
- MIT OpenCourseWare：[18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- NumPy 文档：[Linear algebra](https://numpy.org/doc/stable/reference/routines.linalg.html)
- NumPy 文档：[numpy.linalg.lstsq](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html)

{% endraw %}
