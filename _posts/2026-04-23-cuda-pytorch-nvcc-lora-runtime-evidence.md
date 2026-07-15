---
layout: post
title: "CUDA/PyTorch 实机验收：从 driver、nvcc 到 LoRA 闭环"
date: 2026-04-23 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用可独立执行的命令区分 NVIDIA driver、CUDA runtime、nvcc 编译器和 LoRA 训练栈，并说清每层输出能证明什么。"
tags: [cuda, pytorch, local-llm, lora, verification, teaching]
---
{% raw %}

一台机器能被 `nvidia-smi` 看见，不等于它已经准备好 CUDA C++ 编译、PyTorch CUDA 和模型微调。本文回答一个工程问题：**怎样用独立命令证明 driver、runtime、compiler 和 training stack 四层分别工作？**

文中的 RTX 5070 数据是本地验证记录。学习者应在自己的 WSL 中逐层执行命令，不要把本文的设备名和显存数字当成自己的运行结果。

## 学习目标

1. 区分 driver 可见、CUDA runtime 可用、`nvcc` 可编译、深度学习框架可训练这四层证据。
2. 理解为什么 RTX 5070 是本地验收平台，但不是课程知识边界。
3. 用一组最小命令把 `vector_add.cu`、PyTorch CUDA matmul、LoRA toy training 和 HF/PEFT tiny LoRA 串成证据链。
4. 明确哪些输出只能说明“环境和闭环跑通”，哪些输出还不能说明“专业领域模型效果提升”。

## 先修知识与实验边界

开始前需要会创建 Python virtual environment、安装包、读取命令退出状态，并理解 host/device memory 的基本区别。CUDA kernel、LoRA 公式和训练循环可以边做边学，本文不会假设读者已经完成大模型训练。

实验只在一个隔离环境中安装用户态 toolkit 和 Python 包，不替换 Windows/WSL NVIDIA driver。它生成环境、CUDA C++、PyTorch、依赖栈和 LoRA 五类 JSON/Markdown 报告。真实模型权重、下载缓存和 adapter 文件留在本地，不作为博客附件发布。

## 为什么需要四层运行证据

`nvidia-smi` 只能说明 WSL 能通过驱动看到 GPU。它不能单独证明以下事情：

| 层级 | 要证明什么 | 典型证据 |
| --- | --- | --- |
| Driver | 系统能看到 GPU | `nvidia-smi` 输出设备名、driver、显存、compute capability |
| CUDA runtime | Python 框架能调用 CUDA 库 | `torch.cuda.is_available()` 为真，张量放到 `cuda:0` 并同步 |
| CUDA compiler | CUDA C++ 源码能变成目标 GPU 可执行程序 | `nvcc -arch=sm_120` 编译通过，程序输出正确性标记 |
| Training stack | 小模型微调工具链能跑一轮 | Transformers/PEFT/TRL/bitsandbytes import，通过最小 LoRA loss/adapter 证据 |

这四层故障模式不同。驱动坏了，Python 包装得再好也没用；只有 PyTorch wheel，没有 `nvcc`，仍然不能说 CUDA C++ 编译已验收；LoRA toy loss 下降，只能说明训练闭环和参数更新存在，不能替代专业验证集。

## 本机这次的实测环境

实验机在 WSL2 中暴露出一张 RTX 5070。关键环境摘要如下：

```text
GPU: NVIDIA GeForce RTX 5070
Driver: 595.79
Visible memory: 12227 MiB
Compute capability: 12.0
CUDA compiler: nvcc 12.8, V12.8.93
PyTorch: 2.11.0+cu128
PyTorch CUDA runtime: 12.8
PyTorch arch list: sm_75, sm_80, sm_86, sm_90, sm_100, sm_120
```

本机属于 12GB 消费级 GPU：足够做 CUDA 入门、搜索/访存实验、LoRA/QLoRA 小规模验证，但不足以随意做 7B/8B 全参训练。换成更弱 GPU，实验要缩小 batch、模型和输入长度；换成更强 GPU，可以扩大模型、batch 和 profile 范围，但证据链仍然一样。

## 安装策略：先用户态，避免替换驱动

