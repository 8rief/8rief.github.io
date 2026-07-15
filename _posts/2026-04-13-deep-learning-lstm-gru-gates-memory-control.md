---
layout: post
title: "LSTM/GRU 第一课：gate 为什么能控制写入和保留"
date: 2026-04-13 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, lstm, gru, sequence-modeling, gates, baseline, teaching]
---

上一篇 RNN 文章说明了 hidden state 的基本作用：每一步用 `x_t` 和 `h_{t-1}` 更新状态，开头的 cue 可以被带到最后。这个机制足够解释短 delayed-cue 任务，但它也暴露出一个新问题：如果后面每个 token 都参与同一条更新式，后来的噪声也会不断改写 hidden state。

这篇只解决一个问题：**序列模型怎样区分“这一步应该写入新信息”和“这一步应该保留旧信息”**。LSTM 和 GRU 的核心价值正在这里。它们在 recurrent update 里加入 gate，让模型学习写入、保留、遗忘和暴露状态的时机。

配套代码在 [`deep-learning-lstm-gru-gates`](/labs/#deep-learning-lstm-gru-gates)，也可以直接看 [`README.md`](/assets/labs/deep-learning-lstm-gru-gates/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-lstm-gru-gates/run_lab.sh)。

## 先看 RNN 会怎样被后缀覆盖

继续使用 delayed-cue 任务。每个样本有 13 个 token：

```text
A x x y x y y x y x y x y
B x x y x y y x y x y x y
```

第一个 token 决定标签：

- `A...` → `topic_a`
- `B...` → `topic_b`

后面 12 个 `x/y` 是 distractor。关键设计是：同一段后缀会分别配上 `A` 和 `B`。因此只看后缀、只看最后一个 token，或者被后缀覆盖的模型，都无法稳定判断标签。

这次比较五种方法：

| 方法 | 主要输入 | 预期结果 |
| --- | --- | --- |
| majority baseline | 训练集标签频率 | 标签平衡，50% |
| last-token baseline | 最后一个 `x/y` | 后缀和标签配对打乱，50% |
| vanilla RNN | 每一步都把当前 token 写进同一个 hidden state | 后缀持续覆盖 cue，50% |
| idealized LSTM gates | cue 写入 cell，distractor 只保留 cell | 100% |
| idealized GRU update gate | cue 写入 hidden，distractor 保留 hidden | 100% |

这里的 LSTM/GRU gate 是手写的理想 gate，参数没有从训练中学习。这样做的目的是先看清机制：gate 如果能学到正确的开关，状态为什么能抵抗后续噪声。

## 实验怎么跑

在公开仓库中执行：

```bash
cd assets/labs/deep-learning-lstm-gru-gates
bash run_lab.sh
```

成功时会看到这些稳定标记：

```text
TRAIN_SAMPLES=16
TEST_SAMPLES=16
SEQUENCE_LENGTH=13
MAJORITY_BASELINE_ACC=0.500
LAST_TOKEN_ACC=0.500
VANILLA_RNN_ACC=0.500
LSTM_GATE_ACC=1.000
GRU_UPDATE_GATE_ACC=1.000
GATE_GAIN_OVER_BEST_BASELINE=0.500
LSTM_CELL_STABLE=yes
GRU_KEEP_STABLE=yes
RUN_STATUS=ok
deep_learning_lstm_gru_lab_status=ok
```

运行后本地会生成：

- `reports/gate_probe.json`：accuracy、trace 和边界说明。
- `reports/gate_report.md`：方法对比表和解释。
- `reports/trace_table.csv`：每个测试样本的预测、vanilla hidden、LSTM cell、GRU hidden。

公开仓库不提交 `reports/`。这些报告应该由学习者在自己的机器上重新生成。

## vanilla RNN 的失败路径

实验里的 vanilla RNN 使用一维 hidden state：

```python
VANILLA_RECURRENT_WEIGHT = 0.2
VANILLA_INPUT_WEIGHT = 1.4


def vanilla_rnn_step(previous_hidden, token):
    return math.tanh(
        VANILLA_RECURRENT_WEIGHT * previous_hidden
        + VANILLA_INPUT_WEIGHT * token_signal(token)
    )
```

`A/x` 映射为正信号，`B/y` 映射为负信号。第一步 cue 的确能写进 hidden state；问题在后面 12 个 distractor。由于 recurrent weight 只有 `0.2`，旧状态每一步只留下很小一部分，而当前 `x/y` 输入权重大。经过多步更新后，最终 hidden state 主要反映后缀末端，开头 cue 的影响被压得很小。

这正是 `VANILLA_RNN_ACC=0.500` 的含义。它没有证明所有 RNN 都只能做到 50%，它证明在这个设置下，同一个无门控更新式会被后续输入覆盖。要解决这个失败，需要把“写入”这件事从“时间步存在”里分离出来：看到新 token，并不等于必须把它写进长期状态。

## LSTM 把 cell state 单独拿出来

PyTorch 文档里的 LSTM 一步包含四个门：input gate、forget gate、cell candidate、output gate。把公式压缩成状态更新，可以看成：

```text
c_t = f_t * c_{t-1} + i_t * g_t
h_t = o_t * tanh(c_t)
```

这两行非常适合初学者先理解：

- `c_t` 是 cell state，更像长期记忆通道。
- `f_t` 控制上一时刻 cell state 保留多少。
- `i_t` 控制候选信息 `g_t` 写入多少。
- `o_t` 控制 cell state 暴露到 hidden state 多少。

本实验用理想 gate 写成纯 Python：

```python
def lstm_gate_step(previous_cell, token):
    if token in {"A", "B"}:
        forget_gate = 0.0
        input_gate = 1.0
        candidate = cue_candidate(token)
    else:
        forget_gate = 1.0
        input_gate = 0.0
        candidate = token_signal(token)

    output_gate = 1.0
    cell = forget_gate * previous_cell + input_gate * candidate
    hidden = output_gate * math.tanh(cell)
    return cell, hidden
```

这段代码只表达一个策略：

| 时间步 | token 类型 | `f_t` | `i_t` | 结果 |
| --- | --- | ---: | ---: | --- |
| 第 1 步 | cue `A/B` | 0 | 1 | 清空旧 cell，写入 cue |
| 后续步 | distractor `x/y` | 1 | 0 | 保留旧 cell，拒绝写入 distractor |

因此以 `A` 开头的样本，cell 第一步变成 `+1`；以 `B` 开头的样本，cell 第一步变成 `-1`。后面 12 个 distractor 来了，`f_t=1`、`i_t=0`，cell 不再变化。

实验用 `LSTM_CELL_STABLE=yes` 检查这件事。它比 accuracy 更具体：

```text
A x x y ...: c after first = +1, c final = +1
B x x y ...: c after first = -1, c final = -1
```

`LSTM_GATE_ACC=1.000` 来自这个状态路径，后缀统计没有提供标签信息。

## GRU 用 update gate 合并“写入”和“保留”

GRU 没有单独的 cell state，它直接更新 hidden state。按 PyTorch 文档的约定，核心更新可以写成：

```text
h_t = (1 - z_t) * n_t + z_t * h_{t-1}
```

这里 `z_t` 是 update gate。注意这个约定下，`z_t` 越接近 1，越保留旧 hidden；越接近 0，越采用新 candidate `n_t`。

实验里的理想 GRU gate 是：

```python
def gru_gate_step(previous_hidden, token):
    if token in {"A", "B"}:
        update_gate = 0.0
        candidate = math.tanh(cue_candidate(token))
    else:
        update_gate = 1.0
        candidate = math.tanh(token_signal(token))

    hidden = (1.0 - update_gate) * candidate + update_gate * previous_hidden
    return hidden
```

它的状态策略是：

| 时间步 | token 类型 | `z_t` | 结果 |
| --- | --- | ---: | --- |
| 第 1 步 | cue `A/B` | 0 | 用新 candidate 写入 hidden |
| 后续步 | distractor `x/y` | 1 | 保留 `h_{t-1}` |

所以 GRU 在这个任务上也能把 cue 保留到最后，实验标记是：

```text
GRU_UPDATE_GATE_ACC=1.000
GRU_KEEP_STABLE=yes
```

LSTM 和 GRU 的形态不同，但这篇要抓住共同点：它们都提供了一条可学习的门控路径，让模型可以把“看到输入”和“修改记忆”拆开。

## 结果怎样解读

核心输出是：

```text
MAJORITY_BASELINE_ACC=0.500
LAST_TOKEN_ACC=0.500
VANILLA_RNN_ACC=0.500
LSTM_GATE_ACC=1.000
GRU_UPDATE_GATE_ACC=1.000
GATE_GAIN_OVER_BEST_BASELINE=0.500
```

这条证据链分三层：

1. 数据层：同一后缀同时配 `A` 和 `B`，所以后缀规则没有标签信息。
2. 机制层：vanilla RNN 每一步都写当前输入，后缀会覆盖早期 cue。
3. 门控层：LSTM/GRU 先写 cue，再对 distractor 选择 keep，状态保持稳定。

因此本实验的结论是：**gate 的价值在于给状态更新增加可学习的控制变量**。这个控制变量能表示“现在写入”“现在保留”“现在遗忘”“现在暴露多少”。

## 和真实 PyTorch LSTM/GRU 的关系

真实 `torch.nn.LSTM` 和 `torch.nn.GRU` 会从数据中学习 gate 的权重。它们的 gate 是 sigmoid 输出的连续值，输入通常是 shape 为 `(seq, batch, feature)` 或在 `batch_first=True` 时为 `(batch, seq, feature)` 的张量。

如果用 PyTorch 重写这个实验，最容易混淆三件事：

| 对象 | LSTM | GRU |
| --- | --- | --- |
| 输出序列 | `output`，每个时间步最后一层的 hidden | `output`，每个时间步最后一层的 hidden |
| 最终 hidden | `h_n` | `h_n` |
| 长期 cell | `c_n` | 没有单独 cell |

LSTM 的 `h_n` 和 `c_n` 承担不同角色。`c_n` 更接近长期记忆通道，`h_n` 是经过 output gate 暴露出来的状态。GRU 则把这两者合在 hidden state 中，用 update gate 控制保留或更新。

## 常见错误

### 1. 把 gate 当成固定规则

这篇的 gate 是手写的，因为教学目标是看清状态路径。真实模型的 gate 由权重、输入和上一 hidden state 共同算出，需要通过 loss 和反向传播学习。

### 2. 只说 LSTM 适合长序列，却不解释为什么

“适合长序列”只是结论。机制上，LSTM 的 cell state 可以通过 `f_t * c_{t-1}` 形成更直接的保留路径；当 `f_t` 接近 1 且 `i_t` 接近 0 时，旧信息不会被每个新 token 强制覆盖。

### 3. 混淆 GRU update gate 的方向

在 PyTorch 文档采用的公式里：

```text
h_t = (1 - z_t) * n_t + z_t * h_{t-1}
```

所以 `z_t` 接近 1 表示保留旧 hidden。阅读其他材料时要先确认它使用的记号约定。

### 4. 把这篇当作性能 benchmark

这个实验只有合成数据和手写 gate。它证明 gate 控制写入/保留的机制，不证明 LSTM/GRU 在真实文本、时间序列或语音任务上一定优于某个模型。真实任务需要训练集、验证集、错误分析和更强 baseline。

## 练习

1. 把 suffix 长度从 12 改成 30，观察 vanilla RNN 是否更依赖末尾 distractor。
2. 把 LSTM distractor 步的 `input_gate` 从 `0.0` 改成 `0.2`，观察 cell state 何时开始漂移。
3. 把 GRU distractor 步的 `update_gate` 从 `1.0` 改成 `0.8`，比较 final hidden 的变化。
4. 增加一个 first-token oracle，确认它也是 100%，然后解释为什么它不能替代 recurrent/gated 机制分析。
5. 用二维状态改写 LSTM：`A` 写入 `[1, 0]`，`B` 写入 `[0, 1]`，再比较报告可读性。
6. 下一步用 PyTorch 训练版本重写同一个任务，检查 learned gates 是否真的学到了接近“cue 写入、distractor 保留”的模式。

## 继续往下学什么

学完这篇后，序列模型路线可以继续这样走：

1. 用 `nn.LSTMCell` 或 `nn.GRUCell` 写单步版本，打印每一步 shape 和 state。
2. 用 `nn.LSTM` 或 `nn.GRU` 训练 delayed-cue 分类器，比较 vanilla RNN、LSTM、GRU 的验证集表现。
3. 学 variable-length sequence、padding、packing 和 mask，避免把 padding 当成真实 token。
4. 进入 attention：当序列更长时，与其把所有历史压进一个固定 hidden state，不如让模型按需读取历史位置。
5. 最后再做小型文本分类或字符语言模型，保留 majority、last-token、bag-of-words、RNN、LSTM/GRU、attention 等 baseline。

## 参考资料

- PyTorch `LSTM` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.LSTM.html>
- PyTorch `GRU` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.GRU.html>
- Hochreiter and Schmidhuber, Long Short-Term Memory（PDF copy）：<https://deeplearning.cs.cmu.edu/S23/document/readings/LSTM.pdf>
- Cho et al., Learning Phrase Representations using RNN Encoder–Decoder for Statistical Machine Translation：<https://aclanthology.org/D14-1179/>
- Dive into Deep Learning, Modern Recurrent Neural Networks：<https://d2l.ai/chapter_recurrent-modern/index.html>
