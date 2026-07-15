---
layout: post
title: "线性方程和最小二乘：从无解系统到可解释拟合"
date: 2026-02-14 18:00:00 +0800
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

只给出一条拟合线还不够：需要知道设计矩阵是否满秩、残差有多大、参数能否被独立识别。最小二乘把这些问题连接到投影、rank 和奇异值。

## 为什么要引入最小二乘

如果有 5 个点，大致沿着一条直线上升，但每个点都有噪声，一条直线通常无法同时穿过所有点。此时问题不再是解 `Xw=y`，而是找一个 `w` 让预测 `Xw` 尽量接近 `y`。这就是很多 baseline 模型、趋势拟合和参数估计的基础。

## 正式定义

给定设计矩阵 `X` 和目标向量 `y`，最小二乘问题写成：`min_w ||Xw-y||_2^2`。当 `X` 的列满秩时，正规方程是 `X^T X w = X^T y`。实际计算中更常用数值线性代数库，因为直接求逆可能放大误差。

在几何上，预测 `Xw` 位于 `X` 的列空间中。最优残差 `r=y-Xw` 与每一列正交，因此满足 `X^T r=0`；这正是正规方程的来源。正规方程适合推导，QR 或 SVD 一类算法通常更适合数值计算。

## 直观模型

![线性方程和最小二乘：从无解系统到可解释拟合](/assets/diagrams/math-ai-linear-system-least-squares.svg)

每个样本点都会给直线参数一个约束。噪声让这些约束互相冲突。最小二乘选择让所有垂直误差平方和最小的参数，平方会让大误差受到更强惩罚。

## 怎么算

拟合 `y = slope * x + intercept` 时，可以把每个样本写成一行 `[x_i, 1]`：

```python
import numpy as np

rng = np.random.default_rng(42)
x = np.linspace(-2, 2, 25)
y = 1.8 * x - 0.4 + rng.normal(0, 0.12, size=x.shape)
X = np.column_stack([x, np.ones_like(x)])
coef, residuals, rank, singular_values = np.linalg.lstsq(X, y, rcond=None)
slope, intercept = coef
prediction = X @ coef
mse = np.mean((prediction - y) ** 2)
```

lab 输出：

```text
least_squares_slope=1.809
least_squares_intercept=-0.404
least_squares_mse=0.00943
rank=2
```

`rank=2` 表示两列特征在这个样本上能提供两个独立方向：一列控制斜率，一列控制截距。如果所有 `x` 都相同，斜率和截距就无法被稳定地区分。

这段代码现与 lab 完全一致：固定 seed 42、25 个点、噪声标准差 0.12。复核残差正交性：

```python
residual = y - prediction
print(X.T @ residual)
print(singular_values)
```

预期第一行接近 `[0,0]`，奇异值约为 `[6.009252,5.0]`。浮点计算下“正交”应检查接近零，不能要求逐位为零。

## rank 和奇异值怎样诊断问题

把所有 `x` 设为同一个常数时，设计矩阵两列线性相关，rank 从 2 降到 1。此时多组“斜率 + 截距”会产生同一预测，参数无法唯一识别：

```python
x_bad = np.ones(5)
X_bad = np.column_stack([x_bad, np.ones_like(x_bad)])
_, _, rank_bad, s_bad = np.linalg.lstsq(X_bad, np.arange(5.), rcond=None)
print(rank_bad, s_bad)
```

预期 `rank_bad=1`，并出现一个接近零的奇异值。即使库函数返回参数，也不应把该斜率解释为稳定估计。

## MSE 的量纲和边界

本次 MSE `0.00943` 是残差平方的平均值；其平方根约 `0.0971`，与生成噪声尺度 `0.12` 同量级。它只描述这份合成数据上的拟合误差，没有 train/test 切分，也不构成泛化性能主张。本篇的目标是验证线性代数机制；模型效果比较留给结课项目。

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

## 练习与检查点

把所有 `x` 改成同一个值，观察 `rank` 和奇异值如何变化。思考为什么此时斜率无法可靠估计。

预期 rank 降为 1，第二个奇异值接近 0。继续完成两项检查：

1. 比较 `np.linalg.lstsq` 与手写正规方程在当前良态数据上的参数；
2. 逐渐让两列特征更接近线性相关，记录条件数与参数变化。

若参数剧烈变化而预测变化较小，说明参数解释已受病态设计矩阵影响。

## 参考资料
- MIT OpenCourseWare：[18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- NumPy 文档：[Linear algebra](https://numpy.org/doc/stable/reference/routines.linalg.html)
- NumPy 文档：[numpy.linalg.lstsq](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html)

{% endraw %}
