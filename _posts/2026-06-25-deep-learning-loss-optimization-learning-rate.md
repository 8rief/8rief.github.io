---
layout: post
title: "Loss 和优化：从 logits 到参数更新"
date: 2026-06-25 22:05:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "解释 BCEWithLogitsLoss、反向传播、Adam/SGD 和学习率在训练循环中的位置。"
tags: [deep-learning, loss, optimization, adam, sgd]
---
{% raw %}

> 主题：深度学习基础 / loss / optimizer / learning rate
> 本文解释 lab 中线性模型和 MLP 的训练循环。

训练的直接目标是降低 loss。二分类模型输出 logits，loss 函数把 logits 和标签变成一个标量，autograd 计算梯度，optimizer 根据梯度更新参数。学习率控制每次更新的步幅，过大容易震荡，过小会让训练很慢。

## 学习目标

1. 说明 logits、loss 和梯度之间的关系。
2. 解释 `BCEWithLogitsLoss` 的使用位置。
3. 区分 SGD 和 Adam 的基本作用。
4. 通过 history 文件观察训练过程。

## 先修知识

需要理解二分类标签、sigmoid 和梯度下降的直观含义。

## 核心模型

![Loss 和优化循环](/assets/diagrams/deep-learning-loss-optimization-learning-rate.svg)

每个 batch 都经历同一条路径：forward 产生 logits，loss 对比标签，backward 得到梯度，optimizer 更新参数。

## 逐步实现

训练命令如下：

```bash
python -m dl_foundations.cli train --model mlp --output-dir reports/mlp --epochs 240 --learning-rate 0.03
```

训练函数中的核心片段：

```python
optimizer.zero_grad(set_to_none=True)
logits = model(batch_x)
loss = loss_fn(logits, batch_y)
loss.backward()
optimizer.step()
```

本 lab 使用 `BCEWithLogitsLoss`，因为模型直接输出二分类 logits。优化器使用 Adam，适合教学中快速收敛。若换成 SGD，通常需要重新选择学习率和 epoch 数。

## history 怎样使用

`reports/mlp/history.csv` 每行记录一个 epoch 的训练 loss、训练准确率、validation loss 和 validation 准确率。它回答的问题是：模型是否持续学习，validation 是否跟随改善，训练是否出现明显过拟合。

## 常见错误

1. **先 sigmoid 再用 logits loss。** `BCEWithLogitsLoss` 已经包含稳定的 sigmoid 处理。
2. **学习率只凭感觉。** 改学习率后要看 loss 曲线和 validation 指标。
3. **只保存最后数字。** 没有 history 时，很难判断训练是否稳定。
4. **不同模型使用不同数据划分。** 优化效果比较必须保持数据一致。

## 练习或延伸

1. 把学习率改成 `0.003`，比较收敛速度。
2. 把优化器改成 SGD，记录需要多少 epoch 才接近当前 MLP 准确率。
3. 从 history 中找出 validation loss 第一次低于 `0.1` 的 epoch。

## 参考资料

- PyTorch 文档：[torch.optim](https://docs.pytorch.org/docs/stable/optim.html)
- PyTorch 文档：[Adam](https://docs.pytorch.org/docs/stable/generated/torch.optim.Adam.html)
- PyTorch 文档：[SGD](https://docs.pytorch.org/docs/stable/generated/torch.optim.SGD.html)
- PyTorch 教程：[Optimizing Model Parameters](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)


{% endraw %}
