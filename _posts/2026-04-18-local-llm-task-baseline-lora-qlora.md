---
layout: post
title: "本地小模型微调：先定义任务、baseline，再选择 LoRA 或 QLoRA"
date: 2026-04-18 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从需求和显存预算解释 RAG、LoRA、QLoRA的边界；12GB本地机器先做0.6B/1.7B，4B作为挑战。"
tags: [local-llm, lora, qlora, fine-tuning, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/local-small-model-agent-course/README.md`](/assets/labs/local-small-model-agent-course/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：本地小模型 / task spec / baseline / LoRA / QLoRA
> 本文 lab 已验证：生成 toy RAG baseline、模型参数显存预算表和工具 schema 检查；未训练真实大模型，因此不报告模型效果提升。

本地微调最常见的错误，是先选模型和训练脚本，再回头想任务。正确顺序是：任务定义、评价集、baseline、失败分类，然后才决定 RAG、LoRA 或 QLoRA。

## 学习目标

1. 区分可变知识、稳定行为和工具调用格式。
2. 解释为什么没有 baseline 就不能声称微调有效。
3. 理解 LoRA 和 QLoRA 解决的是显存与训练参数问题。
4. 给 12GB 本地显存制定保守模型路线。

## 需求决定方法

| 需求 | 优先方法 | 原因 |
| --- | --- | --- |
| 文档事实会更新 | RAG | 更新索引比重训更直接 |
| 输出格式稳定 | LoRA/SFT | 行为模式可监督 |
| 领域术语表达 | LoRA | 小数据可改变表达习惯 |
| 工具调用 JSON | LoRA + schema eval | 结构化输出可检查 |
| 复杂推理能力 | 数据和评估优先 | 小数据微调不保证推理提升 |

## 为什么需要任务规格和 baseline

“让模型更懂我的资料”无法直接验收。可执行的任务规格至少要固定：输入、允许使用的上下文、期望输出、不可接受输出、评价集和指标。例如工具调用任务可以写成：

```text
input: 一条中文用户请求
output: tool name + JSON arguments，或明确的 no_tool
hard checks: tool 在 allowlist 中；参数通过 schema；不得虚构字段
quality checks: 任务完成率、参数准确率、拒绝准确率
```

baseline 回答“现有最简单方案已经做到什么程度”。如果 base model 已达到 95% schema pass rate，微调的收益空间和数据需求与 baseline 只有 30% 时完全不同。评价集应在训练前冻结，训练样本和评价样本按任务实体或文档来源去重，避免把记忆训练样本当成泛化能力。

一个最小记录表可以这样设计：

| case_id | expected | base | RAG | LoRA | error_type |
| --- | --- | --- | --- | --- | --- |
| tool-001 | `search_notes` | pass/fail | pass/fail | pass/fail | wrong_tool/bad_args |
| fact-001 | cited answer | pass/fail | pass/fail | pass/fail | retrieval/hallucination |

先记录逐样例结果，再汇总准确率。只有总分而没有失败样例，会让后续数据修订失去方向。

## LoRA 为什么省

LoRA 冻结基座权重，只训练低秩增量矩阵。对一个线性层 `W`，不直接训练完整 `W`，而是训练：

```text
W' = W + B A
rank(A,B) = r, r 远小于 hidden size
```

训练参数减少，optimizer state 和梯度也减少。QLoRA 进一步把 frozen base model 量化到 4-bit，再训练 adapter，从而降低基座权重显存占用。

## 本地显存预算

lab 给出粗略参数显存表，只计算参数本身，不包含 activation、optimizer、临时 workspace 和 KV cache：

```text
0.6B fp16 参数约 1.12GB
1.7B fp16 参数约 3.17GB
4B   fp16 参数约 7.45GB，int4 参数约 1.86GB
7B   fp16 参数约 13.04GB，int4 参数约 3.26GB
```

这解释了为什么 12GB 本地路线应先做 0.6B/1.7B LoRA，4B QLoRA 作为挑战，7B/8B 不作为第一版验收目标。

参数显存只是下界。训练峰值还包含 activation、gradient、optimizer state、量化元数据、临时 workspace 和 allocator 碎片。sequence length、micro-batch size、gradient accumulation、checkpointing 和 attention 实现都会改变峰值。

运行本地 toy lab 可以先验证预算表和 baseline 管线：

```bash
./run_lab.sh
cat reports/local_model_agent_report.md
```

稳定输出包括：

```text
RAG retrieval accuracy on the toy set: 1.00
0.6B fp16 params: 1.12 GB
1.7B fp16 params: 3.17 GB
4B int4 params: 1.86 GB
```

`1.00` 只覆盖 4 条人工查询，说明检索代码按 toy 数据工作；它不能替代真实领域评价。显存数字只按参数量乘位宽估算，也不能当作训练峰值。两项结果都是 readiness 证据。

## baseline 怎么设

至少比较三条线：

```text
base model only
RAG + base model
LoRA 或 QLoRA + RAG / tool schema
```

如果 RAG 已经解决事实问题，微调的目标就应转向格式、风格和工具调用稳定性，而不是重复背文档。

## 最小真实训练闭环

当 CUDA PyTorch 环境就绪后，第一轮应限制变量：固定一个小模型、一份小训练集、一份冻结评价集和一组训练参数。运行记录至少保存：

```text
model revision and tokenizer revision
dataset hash and split rule
LoRA target modules, rank, alpha, dropout
sequence length, batch, accumulation, learning rate, seed
GPU model, software versions, peak allocated memory
base/RAG/adapter per-case evaluation
adapter checkpoint and inference command
```

先用 0.6B 完成“训练—保存—重新加载—同一评价集复测”的闭环。闭环通过后再扩大模型或改为 QLoRA。这样一旦结果变化，可以定位是模型规模、量化、数据还是训练参数造成的。

## RTX 5070 落地与迁移边界

RTX 5070 12GB 适合作为本地小模型实验平台，但不应把路线写成“5070专用”。换成 8GB 时缩短 sequence length、用更小模型；换成 24GB 时可尝试更长上下文或 7B QLoRA；换成 40GB+ 时可以扩大实验，但仍要保留 baseline 和评价集。

## 常见错误

1. **把微调当知识库。** 可变知识优先 RAG。
2. **只看训练 loss。** 任务效果要看评价集和错误类型。
3. **一开始就训大模型。** 先用小模型验证数据、脚本和评价。
4. **忽略 adapter 部署。** 保存、加载、合并和推理路径都要写进报告。

## 练习

写一个任务规格：输入、输出、评价指标、base model baseline、RAG baseline、LoRA 目标。不要写训练脚本，先写失败样例。

## 参考资料

- Hugging Face PEFT：[Quantization](https://huggingface.co/docs/peft/developer_guides/quantization)
- Hugging Face TRL：[SFT Trainer](https://huggingface.co/docs/trl/sft_trainer)
- Hugging Face Transformers：[Causal language modeling](https://huggingface.co/docs/transformers/tasks/language_modeling)
- Qwen 模型卡：[Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B)

{% endraw %}
