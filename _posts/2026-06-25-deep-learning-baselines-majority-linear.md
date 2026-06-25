---
layout: post
title: "Baseline：多数类和线性分类器为什么必须先跑"
date: 2026-06-25 22:06:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 majority baseline 和 linear baseline 建立模型效果参照，再解释 MLP 改进的证据范围。"
tags: [deep-learning, baseline, evaluation, classifier]
---
{% raw %}

> 主题：深度学习基础 / baseline / 模型对照
> 本文直接使用 lab 的三组 test 指标。

深度学习实验需要 baseline。多数类 baseline 回答数据分布本身能得到多少准确率，线性 baseline 回答简单模型在同一特征上能做到什么程度。只有先跑这些对照，MLP 的提升才有解释对象。

## 学习目标

1. 解释 majority baseline 和 linear baseline 的不同含义。
2. 判断一个模型效果主张是否有可比参照。
3. 用同一 test split 比较三组结果。
4. 写出教学实验和真实 benchmark 的边界。

## 先修知识

需要理解二分类准确率，以及线性分类器只能形成一条直线边界。

## 核心模型

![Baseline 对照关系](/assets/diagrams/deep-learning-baselines-majority-linear.svg)

baseline 是必要参照，它们分别排除两种误解：数据类别比例已经很容易、简单线性模型已经足够。

## 逐步实现

三组指标来自同一次 lab：

```text
majority baseline: 57.3%
linear baseline:   49.0%
MLP:               99.0%
MLP - linear:      50.0%
```

多数类 baseline 约为 57.3%，因为 test split 中正类略多。线性 baseline 约为 49.0%，说明单条直线难以处理 XOR 风格结构。MLP 达到 99.0%，提升来自非线性隐藏层对四个簇的组合表达能力。

## 什么时候 baseline 还不够

当前 baseline 足够支撑教学结论：非线性 toy 数据上，MLP 比线性模型更适合。它不支撑真实数据、复杂模型或部署性能的结论。如果文章声称模型在真实任务上有效，就需要真实数据集、更多指标、重复实验和更强 baseline。

## 常见错误

1. **只比较 MLP 和空白结果。** 没有 baseline 时提升幅度缺少意义。
2. **让 baseline 使用更少信息。** 公平对照应使用同一数据划分和同一输入特征。
3. **只用训练集比较。** baseline 和 MLP 都必须在 test split 上报告。
4. **把教学提升写成通用优势。** 本文只说明这个合成任务中的可复现实验结果。

## 练习或延伸

1. 增加一个二层但没有 ReLU 的模型，预测它会接近哪个 baseline。
2. 把 MLP hidden_dim 改成 4、8、32，记录 test accuracy。
3. 写一段实验边界，说明这组 baseline 不能回答哪些问题。

## 参考资料

- PyTorch 教程：[Training with PyTorch](https://docs.pytorch.org/tutorials/beginner/introyt/trainingyt.html)
- PyTorch 文档：[torch.nn](https://docs.pytorch.org/docs/stable/nn.html)
- PyTorch 教程：[Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)


{% endraw %}
