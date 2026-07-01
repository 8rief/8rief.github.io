---
layout: post
title: "评估不止准确率：confusion matrix、错误样本和边界解释"
date: 2026-07-01 20:26:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用测试集 loss、accuracy、TP/TN/FP/FN 和错误分析约束模型效果主张。"
tags: [deep-learning, evaluation, metrics, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / evaluation / error analysis
> 本文 lab 已验证：`reports/metrics.json` 保存 MLP 和 baseline 的 test loss、accuracy、TP/TN/FP/FN。

模型训练完成后，评估要回答两个问题：总体表现如何，错误集中在哪里。accuracy 是最直观的指标，但它无法说明哪类错误多。confusion matrix 把预测和真实标签的组合拆开，能帮助发现偏向、边界和数据问题。

## 学习目标

1. 读取测试集 loss 和 accuracy。
2. 理解 TP、TN、FP、FN。
3. 把 MLP 与 baseline 放在同一张表里比较。
4. 知道 toy 结果的外推边界。

## 先修知识

需要知道二分类有正类和负类。

## 核心模型

![评估不止准确率：confusion matrix、错误样本和边界解释](/assets/diagrams/ai-engineering-evaluation-error-analysis.svg)

评估阶段冻结模型参数，只在测试集上做 forward。预测标签与真实标签组合成 confusion matrix。指标解释必须绑定数据来源和任务边界。

## 可信资料的关键结论

- PyTorch quickstart 评估阶段会关闭训练行为并计算测试准确率；本包用 NumPy 显式实现评估。
- 分类评估应把模型输出、真实标签和错误类型对应起来。
- 模型效果声明必须说明数据集、切分、baseline 和限制。

## 逐步实现

评估函数：

```python
pred = probs.argmax(axis=1)
tp = ((pred == 1) & (y == 1)).sum()
tn = ((pred == 0) & (y == 0)).sum()
fp = ((pred == 1) & (y == 0)).sum()
fn = ((pred == 0) & (y == 1)).sum()
```

本次测试集结果：

```text
majority_test_acc=0.520
linear_test_acc=0.580
mlp_test_acc=1.000
mlp_minus_linear_test_acc=0.420
```

这说明 MLP 在这个非线性 toy 边界上明显优于线性 baseline。这个结论只覆盖本 lab 的合成螺旋数据。

## 常见错误

1. **只给一个高准确率。** 还需要 baseline、数据来源和限制。
2. **把验证集结果当最终测试结果。** 测试集应保留到最后报告。
3. **忽略错误类型。** 不同错误的业务代价可能完全不同。
4. **把 toy 数据 100% 准确率写成通用模型能力。** toy lab 的价值是工程流程。

## 练习或延伸

1. 打印所有 FP/FN 样本的坐标。
2. 把数据 noise 增大，观察 confusion matrix 变化。
3. 增加 precision/recall，并解释它们适合什么任务。

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
