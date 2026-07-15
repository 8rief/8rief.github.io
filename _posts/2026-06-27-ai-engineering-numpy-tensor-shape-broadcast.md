---
layout: post
title: "张量先看 shape：NumPy 数组、矩阵乘法和 broadcasting"
date: 2026-06-27 09:00:00 +0800
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

如果只靠修改 `reshape` 让报错消失，程序可能把特征轴与样本轴混淆，最后得到 shape 合法、语义错误的结果。更稳的方法是在每个运算旁写下轴含义，再用断言固定接口。

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

## 用三条样本手算一次

```python
import numpy as np

x = np.array([[1., 2.], [3., 4.], [-1., 1.]])  # (3, 2)
w = np.array([[0.5, -0.5], [1.0, 2.0]])         # (2, 2)
b = np.array([0.1, -0.2])                       # (2,)
logits = x @ w + b
print(logits)
print(logits.shape)
```

预期输出：

```text
[[ 2.6  3.3]
 [ 5.6  6.3]
 [ 0.6  2.3]]
(3, 2)
```

第一行第一列为 `1×0.5 + 2×1.0 + 0.1 = 2.6`。`b[0]` 被加到每一行的第 0 类分数，`b[1]` 被加到每一行的第 1 类分数。

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

建议在 forward 入口加入契约：

```python
def linear_logits(params, x):
    assert x.ndim == 2 and x.shape[1] == 2
    assert params["W"].shape == (2, 2)
    assert params["b"].shape == (2,)
    out = x @ params["W"] + params["b"]
    assert out.shape == (len(x), 2)
    return out
```

断言把“两个特征、两个类别”的设计假设变成可执行检查，错误会在最靠近来源的位置暴露。

## Broadcasting 为什么成立

NumPy 从最右侧轴开始比较；长度相同或某一侧为 1 时可广播：

```text
(600, 2) +    (2,) -> (600, 2)  按类别加偏置
(600, 2) + (600,1) -> (600, 2)  每个样本加一个值
(600, 2) +  (600,) -> ValueError 最右轴 2 与 600 冲突
```

前两种 shape 都合法，却表达不同含义。调试时应检查被扩展的轴是否正是预期轴，而不能只以“程序能运行”为准。

参数规模也能由 shape 计算：`W1(2×24)+b1(24)+W2(24×2)+b2(2)=122` 个标量。这个数可用于检查 checkpoint 是否缺少数组或 hidden size 是否与代码一致。

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
- NumPy 文档：[ndarray.shape](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.shape.html)
- NumPy 文档：[Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)
- NumPy 文档：[numpy.matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html)

{% endraw %}
