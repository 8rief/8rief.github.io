---
layout: post
title: "领域小模型微调实战：用 Qwen3-0.6B、LoRA 和 RAG 做本地学习 Agent"
date: 2026-04-19 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从任务、训练/评测切分、chat template 和 response-only loss 开始，在 RTX 5070 上跑通 Qwen3-0.6B 领域 LoRA，并诚实比较 base、LoRA 和 RAG+LoRA。"
tags: [qwen, lora, rag, local-llm, fine-tuning, agent, wsl, teaching]
---
{% raw %}

领域微调最常见的错误，是先下载一个尽可能大的模型，运行几个 epoch，看到 training loss 下降就宣布成功。这条路线无法回答三个基本问题：模型到底要改善什么？评测题是否泄漏进了训练数据？结果变好是 LoRA、RAG、prompt 还是评分规则造成的？

本文使用一个有限、可完整复现的 CUDA/本地 AI 学习助手任务，从数据边界开始，在 RTX 5070 12GB 上训练 Qwen3-0.6B LoRA。结果不会被包装成“专业模型已成功”：这是一个教你建立微调证据链的小实验。

## 学习目标

1. 根据任务和显存边界选择小模型，而不把 RTX 5070 写成专用方案。
2. 区分领域知识、SFT 样例和 held-out 评测题。
3. 理解 chat template、prompt token、answer token 和 `-100` label mask。
4. 理解 LoRA 的低秩增量、target modules 和显存节省来源。
5. 使用同一组 held-out 问题比较 base、LoRA 和 RAG+LoRA，并保留失败。

## 先修知识和硬件边界

建议先完成：

- [Agent 第一课：可检查的控制循环](/computer-science-teaching/2026/04/18/local-rag-agent-tool-eval-loop.html)；
- [本地小模型微调：先定义任务和 baseline](/computer-science-teaching/2026/04/18/local-llm-task-baseline-lora-qlora.html)；
- 会使用 Python virtual environment，知道 training set 和 evaluation set 不能混用。
- 如果你想先理解“为什么显存、CPU↔GPU 传输和 batch 会成为边界”，先跑[硬件瓶颈实测第一课](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html)。

本 lab 的 00--07 可以在 CPU-only 环境运行。08--09 明确要求 NVIDIA CUDA GPU；脚本在 CUDA 不可用时会失败，不会静默切到 CPU 并把结果写成 GPU 实验。

## 第一步：在 WSL 中准备隔离环境

如果还没有 lab：

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/local-small-model-agent-course
chmod +x setup_gpu.sh learn.sh run_lab.sh
```

然后执行：

```bash
./setup_gpu.sh
```

该脚本按以下顺序工作：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install torch==2.11.0 \
  --index-url https://download.pytorch.org/whl/cu128
.venv/bin/python -m pip install -r requirements-gpu.txt
```

- `python3 -m venv .venv` 在当前 lab 内创建隔离的 Python 环境。
- 第二条只升级该虚拟环境的 `pip`。
- 第三条从 PyTorch CUDA 12.8 wheel 索引安装固定版本 `torch`。
- 最后一条安装 `transformers==5.13.0`、`peft==0.19.1` 和 `safetensors==0.8.0`。

成功时应看到：

```text
cuda_available True
device NVIDIA GeForce RTX 5070
AGENT_GPU_SETUP_OK
```

对其他 NVIDIA GPU，`device` 会不同。只要 PyTorch CUDA 可用且显存足以加载 0.6B 模型，后面的方法不变。

## 第二步：先跑 base + RAG，不立即训练

```bash
./learn.sh 08-local-qwen
cat reports/local_qwen_ask.json
```

第一条命令执行的完整路径是：

1. 从 `knowledge.jsonl` 检索“`vector_add_ok` 为什么不是性能证据”。
2. 得到 `vector-add-proof` 来源。
3. 将 system message、证据和用户问题交给 Qwen chat template。
4. 使用 greedy decoding（`do_sample=False`）生成回答。
5. 保存回答、source id、检索分数、revision 和显存数据。

模型固定为：

```text
model    = Qwen/Qwen3-0.6B
revision = c1899de289a04d12100db370d81485cdf75e47ca
```

固定 revision 是为了避免远程仓库后续更新时，你在相同代码下实际加载了不同权重或配置。

关键代码：

```python
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    revision=MODEL_REVISION,
    dtype=torch.float16,
    low_cpu_mem_usage=True,
).to("cuda")
```

这里的 `float16` 减少权重和中间张量占用。`low_cpu_mem_usage=True` 减少加载过程中的 CPU 内存峰值，但不代表 GPU 显存无限。

