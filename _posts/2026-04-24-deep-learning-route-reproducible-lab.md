---
layout: post
title: "深度学习路线：先把可复现实验跑起来"
date: 2026-04-24 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个有限的 PyTorch 教学 lab 建立深度学习学习路线：数值计算、数据、baseline、训练、评估和证据。"
tags: [deep-learning, pytorch, reproducibility, lab]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/deep-learning-foundations-pytorch/README.md`](/assets/labs/deep-learning-foundations-pytorch/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：深度学习基础 / 可复现实验 / PyTorch 项目
> 配套 lab：`deep-learning-foundations-pytorch`，唯一入口为 `./run_lab.sh`。

深度学习入门容易直接跳到模型名字。更稳的路线是先把一次小实验拆清楚：数据从哪里来，张量形状如何流动，loss 怎样产生梯度，baseline 怎样定义，模型效果用什么指标判断，checkpoint 和日志如何证明结果可复跑。本文给出整个包的主线，后续文章逐步展开。

这条路线从一个实际问题出发：当终端打印 `accuracy=0.99` 时，你能否说明数字怎样产生、比什么更好、复跑时会生成哪些证据？如果这些问题答不上来，继续堆叠更大的模型只会扩大调试范围。

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

## 为什么先做一个小闭环

教学 lab 刻意使用二维合成数据和 CPU 训练，使一次复跑的成本足够低。学习者可以观察每个中间状态：

```text
固定依赖
  ↓
生成并切分 480 个样本
  ↓
检查 tensor / autograd
  ↓
训练 majority、linear、MLP
  ↓
保存 history / metrics / checkpoint
  ↓
重新加载并比较结果
```

这条链路先建立实验方法，再迁移到真实数据和更大框架。合成数据不提供现实任务证据，但非常适合制造可解释的线性与非线性差异。

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

首次运行需要下载固定版本依赖；后续复跑复用 `.venv`。成功结束时还会打印：

```text
4 passed
test_accuracy_after_load = 0.9895833134651184
claim_boundary = Synthetic local XOR-style dataset...
```

如果脚本在安装阶段失败，先检查 Python 版本和网络；如果测试失败，不要继续引用旧报告；如果训练完成但加载结果不同，检查 checkpoint、模型结构和数据 seed。

## 用三个问题阅读结果

1. **结果是否超过简单参照？** MLP 的 99.0% 高于多数类 57.3% 和线性模型 49.0%。
2. **差异是否符合任务结构？** XOR 的对角同类结构无法由单条直线完整分开，ReLU 隐层可以组合多个线性区域。
3. **结论覆盖到哪里？** 只覆盖固定 seed 的本地合成数据；没有外部数据、多个随机种子或生产延迟测量。

可直接读取最终对照：

```bash
python -m json.tool reports/comparison.json
```

报告中的 `mlp_minus_linear_accuracy` 应约为 `0.5`，并且必须同时存在 `claim_boundary`。缺少边界说明时，高准确率很容易被误读为通用能力。

## 报告文件怎样读

- `reports/environment.json`：Python、NumPy、PyTorch 版本，以及本 lab 使用 CPU 张量的说明。
- `reports/tensor_demo.json`：shape、dtype、broadcasting 和 batch matrix multiplication 的最小例子。
- `reports/autograd_demo.json`：autograd 梯度、解析梯度和有限差分梯度。
- `reports/majority/metrics.json`：多数类 baseline。
- `reports/linear/metrics.json`：线性 baseline。
- `reports/mlp/metrics.json`：小型 MLP 的训练结果。
- `reports/comparison.json`：把 baseline 和 MLP 放到同一张对照表中。

建议按“先过程、后结论”的顺序检查：先确认 environment 和 data summary，再看 autograd 与 history，最后看 metrics、comparison 和 checkpoint round-trip。若直接跳到 comparison，无法判断数字是否来自当前环境和完整测试。

## 本路线的完成标准

学习者应能独立完成以下动作：

```text
[ ] 说出一个 batch 的输入与输出 shape
[ ] 解释 logits、loss、gradient、parameter update 的顺序
[ ] 说明 train/validation/test 的不同职责
[ ] 给模型效果配上 majority 和 linear baseline
[ ] 从 checkpoint 恢复同一测试结果
[ ] 写出数据、设备和结论边界
```

这些能力比记住某个网络名称更可迁移：换到卷积网络、Transformer 或真实表格数据时，证据链仍然成立。

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
