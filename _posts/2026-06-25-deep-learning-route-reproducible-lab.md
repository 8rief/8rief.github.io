---
layout: post
title: "深度学习路线：先把可复现实验跑起来"
date: 2026-06-25 22:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个有限的 PyTorch 教学 lab 建立深度学习学习路线：数值计算、数据、baseline、训练、评估和证据。"
tags: [deep-learning, pytorch, reproducibility, lab]
---
{% raw %}

> 主题：深度学习基础 / 可复现实验 / PyTorch 项目
> 配套 lab：`deep-learning-foundations-pytorch`，唯一入口为 `./run_lab.sh`。

深度学习入门容易直接跳到模型名字。更稳的路线是先把一次小实验拆清楚：数据从哪里来，张量形状如何流动，loss 怎样产生梯度，baseline 怎样定义，模型效果用什么指标判断，checkpoint 和日志如何证明结果可复跑。本文给出整个包的主线，后续文章逐步展开。

## 学习目标

1. 解释深度学习项目中数据、模型、训练、评估和证据的关系。
2. 复跑一个本地 PyTorch lab，并知道每个报告文件的作用。
3. 在看到模型准确率时主动检查 baseline 和实验边界。
4. 建立后续学习 tensor、线性代数、autograd、优化和工程结构的顺序。

## 先修知识

需要会运行 Python 虚拟环境和命令行。暂时只需要知道数组、函数和文件路径的基本概念。

## 核心模型

![深度学习可复现实验路线](/assets/diagrams/deep-learning-route-reproducible-lab.svg)

一次可复现实验有六个稳定状态：环境、数据、baseline、模型、训练记录、评估证据。模型名称只处在链条中间，前后的边界决定结论是否可信。

## 逐步实现

进入 lab 后运行唯一入口：

```bash
./run_lab.sh
```

脚本会创建虚拟环境，安装 NumPy、PyTorch 和 pytest，随后执行测试、张量 demo、autograd demo、三组模型评估和 checkpoint 加载检查。关键输出类似：

```text
4 passed
majority_test_accuracy = 57.3%
linear_test_accuracy   = 49.0%
mlp_test_accuracy      = 99.0%
```

这些数字来自同一个合成 XOR 风格数据集。多数类 baseline 给出最朴素参考，线性分类器说明单条直线的能力边界，MLP 展示非线性层带来的改进。

## 报告文件怎样读

- `reports/environment.json`：Python、NumPy、PyTorch 版本，以及本 lab 使用 CPU 张量的说明。
- `reports/tensor_demo.json`：shape、dtype、broadcasting 和 batch matrix multiplication 的最小例子。
- `reports/autograd_demo.json`：autograd 梯度、解析梯度和有限差分梯度。
- `reports/majority/metrics.json`：多数类 baseline。
- `reports/linear/metrics.json`：线性 baseline。
- `reports/mlp/metrics.json`：小型 MLP 的训练结果。
- `reports/comparison.json`：把 baseline 和 MLP 放到同一张对照表中。

## 常见错误

1. **先背模型名。** 学习路线应先保证数据、loss、梯度和评估能解释。
2. **只看最终准确率。** 没有 baseline 的准确率缺少参照。
3. **忽略随机种子。** 训练结果要能复跑，至少要记录 seed、版本和数据划分。
4. **把教学实验当真实任务结论。** 本包的 XOR 数据集用于解释机制，不能外推到真实业务数据。

## 练习或延伸

1. 打开 `reports/comparison.json`，用一句话解释三组准确率分别回答了什么问题。
2. 把 `run_lab.sh` 中 MLP 的 epoch 减半，观察准确率和 history 的变化。
3. 在 README 中补一段实验边界，说明数据集、设备和结论范围。

## 参考资料

- PyTorch 文档：[torch.Tensor](https://docs.pytorch.org/docs/stable/tensors.html)
- PyTorch 教程：[Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)
- NumPy 文档：[NumPy absolute basics](https://numpy.org/doc/stable/user/absolute_beginners.html)
- PyTorch 文档：[Reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html)


{% endraw %}
