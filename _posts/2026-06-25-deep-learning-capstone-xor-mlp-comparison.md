---
layout: post
title: "结课项目：从 XOR baseline 到 MLP 对比"
date: 2026-06-25 22:09:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "收束深度学习基础包：用合成 XOR 数据、majority/linear baseline 和 MLP 形成可复现实验报告。"
tags: [deep-learning, mlp, baseline, capstone, pytorch]
---
{% raw %}

> 主题：深度学习基础 / 结课项目 / baseline 对比
> 本文收束本包的可复现实验。

结课项目的目标是把基础概念连成一个能运行、能测试、能解释边界的小实验。数据是二维 XOR 风格合成点，模型包含多数类 baseline、线性 baseline 和小型 MLP。最终报告只主张这个本地合成任务中的对比结果。

## 学习目标

1. 复述从数据生成到模型对比的完整链条。
2. 用 baseline 解释 MLP 提升的含义。
3. 检查 reports 中的关键证据文件。
4. 给一个教学项目写出验收清单。

## 先修知识

需要理解前九篇中的 tensor、线性层、autograd、数据划分、loss、baseline 和 checkpoint。

## 核心模型

![XOR baseline 到 MLP 对比](/assets/diagrams/deep-learning-capstone-xor-mlp-comparison.svg)

XOR 风格数据让线性边界受限，MLP 的隐藏层提供非线性组合能力。对比成立的前提是三组方法使用同一数据生成、同一划分和同一 test split。

## 逐步实现

完整命令仍然是：

```bash
./run_lab.sh
```

验收时重点看三类文件：

```text
reports/transcript.txt
reports/comparison.json
reports/mlp/checkpoint.pt
```

本次复跑结果：

| 方法 | test accuracy | 解释 |
| --- | ---: | --- |
| majority baseline | 57.3% | 只利用测试集类别比例形成参照 |
| linear baseline | 49.0% | 单条线性边界难以处理 XOR 结构 |
| MLP | 99.0% | 隐藏层和 ReLU 提供非线性表达 |

`comparison.json` 还写明了边界：这是合成 XOR 风格数据上的教学 baseline 对比，不能当作现实任务 benchmark。

## 项目验收清单

- 环境版本已记录：Python、NumPy、PyTorch。
- 数据生成固定 seed，train/validation/test 划分可复跑。
- tensor demo 能解释 shape、dtype 和 broadcasting。
- autograd demo 通过有限差分检查。
- majority 和 linear baseline 已报告。
- MLP 指标与 baseline 放在同一张对照表。
- checkpoint 加载后准确率一致。
- pytest 覆盖数据、梯度、baseline 对比和 checkpoint。

## 常见错误

1. **把 MLP 成功归因过大。** 本实验只证明它适合这个非线性 toy 数据。
2. **省略 baseline。** 没有 majority 和 linear baseline，MLP 准确率缺少参照。
3. **只交 notebook。** 结课项目需要脚本、测试、报告和可复跑入口。
4. **不保存 transcript。** transcript 是读者复核命令顺序和输出的入口。

## 练习或延伸

1. 把数据改成线性可分的两簇，观察 linear baseline 是否接近 MLP。
2. 增加一个没有隐藏层的模型，说明它和线性 baseline 的关系。
3. 给 README 增加一节“如何解释结果”，用自己的话描述表格中的三行。

## 参考资料

- PyTorch 教程：[Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)
- PyTorch 教程：[Training with PyTorch](https://docs.pytorch.org/tutorials/beginner/introyt/trainingyt.html)
- PyTorch 教程：[Saving and Loading Models](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)


{% endraw %}
