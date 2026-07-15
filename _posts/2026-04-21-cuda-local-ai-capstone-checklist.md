---
layout: post
title: "结课项目：从 CUDA 正确性到本地 Agent 的验收清单"
date: 2026-04-21 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一张学习者可执行的清单验收 CUDA kernel、N-Queens 任务切分、PyTorch CUDA、Qwen LoRA、RAG、工具调用和 held-out 评测。"
tags: [cuda, local-llm, agent, capstone, evaluation, teaching]
---
{% raw %}

结课项目要求你在自己的 WSL 中留下一条能被复查的证据链，而不是再复述一遍概念。这条链从 CUDA 正确性开始，经过 N-Queens 搜索任务切分，再进入 PyTorch、Qwen LoRA、RAG、工具执行和 held-out 评测。

只有当你能说明“某个输出证明了什么、没证明什么”时，这一项才算完成。

## 学习目标

1. 为 CUDA 正确性、搜索切分、本地小模型和 Agent 分别选择证据。
2. 区分 environment ready、correctness pass、quality pass 和 performance claim。
3. 从一个公开 lab 生成可读又可机器检查的 JSON report。
4. 用失败分类决定下一步，而不是默认换更大模型。

## 为什么需要分层验收

这个项目的核心问题是：环境、正确性、模型训练、Agent 系统和最终质量使用不同证据。分层验收让你在失败时能找到具体边界，也防止用弱证据支持过强结论。

整体顺序如下：

```text
driver/device 可见
  -> nvcc/PyTorch runtime 分层验收
  -> CUDA kernel + CPU oracle
  -> N-Queens CPU bitmask + task splitting
  -> Agent task contract
  -> RAG + tool schema + bounded state + trace
  -> Qwen3-0.6B base
  -> LoRA training
  -> base / LoRA / RAG+LoRA held-out comparison
  -> failure taxonomy -> 只修主要失败层
```

## 验收矩阵

| 模块 | 你要能展示的证据 | 证明 | 不证明 |
| --- | --- | --- | --- |
| GPU 环境 | `nvidia-smi`、`nvcc --version`、`torch.cuda.is_available()` 分开输出 | driver、compiler、runtime 各自状态 | kernel 正确或模型质量 |
| CUDA 第一个 kernel | vector add GPU 结果与 CPU oracle 逐项相等 | host/device 正确性闭环 | GPU 比 CPU 快 |
| thread/grid | 数组长度不整除 block 时仍不越界 | 全局索引和 guard 正确 | block size 最优 |
| reduction/atomic | CPU sum/histogram 与 GPU 一致 | 多线程合并正确 | 算法已达峰值性能 |
| N-Queens | N=8 答案为 92，切分后合计仍为 92 | task splitting 保持语义 | GPU 负载已平衡 |
| Agent core | 8 个 unit tests + 8 个 CPU-first steps | RAG、schema、state、trace 和回归门工作 | 开放世界通用 Agent |
| Qwen base | 固定 model revision，输出 source id | 本地模型接入 RAG | 领域能力达标 |
| LoRA | adapter 保存、loss 有限且可重跑 | 冻结基座和低秩训练管线可用 | train loss 下降即专业化成功 |
| Agent quality | 同一 held-out 集的 base/LoRA/RAG+LoRA 逐题结果 | 当前有限集上的改善或回归 | 其他领域、其他用户或长期稳定性 |

## 第一部分：环境证据不能合并成一个“CUDA 可用”

在 WSL 中分别执行：

```bash
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
nvcc --version
python3 - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
PY
```

如果 `nvidia-smi` 通过、`nvcc` 失败，结论是 driver/device 可见但 CUDA C++ compiler 不可用，而不是“CUDA 一半可用”。如果 PyTorch 失败，应继续检查 virtual environment 和 wheel，不应改 kernel 代码。

## 第二部分：CUDA 和 N-Queens 先要有 CPU oracle

完成下列文章的代码和练习：

1. [CUDA 第一个 kernel：vector add 背后的 host/device 边界](/computer-science-teaching/2026/04/21/cuda-host-device-vector-add.html)
2. [CUDA thread/block、SIMT 和访存](/computer-science-teaching/2026/07/03/cuda-thread-index-simt-memory.html)
3. [CUDA reduction、atomic 和 profiling](/computer-science-teaching/2026/04/22/cuda-reduction-atomic-profiling.html)
4. [N-Queens 从 bitmask DFS 到 GPU 子问题](/computer-science-teaching/2026/04/22/nqueens-bitmask-dfs-task-splitting.html)
5. [N-Queens dynamic work fetching 和 shared-memory stack](/computer-science-teaching/2026/04/23/nqueens-dynamic-work-shared-stack.html)