这次没有替换 WSL/Windows NVIDIA driver。执行顺序是：

1. 建立隔离 Python 环境。
2. 用 PyTorch 官方 CUDA wheel 安装 `torch`、`torchvision`、`torchaudio`。
3. 安装 `transformers`、`accelerate`、`peft`、`trl`、`datasets`、`safetensors`、`bitsandbytes`。
4. 发现 PyPI CUDA wheel 提供了 runtime、headers、`ptxas` 等组件，但本环境没有完整 `nvcc` frontend。
5. 下载 NVIDIA CUDA 12.8.1 runfile，只安装 toolkit 到用户可写目录，不安装 driver。
6. 设置 `CUDA_HOME`、`PATH`、`LD_LIBRARY_PATH` 后编译 CUDA C++。

抽象成可复用命令是：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
python -m pip install transformers accelerate peft trl datasets safetensors sentencepiece bitsandbytes

# 如果需要 CUDA C++ nvcc，使用 NVIDIA runfile 只装 toolkit，不装 driver。
wget -c https://developer.download.nvidia.com/compute/cuda/12.8.1/local_installers/cuda_12.8.1_570.124.06_linux.run
bash cuda_12.8.1_570.124.06_linux.run --silent --toolkit --toolkitpath "$HOME/.local/cuda-12.8.1" --no-man-page --override
export CUDA_HOME="$HOME/.local/cuda-12.8.1"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"
```

第一次直接用 `pip` 下载 PyTorch 大 wheel 时发生过两次 `IncompleteRead`。这个失败属于网络传输层，不是 CUDA 或 PyTorch 本身失败。处理方法是对大 wheel 使用可续传下载，或者保留 pip cache 后重试；不要因为下载中断就修改课程结论。

## 先用三组独立命令核对环境

Driver/device 层：

```bash
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
```

CUDA compiler 层：

```bash
export CUDA_HOME="$HOME/.local/cuda-12.8.1"
export PATH="$CUDA_HOME/bin:$PATH"
nvcc --version
```

PyTorch runtime 层：

```bash
.venv/bin/python - <<'PY'
import torch
print("torch", torch.__version__)
print("runtime", torch.version.cuda)
print("available", torch.cuda.is_available())
if torch.cuda.is_available():
    x = torch.arange(16, device="cuda", dtype=torch.float32).reshape(4, 4)
    y = x @ torch.eye(4, device="cuda")
    torch.cuda.synchronize()
    print("device", torch.cuda.get_device_name(0))
    print("last", float(y[-1, -1].cpu()))
PY
```

第一条只证明 GPU 和 driver 可见；第二条证明 shell 能找到 `nvcc`；第三组证明当前 `.venv` 里的 PyTorch 能在 CUDA device 上完成矩阵乘法并同步。三者不能互相替代。

如果你要继续跑 Qwen3-0.6B 和 LoRA，使用公开 Agent lab：

```bash
cd ~/8rief.github.io/assets/labs/local-small-model-agent-course
./setup_gpu.sh
./learn.sh 08-local-qwen
./learn.sh 09-domain-lora
```

该 lab 会生成当前环境的 JSON report，避免从本文手抄易漂移的显存、loss 和生成数字。

## 实验一：PyTorch CUDA smoke test

验证代码做三件事：导入 PyTorch，确认 CUDA 可用，把 `float16` 矩阵乘法放到 GPU 上运行并同步。

```python
import torch

assert torch.cuda.is_available()
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.get_device_name(0))
print(torch.cuda.get_device_capability(0))
print(torch.cuda.get_arch_list())

