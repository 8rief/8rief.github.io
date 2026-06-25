---
layout: post
title: "Autograd 和反向传播：用有限差分检查梯度"
date: 2026-06-25 22:03:00 +0800
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
