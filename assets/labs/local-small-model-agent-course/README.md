# 本地小模型与 Agent：从可检查控制循环到领域 LoRA

这个 lab 面向第一次开发 Agent 的学习者。它不先引入大型框架，而是先把 Agent 拆成可以单独检查的边界：

```text
任务契约
  -> 检索证据
  -> 生成/选择工具调用
  -> schema 验证
  -> 执行工具
  -> 更新状态
  -> 合成回答与来源
  -> held-out 评测和失败回放
```

00--07 使用 Python 标准库，没有 NVIDIA GPU 也可以运行。08--09 再加入 Qwen3-0.6B 和 LoRA，用来观察模型层带来了什么，以及它没有自动解决什么。

## 1. 在 WSL 中取得 lab

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/local-small-model-agent-course
```

`git clone` 会把公开博客源码下载到 `~/8rief.github.io`；第二条 `cd` 进入本 lab 的实际目录。如果你已经 clone 过该仓库，不要重复 clone，进入旧目录后执行 `git pull --ff-only`。

## 2. 先跑不依赖模型的完整闭环

```bash
chmod +x run_lab.sh learn.sh setup_gpu.sh
./run_lab.sh
```

这两条命令分别赋予 shell 脚本可执行权限，然后运行 8 个单元测试和 8 个学习步骤。成功时末尾应出现：

```text
AGENT_07_OPTIMIZE_OK baseline=8/10 improved=10/10 cache_hits=190
AGENT_CPU_COURSE_OK steps=8
LOCAL_AGENT_LAB_OK cpu_steps=8 tests=8
```

这证明本 lab 中的检索、工具验证、状态、控制循环、回归集和缓存按预期工作。它不证明任意领域 Agent 都能达到 100%，因为这里只有 9 条知识和 10 条冻结评测。

## 3. 逐步运行和阅读代码

```bash
./learn.sh list
./learn.sh 01-task-contract
./learn.sh 02-rag-retrieval
./learn.sh 03-tool-validation
./learn.sh 04-state-memory
./learn.sh 05-controller-loop
./learn.sh 06-held-out-eval
./learn.sh 07-failure-driven-optimize
```

| 步骤 | 先看哪个文件 | 要理解的问题 |
| --- | --- | --- |
| 01 | `scripts/course.py:step_contract` | 没有任务和成功条件，为什么无法优化 Agent |
| 02 | `scripts/agent_core.py:LexicalRetriever` | RAG 是怎样把查询变成带分数的来源 |
| 03 | `scripts/agent_core.py:ToolRegistry` | 为什么 JSON 合法不等于工具可执行 |
| 04 | `scripts/agent_core.py:AgentState` | 怎样原子保存状态，以及为什么只保留最近 4 轮 |
| 05 | `scripts/agent_core.py:LearningAgent.ask` | 输入、plan、tool result 和 final 如何进入 trace |
| 06 | `data/eval_cases.jsonl` | 来源命中、关键事实和无证据拒答如何验收 |
| 07 | `scripts/course.py:step_optimization` | 先修 retrieval miss，再加 cache，为什么比盲目换大模型可解释 |

每步都会在 `reports/` 生成 JSON。终端 marker 是给人快速确认的，JSON 是给你逐字检查输入、输出和 trace 的。

## 4. 为什么先用确定性 controller

如果一开始就让模型同时决定检索、工具、参数、记忆和回答，一次失败只能告诉你系统没完成任务。确定性 controller 先固定这些边界，使每个失败都能被标成：

- `retrieval_miss`：没有找到应有证据；
- `wrong_tool`：路由到了错误工具；
- `bad_arguments`：参数字段、类型或作用域错误；
- `unsupported_claim`：没有证据却给出了断言；
- `state_error`：目标或最近状态丢失。

模型随后只替换系统中需要自然语言理解和生成的部分，工具执行器和验收条件仍然保持显式。

## 5. 加入本地 Qwen3-0.6B

下面的步骤会下载较大的 PyTorch wheel 和模型权重。它们只安装到当前 lab 的 `.venv`，不替换 Windows/WSL NVIDIA driver。

```bash
./setup_gpu.sh
./learn.sh 08-local-qwen
```

`setup_gpu.sh` 依次创建 Python 虚拟环境、从 PyTorch CUDA 12.8 wheel 索引安装 `torch`，再安装固定版本的 `transformers` 和 `peft`。成功时应看到 `AGENT_GPU_SETUP_OK`。

08 会固定加载 `Qwen/Qwen3-0.6B` revision `c1899de289a04d12100db370d81485cdf75e47ca`，检索 `vector-add-proof`，把证据放入 chat template，再用 greedy decoding 生成回答。预期末尾：

```text
AGENT_08_LOCAL_QWEN_OK rag=yes sources=1 generated_tokens=...
```

在 RTX 5070 12GB 上的本地验证中，该步骤的 PyTorch `max_memory_allocated` 约为 1170 MiB。这个数字是当次环境观测，不是所有 GPU 的固定需求。

## 6. 训练领域 LoRA 并保留失败

```bash
./learn.sh 09-domain-lora
cat reports/domain_lora_report.json
```

训练脚本会：

1. 加载 8 条 `data/train_sft.jsonl` 领域样例；
2. 先在 held-out 问法上记录 base model loss 和生成结果；
3. 冻结 Qwen 基座，向 attention 的 `q_proj/k_proj/v_proj/o_proj` 注入 rank-8 LoRA；
4. 训练 2 epoch，只有 8 个 optimizer step；
5. 在同一 held-out 集上比较 base、LoRA 和 RAG+LoRA；
6. 将 adapter 写入 `artifacts/qwen3-0.6b-agent-course-lora/`。

RTX 5070 实测 marker：

```text
AGENT_09_DOMAIN_LORA_OK steps=8 loss=5.4119->4.6738 passes=0/0/3 memory_mib=1699.1
```

这个结果故意不包装成成功故事。直接 base 和直接 LoRA 在前 6 条评测上都是 0 pass，RAG+LoRA 是 3 pass。它说明：

- 8 条训练样例和 8 个 optimizer step 足以验证管线，不足以证明专业能力；
- train loss 下降不保证生成答案命中所有关键事实；
- 对这类课程事实问题，先改证据检索往往比继续增加 epoch 更直接。

下一轮应先查看 `baseline_generation`、`lora_generation` 和 `rag_lora_generation` 中的逐题失败，再决定补数据、改检索、改 prompt 还是扩大模型。

## 7. 硬件迁移时改什么

| 环境 | 先尝试 | 遇到 OOM 时 | 不应改变 |
| --- | --- | --- | --- |
| 8GB NVIDIA GPU | Qwen3-0.6B LoRA | 减小 `MAX_LENGTH`，保持 batch=1 | 任务、held-out 集和通过规则 |
| 12GB RTX 5070 | 直接运行本 lab | 先检查是否有其他进程占显存 | 不把 5070 实测写成专用方案 |
| 24GB 及以上 | 先扩数据和上下文，再比较更大模型 | 每次只改一个主变量 | 公平 baseline 和证据边界 |

Apple Silicon、AMD GPU 或 CPU-only 机器仍然可以完成 00--07。本 lab 的 08--09 明确验收 CUDA，没有暗中切换到 CPU 并假装完成 GPU 训练。

## 8. 常见失败的分层排查

1. `python3: command not found`：先安装 WSL Linux 发行版的 Python 3，与 CUDA 无关。
2. `nvidia-smi` 失败：检查 Windows NVIDIA driver 和 WSL GPU 透传，不要先重装 Python 包。
3. `torch.cuda.is_available() == False`：检查虚拟环境里的 PyTorch wheel 和 driver/runtime 兼容性。
4. Hugging Face 下载中断：保留 cache 后重试；这是网络/下载层，不要改训练结论。
5. CUDA OOM：先结束占显存进程，再减 `AGENT_LORA_MAX_LENGTH`；不要同时更换模型、数据和训练参数。
6. loss 下降但 pass 不升：检查逐题答案和 failure type，不要只增 epoch。
7. 工具错误调用被执行：这是 executor 的硬边界缺陷，先修 `ToolRegistry`，不能只改 prompt。

## 9. 练习

1. 新增一条与显存带宽有关的知识，再写一条同义词问法，观察无 alias 时是否 retrieval miss。
2. 为 `ToolRegistry` 增加 `multiply(a, b)`，必须同时加入合法、缺字段、错类型和额外字段测试。
3. 把 `AgentState.max_turns` 从 4 改为 2，阅读 `reports/learner_state.json`，说明被删掉的是什么。
4. 从 `domain_lora_report.json` 选一条 LoRA 失败，只新增一条针对训练样例，保持 seed、epoch、模型和评测不变后复测。
5. 将 `AGENT_LORA_EVAL_LIMIT` 从 6 调到 10，检查无证据拒答样例是否被模型正确处理。

## 10. 参考资料的用法

- ReAct 论文用来理解推理与行动交替的基本问题；本 lab 的 controller 是为初学者简化的可检查实现，不是对论文系统的复制。
- Transformers Tool use 文档说明了工具 JSON schema、assistant tool call 和 tool response 消息如何组织；实际执行和安全验证仍由应用代码负责。
- PEFT LoRA 文档用来核对冻结基座、低秩增量和 adapter 初始化；本地 report 负责证明命令确实运行。
- Qwen 模型卡用来核对模型类型、参数规模和 chat template 用法。
- PyTorch CUDA semantics 用来区分异步执行、显式同步、`memory_allocated` 和 allocator reserved memory。

执行下面的命令可检查 `references.json` 中的 7 个主要来源当前是否可访问：

```bash
python3 scripts/check_references.py
```

预期 marker 为 `AGENT_REFERENCE_CHECK_OK refs=7`。这只证明链接可访问；本 lab 的术语和 API 还需要与当前文档内容一致。
