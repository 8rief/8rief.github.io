---
layout: post
title: "结课项目：从 XOR baseline 到 MLP 对比"
date: 2026-04-24 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "收束深度学习基础包：用合成 XOR 数据、majority/linear baseline 和 MLP 形成可复现实验报告。"
tags: [deep-learning, mlp, baseline, capstone, pytorch]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/deep-learning-foundations-pytorch/README.md`](/assets/labs/deep-learning-foundations-pytorch/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：深度学习基础 / 结课项目 / baseline 对比
> 本文收束本包的可复现实验。

结课项目的目标是把基础概念连成一个能运行、能测试、能解释边界的小实验。数据是二维 XOR 风格合成点，模型包含多数类 baseline、线性 baseline 和小型 MLP。最终报告只主张这个本地合成任务中的对比结果。

项目验收不能停在“脚本没有报错”。真正要检查的是：数据和模型状态是否可追踪，关键机制是否有独立测试，模型效果是否有公平 baseline，保存的 checkpoint 是否能恢复同一结果。

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

## 模型差异发生在哪里

两种可训练模型只差一段非线性表示：

```python
# linear
logits = linear_2_to_1(x)

# MLP
hidden = relu(linear_2_to_16(x))
logits = linear_16_to_1(hidden)
```

如果删除 ReLU，多层线性变换仍可合并成一个线性变换，表达能力不会突破直线边界。结课对比的关键变量是隐藏层带来的分段线性决策区域，而非单纯“参数更多”。

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

结构化原始结果为：

```json
{
  "majority_test_accuracy": 0.5729166865348816,
  "linear_test_accuracy": 0.4895833432674408,
  "mlp_test_accuracy": 0.9895833134651184,
  "mlp_minus_linear_accuracy": 0.4999999701976776
}
```

四舍五入后的 99.0% 对应 96 个测试样本中 95 个预测正确；因此一次样本变化就会改变约 1.04 个百分点。表格适合展示，JSON 适合程序核查，两者应指向同一轮运行。

用下面的验收命令同时检查测试、对照边界和 checkpoint：

```bash
set -euo pipefail
.venv/bin/python -m pytest -q
python -m json.tool reports/comparison.json
python -m json.tool reports/checkpoint_check.json
```

预期测试为 `4 passed`，加载后的准确率为 `0.9895833134651184`。任一步失败，都不能把该批次标记为可复现。

## 项目验收清单

- 环境版本已记录：Python、NumPy、PyTorch。
- 数据生成固定 seed，train/validation/test 划分可复跑。
- tensor demo 能解释 shape、dtype 和 broadcasting。
- autograd demo 通过有限差分检查。
- majority 和 linear baseline 已报告。
- MLP 指标与 baseline 放在同一张对照表。
- checkpoint 加载后准确率一致。
- pytest 覆盖数据、梯度、baseline 对比和 checkpoint。

## 怎样写结论才与证据匹配

可以写：“在 seed 为 20260625、噪声为 0.32 的 480 个二维合成样本上，小型 ReLU MLP 的测试准确率为 98.96%，线性分类器为 48.96%，多数类参照为 57.29%。”

还需补充三条限制：

1. 只运行了一个固定 seed，尚未给出均值和方差；
2. 只比较多数类和线性模型，未覆盖核方法、树模型等强非线性 baseline；
3. 数据由设计好的四簇结构生成，未测量真实数据偏移、噪声标签和部署性能。

这样的表述把确定事实、机制解释和未验证范围分开，读者可以判断结果的适用边界。

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
