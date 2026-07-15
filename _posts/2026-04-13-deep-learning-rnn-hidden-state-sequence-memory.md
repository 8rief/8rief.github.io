---
layout: post
title: "RNN 第一课：hidden state 为什么能把开头信息带到最后"
date: 2026-04-13 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, rnn, sequence-modeling, hidden-state, baseline, teaching]
---

CNN 那篇解决的是空间结构：同一个局部形状移动到新位置，卷积核仍然应该能认出来。序列模型面对的是另一类结构：有些信息出现在开头，但判断要到结尾才发生。只看最后一个 token，或者只看一段后缀，经常看不到真正的依据。

这篇先不训练语言模型，也不引入 LSTM/GRU/attention。我们只做第一层机制：RNN 的 hidden state 怎样随着时间步更新，为什么 `h_t` 里同时有当前输入和历史信息，怎样用 baseline 证明“记忆”这件事确实解决了一个具体失败。

配套代码在 [`deep-learning-rnn-hidden-state`](/labs/#deep-learning-rnn-hidden-state)，也可以直接看 [`README.md`](/assets/labs/deep-learning-rnn-hidden-state/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-rnn-hidden-state/run_lab.sh)。

## 先构造一个必须记住开头的任务

每个样本是一串 6 个 token：

```text
A x y y x x
B y x y x x
```

第一个 token 是 `A` 或 `B`，它决定标签：

- `A...` → `topic_a`
- `B...` → `topic_b`

后面五个 token 只有 `x` 和 `y`。这些后缀被刻意做成平衡的：`x/y` 计数一致，最后一个 token 也不能可靠指示标签。这样可以排除一种偷懒解释：最后一个 token 或后缀统计本身不足以答对，任务要求模型把开头的信息带到最后。

实验比较五种方法：

| 方法 | 看到什么 | 预期表现 |
| --- | --- | --- |
| majority baseline | 只输出训练集中最多的标签 | 标签平衡，所以 50% |
| last-token baseline | 只看最后一个 token | 最后 token 与标签无关，所以 50% |
| suffix-bag baseline | 只看第 2 到第 6 个 token 的计数 | 后缀计数被平衡，所以 50% |
| no-recurrence final state | 每一步只看当前 token，不带 `h_{t-1}` | 最后 token 是中性输入，所以 50% |
| recurrent hidden state | 每一步用当前输入和上一 hidden state 更新 | 能把开头 cue 带到最后，在这个机制任务上 100% |

这个任务很小，但它抓住了 RNN 的入口问题：序列分类不只是在最后一步读一个 token，而是在不断更新一个历史状态。

## 实验怎么跑

在公开仓库中执行：

```bash
cd assets/labs/deep-learning-rnn-hidden-state
bash run_lab.sh
```

成功时会看到这些稳定标记：

```text
TRAIN_SAMPLES=8
TEST_SAMPLES=8
SEQUENCE_LENGTH=6
MAJORITY_BASELINE_ACC=0.500
LAST_TOKEN_ACC=0.500
SUFFIX_BAG_ACC=0.500
NO_RECURRENCE_ACC=0.500
RNN_MEMORY_ACC=1.000
MEMORY_GAIN_OVER_BEST_BASELINE=0.500
HIDDEN_SIGN_STABLE=yes
RUN_STATUS=ok
deep_learning_rnn_lab_status=ok
```

运行后本地会生成：

- `reports/rnn_probe.json`：机器可读的 accuracy、trace 和边界说明。
- `reports/rnn_report.md`：人能读的逐样本对比表。
- `reports/trace_table.csv`：每个测试样本的预测和 hidden state 数值。

公开仓库不提交 `reports/`。学习时应该在自己的机器上重新跑出这些证据。

## RNN 的一步到底算了什么

最简 RNN 可以写成：

```text
h_t = tanh(W_x x_t + W_h h_{t-1} + b)
```

这行式子里有两个来源：

- `x_t`：当前时间步看到的输入。
- `h_{t-1}`：上一时间步留下的状态。

本实验用一维 hidden state，把它写成更直观的纯 Python：

```python
RECURRENT_WEIGHT = 2.0
INPUT_WEIGHT = 3.0


def token_input(token):
    if token == "A":
        return 1.0
    if token == "B":
        return -1.0
    if token in {"x", "y"}:
        return 0.0
    raise ValueError(f"unknown token {token}")


def recurrent_step(previous_hidden, token):
    return math.tanh(
        RECURRENT_WEIGHT * previous_hidden
        + INPUT_WEIGHT * token_input(token)
    )
```

这里 `A` 给 hidden state 一个正输入，`B` 给一个负输入，`x/y` 是中性输入。第一步之后，hidden state 的符号已经带上了开头 cue。后续 token 虽然没有新标签信息，但 `RECURRENT_WEIGHT * previous_hidden` 会把上一状态继续传下去。

整条序列就是反复应用同一个更新函数：

```python
def trace_sequence(sequence):
    hidden = 0.0
    trace = []
    for token in sequence:
        hidden = recurrent_step(hidden, token)
        trace.append(hidden)
    return trace
```

数据流可以画成：

```text
x_1 ──► h_1 ──► h_2 ──► h_3 ──► h_4 ──► h_5 ──► h_6 ──► prediction
        ▲       ▲       ▲       ▲       ▲       ▲
        │       │       │       │       │       │
       h_0     x_2     x_3     x_4     x_5     x_6
```

每一步使用的是同一套规则。序列长度变了，也只是多应用几次这个规则。

## no-recurrence baseline 为什么会忘记

把 recurrent weight 改成 `0.0`，更新就变成：

```text
h_t = tanh(W_x x_t)
```

此时 `h_t` 只依赖当前 token。最后一个 token 是 `x` 或 `y`，它们都被编码成 `0.0`，最终 hidden state 就回到 0 附近。分类器只能按 tie-break 输出同一个标签，所以测试集上是 50%。

这就是 `NO_RECURRENCE_ACC=0.500` 的含义。失败原因在输入路径：更新式里没有历史项。

## 看 trace 时应该看什么

报告里每个样本都有两个关键数值：

- `hidden_after_first`
- `final_hidden`

如果序列以 `A` 开头，两个值都应该是正数；如果以 `B` 开头，两个值都应该是负数。实验用这个条件生成标记：

```text
HIDDEN_SIGN_STABLE=yes
```

这比只看最终 accuracy 更有解释力。accuracy 说明分类结果对；hidden sign 稳定说明信息确实沿时间步传下来了。

一个简化的样子是：

```text
A x y y x x: h after first > 0, final h > 0 -> topic_a
B y x y x x: h after first < 0, final h < 0 -> topic_b
```

## baseline 结果怎样解读

核心输出是：

```text
MAJORITY_BASELINE_ACC=0.500
LAST_TOKEN_ACC=0.500
SUFFIX_BAG_ACC=0.500
NO_RECURRENCE_ACC=0.500
RNN_MEMORY_ACC=1.000
MEMORY_GAIN_OVER_BEST_BASELINE=0.500
```

这说明四个忘记开头信息的方法都只能达到随机水平；带 `h_{t-1}` 的 recurrent update 可以解决这个刻意构造的 delayed-cue 任务。

边界同样重要：本实验的权重是手写的，数据是合成的。它证明 hidden-state carry 这一层机制，不证明真实文本分类、语言建模或长程依赖已经解决。真实任务还要学习 embedding、权重、loss、optimizer，并检查验证集、错误样本和更强 baseline。

## 常见错误

### 1. 把 RNN 理解成“最后一个 token 的分类器”

RNN 的 final hidden state 表示从 `h_0` 到 `h_T` 连续更新后的状态。最后一步当然会看 `x_T`，同时也会看 `h_{T-1}`。

### 2. 只看 accuracy，不看 hidden trace

教学实验里要先证明机制。`RNN_MEMORY_ACC=1.000` 说明结果对，`HIDDEN_SIGN_STABLE=yes` 说明开头 cue 没有在中性后缀中丢失。两者合在一起，才构成这个实验的证据链。

### 3. 以为 RNN 可以天然记住任意长历史

最简 RNN 有梯度消失、梯度爆炸和长程依赖困难。这个实验只有 6 个 token，且权重被手写成容易保留符号的形式。真实长文本任务通常需要门控结构、残差/归一化、attention 或更精细的数据和训练策略。

### 4. 忽略 baseline 的输入边界

如果一个 baseline 直接读取第一个 token，它当然能做对这个任务。这里的对比对象是“最终位置附近的信息是否足够”。所以实验保留 last-token、suffix-bag、no-recurrence final state，而没有把 first-token oracle 当成主 baseline。oracle 可以作为上界检查，但不能解释 hidden state 的价值。

## 练习

1. 把序列长度从 6 改成 12，中间继续填中性 token，观察 `final_hidden` 是否仍保持符号。
2. 把 `RECURRENT_WEIGHT` 从 `2.0` 改成 `0.5`，看 hidden state 是否逐渐衰减。
3. 把中性 token `x/y` 改成带噪声的小输入，例如 `+0.1/-0.1`，观察错误什么时候出现。
4. 增加一个 `first-token oracle`，确认它也是 100%，然后解释它和 RNN hidden state 的问题设定差别。
5. 用二维 hidden state 重写：`A` 存到 `[1, 0]`，`B` 存到 `[0, 1]`，比较报告可读性。
6. 下一步改成可学习版本：随机初始化 `W_x/W_h`，用交叉熵和反向传播通过时间学习这个任务。

## 继续往下学什么

学完这篇后，深度学习路线可以继续按这个顺序走：

1. 用 PyTorch 的 `nn.RNN` 或 `nn.RNNCell` 重写同一个 delayed-cue 任务，确认输入/输出/hidden 的 shape。
2. 加入可学习权重和 backpropagation through time，理解为什么训练长序列更难。
3. 学 LSTM/GRU：它们的核心价值是用门控机制控制写入、保留和遗忘。
4. 再进入 attention：当我们不想把所有历史都压进一个 fixed-size hidden state 时，attention 提供了按需读取历史位置的路径。
5. 最后再做小型文本分类或字符语言模型，并保留 majority、last-token、bag-of-words、RNN/GRU/attention 等可解释 baseline。

## 参考资料

- PyTorch `RNN` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.RNN.html>
- PyTorch `RNNCell` API：<https://docs.pytorch.org/docs/stable/generated/torch.nn.RNNCell.html>
- Dive into Deep Learning, Recurrent Neural Networks：<https://d2l.ai/chapter_recurrent-neural-networks/index.html>
- Stanford CS231n, Recurrent Neural Networks：<https://cs231n.github.io/rnn/>
- Goodfellow, Bengio, Courville, *Deep Learning*, Sequence Modeling: Recurrent and Recursive Nets：<https://www.deeplearningbook.org/contents/rnn.html>
