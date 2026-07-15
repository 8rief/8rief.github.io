---
layout: post
title: "Bayes 公式和混淆矩阵：阳性结果为什么还要看先验"
date: 2026-02-16 09:00:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "用低患病率检测例子解释 Bayes 后验、precision、recall 和 confusion matrix。"
tags: [math, bayes, confusion-matrix, metrics, teaching]
---
{% raw %}
> 主题：数学基础 / Bayes / 评估指标
> 本文 lab 已验证：在 prevalence `0.08`、sensitivity `0.92`、specificity `0.95` 下，阳性后的后验概率约 `0.615`。

很多评估问题看起来只需要一个准确率，实际必须同时看先验比例和错误类型。低患病率筛查、欺诈检测、入侵告警、垃圾邮件识别都有同一个结构：即使检测器很准，阳性结果也要结合事件本身的基础发生率解释。

问题的难点来自条件方向：`P(检测阳性 | 真实阳性)` 与 `P(真实阳性 | 检测阳性)` 看起来相近，分母却完全不同。用具体人数展开，通常比直接套公式更不容易混淆。

## 为什么要引入先验和条件方向

一个检测器的 sensitivity 是 0.92，specificity 是 0.95。听起来已经很好。若目标事件在总体中只占 8%，那么看到一次阳性，目标真实存在的概率是多少？答案不是 92%，因为假阳性来自更大的阴性人群。

## 正式定义

Bayes 公式为 `P(A|B)=P(B|A)P(A)/P(B)`。在二分类检测中，`A` 是真实正类，`B` 是检测阳性。precision 等于 `TP/(TP+FP)`，recall 等于 `TP/(TP+FN)`。sensitivity 与 recall 同义，specificity 等于 `TN/(TN+FP)`。

检测阳性的总概率由两条路径组成：

```text
P(test+) = sensitivity × prevalence
         + (1-specificity) × (1-prevalence)
```

第一项来自真阳性，第二项来自假阳性。后验概率就是第一项占总阳性的比例。

## 直观模型

![Bayes 公式和混淆矩阵：阳性结果为什么还要看先验](/assets/diagrams/math-ai-bayes-confusion-metrics.svg)

先把总体按真实正负类拆开，再让检测器分别产生 TP、FN、FP、TN。阳性结果由 TP 和 FP 混合而成，后验概率就是阳性群体中真实正类所占比例。

## 怎么算

用 10000 个对象做整数化检查：

```python
n = 10_000
prevalence = 0.08
sensitivity = 0.92
specificity = 0.95
positive = n * prevalence
negative = n - positive
tp = positive * sensitivity
fp = negative * (1 - specificity)
posterior = tp / (tp + fp)
```

lab 输出：

```text
TP=736
FP=460
TN=8740
FN=64
bayes_posterior_positive=0.615
precision=0.615
recall=0.920
```

阳性后的概率约 61.5%。这个数和 precision 一致，因为两者都在问“预测阳性里真实阳性占多少”。

用表格检查四项总和：

| 真实状态 | 检测阳性 | 检测阴性 | 合计 |
| --- | ---: | ---: | ---: |
| 正类 | TP=736 | FN=64 | 800 |
| 负类 | FP=460 | TN=8740 | 9200 |
| 合计 | 1196 | 8804 | 10000 |

因此：

```text
precision = 736 / 1196 = 0.6154
recall    = 736 / 800  = 0.9200
accuracy  = (736+8740) / 10000 = 0.9476
```

94.76% accuracy 看起来很高，但永远预测负类也能达到 92%。相比之下，precision 直接回答“处理一次阳性告警时，有多大概率是真的”，更贴近该场景的决策问题。

## 先验变化会怎样

保持 sensitivity 0.92、specificity 0.95，把 prevalence 降到 0.01：

```python
prev = 0.01
posterior = 0.92*prev / (0.92*prev + 0.05*(1-prev))
print(posterior)
```

预期约为 `0.157`。检测器自身参数没有变化，但假阳性来自 99% 的大基数，导致阳性后概率显著下降。这说明 precision 依赖部署人群分布，不能只从离线 sensitivity/specificity 固定推出。

## 指标选择由错误代价决定

漏报代价高时，通常优先提高 recall；误报处理成本高时，需要关注 precision；类别极不均衡时，还应报告 PR 曲线或不同阈值下的指标。数学公式提供约束，最终阈值仍要结合实际代价。

## 有什么用

1. 分类模型评估必须说明数据集正负比例。
2. 低基率任务中，accuracy 很容易被多数类掩盖。
3. 安全告警系统需要同时控制漏报和误报。
4. 模型上线阈值选择通常是在 precision 与 recall 之间做权衡。

## 常见误区

1. **把 sensitivity 当阳性后概率。** sensitivity 条件是“真实为正”，后验条件是“检测为阳性”。
2. **只看 accuracy。** 当负类占 99% 时，全预测负类也能有 99% accuracy。
3. **忽略先验变化。** 同一个检测器在不同人群或业务场景中的 precision 会变化。
4. **混淆 FP 和 FN 的代价。** 安全、医疗、推荐场景对两类错误的容忍度不同。

## 练习与检查点

把 prevalence 从 0.08 改成 0.01，保持 sensitivity 和 specificity 不变，重新计算 posterior。解释为什么检测器参数没变，precision 却下降。

## 参考资料
- MIT OpenCourseWare：[6.041SC Probabilistic Systems Analysis and Applied Probability](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/)
- Penn State STAT 414：[Introduction to Probability Theory](https://online.stat.psu.edu/stat414/)
- scikit-learn 文档：[Classification metrics](https://scikit-learn.org/stable/modules/model_evaluation.html#classification-metrics)

{% endraw %}
