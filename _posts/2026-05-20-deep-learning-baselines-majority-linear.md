---
layout: post
title: "Baseline：多数类和线性分类器为什么必须先跑"
date: 2026-05-20 18:00:00 +0800
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

先看一个常见的误判：某个二分类模型准确率达到 90%，听起来已经很好；如果数据中 95% 的样本都属于同一类，那么永远预测多数类反而能达到 95%。脱离数据分布和简单模型参照，单个准确率无法回答“模型是否学到了有用结构”。

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

## 为什么要引入两级 baseline

多数类和线性模型回答的是两个不同问题：

- **多数类 baseline**：只利用训练集标签频数，不读取输入特征。如果复杂模型没有超过它，首先检查类别不均衡、标签或指标。
- **线性 baseline**：读取与 MLP 完全相同的特征，但决策边界只能是直线。如果 MLP 超过它，才有证据讨论非线性表示的价值。

本 lab 的多数类标签由训练集决定，而准确率在测试集计算。实现可缩减为：

```python
majority = float(train_y.mean() >= 0.5)
pred = torch.full_like(test_y, majority)
accuracy = (pred == test_y).float().mean()
```

训练集正类比例正好是 `0.500`，代码中的 `>=` 使并列时选择类别 1；测试集正类比例为 `0.573`，所以测试准确率也是 `0.573`。这里不能反过来查看测试集后再决定多数类，否则测试标签已经参与了模型选择。

## 逐步实现

三组指标来自同一次 lab：

```text
majority baseline: 57.3%
linear baseline:   49.0%
MLP:               99.0%
MLP - linear:      50.0%
```

多数类 baseline 约为 57.3%，因为 test split 中正类略多。线性 baseline 约为 49.0%，说明单条直线难以处理 XOR 风格结构。MLP 达到 99.0%，提升来自非线性隐藏层对四个簇的组合表达能力。

复查原始结果时，不要从文章抄数字，直接读取结构化报告：

```bash
python - <<'PY'
import json
from pathlib import Path

root = Path("reports")
majority = json.loads((root / "majority/metrics.json").read_text())
linear = json.loads((root / "linear/metrics.json").read_text())
mlp = json.loads((root / "mlp/metrics.json").read_text())
print(f"majority={majority['accuracy']:.3f}")
print(f"linear={linear['test']['accuracy']:.3f}")
print(f"mlp={mlp['test']['accuracy']:.3f}")
PY
```

预期输出为：

```text
majority=0.573
linear=0.490
mlp=0.990
```

线性模型比多数类还低并不矛盾：它确实使用了输入特征，但 XOR 的全局线性方向很弱；有限测试集上的类别比例又让固定预测类别 1 获得了 57.3%。这也是同时保留两个 baseline 的原因。

## 公平比较需要固定什么

比较三种方法时至少保持以下条件一致：

1. 使用同一份 train/validation/test 划分；
2. 输入特征和标准化参数一致；
3. 模型选择只查看 validation，最终一次性报告 test；
4. 指标定义、阈值和随机种子写入报告；
5. 同时保存准确率与 loss，避免只有一个四舍五入后的数字。

本次结果能支持的高确定性结论是：在固定 seed 生成的本地 XOR 风格数据上，带 ReLU 的小型 MLP 明显超过两种简单参照。它没有比较树模型、核方法或更强神经网络，也没有重复多个 seed，因此不构成算法排名。

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
