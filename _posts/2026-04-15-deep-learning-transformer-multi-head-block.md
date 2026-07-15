---
layout: post
title: "Transformer 第二课：multi-head 和 block 怎样把多种关系合在一起"
date: 2026-04-15 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, transformer, multi-head-attention, residual, layer-norm, feed-forward, baseline, teaching]
---

前面已经把 attention、position 和 mask 拆开看过。现在还差一个关键问题：真实 Transformer 为什么要把 attention 做成多头，又为什么在 attention 后面接 residual、LayerNorm 和 feed-forward network？

一个单头 attention 可以按 query 找到一个 value。这个能力很强，但它仍然可能遇到信息瓶颈：同一个 token 的下一步判断可能同时依赖两个不同位置、两种不同关系或两个不同子空间。如果把这些关系压成一个标量或一个混合表示，后面的层可能无法恢复被压掉的区别。multi-head 的核心价值是让多个 head 并行提出不同问题，再把答案拼起来或投影回模型维度。

Transformer block 解决的是另一层问题。attention 负责从别的位置读信息，但当前位置原本的局部信号不能丢；读来的上下文还需要被非线性变换成当前 token 的新表示。residual connection 保留原信号，LayerNorm 控制尺度，feed-forward network 在每个位置上做进一步组合。

配套代码在 [`deep-learning-transformer-block`](/labs/#deep-learning-transformer-block)，也可以直接看 [`README.md`](/assets/labs/deep-learning-transformer-block/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-transformer-block/run_lab.sh)。

## 任务一：一个位置要同时读取两个事实

先构造一个很小的 pair lookup 任务。样本里有两个独立事实：

```text
position 0: color = A 或 B
position 2: shape = X 或 Y
label = color|shape
```

共有四种标签：

```text
A|X, A|Y, B|X, B|Y
```

如果一个机制只读 color，它不知道 shape；只读 shape，它不知道 color。更隐蔽的问题是 blended single head：它尝试用一个标量同时表示两个事实。设 `A=-1, B=+1, X=-1, Y=+1`，混合标量近似为：

```text
score = 0.5 * color + 0.5 * shape
```

于是两种不同标签发生碰撞：

```text
A|Y -> 0.5 * (-1) + 0.5 * (+1) = 0
B|X -> 0.5 * (+1) + 0.5 * (-1) = 0
```

只看这个标量，后续层无法区分 `A|Y` 和 `B|X`。这不是说所有单头模型都必然失败；如果给单头足够宽的 value 空间和足够好的投影，它也可能编码更多信息。本实验刻意把输出压成一个标量，是为了隔离 multi-head 最容易理解的一种作用：在固定瓶颈下，把不同读取结果分开保存。

## multi-head 的最小模型

实验用两个 head：

| head | query 目标 | value 内容 | 负责回答 |
| --- | --- | --- | --- |
| head 0 | position 0 | color code | `A` 还是 `B` |
| head 1 | position 2 | shape code | `X` 还是 `Y` |

每个 head 仍然执行同一个 attention 公式：

```text
scores = Q K^T / sqrt(d_k)
weights = softmax(scores)
head_output = weights V
```

区别在于两个 head 的 query 不同，value 投影也不同。head 0 只把 color 读出来，head 1 只把 shape 读出来。两个结果合起来就是：

```text
[color_score, shape_score]
```

这个二元表示能区分全部四个标签。

实验对比四种方法：

| 方法 | 信息状态 | 准确率 |
| --- | --- | --- |
| single first head | 只读 color，shape 用默认猜测 | `0.500` |
| single second head | 只读 shape，color 用默认猜测 | `0.500` |
| single blended head | 一个标量混合两个事实，两个标签碰撞 | `0.750` |
| two-head lookup | 两个 head 分别保存两个事实 | `1.000` |

稳定标记里对应：

```text
SINGLE_FIRST_HEAD_ACC=0.500
SINGLE_SECOND_HEAD_ACC=0.500
SINGLE_BLEND_HEAD_ACC=0.750
MULTI_HEAD_PAIR_ACC=1.000
MULTI_HEAD_GAIN_OVER_BEST_BASELINE=0.250
HEADS_FOCUS_DIFFERENT_KEYS=yes
```

`HEADS_FOCUS_DIFFERENT_KEYS=yes` 检查的是两个 head 的最高权重是否落在不同位置：color head 选 position 0，shape head 选 position 2。

## 任务二：attention 读来上下文后，本地信号不能丢

再看一个 Transformer block 任务。当前位置需要同时知道：

```text
local signal: 当前 token 自己是 A 还是 B
context signal: 从别的位置读来的上下文是 X 还是 Y
label = local|context
```

这和真实序列模型很像。当前位置的词本身有意义，周围上下文也有意义。只看自己或只看上下文都不够。

实验比较三种 block 变体：

| 方法 | 缺了什么 | 结果 |
| --- | --- | --- |
| no-attention block | 只有 local，没有 context | `0.500` |
| no-residual block | attention 带来 context，但 local 被覆盖 | `0.500` |
| attention + residual + FFN | local 和 context 都保留，再做位置内组合 | `1.000` |

稳定标记：

```text
NO_ATTENTION_BLOCK_ACC=0.500
NO_RESIDUAL_BLOCK_ACC=0.500
ATTENTION_RESIDUAL_FFN_ACC=1.000
BLOCK_GAIN_OVER_BEST_BASELINE=0.500
```

这里的 residual 可以写成最小形式：

```text
mixed = local_vector + attention_context_vector
```

如果 `local_vector` 表示 `A/B`，`attention_context_vector` 表示 `X/Y`，相加后的 `mixed` 同时包含两个事实。position-wise feed-forward/readout 再在当前位置把它变成标签。

## 为什么还要 LayerNorm

深层网络里，每一层都会改变向量尺度。如果尺度持续漂移，后续层会更难训练。LayerNorm 的基本动作是对同一个 token 的特征维做归一化：

```text
normalized = (x - mean(x)) / sqrt(var(x) + eps)
```

本实验为了让 LayerNorm 的效果可检查，使用成对的平衡编码：

```text
A -> [-1, +1, 0, 0]
B -> [+1, -1, 0, 0]
X -> [0, 0, -1, +1]
Y -> [0, 0, +1, -1]
```

local 和 context 相加后，向量均值为 0，RMS 为 1。LayerNorm 后仍然保留符号结构，报告检查：

```text
LAYER_NORM_MEAN_OK=yes
LAYER_NORM_RMS_OK=yes
```

这个例子只解释 LayerNorm 的尺度控制和可检查性。真实模型中的 LayerNorm 还会配合可学习的缩放和平移参数，常见 block 也有 pre-norm 和 post-norm 两种布局。

## 实验怎么跑

在公开仓库中执行：

```bash
cd assets/labs/deep-learning-transformer-block
bash run_lab.sh
```

成功时会看到：

```text
PAIR_TEST_SAMPLES=8
BLOCK_TEST_SAMPLES=8
SINGLE_FIRST_HEAD_ACC=0.500
SINGLE_SECOND_HEAD_ACC=0.500
SINGLE_BLEND_HEAD_ACC=0.750
MULTI_HEAD_PAIR_ACC=1.000
MULTI_HEAD_GAIN_OVER_BEST_BASELINE=0.250
MULTI_HEAD_MIN_TOP_WEIGHT=0.968
HEADS_FOCUS_DIFFERENT_KEYS=yes
NO_ATTENTION_BLOCK_ACC=0.500
NO_RESIDUAL_BLOCK_ACC=0.500
ATTENTION_RESIDUAL_FFN_ACC=1.000
BLOCK_GAIN_OVER_BEST_BASELINE=0.500
LAYER_NORM_MEAN_OK=yes
LAYER_NORM_RMS_OK=yes
RUN_STATUS=ok
deep_learning_transformer_block_lab_status=ok
```

运行后本地生成：

- `reports/transformer_block_probe.json`：所有对照实验的指标。
- `reports/transformer_block_report.md`：简短报告。
- `reports/multi_head_trace_table.csv`：single-head、blended-head 和 two-head 的逐样本预测。
- `reports/block_trace_table.csv`：no-attention、no-residual 和完整 block 的逐样本预测。

公开仓库不提交这些 `reports/`。学习时应该自己运行生成，再对照文章解释。

## 代码里的关键状态

multi-head 部分的两个 head 使用不同 query：

```python
color_output = attention(position_query(0), keys, color_values)
shape_output = attention(position_query(2), keys, shape_values)
prediction = classify(color_output, shape_output)
```

blended single head 使用一个混合 query 和一个标量输出：

```python
query = position_query(0) + position_query(2)
score = attention(query, keys, blended_values)
```

问题出在 `score` 是一个标量。它能表示 `-1, 0, +1` 三种状态，却要区分四种标签，所以会碰撞。

block 部分的核心状态变化是：

```python
residual = local_vector(token)
context = attention(query_for_context, keys, context_values)
mixed = residual + context
normalized = layer_norm(mixed)
prediction = feed_forward_readout(normalized)
```

这里的 feed-forward/readout 是手写分类器，用来表示“当前位置内部的非线性组合”。真实 Transformer 里的 FFN 通常是两层线性层加激活函数，例如 `Linear(d_model, dim_feedforward) -> activation -> Linear(dim_feedforward, d_model)`。

## 和 PyTorch API 的关系

PyTorch 的 `torch.nn.MultiheadAttention` 使用 `embed_dim` 表示总模型维度，`num_heads` 表示并行 head 数。官方文档说明每个 head 的维度是：

```text
head_dim = embed_dim // num_heads
```

前向计算返回：

```text
attn_output, attn_output_weights
```

`attn_output` 是读完 value 之后的表示，`attn_output_weights` 可以用来检查每个 query 关注了哪些 key。实际训练时不应只看最终 loss；小样本调试阶段应该打印或断言 attention weight 的方向是否符合任务边界。

`torch.nn.TransformerEncoderLayer` 把 multi-head self-attention 和 position-wise feed-forward network 放在同一层里，并带有 dropout、LayerNorm、residual 相关结构。它的关键参数包括 `d_model`、`nhead`、`dim_feedforward`、`dropout`、`activation`、`batch_first` 和 `norm_first`。初学时先把这些参数对应到本实验：

| PyTorch 参数/组件 | 本实验中的角色 |
| --- | --- |
| `d_model` / `embed_dim` | 每个 token 的总表示宽度 |
| `nhead` / `num_heads` | 并行读取几种关系 |
| attention weights | 每个 head 读哪些位置 |
| residual | 把 local signal 加回去 |
| LayerNorm | 控制 token 表示尺度 |
| feed-forward | 在每个位置内部组合特征 |

## 常见错误

### 1. 只把 multi-head 理解成“多个一样的 attention”

多个 head 的价值不在数量本身，而在不同 head 可以学习不同投影、不同关系和不同位置模式。调试时可以先问：每个 head 应该负责什么关系？有没有所有 head 都塌缩到同一种关注模式？

### 2. 把 attention 输出当成完整 token 表示

attention 输出主要来自 value 的加权和。没有 residual，当前位置原有信息可能被覆盖。很多结构图把 residual 画成一条短线，但它承担的是信息保留路径。

### 3. 忽略 feed-forward 的位置内计算

attention 负责跨位置混合，FFN 负责对每个位置的表示做进一步变换。只会写 attention 还不等于理解 Transformer block。

### 4. 把 LayerNorm 当成无关细节

LayerNorm 不改变序列长度，也不直接读取别的位置，所以容易被跳过。训练深层模型时，它影响尺度、梯度和稳定性。pre-norm 与 post-norm 的差异也会影响训练行为。

### 5. 用大模型结果掩盖小机制错误

如果一个最小样本里 attention head 读错位置、mask 方向写反、residual 漏掉，大模型训练可能仍然给出一个看似下降的 loss。先让小样本可解释，再扩大数据和模型。

## 练习

1. 把 pair lookup 改成三个事实：color、shape、size。先设计 single scalar baseline，再设计 three-head 输出。
2. 把 `POSITION_SCALE` 从 `3.0` 改成 `1.0`，观察 `MULTI_HEAD_MIN_TOP_WEIGHT` 如何下降。
3. 让两个 head 都查询 position 0，确认 `HEADS_FOCUS_DIFFERENT_KEYS` 会失败，并解释为什么准确率下降。
4. 在 block 任务中移除 residual，观察 local 信息怎样消失。
5. 把 LayerNorm 输入改成非平衡编码，比较归一化前后的均值、RMS 和分类结果。
6. 用 PyTorch 写一个 `MultiheadAttention(embed_dim=4, num_heads=2, batch_first=True)` 的最小样本，打印 `attn_output_weights`。

## 继续往下学什么

现在可以把 Transformer 的支撑机制连起来：

1. attention：query/key/value 负责按需读取。
2. position/mask：决定顺序和可见范围。
3. multi-head：并行读取不同关系。
4. residual/LayerNorm/FFN：保留本地信号、稳定尺度并做位置内变换。

下一步适合做一个完整的最小 Transformer encoder block：用 PyTorch 跑一个小分类任务，保留 baseline、mask 检查、训练曲线、checkpoint 和错误样本分析。再往后才进入 tokenizer、embedding、语言模型训练和部署边界。

## 参考资料

- PyTorch `MultiheadAttention` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html>
- PyTorch `TransformerEncoderLayer` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html>
- PyTorch `Transformer` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.Transformer.html>
- Vaswani et al., Attention Is All You Need：<https://arxiv.org/abs/1706.03762>
- Dive into Deep Learning, Attention Mechanisms and Transformers：<https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html>