预期 marker：

```text
AGENT_08_LOCAL_QWEN_OK rag=yes sources=1 generated_tokens=...
```

在本次 RTX 5070 验证中，`torch.cuda.max_memory_allocated()` 约为 1.17 GiB。PyTorch 的 allocated memory 是活跃张量占用；`nvidia-smi` 还可能显示 allocator reserved memory 和 CUDA context，两者不应混为一个数。

## 第三步：数据分为三个不同对象

lab 中的数据文件是：

```text
data/knowledge.jsonl   # RAG 可检索知识
data/train_sft.jsonl   # LoRA 训练样例
data/eval_cases.jsonl  # 冻结评测问法和通过条件
```

三者的职责不同：

| 数据 | 系统如何使用 | 可以包含 | 不应包含 |
| --- | --- | --- | --- |
| knowledge | 回答前检索 | 可更新事实、操作边界、来源 | 评测题标准答案的隐式索引 |
| train SFT | 反向传播更新 adapter | 任务格式、领域表达、边界反例 | 原样复制的 held-out 问题 |
| eval | 训练前冻结，训练后复测 | 问题、参考答案、关键词、失败类型 | 进入 optimizer 的训练样例 |

一条 SFT 数据是：

```json
{
  "id": "train-005",
  "instruction": "Agent 为什么需要工具 schema？",
  "output": "模型输出是不可信输入……"
}
```

一条 held-out 数据还会附带：

```json
{
  "id": "eval-006",
  "question": "模型输出了 JSON 工具参数，为什么还不能直接执行？",
  "keywords": ["白名单", "类型"],
  "failure_type": "bad_arguments"
}
```

评分规则很粗糙：关键词覆盖达到 0.5 就记为 pass。它的用途是第一轮自动回归，不能替代事实一致性、工具成功率和人工阅读。

## 第四步：理解 chat template 和 response-only label

对 chat model，不能自己猜测特殊 token 怎么拼。代码通过 tokenizer 的 chat template 生成 prompt：

```python
prompt = tokenizer.apply_chat_template(
    [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": instruction},
    ],
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False,
)
```

训练时，输入是 `prompt_ids + answer_ids`，但 prompt 部分的 label 全部设为 `-100`：

```python
input_ids = prompt_ids + answer_ids
labels = [-100] * len(prompt_ids) + answer_ids
```

PyTorch causal-LM loss 会忽略 label 为 `-100` 的位置，所以 optimizer 只学习 assistant answer，不要求模型重建 system/user prompt。

长度超限时，本 lab 优先保留 answer token，从 prompt 左侧裁剪：

```python
prompt_ids = prompt_ids[-(MAX_LENGTH - len(answer_ids)):]
```

如果你直接把整串从右侧截断，有可能删掉全部 answer label，最终得到无有效监督位置的 batch。

## 第五步：LoRA 到底改了什么

对一个冻结线性变换 (W_0\in\mathbb{R}^{d_{out}\times d_{in}})，LoRA 不直接更新全部 (W_0)，而是学习：

\[
W = W_0 + \Delta W,
\qquad
\Delta W = \frac{\alpha}{r}BA,
\]

其中：

\[
A\in\mathbb{R}^{r\times d_{in}},
\qquad
B\in\mathbb{R}^{d_{out}\times r},
\qquad
r\ll \min(d_{in}, d_{out}).
\]

全参数更新需要 (d_{out}d_{in}) 个可训练参数，LoRA 只需要 (r(d_{in}+d_{out}))。减少的不只是权重，还包括梯度和 AdamW 优化器状态。

本 lab 的配置：

```python
config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)
```

`q_proj/k_proj/v_proj/o_proj` 是 attention 中的查询、键、值和输出投影。这个选择是本次小实验的固定变量，不是对所有任务都最优的结论。

## 第六步：运行训练和同一评测

```bash
./learn.sh 09-domain-lora
cat reports/domain_lora_report.json
```

脚本会执行：

```text
base held-out loss + base generation
  -> 注入 LoRA
  -> 8 条训练样例 x 2 epoch
  -> 8 个 optimizer step
  -> LoRA held-out loss + generation
  -> RAG+LoRA held-out loss + generation
  -> 保存 adapter 和 JSON report
```

训练循环中的关键操作：

```python
output = model(
    input_ids=input_tensor,
    attention_mask=torch.ones_like(input_tensor),
    labels=label_tensor,
)
(output.loss / GRAD_ACCUM).backward()

if accumulation_boundary:
    torch.nn.utils.clip_grad_norm_(trainable, 1.0)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
```

