---
layout: post
title: "WSL 从零跑通本地 Agent：每条命令做了什么"
date: 2026-04-19 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 clone 公开 lab、运行 CPU-first Agent，到创建 venv、加载 Qwen3-0.6B 和训练 LoRA；逐条解释命令、输出、证明范围和排错层级。"
tags: [agent, wsl, qwen, lora, rag, python, local-llm, teaching]
---
{% raw %}

这篇文章解决一个非常具体的问题：你在 WSL 里应该按什么顺序输入命令，每条命令实际改变了什么，看到什么输出才能继续。每个步骤都会区分“已证明”和“尚未证明”，避免把环境可见、代码正确和模型质量混在一起。

## 完成后你会得到什么

```text
~/8rief.github.io/assets/labs/local-small-model-agent-course/
  data/                  # 知识、SFT 样例、held-out 评测
  scripts/               # Agent core、runner、Qwen 接入、LoRA 训练
  tests/                 # 8 个边界测试
  reports/               # 运行后生成的 JSON 和 transcript
  artifacts/             # 训练后生成的 LoRA adapter
```

CPU-first 路线使用 Python 标准库。GPU 路线使用 Qwen3-0.6B、Transformers 和 PEFT，会下载较大的 wheel 和模型权重。

## 为什么需要按层运行命令

本路线要解决的核心问题是：同一个“跑不起来”可能来自 WSL 目录、文件权限、NVIDIA driver、PyTorch wheel、模型下载、显存或评测逻辑。按层运行使每次输出只证明一个边界，后一层失败时不需要同时重装所有组件。

## 0. 确认自己真的在 WSL 里

```bash
uname -a
pwd
python3 --version
```

- `uname -a` 显示 Linux kernel 信息。WSL2 通常能在输出中看到 Microsoft/WSL 相关标记。
- `pwd` 显示当前工作目录。后面出现“文件不存在”时，先检查是否进入正确目录。
- `python3 --version` 确认 CPU-first 路线的解释器存在。本 lab 使用 Python 3.10+ 语法。

这一步只证明 shell 和 Python 可用，不证明 GPU 可用。

