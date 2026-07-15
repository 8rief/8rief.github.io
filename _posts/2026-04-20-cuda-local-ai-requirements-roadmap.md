---
layout: post
title: "CUDA 与本地小模型工程总纲：先从需求、瓶颈和证据开始"
date: 2026-04-20 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 CUDA、LoRA、QLoRA、RAG 和本地 agent 放回真实需求里：先定义问题和证据，再落到 RTX 5070 的可复现实验。"
tags: [cuda, gpu, local-llm, fine-tuning, agent, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/cuda-local-ai-foundations/README.md`](/assets/labs/cuda-local-ai-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：CUDA 与本地小模型工程 / 路线总纲 / 环境证据
> 本文 lab 已验证：本机可见一张 NVIDIA GPU，`cuda_cpp_ready=False`，`pytorch_cuda_ready=False`，并生成 `gpu_env_report.md` 和 `cuda_local_ai_roadmap.md`。

学习 CUDA、本地微调和 agent 开发时，最容易犯的错误是先收集工具名：CUDA、PyTorch、Transformers、LoRA、QLoRA、RAG、vLLM、Triton、LangGraph。工具清单看起来完整，但没有说明为什么要学、解决什么瓶颈、如何判断做对了。本文把路线倒过来：先写需求，再抽象原理，最后才选择工具和本地实验。

本系列的实际验证平台是一张 12GB 显存的 RTX 5070，但知识路线不以这张卡为边界。5070只回答“这台机器上怎么复现”；原理部分必须能迁移到 8GB、24GB 或更大显存机器。

## 学习目标

读完并跑完实验后，你应该能做到：

1. 把 CUDA 学习目标写成可验证需求，而不是“想学 GPU”。
2. 区分 GPU 编程、模型微调和 agent 系统分别解决什么问题。
3. 解释为什么本地实验先收集硬件、driver、toolkit 和 Python 包证据。
4. 判断 RTX 5070 在本系列中的角色：实验平台，不是知识边界。
5. 说出为什么要先学性能模型，再读复杂 CUDA 源码。

## 先修知识

建议已经知道命令行、Python 环境、项目目录和基本 Git 工作流。如果这些还不熟，可以先读本栏目中的本地帮助、PATH、环境变量和脚本错误处理文章。数学上只需要知道数组、二进制位和函数输入输出；bitmask、线性代数、概率、梯度和优化已经分别放在数学基础与 AI 工程路线中补齐。

## 先从需求说起

这条路线服务四个需求。

第一，想知道 GPU 为什么能加速。答案不应停在“因为并行”，还要说明并行度够不够、访存是否连续、同步是否太多、数据传输是否盖过了计算。

第二，想读懂真实 CUDA 代码。像 N-Queens GPU 求解器这样的项目不会只写一个简单 kernel，它会同时处理状态压缩、搜索树切分、动态取任务、shared memory 栈和底层指令控制。直接读源码会把太多概念混在一起，所以要先建立性能模型。

第三，想在本地微调专业领域小模型。微调并不等于把所有知识塞进参数。可变事实更适合 RAG，稳定输出格式、领域表达和工具调用习惯才更适合 LoRA 或 QLoRA。

第四，想做一个能完成任务的本地 agent。agent 是系统，不是单个模型：检索、工具、状态、模型、校验和失败回放都要设计。

## 核心模型

![CUDA 与本地小模型工程路线](/assets/diagrams/cuda-local-ai-requirements-roadmap.svg)

这张图的顺序是本系列的写作约束：真实需求先于工具；原理模型先于代码；本地验证先于效果主张；硬件迁移边界要写清楚。

## 为什么需要先做环境证据

这一类结论都依赖当前机器状态。一个 CUDA kernel 编译失败，可能是源码错了，也可能是 `nvcc` 没装、编译目标架构不支持、driver/toolkit 不匹配。一个 LoRA 脚本不能跑，可能是模型太大，也可能是 PyTorch 没有 CUDA wheel、`bitsandbytes` 不支持当前环境，或者只是 Python 包没装。

因此第一步应先记录事实，再根据缺口安装必要组件：

```bash
./run_lab.sh
```

本次总纲 lab 输出：

```text
gpu_visible=True
cuda_cpp_ready=False
pytorch_cuda_ready=False
gaps=8
roadmap_items=5
hardware_tiers=5
```

这个结果的含义是：GPU 能被系统看到，但 CUDA C++ 编译工具和 PyTorch CUDA 训练环境还没就绪。它是一份安装和验证清单。把 gap 公开写出来，可以避免把环境问题误判成原理问题。

后续补充：CUDA C++ 编译工具这一层已经在[硬件瓶颈实测第一课](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html)里用用户态 toolkit 补齐，并跑出 `CUDA_STATUS=ok`。这只关闭了 `nvcc` 缺口；PyTorch CUDA、LoRA/QLoRA 训练栈和专业领域评测仍要按各自实验单独验收。

## 硬件不是中心，硬件预算是边界

本系列用硬件层级来组织实验：

| 层级 | 能做什么 | 边界 |
| --- | --- | --- |
| CPU-only | 算法、数学、baseline、小 toy 模型 | 不作为真实 LLM 微调验收 |
| 6-8GB GPU | CUDA 基础、小模型 LoRA | 短上下文、小 batch |
| 10-12GB GPU | 本地小模型主线；RTX 5070 属于此层 | 4B QLoRA 需谨慎，7B 训练只作挑战 |
| 16-24GB GPU | 4B/7B QLoRA 更稳，较长上下文 | 仍需显存预算和 baseline |
| 40GB+ GPU | 更大模型、多模型、长上下文实验 | 仍不能跳过任务定义和评估 |

硬件升级会扩大可承载规模，但不会改变方法论。没有 baseline 的模型结果仍然不可解释；没有 profiling 的 CUDA 优化仍然可能只是猜测。

如果你还没有建立硬件瓶颈的证据链，建议先读[硬件瓶颈地图](/computer-science-teaching/2026/03/26/hardware-bottleneck-map-cpu-memory-gpu.html)，再跑[硬件瓶颈实测第一课](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html)。前者告诉你先分清 compute、memory、communication 和 capacity，后者让你用本机实验看到 cache locality、stride、branch 和 CUDA timing 为什么必须分层。

## 为什么 CUDA 从 vector add 开始

vector add 是小实验，但不是玩具。它把 CUDA 的基本边界全部暴露出来：CPU 准备数据，GPU 申请显存，host 到 device 拷贝，kernel launch，device 到 host 拷贝，最后检查正确性。矩阵乘法、reduction、N-Queens 和模型训练都会复用这些边界。

如果第一课直接读复杂项目，读者会同时遇到线程索引、shared memory、atomic、分支、栈、编译架构和 profiling，无法判断每个机制为什么出现。

## 为什么模型路线从任务规格开始

本地微调要先回答四个问题：

```text
输入是什么？
输出是什么？
如何评价？
不用微调的 baseline 是什么？
```

如果目标是回答不断变化的文档事实，RAG 是首选，因为知识可以更新。如果目标是固定回答格式、领域术语风格或工具调用结构，LoRA 更合适，因为这些是相对稳定的行为。QLoRA 进一步把 frozen base model 量化到 4-bit，再训练 adapter，适合显存有限的单卡实验。

本地 12GB 显存的合理顺序是：先用小模型跑通数据和评估，再扩大模型。第一阶段不追求 7B 起步，而是先跑 Qwen3-0.6B 或 1.7B 的 LoRA；4B QLoRA 作为显存预算挑战。

## 为什么 agent 不是最后接一个聊天循环

agent 的难点不在“多问模型几次”，而在系统边界：资料怎么检索，工具怎么描述，调用结果怎么验证，失败怎么回放，长上下文怎么控制，输出格式怎么约束。小模型尤其需要系统补足：RAG 负责可变知识，工具负责外部动作，微调负责稳定行为和格式。

所以做本地 agent 验收时至少要保留三个对照：

```text
base model only
RAG + base model
RAG + LoRA + tool schema
```

只有比较这三者，才能说清楚微调和 agent 系统各自带来了什么。

## 当前最小闭环

当前路线先用这些文章形成最小闭环：

1. CUDA 与本地小模型工程总纲。
2. bitmask 状态集合数学补充。
3. 第一个 CUDA kernel：vector add。
4. SIMT、thread/block/grid 和边界检查。
5. global memory 与连续访问。
6. N-Queens bitmask DFS 到 GPU 子问题。
7. 小模型微调任务规格、baseline 和评价集。
8. Qwen3-0.6B LoRA 最小闭环。
9. 本地 RAG + 工具调用 agent 原型。

shared memory、streams、更大模型和复杂 agent 优化不作为当前最小闭环的必要条件；只有在这些主题服务具体实验问题时，才单独作为新的验收问题处理。

## 常见错误

1. **把显卡型号当成教学中心。** 显卡只决定本地可复现实验规模，原理要能迁移。
2. **把 GPU 快理解成单线程快。** GPU 主要靠吞吐和延迟隐藏，不是每个线程都比 CPU 快。
3. **把微调当成知识库。** 可变事实优先 RAG，稳定行为才考虑 LoRA。
4. **没有 baseline 就报告效果。** 没有对照组时，准确率、loss 或主观回答质量都很难解释。
5. **先读复杂 CUDA 源码。** 没有 thread、memory、atomic、profiling 基础时，源码细节会变成记忆负担。

## 练习或延伸

1. 在自己的机器上运行环境探针，记录 GPU、`nvcc` 和 PyTorch CUDA 状态。
2. 把硬件层级表改成你能使用的机器列表，写出每台机器适合哪些实验。
3. 选一个专业领域任务，先写输入、输出、评价指标和 baseline，不要先写训练脚本。

## 参考资料

- NVIDIA 文档：[CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)
- NVIDIA 文档：[CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
- NVIDIA 文档：[CUDA on WSL User Guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- PyTorch 文档：[Get Started Locally](https://pytorch.org/get-started/locally/)
- Hugging Face Transformers 源文档：[Causal language modeling](https://github.com/huggingface/transformers/blob/main/docs/source/en/tasks/language_modeling.md)
- Hugging Face PEFT 源文档：[Quantization](https://github.com/huggingface/peft/blob/main/docs/source/developer_guides/quantization.md)
- Hugging Face TRL 源文档：[SFT Trainer](https://github.com/huggingface/trl/blob/main/docs/source/sft_trainer.md)
- Qwen 模型卡：[Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B)
- 参考项目：[ygch/n_queens](https://github.com/ygch/n_queens)

{% endraw %}
