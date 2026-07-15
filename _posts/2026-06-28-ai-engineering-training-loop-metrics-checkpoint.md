---
layout: post
title: "训练循环是工程系统：seed、epoch、metrics 和 checkpoint"
date: 2026-06-28 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 MLP 训练拆成可复现 seed、训练循环、验证指标、CSV history 和 `.npz` checkpoint。"
tags: [deep-learning, training-loop, checkpoint, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / training loop / checkpoint
> 本文 lab 已验证：生成 `reports/mlp-history.csv`、`reports/training_curve.svg` 和 `models/mlp-weights.npz`。

深度学习工程不只是写一个模型类。训练循环要固定 seed，记录 epoch，区分训练和验证指标，保存模型权重，并能在报告里说明哪个模型最好。本包把这些内容写进 CSV、JSON、SVG 和 `.npz` checkpoint。

只保留最终权重时，无法判断训练是否曾经发散、何时收敛、validation 是否落后于 train；只保留 history 时，又无法重建推理。训练循环应同时产生“过程证据”和“可恢复状态”。

## 学习目标

1. 读懂一个完整训练循环。
2. 解释学习率、epoch 和验证集指标。
3. 保存训练历史和模型 checkpoint。
4. 用 SVG 曲线观察训练过程。

## 先修知识

建议先读 logits/loss 和 gradient check。

## 核心模型

![训练循环是工程系统：seed、epoch、metrics 和 checkpoint](/assets/diagrams/ai-engineering-training-loop-metrics-checkpoint.svg)

训练循环重复执行 forward、loss、backward、参数更新和指标记录。验证集不参与参数更新，只用来观察模型泛化趋势。checkpoint 保存可复用参数，history 保存训练过程证据。

## 一轮训练改变了哪些状态

本 lab 使用全批量梯度下降，每个 epoch 都用 600 条训练样本计算一次梯度：

```text
params(epoch t)
  -> forward(train)
  -> loss + gradients
  -> params(epoch t+1)
  -> evaluate(train, validation)
  -> append history when reaching a record point
```

validation 只进入 forward 和指标计算，不进入 `mlp_loss_and_grads`，因此不会改变参数。

## 可信资料的关键结论

- NumPy `default_rng(seed)` 是现代随机数生成入口，适合固定实验随机性。
- NumPy `savez` 可以把多个数组保存到一个 `.npz` 文件，适合小模型 checkpoint。
- PyTorch 保存模型时也强调保存/加载权重和推理前设置评估状态；本包用 NumPy 保存同样的最小必要状态。

## 逐步实现

训练循环：

```python
for epoch in range(1, epochs + 1):
    _, grads = mlp_loss_and_grads(params, train)
    for key in params:
        params[key] -= lr * grads[key]
    if epoch % 100 == 0:
        record_metrics()
```

初始学习率是 0.7，在 epoch 700 和 1200 各乘以 0.55。衰减发生在当轮参数更新之前：

```python
if epoch in {700, 1200}:
    lr *= 0.55
```

所以三个阶段的学习率分别为 `0.7`、`0.385` 和 `0.21175`。这个计划是该合成任务的教学配置，迁移到新数据后需要重新验证。

保存 history：

```text
reports/mlp-history.csv
reports/linear-history.csv
```

保存 checkpoint：

```python
np.savez(models / "mlp-weights.npz", **mlp_params, mean=mean, std=std)
```

lab 输出：

```text
chart_ready=reports/training_curve.svg
checkpoint_ready=models/mlp-weights.npz
```

history 给出的关键节点为：

```text
epoch    train_loss    train_acc    val_acc
1        0.7400        0.4867       0.520
100      0.0999        0.9867       0.985
200      0.0500        0.9983       1.000
1800     0.0097        1.0000       1.000
```

模型在 200 epoch 时 validation accuracy 已到 1.0，之后 loss 继续下降，表示正确类别概率仍在提高。教学脚本固定跑 1800 epoch 以得到稳定曲线；生产训练通常应根据 validation 目标设计 early stopping，并保存最佳 epoch。

## checkpoint 需要完整恢复推理

检查 `.npz` 内容：

```bash
python - <<'PY'
import numpy as np
with np.load("models/mlp-weights.npz") as ckpt:
    for key in ckpt.files:
        print(key, ckpt[key].shape)
PY
```

预期包含 `W1(2,24)`、`b1(24,)`、`W2(24,2)`、`b2(2,)`、`mean(2,)` 和 `std(2,)`。后两项属于输入变换状态；缺少它们，即使权重正确，原始坐标也无法按训练条件进入模型。

## 常见错误

1. **只保存最后一行准确率。** 没有 history 就无法解释训练过程。
2. **每次运行 seed 不固定。** 教学和调试阶段应优先可复现。
3. **把验证集用于梯度更新。** 验证集用于选择和观察，不参与训练。
4. **只保存权重，不保存 normalization 参数。** 推理时必须用训练集的 mean/std。

## 练习或延伸

1. 把 MLP epoch 从 1800 改成 600，观察曲线和测试准确率。
2. 把 hidden size 从 24 改成 12，比较 history。
3. 加载 `.npz` 后手动对一个点推理。

## 参考资料

- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)
- NumPy 文档：[numpy.savez](https://numpy.org/doc/stable/reference/generated/numpy.savez.html)
- PyTorch 教程：[Optimizing Model Parameters](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)
- PyTorch 教程：[Saving and Loading Models](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)

{% endraw %}
