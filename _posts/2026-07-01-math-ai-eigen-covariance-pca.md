---
layout: post
title: "特征值、协方差和 PCA：找出数据变化最大的方向"
date: 2026-07-01 20:42:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "从二维点云出发，解释协方差矩阵、特征向量和 PCA 主方向如何连接。"
tags: [math, eigenvalue, covariance, pca, teaching]
---
{% raw %}
> 主题：数学基础 / 特征值 / 协方差 / PCA
> 本文 lab 已验证：二维数据的第一主方向解释了约 `97.0%` 的方差。

很多数据表面上有多个维度，但真正变化最大的方向可能只有少数几个。PCA 的核心问题是：能不能找到一条方向，让数据投影到这条方向后保留尽可能多的变化？回答这个问题需要协方差矩阵和特征向量。

## 问题从哪里来

如果两个特征高度相关，例如身高和臂展、访问量和请求数，直接把它们当成完全独立的维度会重复表达同一类变化。降维、可视化、压缩和去噪都需要区分“主要变化方向”和“剩余噪声方向”。

## 正式定义

对中心化后的数据矩阵 `Z`，协方差矩阵可以写成 `C = Z^T Z/(n-1)`。它的对角线描述每个特征自身方差，非对角线描述两个特征一起变化的程度。对称矩阵 `C` 的特征分解满足 `C v = lambda v`。较大的 `lambda` 对应方差更大的方向 `v`。

## 直观模型

![特征值、协方差和 PCA：找出数据变化最大的方向](/assets/diagrams/math-ai-eigen-covariance-pca.svg)

可以把点云想成一团被拉长的橡皮泥。第一特征向量沿着最拉长的方向，第一特征值描述沿这个方向的方差规模。PCA 不是神秘模型，它是在协方差矩阵上找最能解释变化的坐标轴。

## 怎么算

最小 NumPy 流程：

```python
Z = points - points.mean(axis=0)
C = np.cov(Z, rowvar=False)
values, vectors = np.linalg.eigh(C)
order = values.argsort()[::-1]
values = values[order]
vectors = vectors[:, order]
explained = values[0] / values.sum()
```

lab 输出：

```text
pca_first_explained=0.970
first_component=(-0.988, -0.156)
eigenvalues=(4.640, 0.142)
```

第一主成分解释率约 97.0%，说明这个二维点云的变化几乎都沿同一条方向展开。第二个特征值很小，表示垂直方向只剩少量扰动。

## 有什么用

1. 数据可视化中常用 PCA 把高维样本投影到二维或三维。
2. 训练模型前可以用方差方向检查特征是否高度冗余。
3. 协方差和特征值会出现在高斯模型、白化、SVD、谱聚类和推荐系统中。
4. PCA 的“保留多少信息”有可计算指标：解释方差比例。

## 常见误区

1. **未中心化就做解释。** PCA 关注围绕均值的变化，中心化是关键步骤。
2. **把主成分方向当原始特征。** 主成分通常是原始特征的线性组合。
3. **只看二维图判断高维结构。** 低维可视化会丢信息，需要查看解释方差比例。
4. **把相关方向当因果方向。** PCA 只描述变化结构，不解释变化原因。

## 检查点

把点云旋转 45 度，重新计算协方差和特征向量。观察解释方差比例是否保持接近，主方向坐标如何变化。

## 参考资料
- MIT OpenCourseWare：[18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- NumPy 文档：[Linear algebra](https://numpy.org/doc/stable/reference/routines.linalg.html)
- NumPy 文档：[numpy.linalg.eigh](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html)

{% endraw %}
