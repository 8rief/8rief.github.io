---
layout: post
title: "PyTorch 工程结构：Dataset、Module 和训练循环"
date: 2026-05-21 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把教学 lab 拆成 data、models、train、cli、tests 和 reports，说明 PyTorch 项目如何组织。"
tags: [deep-learning, pytorch, dataloader, module, training-loop]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/deep-learning-foundations-pytorch/README.md`](/assets/labs/deep-learning-foundations-pytorch/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：深度学习基础 / PyTorch 工程结构
> 本文关注代码组织，不重复讲具体模型公式。

小型深度学习项目也应该分层。数据生成和划分放在 data 模块，模型结构放在 models 模块，训练与评估放在 train 模块，命令行入口只负责组织流程。这样写的好处是每个边界都能单独测试。

把数据生成、模型、训练和文件写入混在一个函数里，最初可能只有几十行；一旦要更换模型、单测梯度或重新加载 checkpoint，同一逻辑会被复制到多个入口。分层的目的，是让数据、纯计算和副作用各自拥有清晰接口。

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

## 先定义模块之间的契约

项目里的核心接口可以概括为：

```text
make_xor_gaussians(seed) -> DatasetBundle
DatasetBundle.as_dataset(split) -> TensorDataset
build_model(name) -> nn.Module
train_model(name, config) -> TrainingResult
evaluate_model(model, bundle, split, loss_fn) -> Metrics
```

上层只依赖返回类型和语义，无需知道数据如何生成、模型有几层或 JSON 怎样写入。要替换数据集时，模型和评估函数可以保持不变。

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

`DataLoader` 的最小用法是：

```python
generator = torch.Generator().manual_seed(seed)
loader = DataLoader(
    bundle.as_dataset("train"),
    batch_size=64,
    shuffle=True,
    generator=generator,
)

batch_x, batch_y = next(iter(loader))
print(batch_x.shape, batch_y.shape)
```

预期第一批 shape 为：

```text
torch.Size([64, 2]) torch.Size([64])
```

`TensorDataset` 负责按同一个索引返回一行特征和标签；`DataLoader` 负责 batch、shuffle 与迭代。显式传入固定 seed 的 generator，使样本顺序也进入可复现约束。

模型只接收 tensor 并返回 logits：

```python
class MLPClassifier(nn.Module):
    def __init__(self, hidden_dim=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)
```

`nn.Module` 会注册子层参数，让 `model.parameters()`、设备迁移和 `state_dict()` 工作。把优化器或文件路径塞进 `forward` 会破坏这个纯粹边界。

## 为什么 CLI 要薄

CLI 的任务是把命令行参数转成函数调用，并把结果写到报告文件。核心训练逻辑不应藏在 CLI 中，否则测试只能从命令行端到端运行，定位问题会变慢。

较好的调用方向是 `cli -> train -> data/models`，底层模块不反向导入 CLI。端到端脚本验证用户入口，单元测试直接调用 Python 函数，两种测试覆盖不同故障面。

## 测试覆盖哪些边界

当前 tests 检查四件事：数据 shape 和类别比例、autograd 有限差分、MLP 相对线性 baseline 的提升、checkpoint 加载后一致性。这些测试直接对应教学主张。

运行：

```bash
.venv/bin/python -m pytest -q
```

当前预期输出是：

```text
....                                                                     [100%]
4 passed
```

“能启动”只能证明语法和依赖没有立刻失败；这里的测试还检查梯度误差、模型对照和序列化往返，因此能覆盖文章中的关键主张。它仍未覆盖跨平台确定性、异常数据或大规模性能。

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
