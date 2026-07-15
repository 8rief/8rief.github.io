---
layout: post
title: "分类模型输出什么：logits、softmax 和 cross entropy"
date: 2026-06-27 18:00:00 +0800
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

只看 `argmax` 会丢失模型信心：logits `[2,0]` 与 `[20,0]` 都预测类别 0，但后者给类别 0 的概率更接近 1。训练需要连续、可导的 loss 来区分这两种状态。

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

## 从两个 logits 手算 softmax

对 logits `[2,0]`：

```text
exp(2)=7.389, exp(0)=1
P(class 0)=7.389/(7.389+1)=0.8808
P(class 1)=1/(7.389+1)=0.1192
```

如果真实标签为 0，交叉熵为 `-log(0.8808)=0.1269`；若真实标签为 1，损失变成 `-log(0.1192)=2.1269`。模型越确信错误类别，惩罚越大。

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

减去同一个常数不会改变概率比例，因为分子分母都乘以相同因子。它能把每行最大 logit 移到 0，使最大的指数为 1：

```python
logits = np.array([[1000.0, 999.0]])
print(softmax(logits))
```

```text
[[0.73105858 0.26894142]]
```

如果直接计算 `np.exp(1000)`，float64 会溢出并产生无效概率。

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
    "loss": 0.015074452443810244,
    "accuracy": 1.000
  }
}
```

本次 MLP 在 200 个测试样本上全预测正确，准确率为 1.0；loss 仍大于 0，因为正确类别概率没有全部精确等于 1。线性模型测试准确率为 0.58、loss 为 0.5395。accuracy 观察离散决策，loss 观察正确类别概率，两者提供互补信息。

## 反向传播真正需要哪一项

softmax 与交叉熵组合后，对每条样本 logits 的梯度可化简为：

```text
dL/dlogits = (probabilities - one_hot(labels)) / batch_size
```

这正是 NumPy lab 中的 `diff`。预测概率与 one-hot 标签越接近，梯度越小；错误类别概率越高，对应的正梯度越大，梯度下降会压低该 logit。

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

- SciPy 文档：[scipy.special.softmax](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.softmax.html)
- NumPy 文档：[Exponents and logarithms](https://numpy.org/doc/stable/reference/routines.math.html#exponents-and-logarithms)
- PyTorch 文档：[CrossEntropyLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html)
- PyTorch 教程：[Loss Function](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html#loss-function)

{% endraw %}
