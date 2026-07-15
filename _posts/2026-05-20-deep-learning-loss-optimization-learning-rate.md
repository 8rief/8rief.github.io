---
layout: post
title: "Loss 和优化：从 logits 到参数更新"
date: 2026-05-20 09:00:00 +0800
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

只看“调用 Adam”很难理解训练为何有效。一次参数更新可以拆成五个可观察状态：当前参数、forward 输出、标量 loss、每个参数的梯度、更新后的参数。任何一环异常，都会反映在 history 中。

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

## 一个 logit 怎样变成 loss

对单个二分类样本，标签 `y=1`、logit `z=2` 时，概率与损失为：

```python
import math

z, y = 2.0, 1.0
p = 1.0 / (1.0 + math.exp(-z))
loss = -(y * math.log(p) + (1-y) * math.log(1-p))
print(f"p={p:.4f}, loss={loss:.4f}")
```

```text
p=0.8808, loss=0.1269
```

若把 logit 改成 `-2`，模型仍面对正类样本，但正类概率降为约 `0.1192`，loss 上升到约 `2.1269`。交叉熵不仅判断标签是否正确，还会对“自信地分错”给出更大的惩罚。

实际训练使用 `BCEWithLogitsLoss`，它把 sigmoid 与二元交叉熵合并为数值更稳定的公式。输入应是任意实数 logits，标签应是同 shape 的浮点张量。

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

每行代码都改变了明确状态：

1. `zero_grad`：清除上一批次留在参数上的梯度；
2. `model(batch_x)`：根据当前参数构建 forward 计算图；
3. `loss_fn`：把一批预测归约成标量；
4. `backward`：沿图计算并累积梯度；
5. `step`：由优化器读取梯度并原地更新参数。

可以记录一个参数更新前后的差值，确认优化器确实生效：

```python
before = model.net[0].weight.detach().clone()
loss.backward()
optimizer.step()
delta = (model.net[0].weight.detach() - before).abs().max()
print(float(delta))
```

正常训练应得到大于 0 的有限值。若为 0，检查参数是否注册到 optimizer、梯度是否为 `None`、是否提前调用了 `no_grad`；若出现 `nan`，检查学习率、输入尺度和 loss。

## 学习率控制哪一步

SGD 的最小更新式是 `w <- w - lr × grad`。假设 `w=1.0`、梯度 `0.4`：

```text
lr=0.001 -> w=0.9996   步幅很小
lr=0.1   -> w=0.9600   合理移动
lr=10    -> w=-3.0000  可能跨过低点并震荡
```

Adam 还维护梯度的一阶、二阶动量，但学习率仍控制整体步幅。优化器类型变化后，旧学习率通常不能直接沿用。

## history 怎样使用

`reports/mlp/history.csv` 每行记录一个 epoch 的训练 loss、训练准确率、validation loss 和 validation 准确率。它回答的问题是：模型是否持续学习，validation 是否跟随改善，训练是否出现明显过拟合。

用命令查看表头、第一轮和最后一轮：

```bash
{ head -n 2 reports/mlp/history.csv; tail -n 1 reports/mlp/history.csv; }
```

应看到列 `epoch,train_loss,train_accuracy,val_loss,val_accuracy`，最后 epoch 为 240。本次最终 train/validation accuracy 都是 1.0，test accuracy 为 0.9896。这个结果说明固定合成任务已被小型 MLP 拟合；它没有证明相同训练配置适用于真实数据。

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
