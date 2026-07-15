---
layout: post
title: "导数和梯度：用 finite difference 检查方向"
date: 2026-02-16 18:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "从一个二元函数出发，用解析梯度和有限差分互相校验，建立优化前的方向感。"
tags: [math, gradient, finite-difference, teaching]
---
{% raw %}
> 主题：数学基础 / 导数 / 梯度检查
> 本文 lab 已验证：二元函数的解析梯度和有限差分梯度最大相对误差约 `1.41e-10`。

优化算法的核心动作是沿着某个方向更新参数。方向从哪里来？对单变量函数是导数，对多变量函数是梯度。只要梯度算错，后面的训练曲线、收敛速度和模型效果都会失去可信度。

梯度实现经常出现一种危险状态：代码能运行、shape 也正确，更新方向却因符号或平均系数错误而偏离。有限差分只调用 loss，不复用解析梯度代码，因此可以作为独立的局部检查。

## 为什么要引入梯度检查

在机器学习里，损失函数通常依赖成千上万个参数。我们无法靠画图判断每个参数该怎么调。梯度给出局部最陡上升方向，负梯度给出局部最陡下降方向。学习有限差分检查，是为了在实现复杂梯度前先掌握一个独立验证工具。

## 正式定义

单变量导数是 `f'(x)=lim_{h->0} (f(x+h)-f(x))/h`。多变量函数 `f(x_1,...,x_n)` 的梯度是由偏导数组成的向量：`grad f = (partial f/partial x_1, ..., partial f/partial x_n)`。有限差分用很小的 `h` 近似偏导，例如中心差分 `(f(x+h e_i)-f(x-h e_i))/(2h)`。

## 直观模型

![导数和梯度：用 finite difference 检查方向](/assets/diagrams/math-ai-gradient-finite-difference.svg)

站在山坡上的一个点，梯度箭头指向局部上升最快的方向。有限差分是在这个点附近前后各走一小步，用函数值变化估计坡度。

## 怎么算

当前 lab 使用到固定目标点的二次距离：

```python
import numpy as np

target = np.array([0.3, 0.9])

def f(v):
    diff = v - target
    return 0.5 * (diff @ diff)

def analytic(v):
    return v - target

point = np.array([1.2, -0.7])
```

手算可得：

```text
f(point) = 0.5 × (0.9² + (-1.6)²) = 1.685
grad f   = point - target = (0.9, -1.6)
```

中心差分检查每个坐标：

```python
h = 1e-6
numeric = []
for i in range(2):
    e = np.zeros(2); e[i] = 1
    numeric.append((f(point + h*e) - f(point - h*e)) / (2*h))
```

lab 输出：

```text
analytic_gradient=(0.900, -1.600)
numeric_gradient=(0.900, -1.600)
gradient_max_relative_error=1.41e-10
```

这说明解析公式和数值近似在当前点高度一致。后续写反向传播时，有限差分仍是最直接的 debug 工具。

此前若使用另一个二元多项式，却继续引用 `(0.9,-1.6)`，示例与输出就不再对应。复现型文章必须让函数、输入点、解析结果和实验报告来自同一个定义。

## 步长为什么不能无限小

中心差分有两类误差：

- `h` 太大：函数在区间内的弯曲使局部线性近似不准；
- `h` 太小：`f(x+h)` 与 `f(x-h)` 非常接近，相减损失有效数字。

可直接扫描步长：

```python
for h in (1e-1, 1e-3, 1e-6, 1e-9, 1e-12):
    numeric = []
    for i in range(2):
        e = np.zeros(2); e[i] = 1.0
        numeric.append((f(point+h*e) - f(point-h*e)) / (2*h))
    print(h, np.max(np.abs(np.array(numeric) - analytic(point))))
```

本函数是二次函数，中心差分的截断误差非常小；到极小 `h` 时仍会看到浮点舍入误差上升。复杂函数常在一段中间步长处误差最低。

## 怎样定义通过标准

lab 使用相对尺度：

```python
relative = abs(numeric - analytic) / max(1.0, abs(analytic))
```

分母至少为 1，避免真实梯度接近零时相对误差被放大到失去意义。检查标准应结合 dtype、函数尺度和参数数量；单点通过只证明该局部坐标一致，不能替代多个索引和端到端训练测试。

## 有什么用

1. 梯度下降、Adam、SGD 都依赖梯度方向。
2. 手写神经网络时，有限差分能检查反向传播是否正确。
3. 优化问题的 stationary point 满足梯度接近零。
4. 梯度大小能提示学习率是否过大或过小。

## 常见误区

1. **把梯度方向当全局最优方向。** 梯度只描述局部一阶信息。
2. **有限差分步长越小越好。** 太小会被浮点舍入误差影响。
3. **只检查一个参数。** 多参数实现要抽样检查多个坐标。
4. **用训练效果替代梯度检查。** 模型能跑不代表梯度公式正确。

## 练习与检查点

把 `h` 改成 `1e-2`、`1e-8`、`1e-12`，观察相对误差的变化。解释截断误差和浮点误差如何共同影响结果。

## 参考资料
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- PyTorch 教程：[Automatic Differentiation with torch.autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- PyTorch 文档：[torch.autograd.gradcheck](https://docs.pytorch.org/docs/stable/generated/torch.autograd.gradcheck.gradcheck.html)
- NumPy 文档：[Floating point error handling](https://numpy.org/doc/stable/reference/routines.err.html)

{% endraw %}
