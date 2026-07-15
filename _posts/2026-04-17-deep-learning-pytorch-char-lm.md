---
layout: post
title: "PyTorch 字符级语言模型第一课：next-character、GRU hidden state 和采样边界怎么连起来"
date: 2026-04-17 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, pytorch, language-model, gru, sequence-model, baseline, teaching]
---

文本分类把一整段文本压成一个类别，语言模型换了一个问题：已经看到前面的字符，下一步应该预测哪个字符？这个问题看起来只是把标签从“类别”换成“下一个 token”，实际会引出三件更基础的事：训练样本怎样做成错一位的 input/target，RNN/GRU 的 hidden state 怎样携带前文信息，训练时总是喂真实前缀而生成时只能喂模型自己的输出，这两个阶段的边界怎样检查。

这一篇用一个很小的字符级 PyTorch 项目讲清这条链路。语料是合成 grammar：第一个字符是 `a`、`b` 或 `c`，中间经过若干干扰字符，遇到分隔符 `|` 后，最后一个字符必须分别是 `A`、`B` 或 `C`。bigram baseline 在预测最后一个字符时只能看到前一个字符 `|`，因此无法知道开头 cue；GRU 模型如果真的利用 hidden state，就应该把开头 cue 带到分隔符之后。

配套代码在 [`deep-learning-pytorch-char-lm`](/labs/#deep-learning-pytorch-char-lm)，也可以直接看 [`README.md`](/assets/labs/deep-learning-pytorch-char-lm/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-pytorch-char-lm/run_lab.sh)。

## 学完要能做什么

读完并运行实验后，你应该能解释：

1. 字符级 language model 的监督信号为什么来自同一条序列的“错一位”版本；
2. `BOS`、`EOS` 和 `PAD` 分别解决什么边界问题；
3. 为什么 `CrossEntropyLoss` 要拿每个位置的 logits 和 target id，而 padding target 要用 `ignore_index`；
4. `nn.Embedding -> nn.GRU -> nn.Linear` 的形状怎样变化；
5. bigram baseline 为什么能学局部转移，却解决不了这个 final-label 依赖；
6. 训练时的 teacher forcing 和推理时的逐步生成有什么差别；
7. 为什么 toy grammar 上的完美结果不能被写成自然语言生成能力。

## 先看任务：预测下一个字符

实验构造的字符串类似：

```text
anmo|A
bnmo|B
cnmo|C
```

第一位是 cue，最后一位是它对应的大写标签。中间的 `nmo` 是干扰段，`|` 是共享分隔符。对于最后一个标签位置，bigram 只能看到前一个字符 `|`，它会在 `A/B/C` 之间按训练集计数做一个固定选择；GRU 可以通过 hidden state 记住开头的 `a/b/c`。

切分规模很小：

```text
TRAIN_SAMPLES=18
VAL_SAMPLES=9
TEST_SAMPLES=9
VOCAB_SIZE=14
```

训练、验证和测试使用不同 middle string，但字符表相同。这样设计把检查重点放在“能否把开头 cue 带到后面”，同时避开未登录字符处理这个额外问题。

## 为什么 language model 可以从一条序列里造出监督信号

假设原始字符串是：

```text
anmo|A
```

训练时直接从同一条序列构造输入和目标：目标序列比输入序列向前错开一位。

```text
input : <bos> a n m o | A
target: a     n m o | A <eos>
```

第 0 步看到 `<bos>`，目标是 `a`；第 1 步看到 `a`，目标是 `n`；直到看到 `|` 时，目标是 `A`。这就是 next-character prediction。

代码里对应的是：

```python
def encode_example(example, vocab):
    input_tokens = [BOS, *example.raw]
    target_tokens = [*example.raw, EOS]
    input_ids = torch.tensor([vocab[token] for token in input_tokens], dtype=torch.long)
    target_ids = torch.tensor([vocab[token] for token in target_tokens], dtype=torch.long)
    return input_ids, target_ids, example.label_index
```

这里没有人工写“第几个位置是什么标签”的文件；标签来自序列本身。这是语言模型和文本分类最直观的区别：文本分类通常是一段文本对应一个类别，语言模型是一段文本的每个位置都产生一个 next-token 监督信号。

## 为什么需要 BOS、EOS 和 PAD

三个特殊 token 的职责不同：

| token | 解决的问题 | 在实验里的作用 |
| --- | --- | --- |
| `<bos>` | 第一个字符之前没有真实前文 | 让模型在第一步预测原始字符串的第一个字符 |
| `<eos>` | 序列什么时候结束 | 让最后一个真实字符之后还有一个结束目标 |
| `<pad>` | batch 中序列长度不同 | 对齐张量形状，但不参与 loss |

实验输出固定了它们的 id：

```text
PAD_ID=0
BOS_ID=1
EOS_ID=2
```

为什么常把 `PAD_ID` 设成 0？这是工程上的固定边界：`nn.Embedding(..., padding_idx=pad_id)` 会把 padding 行作为特殊位置处理，后续 mask 和 `ignore_index` 也更容易检查。

## 变长序列怎样组成 batch

`DataLoader` 默认只会把样本堆叠起来；变长序列长度不同，直接堆叠会失败。实验使用 `collate_fn` 做两件事：

1. input 用 `<pad>` 的 id 补齐；
2. target 用 `-100` 补齐，交给 `CrossEntropyLoss(ignore_index=-100)` 忽略。

核心代码是：

```python
input_ids = pad_sequence(inputs, batch_first=True, padding_value=pad_id)
target_ids = pad_sequence(targets, batch_first=True, padding_value=-100)
```

为什么 input 和 target 用不同 padding 值？input 需要进入 embedding，所以必须是合法 token id；target 只给 loss 用，`-100` 的意思是“这个位置不算损失”。如果 target 也用 `<pad>` 的 id，模型会被训练去预测 padding，loss 会把补齐出来的位置当成真实任务。

## 模型结构：Embedding、GRU、Linear

实验模型很小：

```python
class CharGRULanguageModel(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, pad_id):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_id)
        self.gru = nn.GRU(embedding_dim, hidden_size, batch_first=True)
        self.output = nn.Linear(hidden_size, vocab_size)

    def forward(self, input_ids):
        embedded = self.embedding(input_ids)
        states, _ = self.gru(embedded)
        return self.output(states)
```

形状变化可以这样读：

```text
input_ids: [batch, time]
embedded : [batch, time, embedding_dim]
states   : [batch, time, hidden_size]
logits   : [batch, time, vocab_size]
```

每个时间步都会输出一个 `vocab_size` 维 logits。第 `t` 个位置的 logits 对应第 `t` 个 target id。对于 `anmo|A`，模型在输入位置 `|` 的输出要预测 `A`。如果 hidden state 没有保留开头的 `a`，最后这个位置就只能像 bigram 一样猜一个固定标签。

## CrossEntropyLoss 吃什么形状

PyTorch 的 `CrossEntropyLoss` 接收未 softmax 的 logits。语言模型的 logits 是三维 `[batch, time, vocab]`，target 是二维 `[batch, time]`，训练前要把前两维摊平：

```python
loss = loss_fn(
    logits.reshape(-1, logits.size(-1)),
    target_ids.reshape(-1),
)
```

摊平后：

```text
logits: [batch * time, vocab_size]
target: [batch * time]
```

这样每个有效时间步都是一个多分类问题。`ignore_index=-100` 会跳过 target 里 padding 出来的位置。这里不要先手动 `softmax`；`CrossEntropyLoss` 内部会把 `log_softmax` 和负对数似然合在一起，数值更稳定。

## baseline 先回答：简单模型能做到哪里

实验报告了三个基线或参考值：

```text
UNIFORM_NLL=2.639
UNIGRAM_FINAL_ACC=0.000
BIGRAM_TOKEN_ACC=0.381
BIGRAM_FINAL_ACC=0.333
```

`UNIFORM_NLL=log(VOCAB_SIZE)`，对应完全不知道下一字符时的平均负对数似然。`unigram` 只看全局最常见目标字符；它在 final label 上拿不到分数。`bigram` 看前一个字符，它能学到一些局部转移，但最后一个标签前的字符总是 `|`，所以 final-label accuracy 只有三选一水平：

```text
BIGRAM_FINAL_ACC=0.333
```

这就是本实验的关键对照：如果一个模型只是记住局部相邻字符，它解决不了“开头 cue 决定末尾标签”的位置。

## 训练结果怎样读

实验跑完后会打印：

```text
MODEL_VAL_FINAL_ACC=1.000
MODEL_TOKEN_ACC=0.524
MODEL_FINAL_ACC=1.000
MODEL_TEST_NLL=1.819
MODEL_BEATS_BIGRAM_FINAL=yes
```

最重要的是 `MODEL_FINAL_ACC=1.000` 和 `MODEL_BEATS_BIGRAM_FINAL=yes`。它说明模型在测试集 final label 位置上学会了利用远处 cue。

`MODEL_TOKEN_ACC=0.524` 不高，原因要诚实解释：验证和测试使用了 held-out middle string，很多中间字符转移没有被训练集完整覆盖。这个实验不追求每个字符位置都像真实语言模型那样预测得好，它只检验一条长距离依赖。把 `MODEL_FINAL_ACC=1.000` 写成“生成文本质量很好”会越过证据边界。

## teacher forcing 和生成边界

训练时，每一步输入的前缀都来自真实序列：

```text
input : <bos> a n m o |
target: a     n m o | A
```

推理时，如果从一个短前缀开始生成，下一步输入来自模型刚刚预测出的字符。错误会沿着后续步骤传播，这叫 exposure bias 的典型来源之一。这个 lab 不直接评估长文本采样质量，只做一个可检查的一步预测：

```text
PROMPT_A_NEXT=A
PROMPT_B_NEXT=B
PROMPT_C_NEXT=C
```

也就是分别给模型看：

```text
anmo|
bnmo|
cnmo|
```

模型下一字符应该输出 `A/B/C`。这比自由生成更适合作为第一课，因为判断标准明确，baseline 也明确。

## checkpoint 为什么也要检查

实验会保存本地 checkpoint：

```python
torch.save({
    "model_state_dict": model.state_dict(),
    "vocab": vocab,
}, checkpoint_path)
```

然后重新构造模型并加载：

```python
payload = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
reloaded_model.load_state_dict(payload["model_state_dict"])
```

最后比较重新加载前后的测试指标：

```text
CHECKPOINT_RELOAD_MATCH=yes
```

语言模型项目里 vocabulary 和权重必须一起保存。只保存权重而丢掉字符到 id 的映射，推理时同一个整数 id 可能对应另一个字符，输出就失去意义。

## 本地怎么运行

如果你的默认 Python 已经能 import PyTorch：

```bash
cd assets/labs/deep-learning-pytorch-char-lm
bash run_lab.sh
```

如果 PyTorch 在另一个虚拟环境里：

```bash
PYTORCH_LAB_PYTHON=/path/to/python ./run_lab.sh
```

成功后会看到：

```text
TRAIN_SAMPLES=18
VAL_SAMPLES=9
TEST_SAMPLES=9
BIGRAM_FINAL_ACC=0.333
MODEL_VAL_FINAL_ACC=1.000
MODEL_FINAL_ACC=1.000
PROMPT_A_NEXT=A
PROMPT_B_NEXT=B
PROMPT_C_NEXT=C
CHECKPOINT_RELOAD_MATCH=yes
RUN_STATUS=ok
deep_learning_pytorch_char_lm_lab_status=ok
```

`reports/` 是你本机生成的证据目录，公开仓库不提交它。重点看这些文件：

| 文件 | 用途 |
| --- | --- |
| `char_lm_probe.json` | split、baseline、模型指标、prompt 预测和检查门 |
| `training_history.csv` | 训练过程中的 selected epoch 指标 |
| `final_predictions.csv` | 测试集中 final-label 位置的预测和 top-3 概率 |
| `vocab.json` | 字符 vocabulary |
| `char_lm_report.md` | 人类可读摘要 |
| `checkpoint.pt` | 本地生成的权重，不应提交到公开仓库 |

## 常见错误

### 1. input 和 target 没有错开一位

如果 input 和 target 完全相同，模型会学“复制当前字符”。检查方法很简单：拿一条样本写出两行对齐表，确认 `input[t+1] == target[t]`。

### 2. padding 位置参与 loss

如果 target padding 使用合法字符 id，而 loss 没有 `ignore_index`，模型会被奖励去预测 padding。症状通常是 loss 看起来下降，但有效位置的预测没有变好。

### 3. 先 softmax 再 CrossEntropyLoss

`CrossEntropyLoss` 要求输入是 logits。手动 softmax 后再传入，会改变数值稳定性和梯度形态。需要概率时，在评估或展示阶段再单独 `torch.softmax(logits, dim=-1)`。

### 4. 把 teacher forcing 下的准确率当成自由生成质量

训练和评估阶段输入的前缀都是真实字符。自由生成会把模型自己的输出接回输入，错误可能累积。本篇只声明 final-label dependency 被学到，不声明开放式生成质量。

### 5. checkpoint 只保存权重，不保存 vocabulary

字符级模型的输出维度和 vocabulary 绑定。权重、special token id、字符映射必须共同保存和复核。

## 练习和延伸

1. 把 middle string 长度从 3 增加到 8，观察 `BIGRAM_FINAL_ACC` 和 `MODEL_FINAL_ACC` 是否变化。
2. 把 GRU 换成普通 `nn.RNN`，比较 final-label accuracy 和训练稳定性。
3. 新增 cue `d -> D`，确认 vocabulary、baseline、输出层维度和测试断言都同步变化。
4. 写一个 temperature sampling 函数，只在 prompt 之后采样 5 步，并记录不同 temperature 下的输出差异。
5. 把这个 toy grammar 改成真实小语料前，先写清楚 train/val/test 切分、OOV 策略、评价指标和版权边界。

## 边界

这个实验只证明四件事：字符序列可以被移位成 next-character 监督信号；GRU hidden state 能在这个短序列中携带开头 cue；final-label 位置上模型超过 bigram baseline；checkpoint 重载后指标一致。它不证明模型会写自然语言，不证明采样质量，也不证明架构优于 Transformer。下一步如果要进入真实语言模型，必须重新定义语料、tokenizer、评价指标、采样策略、训练/验证切分和数据授权。

## 参考资料

- PyTorch `nn.Embedding` 文档：<https://docs.pytorch.org/docs/stable/generated/torch.nn.Embedding.html>
- PyTorch `nn.GRU` 文档：<https://docs.pytorch.org/docs/stable/generated/torch.nn.GRU.html>
- PyTorch `CrossEntropyLoss` 文档：<https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html>
- PyTorch `torch.utils.data` 文档：<https://docs.pytorch.org/docs/stable/data.html>
- PyTorch 保存和加载模型教程：<https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html>
- PyTorch 字符级 RNN 生成教程：<https://docs.pytorch.org/tutorials/intermediate/char_rnn_generation_tutorial.html>
