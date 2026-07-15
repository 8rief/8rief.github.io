---
layout: post
title: "Transformer 第一课：position 和 mask 怎样决定能看哪里"
date: 2026-04-14 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, transformer, attention, positional-encoding, causal-mask, baseline, teaching]
---

上一篇 attention 文章只解决了 query、key、value：query 找 key，key 定位 value，模型可以按需读取历史位置。这个机制还缺两条边界。第一，attention 本身更像在一组 memory slots 上做匹配；如果没有位置信息，`AB` 和 `BA` 很容易被看成同一袋 token。第二，自回归任务在第 `t` 步只能用过去和当前信息；如果 attention 能读未来位置，训练和评估就会泄漏答案。

所以进入 Transformer 前，必须先理解 position 和 mask。position 让模型知道一个内容出现在第几个位置；mask 决定哪些位置允许被读。它们是把 attention 变成序列模型时必须加上的约束。

配套代码在 [`deep-learning-transformer-position-mask`](/labs/#deep-learning-transformer-position-mask)，也可以直接看 [`README.md`](/assets/labs/deep-learning-transformer-position-mask/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-transformer-position-mask/run_lab.sh)。

## 任务一：没有 position 时，AB 和 BA 有什么区别

先看一个只问顺序的小任务：

```text
sequence=AB | query=position 0 | label=A
sequence=BA | query=position 0 | label=B
```

两个样本的 token bag 完全一样，都是一个 `A` 和一个 `B`。如果模型只知道出现了哪些 token，答案只能猜。要答对，模型必须知道“第 0 个位置是什么”。

实验比较三种方法：

| 方法 | 看到什么 | 预期表现 |
| --- | --- | --- |
| bag baseline | 只看 token 多重集合 | `AB` 和 `BA` 都是 `{A,B}`，50% |
| no-position attention | attention 只带 token identity，没有 position key | query=position 0 找不到对应 key，50% |
| positional attention | 每个 slot 有 position key，query 也表示 position 0 | 能选中第 0 个槽，100% |

这个最小例子隔离了一个事实：order-sensitive 任务需要位置信息进入模型；真实模型只是把 token、位置和表示空间换成了更高维的版本。

## 任务二：没有 mask 时，未来 token 会泄漏答案

再看一个只检查 mask 的小任务：

```text
sequence=A A A | query_index=1 | future_index=2 | label=A
sequence=A A B | query_index=1 | future_index=2 | label=B
```

在位置 1 做预测时，位置 2 是未来。未加 mask 的 attention 如果允许 query 直接读位置 2，就能 100% 读出答案。这种结果看起来很高，其实是数据泄漏。

实验比较两种方法：

| 方法 | 允许读取的位置 | 预期表现 |
| --- | --- | --- |
| unmasked future lookup | 可以读位置 2 | 100%，但靠未来泄漏 |
| causal masked lookup | 只能读 `index <= 1` | 未来权重为 0，剩余上下文没有标签信息，50% |

这里的 50% 是正确边界：没有未来信息时，当前上下文确实无法区分两个样本。mask 的作用是防止模型在训练时偷看答案。

## 实验怎么跑

在公开仓库中执行：

```bash
cd assets/labs/deep-learning-transformer-position-mask
bash run_lab.sh
```

成功时会看到这些稳定标记：

```text
ORDER_TEST_SAMPLES=8
FUTURE_TEST_SAMPLES=8
POSITION_BAG_BASELINE_ACC=0.500
NO_POSITION_ATTENTION_ACC=0.500
POSITIONAL_ATTENTION_ACC=1.000
POSITION_GAIN_OVER_BEST_BASELINE=0.500
POSITION_MIN_TOP_WEIGHT=0.944
POSITION_TOP_MATCHES_QUERY=yes
UNMASKED_FUTURE_LOOKUP_ACC=1.000
CAUSAL_MASKED_LOOKUP_ACC=0.500
MASK_BLOCKS_FUTURE=yes
RUN_STATUS=ok
deep_learning_transformer_position_mask_lab_status=ok
```

运行后本地会生成：

- `reports/position_mask_probe.json`：两组任务的 metrics 和边界说明。
- `reports/position_mask_report.md`：方法对比和解释。
- `reports/order_trace_table.csv`：顺序任务的预测和 position attention 权重。
- `reports/future_trace_table.csv`：mask 任务的预测、future weight 和 causal weight。

公开仓库不提交 `reports/`。这些结果应该由学习者在自己的机器上重新生成。

## positional attention 怎样选中第 0 个位置

实验里的 position 向量是手写 one-hot：

```python
def position_vector(position, size):
    return one_hot(position, size, scale=2.0)
```

顺序任务中，query 表示 `position 0`，每个 slot 的 key 也表示自己的位置：

```python
query = position_vector(0, 2)
keys = [position_vector(0, 2), position_vector(1, 2)]
values = [token_vector(token) for token in sequence]
```

attention 计算仍然是上一篇的公式：

```text
scores = Q K^T / sqrt(d_k)
weights = softmax(scores)
output = weights V
```

对于 `sequence=BA`，position-aware attention 会给第 0 个槽最高权重：

```text
position 0 weight ≈ 0.944
position 1 weight ≈ 0.056
output 最大分量对应 B
```

这就是：

```text
POSITIONAL_ATTENTION_ACC=1.000
POSITION_TOP_MATCHES_QUERY=yes
```

no-position attention 失败的原因也很具体。它没有 position key，query=position 0 无法和任何 token key 对齐，于是两个槽权重相同，`AB` 和 `BA` 都会被平均成同一个输出。平均以后顺序信息已经丢失。

## causal mask 怎样阻止读未来

mask 的核心动作是改 attention score。被屏蔽的位置在 softmax 前设为负无穷：

```python
masked_scores = [score if keep else float("-inf")]
weights = softmax(masked_scores)
```

在自回归任务里，位置 `t` 只能读 `index <= t` 的槽：

```python
allowed = [index <= query_index for index in range(len(sequence))]
```

对于 `query_index=1`、`future_index=2` 的样本，causal mask 会把位置 2 屏蔽掉。报告里可以看到：

```text
MASK_BLOCKS_FUTURE=yes
CAUSAL_MASKED_LOOKUP_ACC=0.500
```

`MASK_BLOCKS_FUTURE=yes` 的证据是所有测试样本里 future slot 的 attention weight 都等于 0。`CAUSAL_MASKED_LOOKUP_ACC=0.500` 的含义是：当前位置能看到的上下文没有包含未来标签，所以只剩平衡猜测。

unmasked 的 100% 也要谨慎解读：

```text
UNMASKED_FUTURE_LOOKUP_ACC=1.000
```

它读取了不该读取的位置，因此不能当作模型能力。很多序列模型 bug 都出在这里：训练时无意泄漏未来，评估时分数很好，真正生成时效果崩掉。

## 和 PyTorch API 的关系

PyTorch 的 `torch.nn.Transformer.generate_square_subsequent_mask(sz)` 会生成一个方形 causal mask：不允许看的位置填 `-inf`，允许看的位置填 `0.0`。这和本实验里的 `masked_scores` 是同一个思想。

`torch.nn.MultiheadAttention` 和 `torch.nn.Transformer` 都支持 mask，但要注意具体 API 的布尔语义。按照 PyTorch 文档：

- `Transformer` 里的布尔 mask 通常表示不允许 attention 的位置。
- `MultiheadAttention` 的 `key_padding_mask=True` 表示对应 key 位置要被忽略。
- `scaled_dot_product_attention` 的布尔 `attn_mask` 语义不同，`True` 表示允许参与 attention。

因此写 PyTorch 版本时，不要凭变量名猜 mask 方向。先构造一个 3 个 token 的样本，明确检查被屏蔽位置的 attention weight 是否为 0，再进入训练。

position 也有多种实现。原始 Transformer 使用 sinusoidal positional encoding；很多现代模型使用 learned position embedding、relative position 或 rotary position embedding。初学时先抓住共同目标：把位置信息注入到 attention 可以使用的表示里。

## 常见错误

### 1. 以为 attention 天然知道顺序

点积 attention 只比较向量。没有 position 信息时，换序后的相同 token 集合很容易产生相同表示。序列顺序必须通过 position encoding、相对位置或其他结构进入模型。

### 2. 把 unmasked 高分当成模型能力

如果任务要求预测未来，而 attention 训练时能看到未来 token，高分可能来自泄漏。自回归任务必须检查 causal mask。

### 3. mask 方向写反

布尔 mask 在不同 PyTorch API 中语义可能相反。最小检查方法是：给某个位置一个很容易识别的 value，mask 掉它，然后确认输出和 attention weight 都不再使用它。

### 4. 忽略 padding mask

causal mask 处理时间方向，padding mask 处理 batch 中的无效 token。短句补齐成长句后，如果 padding 没有被 mask，模型可能把 `<pad>` 当成真实信息。

### 5. 把这篇当成完整 Transformer 实现

这篇只解释两个支撑机制。完整 Transformer block 还需要 multi-head attention、feed-forward network、residual connection、LayerNorm、dropout、训练目标和优化过程。

## 练习

1. 把顺序任务改成问 `position 1`，确认 positional attention 仍然能选中正确槽。
2. 把序列长度从 2 扩展到 4，构造同 token bag 不同顺序的样本，观察 bag baseline 为什么继续失败。
3. 把 `POSITION_SCALE` 改成 `1.0`，观察 `POSITION_MIN_TOP_WEIGHT` 怎样变化。
4. 在 mask 任务中把 `query_index` 从 1 改成 0，确认能读的位置更少。
5. 写一个 padding mask 小实验：把真实序列后面补 `<pad>`，检查 `<pad>` 的 attention weight 是否为 0。
6. 用 PyTorch `generate_square_subsequent_mask(4)` 打印 mask，解释每一行哪些列能被读。

## 继续往下学什么

学完这篇后，Transformer 路线可以继续这样走：

1. 用 PyTorch 重写 causal mask 和 padding mask 的最小样本，先验证 mask 方向。
2. 学 multi-head attention：不同 head 可以在不同子空间里读不同关系。
3. 学 feed-forward、residual 和 LayerNorm：attention 读信息，后续层负责变换、稳定和组合。
4. 合成最小 Transformer encoder block，先做小任务，不急着训练大模型。
5. 最后再进入 tokenizer、embedding、训练 loop、评估、checkpoint 和部署边界。

## 参考资料

- PyTorch `Transformer` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.Transformer.html>
- PyTorch `MultiheadAttention` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html>
- PyTorch `scaled_dot_product_attention` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html>
- Vaswani et al., Attention Is All You Need：<https://arxiv.org/abs/1706.03762>
- Dive into Deep Learning, Attention Mechanisms and Transformers：<https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html>
