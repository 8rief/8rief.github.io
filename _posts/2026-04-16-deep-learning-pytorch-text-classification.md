---
layout: post
title: "PyTorch 文本分类项目第一课：tokenize、vocab、collate 和 baseline 怎么串起来"
date: 2026-04-16 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [deep-learning, pytorch, text-classification, dataloader, baseline, teaching]
---

很多人第一次做文本分类时，会直接问该用 BERT、LSTM 还是 Transformer。这个顺序太靠后了。模型之前还有一条更基础的链路：一行文本怎样变成整数 id？不同长度的句子怎样组成 batch？padding 会不会被模型当成真实词？baseline 已经能解决任务时，还要不要训练神经网络？

这一篇用一个很小的 PyTorch 文本分类项目回答这些问题。任务是把短 support ticket 分成 `billing`、`shipping` 和 `tech` 三类。数据是合成的、关键词驱动的；它的用途是把文本分类项目的基本工程边界走通，不承担自然语言理解能力的证明。

配套代码在 [`deep-learning-pytorch-text-classification`](/labs/#deep-learning-pytorch-text-classification)，也可以直接看 [`README.md`](/assets/labs/deep-learning-pytorch-text-classification/README.md) 和 [`run_lab.sh`](/assets/labs/deep-learning-pytorch-text-classification/run_lab.sh)。

## 学完要能做什么

读完并运行实验后，你应该能解释：

1. tokenize、vocab、`<pad>`、`<unk>`分别解决什么问题；
2. 为什么普通 list 不能直接组成变长文本 batch，需要 `collate_fn`；
3. padding 之后为什么还要保存 `lengths` 或 mask；
4. `nn.Embedding` 输出的形状怎样变成一句话的向量；
5. `CrossEntropyLoss` 为什么吃 logits 和类别 id，而不是手动 softmax 后的概率；
6. 为什么文本分类项目必须先报告 baseline 和 confusion matrix；
7. 为什么这个 toy task 上神经模型没有超过关键词规则，也不应该被说成更好。

## 先看任务：三类工单文本

实验里的原始文本类似：

```text
please help with invoice today
my account shows delivery after the update
urgent question about login before noon
```

标签是：

```text
billing
shipping
tech
```

数据切分是平衡的：

```text
TRAIN_SAMPLES=36
VAL_SAMPLES=9
TEST_SAMPLES=9
```

每类都有 12 条训练样本、3 条验证样本、3 条测试样本。训练集覆盖每个类别关键词，验证集和测试集使用不同 phrasing。这个设计避免把任务变成零样本词汇泛化；本篇要讲的是项目管线，不是 OOD 泛化。

## 为什么要先 tokenize

模型不能直接读字符串。第一步是把文本拆成 token：

```python
TOKEN_RE = re.compile(r"[a-z0-9]+")

def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())
```

例如：

```text
"Please help with invoice today"
```

会变成：

```text
["please", "help", "with", "invoice", "today"]
```

这个 tokenizer 很简单，只适合教学。真实项目要考虑大小写、标点、中文分词、emoji、URL、数字归一化、拼写错误、子词切分等问题。这里先保留最小版本，是为了让后续状态变化能被看清楚。

## 为什么要引入 vocab、`<pad>` 和 `<unk>`

token 仍然是字符串，`nn.Embedding` 需要整数索引。因此训练集会生成 vocabulary：

```python
vocab = {
    "<pad>": 0,
    "<unk>": 1,
    "account": 2,
    "address": 3,
    ...
}
```

实验输出：

```text
VOCAB_SIZE=50
PAD_ID=0
UNK_ID=1
```

`<pad>` 用来补齐 batch 里的短句子。`<unk>` 用来表示训练词表里没有见过的词。编码函数是：

```python
def encode(text: str, vocab: dict[str, int]) -> list[int]:
    return [vocab.get(token, vocab["<unk>"]) for token in tokenize(text)]
```

为什么需要引入 `<unk>`？因为真实输入不会只包含训练集词汇。如果遇到 `biometric`、`outage` 这类训练中没出现的词，程序不能崩，也不能临时扩词表后让 embedding 权重维度不匹配。实验专门检查：

```text
UNKNOWN_TOKEN_COUNT=4
```

这表示示例句子里有 4 个 token 被映射成 `<unk>`。

## Dataset 只负责取单条样本

PyTorch 的 `Dataset` 不应该先操心 batch。它只回答两个问题：有多少条数据、给定 index 返回哪条样本。

```python
class TicketDataset(Dataset):
    def __init__(self, examples):
        self.examples = list(examples)

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, index):
        return self.examples[index]
```

一条样本保留两个字段：

```python
@dataclass(frozen=True)
class TextExample:
    text: str
    label: int
```

这样做的好处是边界清楚：数据集负责“单条数据是什么”，batch 形状交给 `DataLoader` 的 `collate_fn`。

## 为什么变长文本需要 collate_fn

图像分类里，每张图片通常已经是同样形状，例如 `(3, 224, 224)`。文本不一样：

```text
please help with invoice today                  # 5 tokens
before noon billing can you check the           # 7 tokens
for my team technical the customer reported     # 7 tokens
```

如果直接把不同长度 list 堆成 tensor，会失败。`collate_fn` 的作用是在组成 mini-batch 时做自定义整理：

```python
def collate(examples):
    encoded = [torch.tensor(encode(e.text, vocab)) for e in examples]
    lengths = torch.tensor([len(x) for x in encoded])
    input_ids = pad_sequence(encoded, batch_first=True, padding_value=pad_id)
    labels = torch.tensor([e.label for e in examples])
    return Batch(input_ids=input_ids, labels=labels, lengths=lengths)
```

实验检查测试 batch 的最大宽度和 padding 数量：

```text
MAX_BATCH_WIDTH=8
PAD_TOKEN_COUNT=9
```

这说明 batch 被补齐到了 8 个 token 宽，其中 9 个位置是 `<pad>`。

## padding 不能参与句向量平均

模型结构很小：

```text
input_ids
  -> nn.Embedding
  -> mask-aware mean pooling
  -> Linear classifier
  -> logits
```

代码核心是：

```python
embedded = self.embedding(input_ids)
mask = input_ids.ne(self.pad_id).unsqueeze(-1)
summed = (embedded * mask).sum(dim=1)
denom = lengths.clamp_min(1).to(embedded.dtype).unsqueeze(-1)
pooled = summed / denom
logits = self.classifier(pooled)
```

如果不乘 mask，`<pad>` 的 embedding 也会进入平均。即使 `padding_idx=0` 会让 pad embedding 初始化为 0，工程上仍然应该明确用 `lengths` 或 mask 表达“这些位置不是文本内容”。这样换模型、换初始化或换 pooling 时不容易埋错。

形状可以这样读：

```text
input_ids:  (batch, seq)
embedded:   (batch, seq, embedding_dim)
mask:       (batch, seq, 1)
summed:     (batch, embedding_dim)
logits:     (batch, num_labels)
```

这里 `num_labels=3`，所以每条文本输出 3 个 logits。

## CrossEntropyLoss 吃的是 logits

分类训练使用：

```python
loss_fn = nn.CrossEntropyLoss()
logits = model(batch.input_ids, batch.lengths)
loss = loss_fn(logits, batch.labels)
```

`batch.labels` 是类别 id，例如：

```text
billing -> 0
shipping -> 1
tech -> 2
```

`CrossEntropyLoss` 期望输入是 raw logits，不需要先手动 softmax。它内部已经包含 log-softmax 和 negative log-likelihood 的组合。初学者常见错误是：

```python
loss = loss_fn(torch.softmax(logits, dim=1), labels)  # 不要这样写
```

这样会改变数值含义，也会让梯度变差。

## baseline：规则已经能解决，就不要夸模型

实验报告三个 baseline：

```text
MAJORITY_BASELINE_ACC=0.333
FIRST_TOKEN_BASELINE_ACC=0.333
KEYWORD_RULE_BASELINE_ACC=1.000
```

它们分别代表：

| baseline | 看什么 | 结果 | 含义 |
| --- | --- | --- | --- |
| majority | 永远预测最多的类 | `0.333` | 三类平衡，只能猜中一类 |
| first-token | 只看第一个词 | `0.333` | 开头多是中性词，信息不足 |
| keyword rule | 扫描类别关键词 | `1.000` | 合成数据由关键词决定，透明规则已足够 |

模型结果是：

```text
MODEL_VAL_ACC=1.000
MODEL_TEST_ACC=1.000
MODEL_MATCHES_KEYWORD_RULE=yes
```

这组数字的正确解释应当很克制：在这个关键词 toy task 上，神经模型学到了足够的线索，透明规则同样能满分。如果真实业务中规则 baseline 已经稳定、可维护、误报可控，直接上模型反而可能增加复杂度。这个实验保留神经网络，是为了教学 PyTorch 文本管线。

## confusion matrix 比单个 accuracy 更具体

测试集每类 3 条。实验输出：

```text
CONFUSION_DIAGONAL=3:3:3
```

对应 confusion matrix：

```text
gold\pred,billing,shipping,tech
billing,3,0,0
shipping,0,3,0
tech,0,0,3
```

accuracy 只告诉你总共对了多少；confusion matrix 告诉你错在什么类别之间。如果未来模型把 `billing` 错成 `shipping`，排查方向会完全不同：可能是词表、样本分布、关键词重叠，也可能是 label 映射错了。

## checkpoint reload 要检查预测一致

训练结束后保存：

```python
torch.save({
    "model_state_dict": model.state_dict(),
    "vocab": vocab,
    "labels": LABELS,
    "history": history,
    "metrics": metrics,
}, checkpoint_path)
```

重新加载时必须重建同样结构的模型，再 `load_state_dict`：

```python
checkpoint = torch.load(path, map_location="cpu", weights_only=True)
model = MeanEmbeddingClassifier(
    vocab_size=len(checkpoint["vocab"]),
    embedding_dim=16,
    num_labels=3,
    pad_id=checkpoint["vocab"]["<pad>"],
)
model.load_state_dict(checkpoint["model_state_dict"])
```

实验检查：

```text
CHECKPOINT_RELOAD_MATCH=yes
```

它检查的不止是文件存在，还会比较 reload 后的预测表是否和保存前一致。

## 运行实验

如果当前 Python 环境已经安装 PyTorch：

```bash
cd assets/labs/deep-learning-pytorch-text-classification
bash run_lab.sh
```

如果默认 `python3` 不能 import `torch`：

```bash
PYTORCH_LAB_PYTHON=/path/to/python bash run_lab.sh
```

成功时会看到：

```text
TRAIN_SAMPLES=36
VAL_SAMPLES=9
TEST_SAMPLES=9
VOCAB_SIZE=50
PAD_ID=0
UNK_ID=1
MAX_BATCH_WIDTH=8
PAD_TOKEN_COUNT=9
MAJORITY_BASELINE_ACC=0.333
FIRST_TOKEN_BASELINE_ACC=0.333
KEYWORD_RULE_BASELINE_ACC=1.000
MODEL_VAL_ACC=1.000
MODEL_TEST_ACC=1.000
MODEL_MATCHES_KEYWORD_RULE=yes
CONFUSION_DIAGONAL=3:3:3
CHECKPOINT_RELOAD_MATCH=yes
UNKNOWN_TOKEN_COUNT=4
RUN_STATUS=ok
deep_learning_pytorch_text_classification_lab_status=ok
```

生成的 `reports/` 包括训练历史、confusion matrix、预测表、词表、报告和本地 checkpoint。公开仓库只提交源码、测试和 runner，不提交这些运行产物。

## 常见错误

**1. 用全量数据建 vocab。** 真实项目应该只用训练集建词表。验证集和测试集出现的新词要走 `<unk>`，否则评估阶段泄漏了信息。

**2. 忘记处理空文本。** 本实验里 `encode` 对空文本返回 `[<unk>]`，避免长度为 0 的样本让 pooling 除以 0。真实项目还应该记录空文本比例。

**3. padding 进入平均池化。** 如果直接 `embedded.mean(dim=1)`，短句子会被 padding 稀释。要用 mask 或 lengths。

**4. label 顺序前后不一致。** 训练、评估、confusion matrix 和 checkpoint 里都要保存同一份 `LABELS`。否则模型预测 id `1` 到底是 `shipping` 还是 `tech` 会变得不可解释。

**5. baseline 太弱就误以为模型有效。** majority baseline 只检查类别平衡，keyword rule 才暴露这个 toy task 的真实难度。baseline 要尽量贴近任务结构。

## 练习

1. 在测试集中加入没有关键词的句子，例如 `my issue is still unresolved`。观察 keyword baseline 和模型预测怎样变化。
2. 把 mean pooling 改成只取第一个 token 的 embedding。你应该能看到它接近 first-token baseline 的思路。
3. 删除 `lengths`，改成 `embedded.mean(dim=1)`。比较 padding 多的 batch 上 logits 是否变化。
4. 把 `keyword_rule_baseline` 的词典故意删掉 `technical`，观察 confusion matrix 哪一行先出问题。
5. 把 synthetic 数据换成你自己的 30 条三分类短文本。先写 baseline，再训练模型，不要先看最终 accuracy。

## 边界

这个实验只证明 PyTorch 文本分类管线是可运行的。它不证明模型理解自然语言，不证明能处理中文分词，不证明能泛化到真实客服数据，也不讨论隐私、标注偏差、上线监控和人工复核流程。进入真实项目之前，至少还要补：数据采样、标注规范、train/val/test 防泄漏、类别不平衡、错误样例审查、阈值策略和人工兜底。

## 参考资料

- PyTorch Docs: [torch.utils.data](https://docs.pytorch.org/docs/stable/data.html)
- PyTorch Tutorial: [Writing Custom Datasets, DataLoaders and Transforms](https://docs.pytorch.org/tutorials/beginner/data_loading_tutorial.html)
- PyTorch Tutorial: [Word Embeddings: Encoding Lexical Semantics](https://docs.pytorch.org/tutorials/beginner/nlp/word_embeddings_tutorial.html)
- PyTorch API: [`torch.nn.CrossEntropyLoss`](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html)
- PyTorch Tutorial: [Saving and Loading Models](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