x = torch.randn(2048, 2048, device="cuda", dtype=torch.float16)
y = x @ x
torch.cuda.synchronize()
print(float(y[0, 0]))
```

本机报告：

```text
cuda_available=True
device=NVIDIA GeForce RTX 5070
capability=12.0
arch_list includes sm_120
5 x fp16 2048x2048 matmul completed
max_memory_allocated_mib=40.1
```

这不是 benchmark。它只能证明 runtime、driver、wheel 和 GPU 指令目标能协同工作。若要做性能结论，还需要固定输入规模、warmup、重复次数、CPU/GPU 口径和统计指标。

## 实验二：CUDA C++ vector_add 真编译

第一版栏目里的 `vector_add.cu` 现在不再是“只生成源码”。编译命令是：

```bash
nvcc -O2 -arch=sm_120 src/vector_add.cu -o reports/vector_add_cuda
reports/vector_add_cuda
```

本机输出：

```text
vector_add_ok n=16 last=45.0
```

`last=45.0` 来自输入 `a[i]=i`、`b[i]=2*i`，最后一个元素是 `15 + 30`。这说明 host 初始化、device 分配、H2D copy、kernel launch、D2H copy、同步、CPU 校验和释放形成了完整闭环。

为什么指定 `sm_120`？因为本机 GPU 的 compute capability 是 12.0。不能把别人的 `sm_86`、`sm_89` 或 `sm_90` 命令机械复制过来；目标架构要来自当前设备和当前 toolkit 的支持范围。

## 实验三：LoRA 原理闭环

为了先证明“低秩适配器真的在 GPU 上训练”，lab 构造了一个冻结线性层和一个隐藏的 rank-4 目标增量，只训练 LoRA 参数。

本机报告：

```text
frozen_params=512
trainable_lora_params=192
rank=4
losses every 20 steps:
2.905014, 0.251299, 0.0282792, 0.00489427, 0.000475459, 5.81426e-05, 7.186e-06
final_loss_ratio=2.47e-06
```

LoRA 把需要学习的权重增量限制在低秩子空间中。全量线性层有 512 个参数；这里实际训练 192 个 adapter 参数。真实大模型会冻结数亿到数十亿个基座参数，只训练占比很小的 adapter 参数。

## 实验四：HF/PEFT tiny causal-LM LoRA

下一步把原理闭环接到常用库：Transformers 负责模型和 tokenizer，PEFT 用 `LoraConfig` 和 `get_peft_model` 包装模型，训练 80 个小步并保存 adapter。

本机栈验证：

```text
transformers=5.13.0
accelerate=1.14.0
peft=0.19.1
trl=1.7.1
datasets=5.0.0
bitsandbytes=0.49.2
bitsandbytes 8-bit linear smoke passed on CUDA
```

最小 LoRA 训练闭环：

```text
model=sshleifer/tiny-gpt2
revision=5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be
seed=20260704
deterministic_algorithms=true
steps=80
trainable_params=256 / 102970
trainable_percent=0.2486%
initial_loss=10.8288
best_loss=10.8189
adapter_saved=true
max_memory_allocated_mib=146.7
```

这组数的正确解释是：HF/PEFT API、CUDA 张量、反向传播、optimizer step 和 adapter 保存都跑通了。它不说明 tiny GPT-2 学会了 CUDA 专业知识，也不说明一个真实领域模型已经达标。真正做专业领域小模型时，还需要：领域样本、清洗规则、train/valid/test 划分、baseline、held-out 评测、失败案例回放和模型卡。

同一实验连续执行两次后，80 个 loss 值、initial/best/final loss 完全一致。确定性来自三项约束：固定模型 revision，固定 CPU/CUDA random seed，并启用 PyTorch deterministic algorithms。elapsed time 仍会随系统负载变化，因此它不参与字节级一致性判断。

## 面向 12GB 本地 GPU 的微调策略

对本机这类 12GB GPU，推荐顺序是：

| 阶段 | 目标 | 为什么 |
| --- | --- | --- |
| toy LoRA | 证明训练闭环 | 排除环境、dtype、梯度和保存问题 |
| tiny HF/PEFT | 证明库 API 闭环 | 排除 tokenizer/model/adapter 集成问题 |
| 0.5B--1.7B LoRA | 做真实任务 baseline | 显存风险低，便于快速迭代数据与评测 |
| 4B QLoRA | 作为进阶 | 需要更严格的量化、batch、长度和显存控制 |
| 7B/8B | 谨慎 stretch | 12GB 下通常边界紧，容易把时间耗在 OOM 调参上 |

专业领域微调应从任务定义开始：输入是什么、输出是什么、哪些答案算错、baseline 是什么、评测集是否覆盖真实失败模式。CUDA 和 LoRA 让这个闭环在本地可执行，但不能替代问题定义和评测。

## 常见错误与定位顺序

1. **把 `nvidia-smi` 当成完整验收。** 它只证明 driver 可见；继续检查 PyTorch runtime、`nvcc` 和训练栈。
2. **把 PyTorch CUDA wheel 当成完整 toolkit。** wheel 可以包含运行库和若干工具，但 CUDA C++ 编译仍需要可用的 `nvcc` frontend。
3. **机械复制 `-arch`。** 先读取设备 capability，再确认当前 toolkit 支持目标架构；本机 12.0 对应 `sm_120`。
4. **runner 使用了系统 Python。** 输出包版本和 `sys.executable`，确保所有脚本进入同一个 virtual environment。
5. **网络下载失败后修改模型结论。** `IncompleteRead`、TLS EOF 和超时属于网络/缓存层，先续传或离线复跑。
6. **训练脚本没有固定 revision 与 seed。** 模型更新和 LoRA 参数随机初始化会让发布数字漂移。
7. **只看最后一个 loss。** 小数据训练会波动；至少保留完整曲线、initial、best、final 和 held-out baseline。
8. **把 tiny LoRA loss 下降写成领域能力提升。** 这组实验只验证 API、梯度、optimizer 和 adapter 保存。
9. **把一次 smoke timing 写成加速结论。** 性能结论需要 warmup、重复、同步边界、统计量和公平 baseline。
10. **在公开报告中保留本地绝对路径。** 对外只给版本、接口、相对产物名和可复现命令。

定位时按 driver → runtime → compiler → dependency imports → toy LoRA → HF/PEFT 的顺序逐层收窄。后层失败时先确认前层仍通过，不要同时更换 driver、toolkit、wheel、模型和训练参数。

## 这次验收后，第一版栏目边界如何变化

更新前：

```text
CUDA C++ source ready, compile skipped because nvcc missing.
Python ML stack absent, real LoRA not claimed.
```

更新后：

```text
CUDA C++ vector_add compiled for sm_120 and ran correctly.
PyTorch CUDA wheel works on the visible RTX 5070.
HF/PEFT/TRL/bitsandbytes stack imports and CUDA smoke pass.
LoRA principle training and tiny HF/PEFT adapter training both run on GPU.
```

仍然没有改变的边界：

1. 没有发布 CUDA 性能 benchmark；`vector_add` 只是正确性验收。
2. 没有声称 tiny LoRA 具备专业领域能力；它只是训练管线验收。
3. 没有把 RTX 5070 写成唯一目标；它只是本地证据平台。
4. 没有替换 driver；如果读者系统 driver 过旧，必须先按官方说明解决 driver/toolkit 兼容性。

## 练习

1. 把 matmul shape 从 `2048×2048` 改成 `512×512`，只比较显存和完成状态，不从单次时间推导性能结论。
2. 故意把 `-arch=sm_120` 改成当前 toolkit 不支持的值，保存 `nvcc` 错误并判断失败属于 compiler 还是 runtime。
3. 连续运行两次 tiny LoRA，比较 `losses` 数组；随后只改 seed，观察哪些字段变化。
4. 为 tiny LoRA 增加 4 条 held-out prompt，分别记录 base model 和 adapter 的 loss。解释为什么训练 loss 不能替代 held-out baseline。
5. 把 runner 的 Python 换成系统 `python3`，观察 import failure，再用 `sys.executable` 和 package report 定位环境边界。
6. 设计一个 0.5B--1.7B 模型的真实任务规格：输入、输出、baseline、评价集、显存预算、checkpoint 和失败分类。先写验收表，再开始下载模型。

## 参考资料

- PyTorch 本地安装选择器：<https://pytorch.org/get-started/locally/>
- NVIDIA CUDA Linux 安装指南：<https://docs.nvidia.com/cuda/cuda-installation-guide-linux/>
- Hugging Face PEFT 文档：<https://huggingface.co/docs/peft/index>
- Hugging Face Transformers 文档：<https://huggingface.co/docs/transformers/index>
- tiny GPT-2 模型页：<https://huggingface.co/sshleifer/tiny-gpt2>

{% endraw %}
