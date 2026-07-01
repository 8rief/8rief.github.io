---
layout: post
title: "AI 工程从问题和 baseline 开始：数据、切分和最小可比结果"
date: 2026-07-01 20:21:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用二维螺旋分类任务建立训练集、验证集、测试集、多数类 baseline 和线性 baseline。"
tags: [deep-learning, ai-engineering, baseline, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / problem framing / baseline
> 本文 lab 已验证：训练/验证/测试行数为 600/200/200，majority baseline test accuracy=0.520，linear baseline test accuracy=0.580。

AI 工程首先要回答一个具体问题：输入是什么，输出是什么，如何判断结果是否有用。直接训练神经网络会掩盖很多基本错误，所以本包从 toy 分类任务开始，先生成数据、切分数据，再建立多数类和线性模型两个 baseline。后续 MLP 的效果主张必须和这些 baseline 对比。

## 学习目标

1. 定义一个最小监督学习任务。
2. 建立训练集、验证集、测试集的职责分工。
3. 实现多数类 baseline 和线性 softmax baseline。
4. 理解模型效果必须和 baseline 对比。

## 先修知识

需要知道表格数据由行和列组成，分类任务的标签可以用 0/1 表示。

## 核心模型

![AI 工程从问题和 baseline 开始：数据、切分和最小可比结果](/assets/diagrams/ai-engineering-problem-data-baseline-split.svg)

AI 工程的第一条证据链是：问题定义 → 数据生成或采集 → 切分 → baseline → 新模型。baseline 给出可比较的最低标准，测试集只用于最终评估。

## 可信资料的关键结论

- NumPy 的数组和随机数生成器足够支持小型可复现实验。
- PyTorch 官方 quickstart 也从数据、模型、损失、优化和评估构成训练流程。
- baseline 是效果主张的边界；没有 baseline 的准确率很难解释。

## 逐步实现

lab 生成二维螺旋数据，每一行包含两个输入特征和一个标签：

```text
split,x0,x1,label
train,0.3548,-0.2191,0
...
```

运行：

```bash
bash run_lab.sh
```

关键输出：

```text
rows_train=600
rows_val=200
rows_test=200
majority_test_acc=0.520
linear_test_acc=0.580
```

多数类 baseline 只预测训练集中最多的类别。线性 baseline 使用 `x @ W + b` 得到 logits，再用 softmax 产生概率。这个任务的类别边界是弯曲的，线性模型只能给出有限结果。

## 常见错误

1. **直接汇报神经网络准确率。** 没有 baseline 就无法判断结果是否有意义。
2. **用测试集调参数。** 验证集用于选择和调参，测试集用于最后报告。
3. **只保存最终模型，不保存数据切分。** 复现实验需要知道模型看过哪些数据。
4. **把 toy 数据效果推广到真实场景。** 本包只训练工程流程和机制。

## 练习或延伸

1. 把训练集比例从 60% 改成 70%，观察 baseline 是否变化。
2. 把 majority baseline 换成随机预测，比较稳定性。
3. 给数据 CSV 增加 `row_id`，方便追踪错误样本。

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