## 1. 下载公开 lab

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/local-small-model-agent-course
```

`cd ~` 先回到 Linux home，避免把仓库意外 clone 到 Windows 挂载目录或另一个项目内。`git clone` 会新建 `~/8rief.github.io`；最后一条进入 Agent lab。

验证当前目录：

```bash
pwd
ls
```

应至少看到：

```text
README.md  data  learn.sh  run_lab.sh  scripts  setup_gpu.sh  tests
```

如果 `git clone` 说目标目录已存在，不要删目录重来，而是：

```bash
cd ~/8rief.github.io
git pull --ff-only
cd assets/labs/local-small-model-agent-course
```

`--ff-only` 只允许快进更新；如果你本地已有与远程分叉的提交，Git 会停下，而不是自动创造一个你没有阅读的 merge。

## 2. 运行不需要 GPU 的 Agent 闭环

```bash
chmod +x run_lab.sh learn.sh setup_gpu.sh
./run_lab.sh
```

`chmod +x` 只改变这三个文件的执行权限。`run_lab.sh` 内部执行：

```bash
python3 -m unittest discover -s tests -v
./learn.sh all
```

第一条自动发现 `tests/` 下的单元测试。第二条运行 00--07：

```text
00 环境边界
01 任务契约
02 RAG 检索
03 工具 schema 验证
04 状态与记忆
05 控制循环与 trace
06 held-out 评测
07 失败驱动优化和 cache
```

最终应该出现：

```text
LOCAL_AGENT_LAB_OK cpu_steps=8 tests=8
```

如果测试失败，先看第一个 `FAIL` 或 `ERROR` 的测试名和 traceback，不要只看最后一行 `FAILED`。

## 3. 只运行一个步骤

```bash
./learn.sh list
./learn.sh 03-tool-validation
cat reports/03-tool-validation.json
```

- `list` 不执行实验，只打印步骤 ID 和标题。
- 第二条只跑工具验证，应输出 `accepted=1 rejected=3`。
- `cat` 读取完整 JSON，可以看到三次拒绝的确切原因。

如果你修改了 `ToolRegistry`，先跑单步加快调试，修好后再跑 `./run_lab.sh` 检查是否引入其他回归。

## 4. 检查 GPU、driver 和 PyTorch 是三层不同证据

先运行：

```bash
nvidia-smi
```

这条命令通过 Windows NVIDIA driver 的 WSL 支持查询 GPU。看到型号和显存，只证明 driver/device 可见。

再运行：

```bash
command -v nvcc || true
```

`command -v` 询问当前 shell 会把 `nvcc` 解析到哪个可执行文件。`|| true` 让命令缺失时仍能继续，因为 Agent 的 Qwen/LoRA 路线使用 PyTorch CUDA runtime，不要求本 lab 编译 CUDA C++。

最后，`setup_gpu.sh` 会用 Python 检查：

```python
torch.cuda.is_available()
torch.cuda.get_device_name(0)
```

只有这一层通过，才证明当前 virtual environment 中的 PyTorch 能把 tensor 放到 CUDA device。

## 5. 创建 GPU 虚拟环境

```bash
./setup_gpu.sh
```

不要为了省一个命令把包直接安装到 system Python。`.venv` 把这个 lab 的 PyTorch/Transformers/PEFT 版本与其他项目隔离。

安装完成后，你可以手动复查：

```bash
.venv/bin/python - <<'PY'
import torch, transformers, peft
print(torch.__version__)
print(transformers.__version__)
print(peft.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
PY
```

这段 heredoc 将 `PY` 之间的文本作为 Python 标准输入，不会创建永久 `.py` 文件。

`setup_gpu.sh` 全部通过时，最后输出：

```text
AGENT_GPU_SETUP_OK
```

它证明当前 `.venv` 里的 PyTorch、Transformers 和 PEFT 可导入，且 PyTorch CUDA 能看到 GPU；它还没有加载 Qwen 或训练 LoRA。

## 6. 运行 Qwen3-0.6B + RAG

```bash
./learn.sh 08-local-qwen
```

`learn.sh` 会调用：

```bash
.venv/bin/python scripts/local_qwen.py ask \
  --question "vector_add_ok 为什么不是性能证据？" \
  --rag
```

`--rag` 让脚本先检索本地知识。如果去掉它，模型会只根据自身参数回答，不会附带本地 source id。

成功时应该看到：

```text
"sources": ["vector-add-proof"]
"device": "NVIDIA GeForce RTX 5070"
AGENT_08_LOCAL_QWEN_OK rag=yes sources=1 generated_tokens=...
```

`generated_tokens` 是实际解码的新 token 数，不包含 prompt。它不是质量分数。

## 7. 运行 LoRA 训练

```bash
./learn.sh 09-domain-lora
```

这条命令会下载/加载模型，运行 base 评测、训练 8 个 optimizer step，再运行 LoRA 和 RAG+LoRA 评测。在 RTX 5070 12GB 的实测 marker 是：

```text
AGENT_09_DOMAIN_LORA_OK steps=8 loss=5.4119->4.6738 passes=0/0/3 memory_mib=1699.1
```

其中 `passes=0/0/3` 是 base/LoRA/RAG+LoRA 在前 6 条 held-out 问题上的真实失败记录，不是需要追求复制的漂亮数字。保留它可以说明训练 loss 下降不等于领域能力达标。

训练产物在：

```text
artifacts/qwen3-0.6b-agent-course-lora/
```

它是 adapter，不是完整 Qwen 基座模型。使用时仍要加载相同 model id 和 revision。

## 8. 用训练后 adapter 手动提问

```bash
.venv/bin/python scripts/local_qwen.py ask \
  --adapter artifacts/qwen3-0.6b-agent-course-lora \
  --question "LoRA loss 下降为什么不能证明专业能力达标？" \
  --rag
```

该命令将基座模型、本地 adapter 和 RAG 证据同时加入。输出 JSON 里应出现非空 `adapter` 路径和至少一个 source。

这仍然只是交互式检查。如果你修改了训练数据或参数，必须重跑 held-out 评测，不能用一个自己挑选的成功问题代替它。

## 9. 读取失败，不要只看总分

```bash
python3 - <<'PY'
import json
r = json.load(open("reports/domain_lora_report.json", encoding="utf-8"))
for method in ("baseline_generation", "lora_generation", "rag_lora_generation"):
    print("\n" + method)
    for row in r[method]:
        print(row["id"], row["passed"], row["keyword_coverage"], row["sources"])
PY
```

这段代码会把每道题的 pass、关键词覆盖和来源打印出来。你的下一步应该根据失败分层：

```text
无 source          -> 检查 retrieval
source 错          -> 检查分词/chunk/threshold
source 对、回答错 -> 检查 prompt/证据使用/训练样例
工具参数错       -> 检查 schema/executor
无证据仍回答     -> 检查拒答门控
```

## 10. 参考链接检查

```bash
python3 scripts/check_references.py
```

该脚本读取 `references.json`，请求 ReAct、Transformers、PEFT、Qwen 和 PyTorch 的 7 个主要来源。成功 marker：

```text
AGENT_REFERENCE_CHECK_OK refs=7
```

它只证明 URL 当前可访问，不证明你已经理解文档。教程中的 API 和概念以官方文档校对，命令是否在本地成功则以 report 和 marker 为证据。

## 排错速查

| 现象 | 所在层 | 先做什么 |
| --- | --- | --- |
| `python3` 不存在 | WSL/Linux 基础环境 | 安装 Python 3，先不看 CUDA |
| `Permission denied: ./learn.sh` | 文件权限 | `chmod +x learn.sh` |
| `nvidia-smi` 失败 | Windows driver / WSL GPU | 检查 Windows 驱动和 WSL，不重装 PEFT |
| `torch.cuda.is_available()` 为 false | Python wheel/runtime | 确认使用 `.venv/bin/python` 和 CUDA wheel |
| 模型下载中断 | 网络/cache | 保留 cache 重试，不改训练数据 |
| CUDA OOM | GPU 显存 | 查占用，减 `AGENT_LORA_MAX_LENGTH` |
| loss 下降但 pass 不变 | 数据/评测/生成 | 读逐题失败，不盲目增 epoch |
| 错误工具被真执行 | executor 硬边界 | 立即修 schema/白名单，不只改 prompt |

## 练习

1. 不运行 GPU 步骤，只完成 00--07，用自己的一组学习笔记替换 `knowledge.jsonl`。
2. 将 `AGENT_LORA_EVAL_LIMIT=10` 加在命令前，理解 shell 环境变量为什么只对该次进程生效。
3. 将一条训练样例改成错误边界，观察 held-out 是否能抓到回归；完成后撤回错误数据。
4. 使用 `--max-new-tokens 64` 和 `192` 分别生成，观察输出是否被截断，不要把 token 更多等同于质量更好。

## 参考资料

- [Qwen3-0.6B 模型卡](https://huggingface.co/Qwen/Qwen3-0.6B)
- [Hugging Face Transformers：Tool use](https://huggingface.co/docs/transformers/en/chat_extras)
- [Hugging Face PEFT：LoRA](https://huggingface.co/docs/peft/main/conceptual_guides/lora)
- [PyTorch CUDA semantics](https://docs.pytorch.org/docs/stable/notes/cuda.html)
- [完整 lab README](/assets/labs/local-small-model-agent-course/README.md)

{% endraw %}
