---
layout: post
title: "PyTorch 推理工程第一课：eval、inference_mode、batching 和 latency 边界怎么检查"
date: 2026-04-17 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, pytorch, inference, deployment, batching, latency, teaching]
---

训练脚本跑完以后，很多初学者会把 `model(x)` 直接放进服务或批处理脚本里。这个动作看起来简单，实际会引出一组新的工程问题：Dropout 还在随机丢特征吗？BatchNorm 还在用当前 batch 统计量吗？推理时有没有继续构建 autograd graph？逐条预测和 batch 预测是否一致？计时的时候有没有把 Python 循环、warmup、GPU 异步执行混在一起？checkpoint 重新加载后的输出是否真的一样？

这一篇用一个小的 PyTorch 二分类模型回答这些问题。模型故意包含 Dropout 和 BatchNorm，让 `model.train()` 和 `model.eval()` 的差异可以被观察到。任务本身只是二维点分类；文章重点是推理边界，而非模型结构。

配套代码在 [`deep-learning-pytorch-inference-boundary`](/labs/#deep-learning-pytorch-inference-boundary)，也可以直接看 [`README.md`](/assets/labs/deep-learning-pytorch-inference-boundary/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-pytorch-inference-boundary/run_lab.sh)。

## 学完要能做什么

读完并运行实验后，你应该能解释：

1. `model.eval()` 改变的是哪些 module 行为；
2. `torch.no_grad()` 和 `torch.inference_mode()` 解决什么问题；
3. 为什么推理脚本仍然要保留 batch 维度；
4. 为什么 batch 输出和逐条输出应该在容差内一致；
5. 为什么本地 latency 只能作为边界清晰的 smoke evidence；
6. checkpoint 重新加载后应该检查什么；
7. 哪些结论不能从 toy CPU timing 外推到生产服务。

## 为什么需要单独讲推理工程

训练阶段关心 loss 是否下降、验证集是否变好；推理阶段关心同一份权重在真实输入上能不能稳定、可追溯、可计时地给出结果。两者共享模型代码，却有不同的运行状态：训练要打开梯度和随机正则化，推理要固定 module 行为、关闭梯度记录、保存输入输出证据，并写清计时边界。把推理当成训练脚本的最后一行，会让这些状态变化藏在默认值里。

## 任务故意简单：把推理边界看清楚

实验数据来自一个二维网格：

```text
输入: (x0, x1)
标签: 如果 x0 + 0.75 * x1 > 0，label = 1；否则 label = 0
```

靠近边界的点被去掉，避免标签噪声干扰推理边界。切分结果是：

```text
TRAIN_SAMPLES=417
VAL_SAMPLES=59
TEST_SAMPLES=118
MAJORITY_BASELINE_ACC=0.492
```

模型是一个很小的 MLP：

```python
class InferenceDemoNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Dropout(p=0.35),
            nn.Linear(16, 2),
        )

    def forward(self, features):
        return self.net(features)
```

Dropout 和 BatchNorm 在这里承担教学作用：它们让模式切换变成可观察状态。没有这些层，忘记 `eval()` 可能不会立刻暴露。

## 第一步：训练结束后先保存可加载的状态

实验训练小模型后保存 checkpoint：

```python
torch.save({
    "model_state_dict": model.state_dict(),
    "input_dim": 2,
    "labels": [0, 1],
}, checkpoint_path)
```

推理脚本要重新构造同样的模型类，再加载权重：

```python
payload = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
reloaded = InferenceDemoNet()
reloaded.load_state_dict(payload["model_state_dict"])
```

然后比较加载前后的测试指标：

```text
CHECKPOINT_RELOAD_MATCH=yes
```

这个检查很重要。推理阶段最危险的情况是静默错配：脚本没有崩溃，但模型类、权重、标签顺序或输入预处理已经和训练时不一致，结果看起来正常，含义却变了。

## 第二步：`model.eval()` 让 module 进入评估行为

`eval()` 不会关闭 autograd，它改变的是 module 的训练/评估模式。Dropout 在训练模式下会随机屏蔽部分激活，BatchNorm 在训练模式下会使用当前 batch 的统计量并更新 running stats；评估模式下，它们使用推理时应有的确定行为。

实验用同一批输入跑两次训练模式，再跑两次评估模式：

```text
TRAIN_MODE_OUTPUT_CHANGED=yes
EVAL_OUTPUT_STABLE=yes
```

对应代码逻辑是：

```python
model.train()
train_logits_a = model(features)
train_logits_b = model(features)

model.eval()
with torch.no_grad():
    eval_logits_a = model(features)
    eval_logits_b = model(features)
```

`TRAIN_MODE_OUTPUT_CHANGED=yes` 说明训练模式下 Dropout 仍在影响输出。`EVAL_OUTPUT_STABLE=yes` 说明评估模式下同一输入得到稳定结果。部署或批量预测前漏掉 `model.eval()`，模型可能不会报错，但输出语义已经不是推理语义。

## 第三步：用 `inference_mode` 关闭推理中的 autograd 负担

`eval()` 管 module 行为；autograd graph 是否构建是另一件事。推理时通常不需要梯度，实验使用：

```python
model.eval()
with torch.inference_mode():
    logits = model(batch.features)
```

报告里有两个检查：

```text
INFERENCE_MODE_ENABLED_INSIDE=yes
INFERENCE_REQUIRES_GRAD=no
```

`torch.no_grad()` 也会关闭梯度记录；`torch.inference_mode()` 面向纯推理路径，通常能进一步减少 autograd 和版本计数相关开销。第一课不需要记住所有内部细节，只要建立边界：`eval()` 和 `inference_mode()` 解决的是两个不同层面的问题，推理脚本一般要同时处理。

## 第四步：推理也要保留 batch 维度

单条样本的 feature 是两个数：

```text
[x0, x1]
```

模型实际期望的是带 batch 维度的二维张量：

```text
[batch, 2]
```

实验同时跑 batch 推理和逐条推理，并比较 logits 最大差异：

```text
BATCH_OUTPUT_MATCH=yes
```

这里用的是容差比较，不是逐 bit 相等。CPU 上 batch 矩阵运算和单样本循环可能走不同计算路径，出现 `1e-6` 量级的浮点差异很正常。真正要检查的是：输出是否在合理容差内一致，预测类别和概率是否没有语义漂移。

## 第五步：prediction table 是推理证据，不只是打印 accuracy

推理脚本会生成 `predictions.csv`，每行包含：

```text
sample_id,x0,x1,gold,pred,prob_1
```

这比只打印 `MODEL_TEST_ACC=1.000` 更有用。accuracy 能说明总体正确率，prediction table 能让你检查具体样本、输入特征、预测类别和概率是否匹配。实验输出：

```text
MODEL_TEST_ACC=1.000
MODEL_BEATS_BASELINE=yes
PREDICTION_TABLE_ROWS=118
```

对于真实项目，prediction table 还应该带上输入版本、预处理版本、模型版本、标签映射版本和运行时间。这里保留最小字段，是为了先把推理证据的形状看清楚。

## 第六步：latency 计时要先写清边界

实验记录了 batch 和逐条推理的本地 CPU 时间：

```text
BATCH_TIMING_RECORDED=yes
```

报告里的示例值类似：

```text
Batch per sample: 0.14 us
Single per sample: 14.58 us
```

这个差距主要来自 Python 循环和调用开销。它能说明“batching 会改变吞吐边界”，但不能写成生产性能结论。生产 benchmark 至少要补充：硬件、线程数、模型大小、输入分布、warmup、重复次数、p50/p95/p99、是否包含预处理/后处理、是否使用 GPU、是否有网络和序列化开销。

如果使用 CUDA，还要记住 GPU 操作通常是异步的。只在 Python 里 `start = time.time(); model(x); end = time.time()`，很可能只测到 kernel 提交时间。CUDA timing 需要事件或显式同步，例如在测量边界里调用 `torch.cuda.synchronize()`。

## 本地怎么运行

如果你的默认 Python 已经能 import PyTorch：

```bash
cd assets/labs/deep-learning-pytorch-inference-boundary
bash run_lab.sh
```

如果 PyTorch 在另一个虚拟环境里：

```bash
PYTORCH_LAB_PYTHON=/path/to/python ./run_lab.sh
```

成功后会看到：

```text
MODEL_BEATS_BASELINE=yes
TRAIN_MODE_OUTPUT_CHANGED=yes
EVAL_OUTPUT_STABLE=yes
INFERENCE_MODE_ENABLED_INSIDE=yes
INFERENCE_REQUIRES_GRAD=no
BATCH_OUTPUT_MATCH=yes
BATCH_TIMING_RECORDED=yes
CHECKPOINT_RELOAD_MATCH=yes
RUN_STATUS=ok
deep_learning_pytorch_inference_boundary_lab_status=ok
```

`reports/` 是你本机生成的证据目录，公开仓库不提交它。重点看这些文件：

| 文件 | 用途 |
| --- | --- |
| `inference_probe.json` | split、metric、mode check、batch check、timing 和 checkpoint hash |
| `training_history.csv` | 训练过程 selected epoch 指标 |
| `predictions.csv` | 推理输出表 |
| `artifact_manifest.json` | 本地生成报告和 checkpoint 的清单 |
| `inference_report.md` | 人类可读摘要 |
| `checkpoint.pt` | 本地生成权重，不应提交到公开仓库 |

## 常见错误

### 1. 只写 `eval()`，忘记关闭梯度

`model.eval()` 不等于关闭 autograd。推理脚本还应该使用 `torch.no_grad()` 或 `torch.inference_mode()`。否则输出可能正确，但内存和计算开销更大，还可能在长批处理里积累无意义的 graph。

### 2. 只写 `inference_mode()`，忘记 `eval()`

`inference_mode()` 不会自动把 Dropout、BatchNorm 切到评估行为。推理路径一般需要：

```python
model.eval()
with torch.inference_mode():
    logits = model(features)
```

### 3. 单条输入少了 batch 维度

`[2]` 和 `[1, 2]` 是不同形状。某些模型会直接报错，某些模型可能广播或走到不符合预期的路径。推理接口最好固定接收 `[batch, feature]`。

### 4. 把 toy timing 当成生产 benchmark

本实验只证明计时边界的写法。生产服务还要测数据加载、预处理、后处理、序列化、网络、队列和并发。GPU 上还要处理异步执行和同步边界。

### 5. checkpoint 加载后不做输出一致性检查

`load_state_dict` 成功只说明参数名和形状匹配。标签映射、输入标准化、模型版本和后处理仍可能错。至少要保留一组固定输入，比较 reload 前后的 logits、predictions 或 metrics。

## 练习和延伸

1. 把 `Dropout(p=0.35)` 改成 `p=0.0`，观察 `TRAIN_MODE_OUTPUT_CHANGED` 是否变化，并解释原因。
2. 把 batch size 从 128 改成 1、16、64、256，记录 `batch_per_sample_us` 的趋势，但不要把它写成生产结论。
3. 给 `predictions.csv` 增加 `model_sha256` 和 `run_id` 字段，让每一行预测能追溯到 checkpoint。
4. 如果你的机器有 CUDA，增加一个 GPU timing 分支，使用 CUDA event 或 `torch.cuda.synchronize()` 明确测量边界。
5. 把这个 toy 模型包装成一个只接收 JSON 输入的本地 CLI，要求输出预测表和错误码。

## 边界

这篇只证明 PyTorch 推理路径的几个最低限度边界：评估模式、无梯度推理、checkpoint 重载、batch 输出一致性、预测表和本地 timing 记录。它不覆盖模型服务框架、ONNX/TorchScript 导出、量化、GPU kernel 优化、多进程服务、A/B 测试或线上监控。后续如果进入部署，需要单独建立服务接口、输入 schema、并发、资源限制、日志、指标和回滚策略。

## 参考资料

- PyTorch `Module.eval` 文档：<https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.eval>
- PyTorch `torch.no_grad` 文档：<https://docs.pytorch.org/docs/stable/generated/torch.no_grad.html>
- PyTorch `torch.inference_mode` 文档：<https://docs.pytorch.org/docs/stable/generated/torch.autograd.grad_mode.inference_mode.html>
- PyTorch `torch.utils.data` 文档：<https://docs.pytorch.org/docs/stable/data.html>
- PyTorch 保存和加载模型教程：<https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html>
- PyTorch CUDA 异步执行说明：<https://docs.pytorch.org/docs/stable/notes/cuda.html#asynchronous-execution>
