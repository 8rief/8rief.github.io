---
layout: post
title: "概率统计基础：数据划分、噪声和指标怎样影响结论"
date: 2026-06-25 22:04:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用合成数据说明随机种子、类别比例、train/val/test 划分和准确率解释边界。"
tags: [deep-learning, statistics, dataset, metrics]
---
{% raw %}

> 主题：深度学习基础 / 数据划分 / 统计指标
> 本文对应 lab 的 `data-summary` 和 `comparison` 输出。

模型训练前先要定义数据。数据的随机生成、类别比例、噪声大小和划分方式会直接影响最终指标。教学实验可以使用合成数据，但必须把数据分布和结论边界写清楚。

## 学习目标

1. 解释 train、validation、test 三个划分的作用。
2. 理解类别比例对 majority baseline 的影响。
3. 说明随机种子和噪声为什么要记录。
4. 用准确率解释二分类结果，同时知道它的限制。

## 先修知识

需要知道随机抽样、均值和比例的基本含义。

## 核心模型

![数据划分和指标解释](/assets/diagrams/deep-learning-probability-data-split-metrics.svg)

固定 seed 生成数据，shuffle 后切成 train、validation 和 test。训练只看 train，调参观察 validation，最终报告 test。

## 逐步实现

运行：

```bash
python -m dl_foundations.cli data-summary --output reports/data_summary.json
```

本 lab 的划分摘要为：

```text
train = 288 examples, positive_rate = 0.500
val   = 96 examples, positive_rate = 0.427
test  = 96 examples, positive_rate = 0.573
```

测试集正类比例约为 0.573，所以多数类 baseline 的准确率为 57.3%。这说明 baseline 的数值来自数据分布本身，不能随意填写。

## 为什么要保留 validation

训练集用于更新参数，validation 用于观察训练是否有效，test 用于最后报告。即使是小型教学实验，也应避免一边看 test 一边反复调整模型，否则 test 指标会变成调参过程的一部分。

## 常见错误

1. **只报告训练集准确率。** 训练集表现不能代表泛化能力。
2. **忽略类别比例。** 在类别不均衡时，准确率可能被多数类掩盖。
3. **不记录 seed。** 复跑时样本位置变化，结果难以对照。
4. **把合成数据结论外推。** 合成数据适合解释机制，真实任务还需要真实数据评估。

## 练习或延伸

1. 把 `noise` 从 `0.32` 改成 `0.50`，比较 MLP 准确率。
2. 把数据划分改成 70/15/15，观察 test 正类比例是否变化。
3. 增加 precision 和 recall 指标，说明它们在类别不均衡时的价值。

## 参考资料

- PyTorch 文档：[torch.utils.data](https://docs.pytorch.org/docs/stable/data.html)
- NumPy 文档：[Random sampling](https://numpy.org/doc/stable/reference/random/index.html)
- PyTorch 文档：[Reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html)


{% endraw %}
