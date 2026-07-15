---
layout: post
title: "Autograd 和反向传播：用有限差分检查梯度"
date: 2026-05-19 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个二次损失例子对比 autograd、解析梯度和有限差分，建立反向传播的可验证理解。"
tags: [deep-learning, autograd, backpropagation, gradients]
---
{% raw %}

> 主题：深度学习基础 / 自动微分 / 反向传播
> 本文对应 lab 的 `demo-autograd` 命令。

反向传播可以先理解为链式法则在计算图上的系统执行。PyTorch autograd 会记录 tensor 运算，标量 loss 调用 `backward()` 后，参数的 `.grad` 中保存梯度。为了避免把 autograd 当黑箱，本文用解析梯度和有限差分做交叉检查。

梯度代码最危险的故障并非语法报错，而是程序正常运行、loss 也在变化，却因为漏掉转置、平均系数或激活函数导数而学习错误方向。对一个足够小的函数同时计算三种梯度，可以在训练模型前隔离这类问题。

## 学习目标

1. 解释 forward、loss、backward、grad 的顺序。
2. 理解为什么训练需要标量 loss。
3. 用有限差分检查一个简单梯度。
4. 识别训练循环中 `zero_grad`、`backward`、`step` 的位置。

## 先修知识

需要知道函数导数和均方误差的基本概念。

## 核心模型

![Autograd 计算图和梯度检查](/assets/diagrams/deep-learning-autograd-backprop-gradient-check.svg)

输入和参数经过 forward 生成预测，预测与标签生成 loss，`backward()` 沿图反向累积梯度，optimizer 使用梯度更新参数。

## 先写出可验证的函数

本例有两条样本，预测与均方误差为：

```text
X = [[1, 2],       y = [1, 0]
     [3, 4]]

prediction = Xw
L(w) = mean((Xw - y)^2)
```

对权重求导：

```text
∂L/∂w = (2/n) Xᵀ(Xw-y)
```

当 `w=[0.2,-0.4]` 时，loss 为 `1.7800001`，解析梯度为 `[-4.6,-7.2]`。这是可以独立于框架手算的参照。

## 逐步实现

运行：

```bash
python -m dl_foundations.cli demo-autograd --output reports/autograd_demo.json
```

本次输出中，autograd 梯度、解析梯度和有限差分梯度几乎一致：

```text
autograd_grad = [-4.599999904632568, -7.199999809265137]
analytic_grad = [-4.599999904632568, -7.199999809265137]
finite_difference_grad = [-4.600048065185547, -7.199942588806152]
max_abs_error = 5.72e-05
```

有限差分的思想是把某个参数向正负方向各移动一点，观察 loss 的变化率。它速度慢，但适合检查小例子。

中心差分公式为：

```text
g_i ≈ [L(w + εe_i) - L(w - εe_i)] / (2ε)
```

其中 `e_i` 只在第 `i` 个位置为 1。中心差分比单边差分通常有更小的截断误差，但 `ε` 不能无限减小：太大时局部线性近似粗糙，太小时浮点舍入误差占主导。

完整的最小检查逻辑：

```python
eps = 1e-3
finite = []
for i in range(w.numel()):
    plus = w.detach().clone()
    minus = w.detach().clone()
    plus[i] += eps
    minus[i] -= eps
    finite.append((loss_for(plus) - loss_for(minus)) / (2 * eps))
```

本次最大绝对误差 `5.72e-05` 相对梯度量级约为 `1e-5`，与 float32 和 `1e-3` 步长相符。判断时应设置与 dtype、函数尺度匹配的容差，不能要求逐位相等。

## 训练循环中的梯度状态

典型顺序是：

```python
optimizer.zero_grad(set_to_none=True)
logits = model(batch_x)
loss = loss_fn(logits, batch_y)
loss.backward()
optimizer.step()
```

梯度默认会累积，所以每个 batch 前要清空旧梯度。`step()` 只根据当前梯度和优化器状态更新参数。

可以直接观察累积行为：

```python
loss_for(w).backward()
first = w.grad.clone()
loss_for(w).backward()
second = w.grad.clone()
print(torch.allclose(second, 2 * first))
```

预期输出 `True`。第二次 `backward()` 基于新的 forward 图，但会把结果加到已有 `.grad`；这解释了训练循环为什么每批先清梯度。梯度累积本身也可以有意使用，例如合并多个 micro-batch，但那需要显式设计。

## 三种梯度各自排查什么

| 方法 | 来源 | 主要价值 |
| --- | --- | --- |
| autograd | 框架计算图 | 实际训练将使用的梯度 |
| 解析公式 | 人工推导 | 检查问题建模和公式 |
| 有限差分 | loss 数值变化 | 独立检查实现局部一致性 |

三者一致能强力支持这个小函数的梯度实现；它不能自动证明完整训练代码、数据标签或评估指标都正确，因此 lab 还需要端到端 baseline 与 checkpoint 测试。

## 常见错误

1. **忘记清空梯度。** 多个 batch 的梯度会叠加，学习过程变得难解释。
2. **对非标量直接 backward。** 多输出需要指定梯度或先归约成 loss。
3. **在评估阶段保留梯度。** 评估可用 `torch.no_grad()` 减少不必要的图记录。
4. **把有限差分误差要求到零。** 浮点数和步长会带来微小误差。

## 练习或延伸

1. 把有限差分步长从 `1e-3` 改成 `1e-1` 和 `1e-5`，观察误差变化。
2. 删除 `zero_grad` 后训练几轮，观察 loss 是否异常。
3. 用 `torch.no_grad()` 包住评估函数，确认测试仍通过。

## 参考资料

- PyTorch 教程：[A Gentle Introduction to torch.autograd](https://docs.pytorch.org/tutorials/beginner/blitz/autograd_tutorial.html)
- PyTorch 教程：[Automatic Differentiation with torch.autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- PyTorch 文档：[torch.autograd](https://docs.pytorch.org/docs/stable/autograd.html)


{% endraw %}
