---
layout: post
title: "线性代数：从矩阵乘法到 logits"
date: 2026-06-25 22:02:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 XW+b 解释神经网络线性层、批量仿射变换和二分类 logits 的数据流。"
tags: [deep-learning, linear-algebra, logits, pytorch]
---
{% raw %}

> 主题：深度学习基础 / 线性代数 / logits
> 本文把后续线性 baseline 和 MLP 的第一层解释清楚。

神经网络里的线性层可以先看成批量矩阵乘法。输入矩阵 `X` 的每一行是一条样本，权重矩阵 `W` 的列对应输出通道，偏置 `b` 给每个输出通道一个平移。理解 `XW+b` 后，线性分类器和 MLP 的结构就有了共同语言。

## 学习目标

1. 写出 batch 输入和权重矩阵的 shape 关系。
2. 解释仿射层为什么输出 logits。
3. 区分 logits、概率和预测标签。
4. 看懂线性 baseline 在 XOR 数据上的能力边界。

## 先修知识

需要知道矩阵乘法的行列匹配规则，以及二分类任务中标签为 0 或 1。

## 核心模型

![矩阵乘法到 logits](/assets/diagrams/deep-learning-linear-algebra-logits.svg)

`X` 的形状是 `n × d`，`W` 的形状是 `d × 1`，`b` 是一个标量或长度为 1 的向量，输出 logits 是 `n` 个实数。二分类中，logit 经过 sigmoid 后才变成概率。

## 逐步实现

线性分类器的核心代码很短：

```python
class LinearClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(2, 1)

    def forward(self, x):
        return self.linear(x).squeeze(-1)
```

这里输入特征数为 2，因为合成数据是二维点。`nn.Linear(2, 1)` 内部维护一个 `1 × 2` 的权重和一个偏置。输出仍叫 logits，因为训练时会交给 `BCEWithLogitsLoss`，避免手动先做 sigmoid。

## logits 为什么直接进 loss

概率需要落在 0 到 1 之间，logits 可以是任意实数。很多 loss 函数把 sigmoid 和对数损失合在一起做，可以提高数值稳定性。写训练代码时，把 logits 交给对应 loss，把 sigmoid 放到评估和解释阶段。

## 与 baseline 的关系

线性 baseline 只能学习一条直线边界。XOR 风格数据要求两个对角区域同类，单条直线很难同时分开四个簇。这个限制让后续 MLP 对比有了清晰意义。

## 常见错误

1. **把 logits 当概率输出。** 打印 logits 可以调试模型，但阈值判断前要经过 sigmoid。
2. **矩阵维度顺序写反。** 检查 `batch × feature` 和 `feature × output` 是否匹配。
3. **直接比较不同数据集准确率。** baseline 和模型必须在同一数据划分上比较。
4. **忽略偏置项。** 没有偏置时，线性边界被限制通过原点。

## 练习或延伸

1. 把 `nn.Linear(2, 1)` 改成 `nn.Linear(2, 3)`，解释输出 shape。
2. 在训练后打印线性层权重和偏置，描述它代表哪条直线。
3. 用纸画出 XOR 四个中心点，说明单条直线为什么难以分开。

## 参考资料

- PyTorch 文档：[torch.nn](https://docs.pytorch.org/docs/stable/nn.html)
- PyTorch 文档：[torch.nn.Linear](https://docs.pytorch.org/docs/stable/generated/torch.nn.Linear.html)
- PyTorch 文档：[BCEWithLogitsLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html)


{% endraw %}
