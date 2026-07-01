---
layout: post
title: "张量先看 shape：NumPy 数组、矩阵乘法和 broadcasting"
date: 2026-07-01 20:22:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 `X @ W + b` 理解深度学习中最常见的 shape 和 broadcasting 问题。"
tags: [deep-learning, numpy, tensor, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / tensor / shape
> 本文 lab 已验证：输入特征 shape 为 `(600, 2)`，线性权重 shape 为 `(2, 2)`，MLP 隐层权重 shape 为 `(2, 24)`。

0 基础学习深度学习时，很多错误来自 shape 不匹配。`X @ W + b` 这行代码已经包含核心模型：一批样本、一个权重矩阵、一个偏置向量和一次 broadcasting。先把 shape 看清楚，后面的 softmax、反向传播和训练循环才有可解释的状态变化。

## 学习目标

1. 读懂二维数组的 shape。
2. 解释 `@` 矩阵乘法的输入输出维度。
3. 理解 bias broadcasting。
4. 用 shape 检查模型是否连接正确。

## 先修知识

需要知道矩阵可以看作二维表格，行表示样本，列表示特征。

## 核心模型

![张量先看 shape：NumPy 数组、矩阵乘法和 broadcasting](/assets/diagrams/ai-engineering-numpy-tensor-shape-broadcast.svg)

一批输入 `X` 的 shape 是 `(batch, features)`。权重 `W` 的 shape 是 `(features, outputs)`。矩阵乘法得到 `(batch, outputs)`。偏置 `b` 的 shape 是 `(outputs,)`，会广播到每一行。

## 可信资料的关键结论

- NumPy 的核心对象是 N 维数组，shape 描述每个维度的大小。
- `@` 运算符对应 NumPy 矩阵乘法，适合表达线性层。
- Broadcasting 让较小数组按规则扩展到兼容 shape，是 bias 加法的基础。

## 逐步实现

线性模型：

```python
logits = x @ W + b
```

在本 lab 中：

```text
x_train: (600, 2)
W:       (2, 2)
b:       (2,)
logits:  (600, 2)
```

MLP 多了一层隐层：

```python
hidden = np.tanh(x @ W1 + b1)
logits = hidden @ W2 + b2
```

对应 shape：

```text
W1:     (2, 24)
hidden: (600, 24)
W2:     (24, 2)
logits: (600, 2)
```

如果输出类别有 2 个，最后一维就是 2。每一行 logits 对应一个样本对两个类别的未归一化分数。

## 常见错误

1. **把样本数和特征数写反。** 训练数据常用 `(样本数, 特征数)`。
2. **没有检查 bias shape。** `b` 应能广播到 logits 的每一行。
3. **混用 `dot` 和 `@` 后不看结果 shape。** 教学中优先使用 `@` 表达矩阵乘法。
4. **看到报错只改代码到能运行。** 正确做法是先写出每一步期望 shape。

## 练习或延伸

1. 把 hidden size 从 24 改成 8，列出所有参数 shape。
2. 故意把 `W1` shape 改错，阅读 NumPy 报错。
3. 为每个 forward 函数加入 shape assert。

## 参考资料

- NumPy 文档：[NumPy: the absolute basics for beginners](https://numpy.org/doc/stable/user/absolute_beginners.html)
- NumPy 文档：[Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)
- NumPy 文档：[numpy.matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html)
- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)
- NumPy 文档：[numpy.savez](https://numpy.org/doc/stable/reference/generated/numpy.savez.html)
- PyTorch 教程：[Quickstart](https://pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html)
- PyTorch 教程：[Autograd](https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- PyTorch 教程：[Save and Load the Model](https://pytorch.org/tutorials/beginner/basics/saveloadrun_tutorial.html)

{% endraw %}
