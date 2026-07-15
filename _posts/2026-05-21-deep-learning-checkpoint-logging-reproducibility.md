---
layout: post
title: "Checkpoint、日志和可复现性：让结果能被复查"
date: 2026-05-21 18:00:00 +0800
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

设想训练运行了二十分钟，终端最后只留下“accuracy=0.99”。第二天你无法回答：使用了哪个模型、哪个 seed、多少 epoch、哪份数据，或者这个数字能否由保存的权重重新得到。日志和 checkpoint 共同解决的正是“结果从哪里来、如何重建”。

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

## 四类产物分别证明什么

它们不能互相替代：

```text
environment.json ──证明──> 运行条件
history.csv      ──证明──> 训练过程
metrics.json     ──证明──> 冻结模型在各划分上的结果
checkpoint.pt    ──证明──> 可恢复的参数状态
```

history 能发现 loss 在中途发散，但不能恢复参数；checkpoint 能恢复参数，却不能说明训练是否稳定。可复查实验需要把二者关联到相同的 seed、模型配置和数据版本。

## 逐步实现

lab 保存 MLP checkpoint 后执行：

```bash
python -m dl_foundations.cli checkpoint-check \
  --checkpoint reports/mlp/checkpoint.pt \
  --output reports/checkpoint_check.json
```

输出记录加载后的 test accuracy，与训练结束时的 accuracy 一致。这说明保存的 `state_dict` 能恢复模型参数。

本次加载检查的预期输出为：

```json
{
  "checkpoint": "reports/mlp/checkpoint.pt",
  "test_accuracy_after_load": 0.9895833134651184
}
```

它与 `reports/mlp/metrics.json` 中的 `test.accuracy` 相同。可以再做一次机器可判定的核对：

```bash
python - <<'PY'
import json
from math import isclose

saved = json.load(open("reports/mlp/metrics.json"))["test"]["accuracy"]
loaded = json.load(open("reports/checkpoint_check.json"))["test_accuracy_after_load"]
assert isclose(saved, loaded, rel_tol=0.0, abs_tol=1e-12)
print(f"checkpoint_roundtrip_ok={loaded:.6f}")
PY
```

预期看到 `checkpoint_roundtrip_ok=0.989583`。如果断言失败，优先检查模型结构、数据 seed、预处理和 checkpoint 路径。

## checkpoint 中保存了哪些状态

本 lab 保存的是一个带元数据的字典：

```python
torch.save({
    "model_name": model_name,
    "model_state_dict": model.state_dict(),
    "seed": seed,
    "epochs": epochs,
    "learning_rate": learning_rate,
    "test_accuracy": test_metrics.accuracy,
}, checkpoint_path)
```

加载顺序必须与保存约定匹配：先读取元数据并构造同名模型，再加载 `state_dict`，最后用相同 seed 重建数据。生产项目通常还需要优化器状态、数据或代码版本、最佳 validation epoch 和文件校验值；当前教学包只声明“可恢复推理和评估”，不声明“可从中断 epoch 无缝续训”。

## 保存什么

- `environment.json`：Python、NumPy、PyTorch 版本和设备边界。
- `history.csv`：每个 epoch 的 train/validation loss 和 accuracy。
- `metrics.json`：最终 train/validation/test 指标。
- `checkpoint.pt`：模型名称、参数、seed、epoch、学习率和 test accuracy 摘要。
- `comparison.json`：baseline 与 MLP 的同表对照。

## 可复现性的边界

固定 seed 可以让本机实验稳定，但不同 PyTorch 版本、硬件平台和底层算子仍可能产生差异。因此公开写作应报告版本和实验边界，避免把一次本地结果写成跨平台保证。

本次实际环境记录为 Python 3.12.3、NumPy 2.4.6、PyTorch 2.12.1+cu130；lab 明确在 CPU 张量上训练。环境检测到 CUDA 可用，不等于本实验使用了 GPU。复现报告应区分“机器具备的能力”和“本次运行选择的设备”。

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
