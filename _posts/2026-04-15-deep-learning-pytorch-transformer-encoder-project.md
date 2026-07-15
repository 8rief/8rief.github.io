---
layout: post
title: "PyTorch Transformer encoder 项目：从 baseline 到训练、mask 和 checkpoint"
date: 2026-04-15 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, pytorch, transformer, training-loop, checkpoint, baseline, teaching]
---

前面几篇把 Transformer 拆成了机制：attention 负责读 value，position 和 mask 决定顺序与可见范围，multi-head 和 block 负责并行关系、残差路径、归一化和位置内变换。现在需要把这些机制放进一个真实 PyTorch 小项目里，否则初学者很容易停在“知道概念，但不知道一个训练脚本到底要有哪些部分”。

这一篇只做一件事：从一个 order-sensitive 小任务出发，写出可运行的 `nn.TransformerEncoder` 分类项目。它包含数据构造、baseline、padding mask、模型、训练循环、评估、checkpoint 和报告。任务很小，目标是把工程闭环搭清楚，而非证明模型能力很强。

配套代码在 [`deep-learning-pytorch-transformer-encoder`](/labs/#deep-learning-pytorch-transformer-encoder)，也可以直接看 [`README.md`](/assets/labs/deep-learning-pytorch-transformer-encoder/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-pytorch-transformer-encoder/run_lab.sh)。

## 先定义一个小到能解释的任务

输入序列固定为 5 个位置：

```text
<cls> token_0 token_1 N <pad>
```

`token_0` 和 `token_1` 只可能是 `A` 或 `B`。标签是这两个 token 的有序组合：

```text
AA, AB, BA, BB
```

注意这里是有序组合。`AB` 和 `BA` 的 token bag 相同，但标签不同。这个任务正好检查模型是否能使用 position 信息，而不是只看出现了哪些 token。

数据规模刻意很小：

```text
TRAIN_SAMPLES=48
TEST_SAMPLES=8
SEQUENCE_LENGTH=5
LABEL_COUNT=4
```

这样的样本量不能说明真实泛化能力，但足够检查项目结构是否正确：baseline 是否合理、mask 形状是否正确、训练 loop 是否真的更新参数、checkpoint reload 是否保持预测一致。

## baseline 先回答“不用 Transformer 能做到哪里”

任何模型训练前都要有 baseline。这里用三个确定性 baseline：

| baseline | 看到了什么 | 准确率 | 解释 |
| --- | --- | --- | --- |
| majority | 永远预测训练集中最多的标签 | `0.250` | 四类均衡，只能猜中一类 |
| last-token | 只看 `token_1`，默认 `token_0=A` | `0.500` | 能区分第二个 token，丢掉第一个 token |
| bag-sorted | 看 `{token_0, token_1}`，再排序 | `0.750` | `AA`、`BB`、`AB` 能对，`BA` 会和 `AB` 碰撞 |

对应输出是：

```text
MAJORITY_BASELINE_ACC=0.250
LAST_TOKEN_BASELINE_ACC=0.500
BAG_SORTED_BASELINE_ACC=0.750
```

这三个数字给训练结果设了边界。Transformer 如果只能达到 `0.750`，说明它没有真正解决顺序问题；如果能达到 `1.000`，至少说明在这个小规则上，position-aware encoder 已经把 `AB` 和 `BA` 分开了。

## 输入、label 和 padding mask 怎样变成 tensor

样本先被编码成整数：

```python
PAD = 0
CLS = 1
A = 2
B = 3
NOISE = 4
```

一条 `AB` 样本是：

```text
<cls> A B N <pad>
```

对应：

```python
[1, 2, 3, 4, 0]
```

label `AB` 对应一个类别 id，例如：

```python
LABELS = ["AA", "AB", "BA", "BB"]
```

padding mask 来自 `input_ids == PAD`：

```python
padding_mask = input_ids.eq(PAD)
```

PyTorch 的 `TransformerEncoderLayer` 在 `batch_first=True` 时，输入形状是：

```text
(batch, seq, feature)
```

`src_key_padding_mask` 的形状是：

```text
(batch, seq)
```

本实验检查：

```text
PADDING_MASK_SHAPE_OK=yes
PADDING_MASK_TRUE_COUNT=8
```

`PADDING_MASK_TRUE_COUNT=8` 是因为测试集有 8 条样本，每条样本最后一个位置都是 `<pad>`。

## 模型结构：embedding、position、encoder、classifier

最小模型包含四层：

```text
input ids
  -> token embedding + position embedding
  -> TransformerEncoderLayer
  -> 取 <cls> 位置
  -> Linear classifier
```

对应代码结构是：

```python
self.token_embedding = nn.Embedding(vocab_size, d_model, padding_idx=PAD)
self.position_embedding = nn.Embedding(max_len, d_model)

layer = nn.TransformerEncoderLayer(
    d_model=d_model,
    nhead=2,
    dim_feedforward=32,
    dropout=0.0,
    activation="gelu",
    batch_first=True,
    norm_first=True,
)
self.encoder = nn.TransformerEncoder(layer, num_layers=1, enable_nested_tensor=False)
self.classifier = nn.Linear(d_model, num_labels)
```

`position_embedding` 是这篇的关键。如果只有 token embedding，`AB` 和 `BA` 更容易被压成相同的 bag 表示；加上位置后，同一个 `A` 出现在 position 1 或 position 2 会得到不同表示。

前向计算里，位置 id 由序列长度生成：

```python
positions = torch.arange(seq_len).unsqueeze(0).expand(batch, seq_len)
hidden = token_embedding(input_ids) + position_embedding(positions)
encoded = encoder(hidden, src_key_padding_mask=padding_mask)
cls_state = encoded[:, 0, :]
logits = classifier(cls_state)
```

`logits` 的形状是：

```text
(batch, 4)
```

因为有四个标签：`AA`、`AB`、`BA`、`BB`。

## 训练循环要有哪些动作

训练循环最小闭环是：

```python
model.train()
for input_ids, labels, padding_mask in loader:
    optimizer.zero_grad(set_to_none=True)
    logits = model(input_ids, padding_mask)
    loss = criterion(logits, labels)
    loss.backward()
    optimizer.step()
```

这里的 loss 是：

```python
criterion = nn.CrossEntropyLoss()
```

`CrossEntropyLoss` 期望输入是未经过 softmax 的 logits，target 是类别 id。初学者常犯的错误是先手动 softmax 再交给 `CrossEntropyLoss`，这会让数值和梯度都变得不符合预期。

优化器使用：

```python
optimizer = torch.optim.AdamW(model.parameters(), lr=0.03, weight_decay=0.0)
```

这个学习率只适用于这个小实验。真实项目要用验证集、学习率搜索和更严格的训练记录。

## 评估要切换 eval，并关掉梯度

评估时应该写成：

```python
model.eval()
with torch.no_grad():
    logits = model(input_ids, padding_mask)
    preds = logits.argmax(dim=1)
```

`model.eval()` 会影响 dropout、batch norm 等模块的行为。这个实验里 dropout 设为 `0.0`，但仍保留 `eval()`，因为这是训练项目的基本边界。`torch.no_grad()` 告诉 PyTorch 不需要构建反向传播图，评估更省内存，也避免把评估误混进训练状态。

实验最终输出：

```text
TRANSFORMER_TRAIN_ACC=1.000
TRANSFORMER_TEST_ACC=1.000
TRANSFORMER_GAIN_OVER_BEST_BASELINE=0.250
LOSS_DECREASED=yes
```

`TRANSFORMER_GAIN_OVER_BEST_BASELINE=0.250` 的意思是：最佳 deterministic baseline 是 bag-sorted 的 `0.750`，训练后的 Transformer 达到 `1.000`，多出来的 `0.250` 来自正确区分 `AB` 和 `BA`。

## checkpoint 证明什么

训练结束后保存：

```python
torch.save({
    "model_state_dict": model.state_dict(),
    "labels": LABELS,
    "vocab": VOCAB,
}, path)
```

再创建一个同结构模型，加载：

```python
snapshot = torch.load(path, map_location=device)
reloaded.load_state_dict(snapshot["model_state_dict"])
```

然后比较 reload 前后的预测：

```text
CHECKPOINT_RELOAD_MATCH=yes
```

这个标记证明：当前模型权重可以被保存和恢复，恢复后的预测与保存前一致。它的证据边界只到推理一致性；真实任务泛化和可恢复训练还需要额外证据。完整恢复训练还要保存 optimizer state、epoch、随机种子、数据版本和配置。

## 实验怎么跑

这个包需要 PyTorch。默认 `python3` 没有安装 torch 时，先选择一个有 PyTorch 的 Python：

```bash
PYTORCH_LAB_PYTHON=/path/to/python ./run_lab.sh
```

如果你自己创建环境，可以按 PyTorch 官网为 CPU 或 CUDA 选择安装命令。不同系统的安装命令可能不同，不要在文章里照抄别人的 CUDA wheel。

运行成功会看到：

```text
TRAIN_SAMPLES=48
TEST_SAMPLES=8
SEQUENCE_LENGTH=5
LABEL_COUNT=4
MAJORITY_BASELINE_ACC=0.250
LAST_TOKEN_BASELINE_ACC=0.500
BAG_SORTED_BASELINE_ACC=0.750
TRANSFORMER_TRAIN_ACC=1.000
TRANSFORMER_TEST_ACC=1.000
TRANSFORMER_GAIN_OVER_BEST_BASELINE=0.250
LOSS_DECREASED=yes
PADDING_MASK_SHAPE_OK=yes
PADDING_MASK_TRUE_COUNT=8
POSITION_EMBEDDING_PRESENT=yes
CHECKPOINT_RELOAD_MATCH=yes
RUN_STATUS=ok
deep_learning_pytorch_transformer_encoder_lab_status=ok
```

运行后本地生成：

- `reports/pytorch_transformer_probe.json`：环境、baseline、模型指标和 gate 结果。
- `reports/training_history.csv`：关键 epoch 的 loss、train accuracy 和 test accuracy。
- `reports/prediction_table.csv`：每条测试样本的预测和 logits。
- `reports/pytorch_transformer_report.md`：简短报告。
- `reports/checkpoint.pt`：本地 checkpoint。

公开仓库不提交 `reports/` 和 checkpoint。学习时应该在自己的机器上重新生成。

## 和 PyTorch 文档的对应关系

PyTorch 文档里，`TransformerEncoderLayer` 的关键参数包括：

| 参数 | 本实验取值 | 作用 |
| --- | --- | --- |
| `d_model` | `16` | token 表示宽度 |
| `nhead` | `2` | attention head 数 |
| `dim_feedforward` | `32` | FFN 中间层宽度 |
| `dropout` | `0.0` | 小实验中关闭随机 dropout |
| `batch_first` | `True` | 输入使用 `(batch, seq, feature)` |
| `norm_first` | `True` | 先归一化再进子层，训练更稳定 |

`TransformerEncoder` 把一个 encoder layer 堆叠成多层。本实验只用一层，因为目标是检查项目闭环，深度留到后续训练工程再讨论。

`src_key_padding_mask` 用来告诉 encoder 哪些 key 位置是 padding。这个实验中每条样本最后一位是 `<pad>`，所以测试集的 padding mask 有 8 个 `True`。

## 常见错误

### 1. 没有 baseline 就说模型有效

`TRANSFORMER_TEST_ACC=1.000` 单独看没有意义。必须和 `MAJORITY_BASELINE_ACC`、`LAST_TOKEN_BASELINE_ACC`、`BAG_SORTED_BASELINE_ACC` 一起看，才能知道模型到底解决了什么。

### 2. 把 logits 先 softmax 再传给 CrossEntropyLoss

`nn.CrossEntropyLoss` 内部已经组合了 log-softmax 和 negative log-likelihood。训练时传 logits，不要先手动 softmax。

### 3. 忘记 padding mask

短序列 batch 化时通常会补 `<pad>`。如果不传 `src_key_padding_mask`，模型可能把 padding 当成真实 token。先用小样本检查 mask 形状和值，再训练。

### 4. 评估时不切换 eval

评估前写 `model.eval()`，评估块里写 `torch.no_grad()`。这一步明确隔离训练状态和评估状态。

### 5. checkpoint 只保存了权重，却声称能恢复训练

只保存 `model_state_dict` 可以恢复推理预测。要恢复训练，还需要 optimizer state、epoch、数据版本、配置和随机种子。

### 6. 把这个小任务当成真实泛化结论

这个实验是 synthetic rule check。它证明项目结构、mask、训练和 checkpoint 闭环能跑通，不证明真实语言理解能力。

## 练习

1. 去掉 `position_embedding`，重新训练并记录 `AB` 和 `BA` 是否还能稳定区分。
2. 把 `token_0 token_1` 扩展成三个位置，标签改成三 token 有序组合，观察 baseline 怎样变化。
3. 把 `dropout` 改成 `0.1`，比较固定 seed 下 loss 曲线是否仍稳定。
4. 保存 optimizer state 和 epoch，写一个 `resume` 命令，让训练能从 checkpoint 继续。
5. 把 `batch_first=True` 改成默认形式，重写输入维度，确认 shape 注释是否都要变化。
6. 在 `prediction_table.csv` 里找一条样本，手动解释 logits 最大值为什么对应预测标签。

## 继续往下学什么

完成这个包后，深度学习路线从机制实验进入了真实训练项目。下一步可以做两个方向：

1. **训练工程方向**：配置文件、日志、checkpoint resume、验证集、early stopping、model card 和可复现实验清单。
2. **模型任务方向**：把 synthetic 分类换成小文本分类或字符级语言模型，引入 tokenizer、Dataset、padding collate、学习率调度和错误样本分析。

无论走哪条路线，都继续保留 baseline。没有 baseline 的训练曲线，只能说明 loss 在变，不能说明模型解决了任务。

## 参考资料

- PyTorch `TransformerEncoderLayer` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html>
- PyTorch `TransformerEncoder` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoder.html>
- PyTorch `Embedding` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.Embedding.html>
- PyTorch `CrossEntropyLoss` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html>
- PyTorch 保存/加载模型教程：<https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html>
- PyTorch 官方安装入口：<https://pytorch.org/get-started/locally/>
