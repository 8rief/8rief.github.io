---
layout: post
title: "概率统计基础：数据划分、噪声和指标怎样影响结论"
date: 2026-05-19 18:00:00 +0800
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

如果同一份数据一边用于调参、一边用于报告最终成绩，模型会逐渐适应这份数据，最后的数字就不再代表对未见样本的检验。数据划分的核心作用，是把“学习”“选择”和“最终审计”分成三个互不混用的阶段。

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

## 数据是怎样生成和切分的

四个二维高斯簇位于 `(-1,-1)`、`(-1,1)`、`(1,-1)`、`(1,1)`，对角位置同类，形成 XOR 风格结构。每个中心生成 120 个点，总计 480 个样本：

```python
rng = np.random.default_rng(20260625)
centers = np.array([
    [-1.0, -1.0], [-1.0, 1.0],
    [ 1.0, -1.0], [ 1.0, 1.0],
], dtype=np.float32)
labels = np.array([0.0, 1.0, 1.0, 0.0], dtype=np.float32)

x = np.concatenate([
    center + rng.normal(0.0, 0.32, size=(120, 2))
    for center in centers
])
```

随机打乱后按 60%/20%/20% 顺序切分。标准化所用均值和标准差只能从训练集计算，再原样应用到 validation 和 test：

```python
train_end = int(len(x) * 0.60)
val_end = int(len(x) * 0.80)
train_x, val_x, test_x = x[:train_end], x[train_end:val_end], x[val_end:]

mean = train_x.mean(axis=0, keepdims=True)
std = np.maximum(train_x.std(axis=0, keepdims=True), 1e-6)
train_x = (train_x - mean) / std
val_x = (val_x - mean) / std
test_x = (test_x - mean) / std
```

若分别用 validation 或 test 自己的统计量做标准化，数据管线已经读取了评估集信息，这是一种数据泄漏。

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

这里还有一个容易忽略的统计现象：总体数据由四个等量簇组成，理论正类比例是 0.5；随机切分只有 96 个测试样本，因此观察到 0.573 并不表示生成器偏向正类。用二项分布的标准误近似，

```text
SE = sqrt(p(1-p)/n) = sqrt(0.5 × 0.5 / 96) ≈ 0.051
```

`0.573` 距离 `0.5` 约 1.43 个标准误，属于小样本切分中可能出现的波动。固定 seed 的意义是让调试基准稳定，并不意味着这一次切分代表所有随机切分。

## 为什么要保留 validation

训练集用于更新参数，validation 用于观察训练是否有效，test 用于最后报告。即使是小型教学实验，也应避免一边看 test 一边反复调整模型，否则 test 指标会变成调参过程的一部分。

可以用一张“允许的动作表”约束流程：

| 划分 | 可以做什么 | 禁止做什么 |
| --- | --- | --- |
| train | 拟合参数、计算标准化统计量 | 把训练准确率当最终结论 |
| validation | 选学习率、epoch、隐藏层大小 | 参与梯度更新 |
| test | 在方案冻结后做一次最终评估 | 反复查看后继续调参 |

运行下面的检查，可确认三份样本数量相加仍为 480：

```bash
python - <<'PY'
import json
d = json.load(open("reports/data_summary.json"))
print(d["train"] + d["val"] + d["test"])
print(round(d["test_positive_rate"], 3))
PY
```

预期输出是 `480` 和 `0.573`。若总数不对，先排查切片边界；若正类比例变化，检查 seed、shuffle 顺序和数据生成参数。

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
