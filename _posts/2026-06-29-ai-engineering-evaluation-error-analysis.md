---
layout: post
title: "评估不止准确率：confusion matrix、错误样本和边界解释"
date: 2026-06-29 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用测试集 loss、accuracy、TP/TN/FP/FN 和错误分析约束模型效果主张。"
tags: [deep-learning, evaluation, metrics, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / evaluation / error analysis
> 本文 lab 已验证：`reports/metrics.json` 保存 MLP 和 baseline 的 test loss、accuracy、TP/TN/FP/FN。

模型训练完成后，评估要回答两个问题：总体表现如何，错误集中在哪里。accuracy 是最直观的指标，但它无法说明哪类错误多。confusion matrix 把预测和真实标签的组合拆开，能帮助发现偏向、边界和数据问题。

两个模型都达到 90% accuracy 时，错误代价仍可能完全不同：一个漏掉大量正类，另一个产生大量误报。把预测拆成 TP、TN、FP、FN，才能继续计算 precision、recall 并定位样本。

## 学习目标

1. 读取测试集 loss 和 accuracy。
2. 理解 TP、TN、FP、FN。
3. 把 MLP 与 baseline 放在同一张表里比较。
4. 知道 toy 结果的外推边界。

## 先修知识

需要知道二分类有正类和负类。

## 核心模型

![评估不止准确率：confusion matrix、错误样本和边界解释](/assets/diagrams/ai-engineering-evaluation-error-analysis.svg)

评估阶段冻结模型参数，只在测试集上做 forward。预测标签与真实标签组合成 confusion matrix。指标解释必须绑定数据来源和任务边界。

## 四个格子怎样定义

以标签 1 为正类：

```text
                 predicted 0   predicted 1
actual 0              TN             FP
actual 1              FN             TP
```

四项之和必须等于测试样本数；accuracy 的分子是 `TP+TN`。

## 可信资料的关键结论

- PyTorch quickstart 评估阶段会关闭训练行为并计算测试准确率；本包用 NumPy 显式实现评估。
- 分类评估应把模型输出、真实标签和错误类型对应起来。
- 模型效果声明必须说明数据集、切分、baseline 和限制。

## 逐步实现

评估函数：

```python
pred = probs.argmax(axis=1)
tp = ((pred == 1) & (y == 1)).sum()
tn = ((pred == 0) & (y == 0)).sum()
fp = ((pred == 1) & (y == 0)).sum()
fn = ((pred == 0) & (y == 1)).sum()
```

本次测试集结果：

```text
majority_test_acc=0.520
linear_test_acc=0.580
mlp_test_acc=1.000
mlp_minus_linear_test_acc=0.420
```

这说明 MLP 在这个非线性 toy 边界上明显优于线性 baseline。这个结论只覆盖本 lab 的合成螺旋数据。

结构化 confusion matrix 为：

```text
linear: TN=58, FP=46, FN=38, TP=58, total=200
MLP:    TN=104, FP=0, FN=0, TP=96, total=200
```

线性模型的 accuracy 为 `(58+58)/200=0.58`。其正类 precision 为 `58/(58+46)≈0.558`，recall 为 `58/(58+38)≈0.604`。可复核：

```python
tp, tn, fp, fn = 58, 58, 46, 38
precision = tp / (tp + fp)
recall = tp / (tp + fn)
accuracy = (tp + tn) / (tp + tn + fp + fn)
print(f"accuracy={accuracy:.3f} precision={precision:.3f} recall={recall:.3f}")
```

```text
accuracy=0.580 precision=0.558 recall=0.604
```

MLP 在该固定测试集没有错误，因此从这 200 个点里无法分析其失败模式。合理的下一步是增加噪声、改变 seed 或构造边界附近样本，再观察首批 FP/FN；不能从“当前错误为空”推断模型在外部数据也不会失败。

## 错误分析要回到具体样本

当存在错误时，至少保存索引、原始坐标、真实标签、预测标签和概率：

```python
wrong = np.flatnonzero(pred != y)
for i in wrong[:10]:
    print(i, x[i].tolist(), int(y[i]), int(pred[i]), probs[i].tolist())
```

若错误集中在螺旋交界处，可能是模型容量或噪声问题；若集中在某一标签，可能是类别分布或阈值问题；若出现极端坐标，先检查数据和标准化。错误分析用于提出可验证假设，不能只停在罗列样本。

## 常见错误

1. **只给一个高准确率。** 还需要 baseline、数据来源和限制。
2. **把验证集结果当最终测试结果。** 测试集应保留到最后报告。
3. **忽略错误类型。** 不同错误的业务代价可能完全不同。
4. **把 toy 数据 100% 准确率写成通用模型能力。** toy lab 的价值是工程流程。

## 练习或延伸

1. 打印所有 FP/FN 样本的坐标。
2. 把数据 noise 增大，观察 confusion matrix 变化。
3. 增加 precision/recall，并解释它们适合什么任务。

## 参考资料

- scikit-learn 文档：[Confusion matrix](https://scikit-learn.org/stable/modules/model_evaluation.html#confusion-matrix)
- scikit-learn 文档：[Precision, recall and F-measures](https://scikit-learn.org/stable/modules/model_evaluation.html#precision-recall-f-measure-metrics)
- Google Machine Learning Crash Course：[Classification: Accuracy, recall, precision](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)
- PyTorch 教程：[Quickstart 的模型评估流程](https://docs.pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html)

{% endraw %}
