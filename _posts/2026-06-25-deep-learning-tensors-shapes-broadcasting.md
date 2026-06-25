---
layout: post
title: "Tensor 形状：把 batch、dtype 和 broadcasting 讲清楚"
date: 2026-06-25 22:01:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 shape、dtype、batch 维和 broadcasting 出发，建立后续神经网络代码的基本数据模型。"
tags: [deep-learning, tensor, numpy, pytorch]
---
{% raw %}

> 主题：深度学习基础 / tensor / shape / broadcasting
> 本文对应 lab 的 `demo-tensors` 命令。

Tensor 是深度学习项目中最基本的数据容器。学习 tensor 的重点是能在每一步说清楚 shape、dtype、device 和 batch 维如何变化。只要 shape 解释清楚，线性层、loss 和训练循环会变得可调试。

## 学习目标

1. 区分标量、向量、矩阵和 batch tensor。
2. 解释 `dtype` 对数值计算的影响。
3. 读懂 broadcasting 在逐元素运算中的 shape 规则。
4. 用 batch-first 视角理解后续模型输入。

## 先修知识

需要知道 Python list 和二维表格的基本含义。NumPy 或 PyTorch 经验有帮助；没有经验也可以从本例开始。

## 核心模型

![Tensor 形状和 broadcasting](/assets/diagrams/deep-learning-tensors-shapes-broadcasting.svg)

把样本组织成 `batch × feature` 是最常见的入口。单个样本是一个特征向量，多条样本堆成矩阵，多批数据进入训练循环。

## 逐步实现

运行：

```bash
python -m dl_foundations.cli demo-tensors --output reports/tensor_demo.json
```

本次 lab 的输出记录了几个关键形状：

```text
x_shape = [3, 4]
broadcast_shape = [3, 4]
batch_shape = [2, 3, 4]
weights_shape = [4, 2]
logits_shape = [2, 3, 2]
```

`x` 是一个 `3 × 4` 的矩阵，`scale` 是长度为 4 的向量。逐元素相乘时，`scale` 会沿第一个维度扩展，结果仍是 `3 × 4`。批量矩阵乘法中，`batch` 的形状是 `2 × 3 × 4`，权重是 `4 × 2`，输出变成 `2 × 3 × 2`。

## 为什么 batch 维要放在前面

训练循环每次取一批样本。把 batch 放在第一个维度后，`DataLoader` 可以自然拼接样本，模型的 `forward` 也能同时处理多条输入。调试时先打印 `x.shape`，再检查最后一维是否等于特征数。

## 常见错误

1. **把样本数和特征数混在一起。** `n × d` 中 `n` 是样本数，`d` 是每个样本的特征数。
2. **忽略 dtype。** 分类标签常用整数或浮点形式，loss 函数对类型有要求。
3. **误用 broadcasting。** broadcasting 会让代码更短，也可能掩盖维度写错的问题。
4. **忘记 batch 维。** 单样本预测也常需要补成 `1 × d`。

## 练习或延伸

1. 把 demo 中的 `weights` 改成 `4 × 3`，预测 `logits_shape`。
2. 构造一个 `5 × 2` 的输入和 `2 × 1` 的权重，写出矩阵乘法结果 shape。
3. 在训练代码前打印第一批数据的 shape，确认 batch-first 约定。

## 参考资料

- PyTorch 文档：[torch.Tensor](https://docs.pytorch.org/docs/stable/tensors.html)
- PyTorch 文档：[Tensor attributes](https://docs.pytorch.org/docs/stable/tensor_attributes.html)
- NumPy 文档：[Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)


{% endraw %}
