---
layout: post
title: "PyTorch 训练工程第一课：config、验证集、checkpoint 和 resume 怎样留下证据"
date: 2026-04-16 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, pytorch, training-engineering, checkpoint, reproducibility, baseline, teaching]
---

一个模型能在 notebook 里跑通一次，只说明代码没有立刻崩。真正开始做项目时，问题会变成另一组：这次训练用了哪个配置？验证集是不是和测试集混了？中途断电后能不能从第 4 个 epoch 接着跑？最优 checkpoint 重新加载后预测是否一致？别人看报告时，能不能知道这个模型只是一个 toy task，而不是可部署模型？

这一篇不再追求更复杂的模型。我们用一个非常小的 PyTorch 二分类任务，专门训练“训练工程”的骨架：config、split、baseline、训练/评估模式、checkpoint、resume、JSONL 日志、model card 和 artifact manifest。配套代码在 [`deep-learning-pytorch-training-engineering`](/labs/#deep-learning-pytorch-training-engineering)，也可以直接看 [`README.md`](/assets/labs/deep-learning-pytorch-training-engineering/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-pytorch-training-engineering/run_lab.sh)。

## 学完要能做什么

读完并跑完实验后，你应该能解释五件事：

1. 为什么训练脚本不能只写超参数常量，而要有可哈希的 config。
2. 为什么模型结果前必须先报 majority baseline 和简单 heuristic baseline。
3. `model.train()`、`model.eval()`、`torch.no_grad()`分别改变什么边界。
4. checkpoint 里为什么不只保存 `model.state_dict()`，还要保存 optimizer、scheduler、epoch 和 config hash。
5. resume 是否正确，不能靠“继续跑了”判断，而要和 uninterrupted run 做可检查对照。

## 任务故意很小，因为重点不是模型能力

实验任务是二维点分类：

```text
输入: (x, y)
标签: 如果 x + y > 0，label = 1；如果 x + y < 0，label = 0
```

`x + y = 0` 的点被排除，因为边界点会让初学者分不清是模型错了，还是标签规则本身有歧义。实验从固定网格构造样本，再按类别平衡切分：

```text
TRAIN_SAMPLES=60
VAL_SAMPLES=16
TEST_SAMPLES=14
```

这个任务线性可分，`nn.Linear(2, 2)` 就能学会。这样做是有意的：如果任务本身很复杂，训练失败时很难判断是模型结构不够、数据太少、学习率不合适，还是 checkpoint/resume 写错了。第一节训练工程课应该把变量数量压低，让每个工程状态都能被检查。

## config 要能复现，也要能拒绝不匹配的 checkpoint

实验配置放在 `config/training_config.json`：

```json
{
  "seed": 314159,
  "device": "cpu",
  "epochs": 8,
  "checkpoint_epoch": 4,
  "learning_rate": 0.4,
  "momentum": 0.9,
  "scheduler_step_size": 4,
  "scheduler_gamma": 0.5
}
```

代码会把完整配置按稳定 JSON 顺序编码，然后计算 SHA-256：

```python
def stable_config_json(config):
    return json.dumps(config, sort_keys=True, separators=(",", ":"))

config_hash = sha256(stable_config_json(config).encode("utf-8")).hexdigest()
```

为什么需要引入 config hash？它的作用是防误用，而不是承担安全认证。加载 checkpoint 时，如果 checkpoint 里的 `config_hash` 和当前配置不同，脚本直接失败。否则一个常见错误会悄悄发生：你以为在继续上次训练，其实学习率、数据切分或模型结构已经换了。

实验输出里有一行：

```text
CONFIG_HASH_MATCH=yes
```

它证明当前 config 和 checkpoint 记录的 config 是同一个训练契约。

## baseline 先告诉你模型到底超过了什么

二分类数据平衡，所以 majority baseline 是：

```text
MAJORITY_BASELINE_ACC=0.500
```

再加一个故意不完整的 heuristic：只看 `x` 的符号，忽略 `y`：

```python
pred = 1 if x > 0 else 0
```

它在测试集上是：

```text
HEURISTIC_BASELINE_ACC=0.786
```

这两个数字让模型结果有了参照。如果最终模型是 `0.70`，它甚至不如简单规则；如果模型是 `1.00`，至少说明训练 loop、loss 和优化器在这个小规则上能工作。

最终实验输出是：

```text
FINAL_VAL_ACC=1.000
FINAL_TEST_ACC=1.000
```

这个 `1.000` 只属于这个合成任务，不代表真实泛化能力。文章和 model card 都会保留这个边界。

## 训练和评估是两种状态

训练时的核心步骤是：

```python
model.train()
optimizer.zero_grad(set_to_none=True)
logits = model(train_features)
loss = loss_fn(logits, train_labels)
loss.backward()
optimizer.step()
scheduler.step()
```

这里有三个状态变化：

- `zero_grad` 清掉上一轮梯度，否则梯度会累积。
- `backward` 把 loss 对参数的梯度写入各个 parameter。
- `optimizer.step` 根据当前梯度更新参数。

评估时不应该构建反向传播图：

```python
model.eval()
with torch.no_grad():
    logits = model(features)
    pred = logits.argmax(dim=1)
```

`model.eval()` 会把模块切到评估模式；这对 dropout、batch norm 这类模块尤其重要。`torch.no_grad()` 关闭梯度记录，减少不必要的内存和计算。即使这个实验的模型只有一个 `Linear`，仍然保留这两个动作，因为训练工程的习惯应该在小项目里就固定下来。

## checkpoint 不是只保存权重

只保存模型权重适合“训练完拿去推理”的场景。要从中途继续训练，checkpoint 至少需要这些字段：

```python
torch.save({
    "epoch": epoch,
    "config": config_dict,
    "config_hash": config_hash,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "scheduler_state_dict": scheduler.state_dict(),
    "torch_rng_state": torch.get_rng_state(),
    "metrics": metrics,
}, path)
```

原因分别是：

| 字段 | 不保存会怎样 |
| --- | --- |
| `epoch` | 不知道下一轮应该从第几个 epoch 开始 |
| `config_hash` | 可能用错配置继续训练 |
| `model_state_dict` | 模型参数无法恢复 |
| `optimizer_state_dict` | momentum、Adam 统计量等优化状态丢失 |
| `scheduler_state_dict` | 学习率进度丢失，resume 后学习率可能回到初始值 |
| `torch_rng_state` | 涉及随机采样、dropout、shuffle 时难以复现 |
| `metrics` | 不能判断这个 checkpoint 当时为什么被保存 |

恢复时先创建同结构的对象，再加载状态：

```python
model, optimizer, scheduler, loss_fn = make_training_objects(config)
checkpoint = torch.load(path, map_location="cpu", weights_only=True)
model.load_state_dict(checkpoint["model_state_dict"])
optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
```

PyTorch 官方文档也把 `torch.save`、`torch.load` 和 `load_state_dict` 作为保存/加载模型时必须熟悉的核心函数，并在 general checkpoint 例子里保存 epoch、model state 和 optimizer state。这里额外加入 scheduler、config hash 和 RNG state，是为了让“继续训练”这个动作更容易被检查。

## resume 要和 uninterrupted run 对照

这个实验不只检查“能加载”。它做了两个 run：

```text
full run:   epoch 1 -> 8，中途保存 epoch 4 checkpoint
resume run: 从 epoch 4 checkpoint 加载，再跑 epoch 5 -> 8
```

然后比较两个最终模型的参数：

```python
state_dicts_allclose(full_final.pt, resume_final.pt)
```

输出是：

```text
RESUME_MATCHES_FULL_RUN=yes
```

这比“resume 后 loss 继续下降”更强。后者只能说明训练没有坏到完全不能跑；前者说明在这个 deterministic CPU 实验里，中断再恢复和不中断训练到同一终点。

实验还会重新加载 best checkpoint，检查保存时记录的测试 logits 和重新前向计算得到的 logits 一致：

```text
BEST_CHECKPOINT_RELOAD_MATCH=yes
```

这一步抓的是另一类常见错误：checkpoint 文件存在，但加载后模型结构、权重或 eval 边界不一致。

## JSONL 日志、model card 和 manifest 分别解决什么问题

训练工程需要引入日志和清单，是因为一个 `.pt` 文件只能回答“参数在哪里”，不能回答“这次训练怎样发生、报告对应哪批文件、读者能否理解适用边界”。这个实验会生成：

```text
JSONL_LOG_ROWS=12
MODEL_CARD_READY=yes
ARTIFACT_MANIFEST_READY=yes
```

`JSONL_LOG_ROWS=12` 来自 8 行 full-run epoch 日志和 4 行 resume-run epoch 日志。JSONL 的好处是每一行都是独立 JSON，训练长了也能逐行追加、grep、采样或导入表格。

`model_card.md` 用来说明：任务是什么、数据怎么切、baseline 是多少、最终指标是多少、边界在哪里。它避免一个 toy 模型被误读成真实模型。

`artifact_manifest.json` 记录本地报告、日志、预测表和 checkpoint 的 SHA-256。它不能替代版本控制，但能回答一个很实际的问题：你现在看的报告和刚才训练生成的文件是不是同一批？

## 运行实验

如果当前 Python 环境已经安装 PyTorch：

```bash
cd assets/labs/deep-learning-pytorch-training-engineering
bash run_lab.sh
```

如果 `python3` 不能 import `torch`，指定解释器：

```bash
PYTORCH_LAB_PYTHON=/path/to/python bash run_lab.sh
```

成功后会看到这些稳定标记：

```text
CONFIG_HASH_MATCH=yes
TRAIN_SAMPLES=60
VAL_SAMPLES=16
TEST_SAMPLES=14
MAJORITY_BASELINE_ACC=0.500
HEURISTIC_BASELINE_ACC=0.786
FINAL_VAL_ACC=1.000
FINAL_TEST_ACC=1.000
BEST_CHECKPOINT_RELOAD_MATCH=yes
RESUME_MATCHES_FULL_RUN=yes
JSONL_LOG_ROWS=12
MODEL_CARD_READY=yes
ARTIFACT_MANIFEST_READY=yes
RUN_STATUS=ok
deep_learning_pytorch_training_engineering_lab_status=ok
```

生成的 `reports/` 是你的本地证据。公开仓库只保留源码、测试、配置和 runner，不提交 checkpoint、报告、缓存或模型权重。

## 常见错误

**1. 只保存模型权重，resume 后学习率或 momentum 不对。** 继续训练要保存 optimizer 和 scheduler 状态。否则恢复后的参数虽然对，优化轨迹已经变了。

**2. 验证集和测试集混用。** 验证集用于选择 checkpoint 和调超参数；测试集用于最后报告。这个实验里 `val` 和 `test` 都很小，但仍然分开，是为了固定习惯。

**3. 评估时忘记 `model.eval()` 或 `torch.no_grad()`。** 在只有 `Linear` 的 toy 模型里可能看不出差异，但一旦加入 dropout、batch norm 或大 batch，问题会暴露。

**4. checkpoint 文件存在就以为可复现。** 文件存在只是第一层。还要检查 config hash、reload prediction、resume 对照和报告哈希。

**5. 把 deterministic 当成跨机器保证。** 本实验在 CPU、单进程、小算子上做可复现检查。PyTorch 官方 reproducibility note 明确提醒：不同 PyTorch release、平台、CPU/GPU 执行之间不保证完全复现。真实项目要记录版本、硬件、设备、随机源和非确定性算子边界。

## 练习

1. 把 `checkpoint_epoch` 从 `4` 改成 `2`，重新运行。观察 `JSONL_LOG_ROWS` 是否还是 `epochs + (epochs - checkpoint_epoch)`。
2. 删除 `scheduler_state_dict` 的保存和加载，再比较 full run 与 resume run。你应该能看到 resume 不再严格等价。
3. 把 heuristic 改成 `x + y > 1`，重新计算 baseline。思考为什么 baseline 也必须写进报告，而不能只写模型 accuracy。
4. 把模型改成两层 MLP。指标不会更有意义，但 checkpoint 结构应该不变：训练工程契约不应该依赖具体模型层数。

## 参考资料

- PyTorch Tutorials: [Saving and Loading Models](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
- PyTorch Tutorials: [Optimizing Model Parameters](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)
- PyTorch API: [`torch.no_grad`](https://docs.pytorch.org/docs/stable/generated/torch.no_grad.html)
- PyTorch API: [`torch.use_deterministic_algorithms`](https://docs.pytorch.org/docs/stable/generated/torch.use_deterministic_algorithms.html)
- PyTorch Developer Notes: [Reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html)
