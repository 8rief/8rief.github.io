---
layout: post
title: "AI 工程从问题和 baseline 开始：数据、切分和最小可比结果"
date: 2026-04-11 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用二维螺旋分类任务建立训练集、验证集、测试集、多数类 baseline 和线性 baseline。"
tags: [deep-learning, ai-engineering, baseline, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/deep-learning-ai-engineering/README.md`](/assets/labs/deep-learning-ai-engineering/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：深度学习/AI 工程 / problem framing / baseline
> 本文 lab 已验证：训练/验证/测试行数为 600/200/200，majority baseline test accuracy=0.520，linear baseline test accuracy=0.580。

AI 工程首先要回答一个具体问题：输入是什么，输出是什么，如何判断结果是否有用。直接训练神经网络会掩盖很多基本错误，所以本包从 toy 分类任务开始，先生成数据、切分数据，再建立多数类和线性模型两个 baseline。后续 MLP 的效果主张必须和这些 baseline 对比。

假设脚本打印 100% 准确率，却没有写明输入字段、数据切分和参照模型，这个数字几乎无法审计：标签可能意外进入特征，测试集可能参与训练，任务本身也可能只需预测多数类。问题定义和 baseline 是模型代码之前的质量门。

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

## 先把任务写成输入输出契约

本 lab 的单条样本契约是：

```text
input:  x = [x0, x1], 两个 float64 数值
target: y ∈ {0, 1}
output: [P(y=0|x), P(y=1|x)]
metric: 固定 test split 上的 accuracy 与 cross entropy
```

数据由两条相互缠绕的二维螺旋生成。每类 500 个点，共 1000 行；固定 seed 7 打乱后按 60%/20%/20% 切分。任务被刻意设计成非线性，以便检验线性和带隐藏层模型的差异。

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

标准化统计量只从训练集计算：

```python
mean = train.x.mean(axis=0)
std = train.x.std(axis=0) + 1e-8
train_x = (train.x - mean) / std
val_x = (val.x - mean) / std
test_x = (test.x - mean) / std
```

本次保存的 `mean` 约为 `[-0.0150,-0.00329]`，`std` 约为 `[0.4345,0.3959]`。validation 和 test 若自行计算均值、标准差，会把评估集分布泄漏进预处理。

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

可用独立命令检查数据文件，而不依赖训练日志：

```bash
python - <<'PY'
import csv
from pathlib import Path
for name in ("train", "val", "test"):
    with (Path("data") / f"{name}.csv").open() as f:
        rows = list(csv.DictReader(f))
    labels = [int(row["label"]) for row in rows]
    print(name, len(rows), sum(labels) / len(labels))
PY
```

预期行数是 600、200、200；比例会随固定切分略有变化。若三份数据有重复 `row_id`、总数不为 1000 或标签超出 `{0,1}`，应在训练前终止流程。

## 两个 baseline 怎样约束结论

多数类模型从训练标签计数得到类别 0，测试准确率为 0.520；线性 softmax 模型使用全部两个特征，测试准确率为 0.580。后续 MLP 的 1.000 必须与这两个结果同表报告：

```text
majority  0.520  检查类别比例带来的最低参照
linear    0.580  检查单条线性边界的能力
MLP       1.000  检查非线性隐藏层在此任务上的增益
```

可支持的结论仅限固定合成螺旋数据。一个 seed、一个生成器和两个简单 baseline 无法支持真实业务效果、鲁棒性或算法排名。

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

- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)
- NumPy 文档：[Statistics](https://numpy.org/doc/stable/reference/routines.statistics.html)
- scikit-learn 文档：[Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html)
- PyTorch 教程：[Quickstart](https://docs.pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html)

{% endraw %}