- 除以 `GRAD_ACCUM` 使多个 micro-batch 的梯度累积后再做一次 optimizer step。
- gradient clipping 防止单次过大梯度使小实验突然发散。
- `zero_grad(set_to_none=True)` 在每次 step 后清除梯度引用，避免下一轮无意继续累加。

RTX 5070 本次实测：

```text
AGENT_09_DOMAIN_LORA_OK steps=8 loss=5.4119->4.6738 passes=0/0/3 memory_mib=1699.1
```

三个 pass 数依次是：

```text
base direct = 0/6
LoRA direct = 0/6
RAG + LoRA = 3/6
```

这组数据的正确解释：

1. 训练 loss 从 5.4119 降到 4.6738，证明 adapter 参数获得了有效梯度，训练管线可工作。
2. LoRA direct 没有让 6 条关键词评测通过，说明这么少的数据和 step 不足以建立稳定领域回答。
3. RAG+LoRA 通过 3/6，说明对课程事实题，在 prompt 中提供证据比单独依赖参数记忆更直接。
4. 3/6 仍然不及格；下一轮应该阅读逐题失败，而不是只把 epoch 从 2 改成 20。

## 为什么要同时看 loss 和生成 pass

held-out loss 问的是：在给定参考答案 token 的情况下，模型给这些 token 多大概率。生成 pass 问的是：模型自己解码时，是否真的说出验收所需的关键事实。

两者可能不一致：

- eval loss 变小，但 greedy generation 仍可能在开头选了另一条路径。
- 关键词 pass 变好，但答案仍可能有关键词堆叠或事实关系错误。
- RAG 带来更低 loss，但如果来源错了，流畅回答反而更危险。

所以 report 同时保留 `baseline_generation`、`lora_generation`、`rag_lora_generation` 和三组 loss。

## 面向不同硬件的调整

| 显存条件 | 建议起点 | 先调整什么 | 不要动什么 |
| --- | --- | --- | --- |
| 8GB | Qwen3-0.6B LoRA | `MAX_LENGTH`、输出 token、gradient accumulation | held-out 题和通过规则 |
| 12GB RTX 5070 | 本文默认配置 | 先扩数据，再考虑 1.7B | 不要把验证平台写成知识边界 |
| 24GB+ | 1.7B LoRA 或受控的 4B QLoRA 对比 | 一次只改模型规模一个主变量 | 不能同时改数据、prompt、评分和模型 |

显存更多不代表第一步就应该换更大模型。如果主要失败是 retrieval miss 或评测泄漏，更大模型只会更贵地重复系统错误。

## 常见错误和排查顺序

1. **`torch.cuda.is_available()` 为 false。** 先检查 driver 可见性、虚拟环境和 PyTorch CUDA wheel，不要改 LoRA 参数。
2. **Hugging Face 下载中断。** 保留 cache 重试，这属于网络层，不是训练代码错误。
3. **CUDA OOM。** 先查其他占显存进程，再减 `MAX_LENGTH`；不要同时更换模型和数据。
4. **loss 是 NaN。** 检查 answer label 是否全被截断，以及学习率、dtype 和输入是否有非法值。
5. **train loss 降、held-out 不升。** 这是数据/泛化问题，先阅读失败样例，不要把更低 train loss 当成能力证据。
6. **RAG+LoRA 不如 RAG。** 检查模型是否忽略证据、prompt 是否过长、训练样例是否鼓励了自由发挥。

## 练习

1. 保持模型、seed、epoch 和 prompt 不变，只为一条失败补一条 SFT 样例，观察是否修复且不破坏其他题。
2. 将 `AGENT_LORA_EVAL_LIMIT=10` 后复测，特别检查“火星实时气象”是否能拒答。
3. 只将 target modules 改为 `q_proj/v_proj`，比较可训练参数、显存和 held-out 结果。
4. 将 Qwen3-0.6B 替换为另一个合法的小模型时，先核对 chat template 和 LoRA target module 名，不要直接复制参数。

## 参考资料

- [Qwen3-0.6B 模型卡](https://huggingface.co/Qwen/Qwen3-0.6B)
- [Hugging Face PEFT：LoRA 概念](https://huggingface.co/docs/peft/main/conceptual_guides/lora)
- [Hugging Face Transformers：Chat templates](https://huggingface.co/docs/transformers/en/chat_templating)
- [Hugging Face Transformers：Generation strategies](https://huggingface.co/docs/transformers/generation_strategies)
- [PyTorch CUDA semantics](https://docs.pytorch.org/docs/stable/notes/cuda.html)
- [本文完整 lab 和代码](/assets/labs/local-small-model-agent-course/README.md)

{% endraw %}