对每个 GPU 结果，你都应保留一个更简单、先验证过的 CPU 版本。性能优化不能用来弥补正确性证据缺失。

## 第三部分：从公开 Agent lab 复跑系统闭环

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/local-small-model-agent-course
chmod +x run_lab.sh learn.sh setup_gpu.sh
./run_lab.sh
```

验收 marker：

```text
AGENT_06_EVAL_OK passed=10 total=10 failures=0
AGENT_07_OPTIMIZE_OK baseline=8/10 improved=10/10 cache_hits=190
AGENT_CPU_COURSE_OK steps=8
LOCAL_AGENT_LAB_OK cpu_steps=8 tests=8
```

你还应手动打开：

```bash
cat reports/03-tool-validation.json
cat reports/05-controller-loop.json
cat reports/07-failure-driven-optimize.json
```

不要只看 marker。第一个 JSON 展示为什么三个工具调用被拒绝，第二个展示四阶段 trace，第三个展示优化前后的失败和 cache 计数。

## 第四部分：加入本地 Qwen 和 LoRA

```bash
./setup_gpu.sh
./learn.sh 08-local-qwen
./learn.sh 09-domain-lora
```

RTX 5070 12GB 的实测记录：

```text
AGENT_08_LOCAL_QWEN_OK rag=yes sources=1 generated_tokens=...
AGENT_09_DOMAIN_LORA_OK steps=8 loss=5.4119->4.6738 passes=0/0/3 memory_mib=1699.1
```

这些数字不是“必须复制到小数点后四位”的答案。你要核对的是：

- model id 和 revision 是否固定；
- train/eval 是否分开；
- adapter 是否真正保存；
- loss 是否有限且训练过程无错；
- 同一 held-out 集上的三种方法是否都有逐题记录；
- 失败是否被保留，而不是只报最好样例。

## 第五部分：写一份自己的验收报告

建议使用以下结构：

```markdown
# 本地 CUDA 与 Agent 结课报告

## 环境
- GPU / driver / visible memory
- nvcc
- Python / PyTorch / CUDA runtime
- model id / revision

## 正确性
- vector add CPU/GPU 校验
- N-Queens CPU oracle 与 split total
- Agent unit tests 和 CPU-course marker

## 模型实验
- train/eval 切分
- LoRA target modules / rank / alpha
- train loss、held-out loss、显存
- base / LoRA / RAG+LoRA 逐题结果

## 失败分类
- retrieval
- tool/arguments
- unsupported claim
- state
- model generation

## 结论边界与下一步
```

报告中的实测数据要从当次 JSON 读取，不要从本文或上次 transcript 手抄。

## 最终自检

- [ ] 我能区分 driver、runtime 和 compiler。
- [ ] 每个 GPU 正确性实验都有 CPU oracle。
- [ ] 我没有把 vector-add 正确性 marker 写成加速证据。
- [ ] Agent 的工具执行前有白名单和参数验证。
- [ ] 状态是有界的，trace 能显示失败发生在哪层。
- [ ] eval answer 没有进入训练集或 RAG 索引。
- [ ] 模型 revision、seed、主要训练参数和评分规则已记录。
- [ ] 我同时保留 loss、生成结果、source 和 failure type。
- [ ] 我没有用 0.6B 小数据实验声称通用专业能力。
- [ ] 下一步针对主要失败层，而不是默认换大模型。

## 常见的不合格结论

1. **“`nvidia-smi` 有输出，所以 CUDA C++ 已准备好。”** 缺少 `nvcc` 证据。
2. **“vector add 运行正确，所以 GPU 更快。”** 缺少公平计时和 CPU baseline。
3. **“LoRA train loss 下降，所以已经专业化。”** 缺少 held-out 生成与失败分类。
4. **“RAG top-1 命中，所以最终答案正确。”** 模型可能忽略证据或添加不受支持的断言。
5. **“一条 demo 成功，所以 Agent 稳定。”** 缺少冻结回归集和错误路径。

## 参考资料

- [NVIDIA CUDA C++ Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)
- [NVIDIA CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
- [PyTorch CUDA semantics](https://docs.pytorch.org/docs/stable/notes/cuda.html)
- [Hugging Face PEFT：LoRA](https://huggingface.co/docs/peft/main/conceptual_guides/lora)
- [Qwen3-0.6B 模型卡](https://huggingface.co/Qwen/Qwen3-0.6B)
- [公开 Agent lab](/assets/labs/local-small-model-agent-course/README.md)

{% endraw %}
