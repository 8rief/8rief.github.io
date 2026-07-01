---
layout: post
title: "从训练到推理：加载 checkpoint、单点预测和 model card"
date: 2026-07-01 20:27:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把训练好的 NumPy MLP 保存为 `.npz`，记录 normalization 参数，并用 model card 说明用途和限制。"
tags: [deep-learning, inference, model-card, teaching]
---
{% raw %}
> 主题：深度学习/AI 工程 / inference / model card
> 本文 lab 已验证：生成 `models/mlp-weights.npz`、`models/model-card.md`，并输出 inference demo label。

训练只是模型生命周期的一部分。推理需要加载权重、使用同一套 normalization、输出概率和预测标签。对外展示模型时，还应说明数据来源、用途、baseline、限制和不适用场景。本包用一个简短 model card 固定这些信息。

## 学习目标

1. 理解训练和推理的状态差异。
2. 知道 normalization 参数也属于模型状态。
3. 保存并解释 `.npz` checkpoint。
4. 写出最小 model card。

## 先修知识

建议先读训练循环和评估两篇。

## 核心模型

![从训练到推理：加载 checkpoint、单点预测和 model card](/assets/diagrams/ai-engineering-inference-model-card-boundary.svg)

推理链路是：原始输入点 → 使用训练集 mean/std 标准化 → MLP forward → softmax 概率 → predicted label。model card 是模型的使用边界说明。

## 可信资料的关键结论

- PyTorch 教程强调保存和加载模型权重，推理前使用评估模式；本包用 NumPy 展示最小同构流程。
- NumPy `.npz` 适合保存小模型多个数组。
- model card 帮助把模型的 intended use、data、metrics 和 limitations 写清楚。

## 逐步实现

保存 checkpoint：

```python
np.savez(
    "models/mlp-weights.npz",
    W1=W1, b1=b1, W2=W2, b2=b2,
    mean=mean, std=std,
)
```

推理时必须复用训练集 normalization：

```python
x = (raw_point - mean) / std
probs = softmax(mlp_forward(params, x)[1])
predicted_label = int(probs.argmax())
```

lab 输出：

```text
checkpoint_ready=models/mlp-weights.npz
model_card_ready=models/model-card.md
inference_predicted_label=0
```

model card 记录 intended use、training data、baselines 和 limitations。

## 常见错误

1. **推理时重新计算测试集 mean/std。** 推理必须使用训练时保存的 normalization。
2. **只保存权重数组，不说明模型结构。** checkpoint 和代码结构要匹配。
3. **省略模型用途和限制。** 读者会误用 toy 模型。
4. **把单点推理成功当成模型质量证明。** 质量证明仍来自测试集和 baseline。

## 练习或延伸

1. 写一个 `predict.py`，从命令行读取 `x0 x1` 并输出概率。
2. 在 model card 中增加训练日期和指标表。
3. 把 checkpoint 文件名加上模型版本，例如 `mlp-v1.npz`。

## 参考资料

- NumPy 文档：[NumPy: the absolute basics for beginners](https://numpy.org/doc/stable/user/absolute_beginners.html)
- NumPy 文档：[Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)
- NumPy 文档：[numpy.matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html)
- NumPy 文档：[Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)
- NumPy 文档：[numpy.savez](https://numpy.org/doc/stable/reference/generated/numpy.savez.html)
- PyTorch 教程：[Quickstart](https://pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html)
- PyTorch 教程：[Autograd](https://pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- PyTorch 教程：[Save and Load the Model](https://pytorch.org/tutorials/beginner/basics/saveloadrun_tutorial.html)

{% endraw %}
