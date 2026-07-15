---
layout: post
title: "Attention 第一课：query、key、value 为什么能按需读取历史位置"
date: 2026-04-14 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, attention, transformer, query-key-value, baseline, teaching]
---

RNN、LSTM 和 GRU 都把序列历史压进一个状态。门控结构能控制写入和保留，已经比最简 RNN 稳定很多；但如果任务需要在结尾根据一个问题回看某个早期位置，固定长度状态仍然会承受压力。信息越多，越难把每个位置的细节和它的用途都压成一个向量。

Attention 的第一层价值是把“压缩全部历史”改成“按查询读取历史”。它让模型为当前位置构造一个 query，用 query 去比较每个历史位置的 key，再按权重读取对应的 value。这个机制在 Transformer 里成为核心组件，但初学时先看清 query、key、value 的数据流更重要。

配套代码在 [`deep-learning-attention-key-value`](/labs/#deep-learning-attention-key-value)，也可以直接看 [`README.md`](/assets/labs/deep-learning-attention-key-value/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-attention-key-value/run_lab.sh)。

## 先构造一个固定摘要会失败的任务

每个样本有四个记忆槽：

```text
red:apple blue:coin green:leaf gold:sky | query=blue | label=coin
```

四个 key 固定为 `red`、`blue`、`green`、`gold`。四个 value 固定为 `apple`、`sky`、`leaf`、`coin`。每个样本都包含同一组 key 和同一组 value，只改变 key-value 配对。标签由 query 指向的 key 决定：`query=blue` 时，答案就是 `blue` 这个 key 当前绑定的 value。

这类任务要保存的是绑定关系：

```text
blue -> coin
```

如果只知道样本里出现过 `apple/sky/leaf/coin`，答案仍然不确定。固定摘要容易丢失这种绑定关系，因为它把多个槽混在一起。Attention 的优势正好可以在这个小任务里看出来：query 先找到 key，再读这个 key 对应的 value。

实验比较五种方法：

| 方法 | 看到什么 | 预期表现 |
| --- | --- | --- |
| majority baseline | 训练集最常见标签 | 四类标签平衡，25% |
| last-value baseline | 最后一个记忆槽的 value | query 只在四分之一样本问最后一个 key，25% |
| bag-of-values baseline | value 多重集合 | 每个样本都是同一组 value，25% |
| fixed-summary baseline | 四个 value 向量的平均值 | 绑定关系被平均掉，25% |
| attention lookup | query-key 匹配后读 value | 能读到正确槽，100% |

## 实验怎么跑

在公开仓库中执行：

```bash
cd assets/labs/deep-learning-attention-key-value
bash run_lab.sh
```

成功时会看到这些稳定标记：

```text
TRAIN_SAMPLES=32
TEST_SAMPLES=32
MEMORY_SLOTS=4
KEY_DIM=4
VALUE_DIM=4
MAJORITY_BASELINE_ACC=0.250
LAST_VALUE_ACC=0.250
BAG_OF_VALUES_ACC=0.250
FIXED_SUMMARY_ACC=0.250
ATTENTION_LOOKUP_ACC=1.000
ATTENTION_GAIN_OVER_BEST_BASELINE=0.750
ATTENTION_MIN_TOP_WEIGHT=0.711
TOP_KEYS_MATCH_QUERY=yes
RUN_STATUS=ok
deep_learning_attention_lab_status=ok
```

运行后本地会生成：

- `reports/attention_probe.json`：accuracy、attention weights 和边界说明。
- `reports/attention_report.md`：方法对比表和解释。
- `reports/trace_table.csv`：每个测试样本的 query、slots、预测和 attention 权重。

公开仓库不提交 `reports/`。学习时应该在自己的机器上重新跑出这些证据。

## query、key、value 分别承担什么角色

先不要把 attention 想成大模型组件。它在这个任务里只有三类向量：

| 名称 | 来自哪里 | 在本任务中的含义 |
| --- | --- | --- |
| query | 要回答的问题 | 我现在要找哪个 key，例如 `blue` |
| key | 每个记忆槽的索引 | 这个槽叫什么，例如 `red`、`blue` |
| value | 每个记忆槽的内容 | 找到槽以后要读出的答案，例如 `coin` |

数据流可以画成：

```text
query=blue
    │
    ├─ compare with key(red)   -> small weight -> value(apple)
    ├─ compare with key(blue)  -> large weight -> value(coin)
    ├─ compare with key(green) -> small weight -> value(leaf)
    └─ compare with key(gold)  -> small weight -> value(sky)
                                      │
                                      ▼
                            weighted sum -> coin
```

这个结构保留了两条路径：key 用来定位，value 用来读内容。定位和内容分开以后，模型就可以表达“用 blue 找到槽，再读取这个槽里的 coin”。

## scaled dot-product attention 怎样算

PyTorch 的 `scaled_dot_product_attention` 对应的核心公式是：

```text
scores = Q K^T / sqrt(d_k)
weights = softmax(scores)
output = weights V
```

本实验只做单个 query 和四个 memory slots，所以可以写成纯 Python：

```python
def scaled_dot_product_attention(query, keys, values):
    scale = 1.0 / math.sqrt(len(query))
    scores = [dot(query, key) * scale for key in keys]
    weights = softmax(scores)
    output = weighted_sum(weights, values)
    return output, weights, scores
```

每个 key 是 one-hot 向量并乘以一个固定 scale。`query=blue` 时，query 向量和 `key=blue` 的点积最大，和其他 key 的点积为 0。softmax 会把最大 score 转成最大的权重。

一个典型 trace 长这样：

```text
slots:   red:apple blue:coin green:leaf gold:sky
query:   blue
weights: red:0.096 blue:0.711 green:0.096 gold:0.096
output:  value vector 最大分量对应 coin
```

`ATTENTION_MIN_TOP_WEIGHT=0.711` 表示所有测试样本里，正确 key 的 attention weight 至少是 0.711。这个值保留了 softmax 的连续权重特征；即使权重仍是软分布，正确 value 的分量依然最大，所以 `ATTENTION_LOOKUP_ACC=1.000`。

## fixed summary 为什么失败

fixed-summary baseline 把四个 value 向量平均：

```python
def predict_fixed_summary(sample):
    summary = average(value_vector(slot.value) for slot in sample.slots)
    return argmax(summary)
```

每个样本都包含 `apple/sky/leaf/coin` 各一次。平均以后总是同一个向量：

```text
[0.25, 0.25, 0.25, 0.25]
```

这个 summary 没有记录 `blue` 绑定了哪个 value。分类器只能按 tie-break 输出同一个答案，因此在四类平衡测试集上是 25%。

这个失败来自输入信息被压扁。平均值里看不到 key-value binding；后续分类器再复杂，也无法从这个 summary 恢复哪个 value 属于 `blue`。

## attention 结果怎样解读

核心输出是：

```text
MAJORITY_BASELINE_ACC=0.250
LAST_VALUE_ACC=0.250
BAG_OF_VALUES_ACC=0.250
FIXED_SUMMARY_ACC=0.250
ATTENTION_LOOKUP_ACC=1.000
ATTENTION_GAIN_OVER_BEST_BASELINE=0.750
TOP_KEYS_MATCH_QUERY=yes
```

这条证据链分三层：

1. 数据层：每个样本有同一组 key 和同一组 value，标签只由 query 指向的绑定关系决定。
2. baseline 层：只看标签频率、最后 value、value 集合或平均 summary，都无法恢复绑定关系。
3. attention 层：query-key score 让正确 key 得到最大权重，weighted value 输出对应答案。

所以本实验的结论是：**attention 的基础能力是按 query 在历史位置中寻址，然后读取对应 value**。Transformer 在这个基础上组合多头、位置编码、前馈网络、残差、归一化和 mask。

## 和 PyTorch API 的关系

真实 PyTorch 里常见两个入口：

- `torch.nn.functional.scaled_dot_product_attention`
- `torch.nn.MultiheadAttention`

`MultiheadAttention` 的输入通常是 query、key、value 三个张量。默认 shape 是 `(seq, batch, feature)`；设置 `batch_first=True` 后是 `(batch, seq, feature)`。输出包括 attention output；如果要求返回权重，还可以得到 attention weights。

需要注意两点：

1. PyTorch 的 mask 语义要按具体 API 查文档。`MultiheadAttention` 的 padding mask 中，`True` 通常表示这个 key 位置要被忽略；`scaled_dot_product_attention` 的布尔 `attn_mask` 语义不同，`True` 表示允许参与 attention。
2. Multi-head attention 会把 embedding 投影到多个子空间；每个 head 可以学习不同的匹配关系，再把结果拼接和投影。

这篇暂不训练 PyTorch 模型，因为目标是先建立机制。如果下一步用 PyTorch 重写，优先检查每个张量的 shape、mask 方向、attention weight 是否真的看向 query 指定的位置，然后再看 loss 曲线。

## 常见错误

### 1. 把 attention weight 当成最终答案

attention weight 表示模型从哪些位置读取信息。最终输出是 `weights V`，也就是按权重加权后的 value 向量。权重大说明读取多，但答案还取决于 value 里存了什么。

### 2. 忽略 key 和 value 的分工

如果 key 和 value 混在一起，很容易把 attention 误解成“相似 token 互相平均”。更准确的说法是：query 和 key 决定权重，value 决定被读出的内容。

### 3. 忘记除以 `sqrt(d_k)`

key/query 维度变大时，点积幅度会变大，softmax 更容易饱和。scaled dot-product attention 用 `sqrt(d_k)` 缩放 score，让训练更稳定。这个缩放不改变本实验的 argmax 结果，但会影响权重分布。

### 4. 把 attention 等同于完整 Transformer

Transformer block 还包含 multi-head attention、position 信息、feed-forward network、residual connection、LayerNorm、dropout 和 mask。attention 是核心寻址/读取机制，不等于完整模型。

### 5. mask 方向写反

不同 API 的布尔 mask 约定可能相反。写 PyTorch 版本时，要用一个极小样本检查被 mask 的位置权重是否变成 0，再进入真实训练。

## 练习

1. 把 `KEY_SCALE` 从 `2.0` 改成 `1.0`，观察 `ATTENTION_MIN_TOP_WEIGHT` 怎样变化，accuracy 是否仍然是 1.000。
2. 把 memory slots 从 4 个扩展到 8 个，保持每个样本只问一个 key，观察 baseline 和 attention 的差距。
3. 给 key 向量加一点噪声，观察什么时候 top key 开始选错。
4. 增加一个 hard-argmax lookup baseline，解释它和 softmax attention 的差别。
5. 用 PyTorch `scaled_dot_product_attention` 重写同一个例子，打印 query/key/value/output 的 shape。
6. 下一步加入 causal mask：让某个位置只能看它之前的位置，解释这和自回归语言模型有什么关系。

## 继续往下学什么

学完这篇后，深度学习路线可以继续这样走：

1. 用 PyTorch 重写单头 scaled dot-product attention，先只检查 shape、weights 和 mask。
2. 学 multi-head attention：为什么要把同一序列投影到多个子空间。
3. 学位置编码：attention 本身只看集合式的 key/value，序列顺序需要额外信息进入模型。
4. 学 causal mask 和 padding mask：哪些位置允许读，哪些位置必须屏蔽。
5. 再把 attention、feed-forward、residual 和 LayerNorm 组合成最小 Transformer block。

## 参考资料

- PyTorch `scaled_dot_product_attention` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html>
- PyTorch `MultiheadAttention` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html>
- PyTorch `Transformer` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.Transformer.html>
- Vaswani et al., Attention Is All You Need：<https://arxiv.org/abs/1706.03762>
- Dive into Deep Learning, Attention Mechanisms and Transformers：<https://d2l.ai/chapter_attention-mechanisms-and-transformers/index.html>
