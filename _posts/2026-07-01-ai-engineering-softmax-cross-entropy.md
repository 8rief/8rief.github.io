---
layout: post
title: "分类模型输出什么：logits、softmax 和 cross entropy"
date: 2026-07-01 20:23:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从两个类别的 logits 出发，理解概率、损失和训练目标。"
tags: [deep-learning, loss, softmax, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / logits / loss
> 本文 lab 已验证：majority、linear、MLP 的 test accuracy 和 cross entropy loss 都写入 `reports/metrics.json`。

分类模型的最后一层通常输出 logits。logits 还不是概率，需要经过 softmax。训练时用 cross entropy 衡量模型给真实类别的概率有多低。这个损失函数把“分错了”和“信心不足”都转成一个可优化的数字。

## 学习目标

1. 区分 logits、probabilities 和 predicted label。
2. 实现稳定 softmax。
3. 解释 cross entropy 为什么能作为分类损失。
4. 把 loss 和 accuracy 同时记录到报告。

## 先修知识

需要知道概率在 0 到 1 之间，并且所有类别概率之和为 1。

## 核心模型

![分类模型输出什么：logits、softmax 和 cross entropy](/assets/diagrams/ai-engineering-softmax-cross-entropy.svg)

logits 是模型分数。softmax 把每行分数归一化成概率。cross entropy 取真实类别概率的负对数；真实类别概率越高，loss 越小。

## 可信资料的关键结论

- PyTorch quickstart 使用 loss function 和 optimizer 组织训练；本包用 NumPy 手写同一类核心计算。
- 分类任务常用 logits → softmax → cross entropy 的链路。
- 同时记录 loss 和 accuracy 能减少单一指标误导。

## 逐步实现

softmax 实现先减去每行最大值，避免指数过大：

```python
def softmax(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)
```

cross entropy：

```python
def cross_entropy(probs, y):
    eps = 1e-12
    return -np.log(probs[np.arange(len(y)), y] + eps).mean()
```

预测标签：

```python
pred = probs.argmax(axis=1)
```

报告中同时保存 loss 和 accuracy：

```json
"mlp": {
  "test": {
    "loss": 0.002,
    "accuracy": 1.000
  }
}
```

## 常见错误

1. **直接把 logits 当概率。** logits 可以是任意实数。
2. **softmax 前不做数值稳定处理。** 大 logits 可能导致溢出。
3. **只看 accuracy。** loss 能显示模型信心变化，训练时很重要。
4. **把 loss 越大越好。** 优化目标通常是让 loss 下降。

## 练习或延伸

1. 构造 logits `[2, 0]` 和 `[10, 0]`，比较 softmax 后真实类别概率。
2. 把 `eps` 去掉，思考概率为 0 时会发生什么。
3. 输出测试集中前 5 个样本的 logits、probabilities 和 predicted label。

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
