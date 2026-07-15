---
layout: post
title: "特征值、协方差和 PCA：找出数据变化最大的方向"
date: 2026-02-15 09:00:00 +0800
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

直接调用 PCA API 容易忽略两个前提：数据必须先围绕均值讨论变化；不同特征量纲悬殊时，还要决定是否标准化。本文只处理同量纲二维合成点，先把协方差到投影的状态变化算清楚。

## 为什么要引入 PCA

如果两个特征高度相关，例如身高和臂展、访问量和请求数，直接把它们当成完全独立的维度会重复表达同一类变化。降维、可视化、压缩和去噪都需要区分“主要变化方向”和“剩余噪声方向”。

## 正式定义

对中心化后的数据矩阵 `Z`，协方差矩阵可以写成 `C = Z^T Z/(n-1)`。它的对角线描述每个特征自身方差，非对角线描述两个特征一起变化的程度。对称矩阵 `C` 的特征分解满足 `C v = lambda v`。较大的 `lambda` 对应方差更大的方向 `v`。

若 `v` 是单位向量，数据投影 `s=Zv` 的样本方差为 `v^T C v`。在约束 `||v||=1` 下使该式最大，解就是最大特征值对应的特征向量。这给出了“最大方差方向”与特征分解之间的联系。

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

本次协方差矩阵为：

```text
[[4.530420, 0.693640],
 [0.693640, 0.251972]]
```

它是实对称矩阵，因此使用 `np.linalg.eigh`，返回实特征值和正交特征向量。可执行三个不变量检查：

```python
assert np.allclose(C, C.T)
assert np.allclose(vectors.T @ vectors, np.eye(2))
assert np.allclose(C @ vectors[:, 0], values[0] * vectors[:, 0])
```

特征向量的符号没有唯一性：`v` 与 `-v` 表示同一条轴。不同库或平台给出 `(0.988,0.156)` 也不代表结果错误；比较主方向时应比较轴或投影子空间。

## 从二维压到一维，再重建

```python
v1 = vectors[:, 0]
score = Z @ v1
reconstructed = np.outer(score, v1)
relative_error = np.sum((Z - reconstructed) ** 2) / np.sum(Z ** 2)
print(relative_error)
```

只保留第一主成分时，预期相对平方重建误差约为 `1-0.97024=0.02976`。解释方差比例和重建误差从两个方向描述同一信息损失。

## 是否需要标准化

中心化消除均值，标准化还会把每列缩放到相似方差。如果一列单位是米、另一列单位是毫米，未标准化 PCA 可能主要追随数值尺度。是否标准化取决于“绝对方差是否有业务意义”，不能机械套用。

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

## 练习与检查点

把点云旋转 45 度，重新计算协方差和特征向量。观察解释方差比例是否保持接近，主方向坐标如何变化。

预期两个特征值和解释方差比例基本不变，特征向量随点云一起旋转；允许方向整体乘以 `-1`。再只保留第一主成分重建点云，验证相对平方误差约为 2.98%。

最后把第二列放大 1000 倍，分别比较只中心化与先标准化的结果，解释主方向为何改变。

## 参考资料
- MIT OpenCourseWare：[18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- NumPy 文档：[Linear algebra](https://numpy.org/doc/stable/reference/routines.linalg.html)
- NumPy 文档：[numpy.linalg.eigh](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html)
- NumPy 文档：[numpy.cov](https://numpy.org/doc/stable/reference/generated/numpy.cov.html)

{% endraw %}
