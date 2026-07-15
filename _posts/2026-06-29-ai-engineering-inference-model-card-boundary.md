---
layout: post
title: "从训练到推理：加载 checkpoint、单点预测和 model card"
date: 2026-06-29 18:00:00 +0800
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

常见线上故障并非权重文件损坏，而是推理端遗漏训练时的预处理、类别顺序或输入 shape。模型交付必须把这些约定和权重一起版本化。

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

## 从 checkpoint 恢复全部状态

```python
import numpy as np

with np.load("models/mlp-weights.npz") as ckpt:
    params = {name: ckpt[name] for name in ("W1", "b1", "W2", "b2")}
    mean = ckpt["mean"]
    std = ckpt["std"]

assert params["W1"].shape == (2, 24)
assert params["W2"].shape == (24, 2)
assert mean.shape == std.shape == (2,)
```

这些 shape 断言同时检查模型结构版本。若后续把 hidden size 改为 32，旧 checkpoint 应明确拒绝加载或经迁移处理，不能静默广播。

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

本次单点输入 `[0.35,-0.15]`，训练集统计量为：

```text
mean = [-0.0149997, -0.00328986]
std  = [ 0.4345177,  0.39589495]
```

标准化后约为 `[0.8400,-0.3706]`。模型输出：

```json
{
  "probabilities": [0.987220987838762, 0.012779012161238116],
  "predicted_label": 0
}
```

两项概率之和应接近 1，`argmax` 对应类别 0。这个单点只验证推理链路能运行，不参与 test accuracy 计算。

lab 输出：

```text
checkpoint_ready=models/mlp-weights.npz
model_card_ready=models/model-card.md
inference_predicted_label=0
```

model card 记录 intended use、training data、baselines 和 limitations。

## model card 至少回答六个问题

1. 模型解决什么输入输出任务；
2. 训练数据从哪里来、使用什么 seed；
3. 与哪些 baseline 比较、结果是多少；
4. checkpoint 需要什么代码和预处理；
5. 哪些数据与用途未验证；
6. 哪些指标不能从当前实验推出。

当前卡片明确限定为合成二维螺旋教学分类器。它没有外部数据、群体公平性、鲁棒性、延迟或安全测试，因此不得用于真实决策。model card 约束如何使用模型；`metrics.json` 和测试日志则提供可核查证据，两者应同时保留。

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

- NumPy 文档：[numpy.load](https://numpy.org/doc/stable/reference/generated/numpy.load.html)
- NumPy 文档：[numpy.savez](https://numpy.org/doc/stable/reference/generated/numpy.savez.html)
- PyTorch 教程：[Saving and Loading Models](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
- Mitchell 等：[Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993)

{% endraw %}
