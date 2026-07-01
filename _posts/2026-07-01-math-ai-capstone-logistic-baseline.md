---
layout: post
title: "结课项目：用数学基础做一个可验证 logistic baseline"
date: 2026-07-01 20:49:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "把向量、概率、梯度、优化和评估合成一个小型 logistic regression baseline。"
tags: [math, logistic-regression, baseline, teaching]
---
{% raw %}
> 主题：数学基础 / logistic regression / baseline
> 本文 lab 已验证：小型 logistic regression 在测试集 accuracy 上比 majority baseline 高约 `0.173`。

数学基础最终要服务于可验证的项目。这个结课项目把前面学过的向量、矩阵、概率、梯度、优化和评估放到一条链路里：用 logistic regression 做一个二分类 baseline，再和 majority baseline 比较。

## 问题从哪里来

深度学习项目常常一开始就写复杂模型。更稳妥的流程是先做简单 baseline：如果 majority baseline 已经很强，复杂模型要证明自己确实带来增益；如果简单线性模型已经足够，复杂模型可能没有必要。logistic regression 正好连接线性代数和概率解释。

## 正式定义

给定输入矩阵 `X`、权重 `w` 和偏置 `b`，logit 为 `z=Xw+b`。sigmoid 把 logit 转成正类概率：`p=1/(1+exp(-z))`。二分类交叉熵为 `L=-mean(y log p + (1-y) log(1-p))`。梯度可写成 `dL/dw = X^T(p-y)/n`，`dL/db=mean(p-y)`。

## 直观模型

![结课项目：用数学基础做一个可验证 logistic baseline](/assets/diagrams/math-ai-capstone-logistic-baseline.svg)

线性部分给出分界方向，sigmoid 把分数压到 0 到 1，交叉熵衡量概率预测与真实标签的距离，梯度下降让参数沿降低损失的方向更新。

## 怎么算

训练循环摘要：

```python
w = np.zeros(X_train.shape[1])
b = 0.0
for epoch in range(201):
    logits = X_train @ w + b
    p = 1 / (1 + np.exp(-logits))
    grad_w = X_train.T @ (p - y_train) / len(y_train)
    grad_b = np.mean(p - y_train)
    w -= lr * grad_w
    b -= lr * grad_b
```

lab 输出：

```text
majority_test_acc=0.587
logistic_test_acc=0.760
capstone_accuracy_gain=0.173
weights=(1.781, -1.517)
bias=0.217
```

这个结果说明在本合成数据上，logistic baseline 明显优于只预测多数类。结论只覆盖这个固定 seed 的教学数据，不用于说明真实业务数据上的效果。

## 有什么用

1. logistic regression 是分类任务中非常重要的简单 baseline。
2. 它展示了线性代数、概率解释、交叉熵和梯度下降如何连接。
3. baseline 让后续 MLP、CNN、Transformer 的效果声明有参照物。
4. 小项目保留 metrics、history 和 transcript，可以形成可复现证据链。

## 常见误区

1. **没有 baseline 就报告模型准确率。** 单独 accuracy 无法说明模型是否有增益。
2. **把概率阈值固定成唯一选择。** 默认 0.5 只是起点，实际任务需结合错误代价调阈值。
3. **忽略特征尺度。** 特征尺度差异会影响梯度下降稳定性。
4. **用一次随机切分下结论。** 教学 lab 可以固定 seed，严肃实验应多 seed 或交叉验证。

## 检查点

把训练轮数改成 20、50、200，比较 loss 和 test accuracy。观察训练是否已经进入平台期。

## 参考资料
- MIT OpenCourseWare：[18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- NumPy 文档：[Linear algebra](https://numpy.org/doc/stable/reference/routines.linalg.html)
- MIT OpenCourseWare：[6.041SC Probabilistic Systems Analysis and Applied Probability](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/)
- Penn State STAT 414：[Introduction to Probability Theory](https://online.stat.psu.edu/stat414/)
- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- PyTorch 教程：[Automatic Differentiation with torch.autograd](https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- NumPy 文档：[numpy.exp](https://numpy.org/doc/stable/reference/generated/numpy.exp.html)

{% endraw %}
