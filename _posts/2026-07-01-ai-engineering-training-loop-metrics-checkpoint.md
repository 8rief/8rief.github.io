---
layout: post
title: "训练循环是工程系统：seed、epoch、metrics 和 checkpoint"
date: 2026-07-01 20:25:00 +0800
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

- NumPy 文档：[NumPy: the absolute basics for beginners](https://numpy.org/doc/stable/user/absolute_beginners.html)
- NumPy 文档：[Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)
- NumPy 文档：[numpy.matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html)
- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)
- NumPy 文档：[numpy.savez](https://numpy.org/doc/stable/reference/generated/numpy.savez.html)
- PyTorch 教程：[Quickstart](https://pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html)
- PyTorch 教程：[Autograd](https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- PyTorch 教程：[Save and Load the Model](https://pytorch.org/tutorials/beginner/basics/saveloadrun_tutorial.html)

{% endraw %}
