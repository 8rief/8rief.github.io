---
layout: post
title: "PyTorch 工程结构：Dataset、Module 和训练循环"
date: 2026-06-25 22:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把教学 lab 拆成 data、models、train、cli、tests 和 reports，说明 PyTorch 项目如何组织。"
tags: [deep-learning, pytorch, dataloader, module, training-loop]
---
{% raw %}

> 主题：深度学习基础 / PyTorch 工程结构
> 本文关注代码组织，不重复讲具体模型公式。

小型深度学习项目也应该分层。数据生成和划分放在 data 模块，模型结构放在 models 模块，训练与评估放在 train 模块，命令行入口只负责组织流程。这样写的好处是每个边界都能单独测试。

## 学习目标

1. 说明 `Dataset`、`DataLoader`、`nn.Module` 和训练函数的职责。
2. 读懂一个最小 PyTorch 项目的目录结构。
3. 区分训练代码、评估代码和 CLI 编排。
4. 给深度学习代码写可回归测试。

## 先修知识

需要完成前几篇的 tensor、线性层、loss 和 autograd 基础。

## 核心模型

![PyTorch 项目结构](/assets/diagrams/deep-learning-pytorch-dataset-module-training-loop.svg)

`data` 提供 tensor，`models` 定义 forward，`train` 连接 loss 和 optimizer，`cli` 生成可复跑入口，`tests` 检查稳定行为，`reports` 保存证据。

## 逐步实现

项目目录如下：

```text
deep-learning-foundations-pytorch/
├── requirements.txt
├── run_lab.sh
├── src/dl_foundations/
│   ├── data.py
│   ├── models.py
│   ├── train.py
│   └── cli.py
├── tests/
└── reports/
```

`data.py` 返回 `DatasetBundle`，其中包含 train、validation 和 test tensor。训练时用 `TensorDataset` 和 `DataLoader` 形成 batch。`models.py` 中的模型继承 `nn.Module`，只定义结构和 forward。`train.py` 中统一设置 seed、loss、optimizer、history 和 checkpoint。

## 为什么 CLI 要薄

CLI 的任务是把命令行参数转成函数调用，并把结果写到报告文件。核心训练逻辑不应藏在 CLI 中，否则测试只能从命令行端到端运行，定位问题会变慢。

## 测试覆盖哪些边界

当前 tests 检查四件事：数据 shape 和类别比例、autograd 有限差分、MLP 相对线性 baseline 的提升、checkpoint 加载后一致性。这些测试直接对应教学主张。

## 常见错误

1. **把所有代码写进一个 notebook。** 展示方便，但复跑和测试边界容易混乱。
2. **模型 forward 里做文件读写。** 模型应只表达 tensor 到 tensor 的变换。
3. **训练函数不返回指标。** 没有结构化返回值，报告和测试都难写。
4. **测试只检查程序能运行。** 测试应检查与主张相关的可观察行为。

## 练习或延伸

1. 给 `models.py` 增加一个 `MLPClassifier(hidden_dim=4)` 的变体。
2. 把 `DataLoader` 的 batch size 改成 32，观察训练时间和指标。
3. 增加一个测试，确认 history CSV 的最后一行 epoch 等于传入 epoch 数。

## 参考资料

- PyTorch 文档：[torch.utils.data](https://docs.pytorch.org/docs/stable/data.html)
- PyTorch 文档：[torch.nn.Module](https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html)
- PyTorch 教程：[Training with PyTorch](https://docs.pytorch.org/tutorials/beginner/introyt/trainingyt.html)


{% endraw %}
