---
layout: post
title: "结课项目：从 baseline 到 NumPy MLP 的可复现 AI 工程包"
date: 2026-07-01 20:28:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把数据、baseline、MLP、梯度检查、训练曲线、checkpoint、model card 和 transcript 合成一个可复现小项目。"
tags: [deep-learning, ai-engineering, capstone, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / capstone / reproducible package
> 本文 lab 已验证：一条命令生成数据集、baseline 对比、MLP checkpoint、训练曲线、model card、报告和 transcript。

这个结课项目完成一个 CPU-only 的 AI 工程闭环：固定 seed 生成数据，切分训练/验证/测试集，训练 majority 和 linear baseline，训练 NumPy MLP，做 gradient check，保存 metrics、history、SVG 曲线、checkpoint、model card 和 transcript。项目不追求真实任务效果，重点是让学习者掌握可复现实验和效果声明的工程边界。

## 学习目标

1. 从空目录运行一个可复现 AI 工程 lab。
2. 用 baseline 约束 MLP 效果主张。
3. 解释每个报告产物的作用。
4. 知道下一步如何迁移到 PyTorch 和真实数据。

## 先修知识

建议按顺序读完本包前七篇。需要 Python、NumPy 和基本终端能力。

## 核心模型

![结课项目：从 baseline 到 NumPy MLP 的可复现 AI 工程包](/assets/diagrams/ai-engineering-capstone-numpy-mlp-release.svg)

项目证据链是：数据生成 → 切分/标准化 → baseline → MLP → gradient check → training history → test metrics → checkpoint → model card → transcript。每一步都有可见文件或可断言指标。

## 可信资料的关键结论

- NumPy 提供数组、广播、矩阵乘法、随机数和数组保存能力，足以实现小型 from-scratch lab。
- PyTorch 官方教程中的 Dataset/DataLoader、autograd、optimizer、checkpoint 是后续工程化迁移方向。
- 可复现 AI 工程交付需要 baseline、数据切分、固定 seed、训练历史、测试指标、checkpoint、模型说明和限制。

## 逐步实现

运行完整 lab：

```bash
bash run_lab.sh
```

核心输出：

```text
rows_train=600
rows_val=200
rows_test=200
majority_test_acc=0.520
linear_test_acc=0.580
mlp_test_acc=1.000
mlp_minus_linear_test_acc=0.420
gradient_max_relative_error=3.00e-12
deep_learning_ai_status=ok
```

项目结构：

```text
deep-learning-ai-engineering/
  scripts/train.py
  scripts/test_train.py
  data/train.csv
  data/val.csv
  data/test.csv
  reports/metrics.json
  reports/linear-history.csv
  reports/mlp-history.csv
  reports/training_curve.svg
  reports/report.md
  reports/transcript.txt
  models/mlp-weights.npz
  models/model-card.md
```

可展示产物：

```text
reports/report.md
reports/training_curve.svg
models/model-card.md
```

可审计产物：

```text
reports/metrics.json
reports/transcript.txt
reports/*-history.csv
data/*.csv
models/mlp-weights.npz
```

本包的效果主张只限于合成螺旋数据：MLP 在测试集上比线性 baseline 高 0.420 accuracy。

## 常见错误

1. **训练出高分就结束。** 工程交付还需要 checkpoint、报告、模型边界和复现命令。
2. **只保留图，不保留原始 metrics。** 图应由可审计数据生成。
3. **用真实业务词包装 toy 任务。** toy lab 用于学习流程，不用于业务判断。
4. **跳过 baseline。** 深度学习模型必须和简单方法比较。

## 练习或延伸

1. 把 NumPy MLP 改写成 PyTorch `nn.Module`，保持同一数据切分和指标。
2. 增加 early stopping，并记录最佳验证集 epoch。
3. 把训练曲线扩展为 loss 和 accuracy 两张图。
4. 为 checkpoint 加入 SHA256，写入 model card。

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
