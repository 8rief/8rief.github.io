---
layout: post
title: "结课项目：用数学基础做一个可验证 logistic baseline"
date: 2026-02-18 18:00:00 +0800
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

项目验收应同时覆盖数据生成、切分、参数更新、history、baseline 和最终结论，并能由同一条命令重建。

## 为什么要引入 logistic baseline

深度学习项目常常一开始就写复杂模型。更稳妥的流程是先做简单 baseline：如果 majority baseline 已经很强，复杂模型要证明自己确实带来增益；如果简单线性模型已经足够，复杂模型可能没有必要。logistic regression 正好连接线性代数和概率解释。

## 正式定义

给定输入矩阵 `X`、权重 `w` 和偏置 `b`，logit 为 `z=Xw+b`。sigmoid 把 logit 转成正类概率：`p=1/(1+exp(-z))`。二分类交叉熵为 `L=-mean(y log p + (1-y) log(1-p))`。梯度可写成 `dL/dw = X^T(p-y)/n`，`dL/db=mean(p-y)`。

## 直观模型

![结课项目：用数学基础做一个可验证 logistic baseline](/assets/diagrams/math-ai-capstone-logistic-baseline.svg)

线性部分给出分界方向，sigmoid 把分数压到 0 到 1，交叉熵衡量概率预测与真实标签的距离，梯度下降让参数沿降低损失的方向更新。

## 数据和比较协议

lab 用 seed 23 生成 500 条二维样本：

```python
rng = np.random.default_rng(23)
x = rng.normal(size=(500, 2))
true_w = np.array([1.4, -1.1])
logits = x @ true_w + 0.2
probs = 1 / (1 + np.exp(-logits))
y = rng.binomial(1, probs)

x_train, x_test = x[:350], x[350:]
y_train, y_test = y[:350], y[350:]
```

标签按概率采样，所以即使知道生成参数，也存在不可约随机重叠。多数类标签只从 350 条训练标签决定，再固定到 150 条测试样本；logistic regression 使用相同切分。

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

训练 history 显示状态变化：

```text
epoch   loss      train_acc
0       0.693147  0.5343
20      0.448645  0.8000
40      0.423759  0.8029
100     0.413755  0.8029
200     0.413032  0.8000
```

loss 持续下降，而离散 accuracy 在 0.80 附近小幅变化。这是正常现象：参数仍在提高概率校准或间隔，但少量样本是否跨过 0.5 阈值会离散跳动。

可从结构化报告复核 baseline 增益：

```bash
python - <<'PY'
import json
m = json.load(open("reports/metrics.json"))["capstone"]
gain = m["logistic_test_acc"] - m["majority_test_acc"]
assert abs(gain - m["accuracy_gain"]) < 1e-12
print(f"majority={m['majority_test_acc']:.3f}")
print(f"logistic={m['logistic_test_acc']:.3f}")
print(f"gain={gain:.3f}")
PY
```

预期输出为 `0.587`、`0.760` 和 `0.173`。baseline 与模型必须使用同一 test split，增益才有含义。

## 参数怎样解释

训练结果 `w=(1.781,-1.517)`、`b=0.217` 与生成方向 `(1.4,-1.1)` 符号一致。决策边界由 `1.781x0-1.517x1+0.217=0` 给出；权重绝对值还受采样噪声、有限数据和未正则化训练影响，不能期待等于生成参数。

## 证据边界

当前实验有明确限制：

1. 只有一次固定随机切分，没有多 seed 均值和方差；
2. 只有 majority baseline，没有与其他线性实现或非线性模型比较；
3. 没有 validation split，学习率和 epoch 是预先固定的教学配置；
4. 数据是已知 logistic 机制生成的二维合成样本。

因此可支持的结论是“当前合成任务上线性概率模型超过多数类参照 0.173 accuracy”。它不支持真实任务效果、算法排名或部署可靠性主张。

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

## 练习与检查点

把训练轮数改成 20、50、200，比较 loss 和 test accuracy。观察训练是否已经进入平台期。

## 参考资料
- MIT OpenCourseWare：[18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)
- Mathematics for Machine Learning：[在线教材](https://mml-book.github.io/)
- MIT OpenCourseWare：[6.041SC Probabilistic Systems Analysis and Applied Probability](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/)
- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)
- scikit-learn 文档：[Logistic regression](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression)
- PyTorch 教程：[Optimizing Model Parameters](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)

{% endraw %}
