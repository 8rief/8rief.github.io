---
layout: post
title: "Checkpoint、日志和可复现性：让结果能被复查"
date: 2026-06-25 22:08:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "说明 seed、环境版本、history、metrics 和 checkpoint 如何组成深度学习实验的证据链。"
tags: [deep-learning, checkpoint, logging, reproducibility]
---
{% raw %}

> 主题：深度学习基础 / checkpoint / reproducibility
> 本文对应 lab 的 reports 目录和 checkpoint 加载检查。

实验结果需要能被复查。深度学习代码包含随机初始化、shuffle、batch 训练和浮点计算，更要记录环境、随机种子、数据划分、训练 history、最终指标和 checkpoint。证据链越清楚，后续修改越容易定位影响。

## 学习目标

1. 说明 seed、版本和数据划分为什么属于实验证据。
2. 区分 metrics、history 和 checkpoint 的用途。
3. 用加载 checkpoint 的方式检查模型保存是否有效。
4. 写出可公开展示的实验边界。

## 先修知识

需要理解训练循环和模型参数会随 optimizer 更新。

## 核心模型

![实验证据链](/assets/diagrams/deep-learning-checkpoint-logging-reproducibility.svg)

环境说明能解释运行条件，history 能解释训练过程，metrics 能解释最终结果，checkpoint 能让模型状态被重新加载。

## 逐步实现

lab 保存 MLP checkpoint 后执行：

```bash
python -m dl_foundations.cli checkpoint-check \
  --checkpoint reports/mlp/checkpoint.pt \
  --output reports/checkpoint_check.json
```

输出记录加载后的 test accuracy，与训练结束时的 accuracy 一致。这说明保存的 `state_dict` 能恢复模型参数。

## 保存什么

- `environment.json`：Python、NumPy、PyTorch 版本和设备边界。
- `history.csv`：每个 epoch 的 train/validation loss 和 accuracy。
- `metrics.json`：最终 train/validation/test 指标。
- `checkpoint.pt`：模型名称、参数、seed、epoch、学习率和 test accuracy 摘要。
- `comparison.json`：baseline 与 MLP 的同表对照。

## 可复现性的边界

固定 seed 可以让本机实验稳定，但不同 PyTorch 版本、硬件平台和底层算子仍可能产生差异。因此公开写作应报告版本和实验边界，避免把一次本地结果写成跨平台保证。

## 常见错误

1. **只保存模型文件。** 没有 metrics 和 history，难以判断模型从哪里来。
2. **只保存最终截图。** 截图不可复跑，不能替代结构化报告。
3. **加载 checkpoint 时不重建同一模型结构。** `state_dict` 需要匹配模型定义。
4. **公开文章隐藏实验边界。** 读者需要知道数据、seed、版本和设备。

## 练习或延伸

1. 在 checkpoint 中增加 validation accuracy，并重新跑加载检查。
2. 把 `torch.use_deterministic_algorithms(True)` 注释掉，观察本机结果是否变化。
3. 写一个脚本读取 `history.csv`，输出 validation accuracy 最高的 epoch。

## 参考资料

- PyTorch 教程：[Saving and Loading Models](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
- PyTorch 文档：[torch.save](https://docs.pytorch.org/docs/stable/generated/torch.save.html)
- PyTorch 文档：[Reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html)


{% endraw %}
