---
layout: post
title: "Agent 第一课：不用框架，先写可检查的控制循环"
date: 2026-04-18 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从任务契约、RAG、工具 schema、状态和 trace 开始，用 Python 标准库写出第一个能运行、能拒绝、能调试的本地 Agent。"
tags: [agent, rag, tool-use, state, python, evaluation, teaching]
---
{% raw %}

如果第一次学 Agent 就安装一个大型框架，你很容易记住 API，却不知道回答错了时该改检索、工具、状态还是模型。这一课先不使用大模型，而是用 Python 标准库写出一个确定性 Agent。等所有边界都能观察、能测试之后，下一课再把 Qwen 接进来。

![本地 Agent 的可检查控制循环](/assets/diagrams/local-agent-control-loop.svg)

## 学习目标

完成本文后，你应该能：

1. 把 Agent 解释为一个有状态的控制程序，而不是单独的聊天模型。
2. 用一个小型 BM25 风格检索器找到来源，并知道检索命中不等于回答正确。
3. 在工具执行前检查工具名、必需字段、类型和额外字段。
4. 将当前目标和最近对话保存为有界状态。
5. 用 trace 看到 `input -> plan -> tool_result -> final` 的整条路径。

## 先修知识

你只需要会在 WSL 终端执行命令，了解 Python 函数、列表、字典和 JSON。不需要 GPU，也不需要先懂 Transformer。

## 第一步：在 WSL 中跑通基础 lab

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/local-small-model-agent-course
chmod +x run_lab.sh learn.sh setup_gpu.sh
./run_lab.sh
```

这组命令做了四件事：

1. `git clone` 下载包含完整代码和数据的公开仓库。
2. `cd` 进入 Agent lab，后面的相对路径才会指向正确文件。
3. `chmod +x` 为三个 shell 脚本增加可执行权限。
4. `run_lab.sh` 先跑 8 个单元测试，再跑 8 个 CPU-first 学习步骤。

预期尾部输出：

```text
AGENT_06_EVAL_OK passed=10 total=10 failures=0
AGENT_07_OPTIMIZE_OK baseline=8/10 improved=10/10 cache_hits=190
AGENT_CPU_COURSE_OK steps=8
LOCAL_AGENT_LAB_OK cpu_steps=8 tests=8
```

这个 marker 只验收本 lab 的有限知识库和冻结评测集，不能外推为通用 Agent 能力。

## 第二步：先写任务契约

运行：

```bash
./learn.sh 01-task-contract
cat reports/01-task-contract.json
```

第一条命令生成任务契约，第二条直接阅读结果。契约有五个字段：

```text
task     : 回答 CUDA/本地模型课程问题
inputs   : 学习者问题、本地知识、工具白名单
outputs  : 回答、source id、trace、error type
success  : 有证据的回答、合法工具调用、有界状态
refusal  : 找不到证据时明确说证据不足
```

为什么要先写这些？因为“优化 Agent”不是可执行目标。你必须先决定什么是成功、什么时候应拒答，才能判断下一步应该改数据还是改模型。

## 第三步：把本地文档变成可检索证据

运行：

```bash
./learn.sh 02-rag-retrieval
cat reports/02-rag-retrieval.json
```

本 lab 的知识库是 `data/knowledge.jsonl`。每行是一条独立 JSON：

```json
{"id":"lora-boundary","title":"LoRA 冻结基座并训练低秩增量","text":"LoRA 保持基座模型权重冻结……"}
```

检索器对英文 token、中文单字和中文二元组计数，再使用一个 BM25 风格分数。对某个查询词 (t) 和文档 (d)，核心形式是：

\[
\operatorname{score}(t,d)=\operatorname{idf}(t)
\frac{tf(t,d)(k_1+1)}{tf(t,d)+k_1(1-b+b|d|/\overline{|d|})}.
\]

- `tf` 表示词在当前文档中出现多少次。
- `idf` 让稀有词比所有文档都出现的词更有区分度。
- 长度归一化避免长文档因为词多而总是得分更高。

这不是完整搜索引擎，但它让你能逐行追踪“问题怎么变成 top-k 来源”。本步的查询会输出：

```text
AGENT_02_RAG_OK top1=lora-boundary hits=2
```

还有一个容易忽略的边界：查询“火星实时气象”也可能与本地文档共享“实时”“数据”等普通词。因此本 lab 还设置最低相关分数；低于阈值时返回空结果，让 Agent 说“证据不足”。

## 第四步：把工具调用当作不可信输入

运行：

```bash
./learn.sh 03-tool-validation
cat reports/03-tool-validation.json
```

模型生成了合法 JSON，不代表它有权执行任意函数。`ToolRegistry.execute()` 先验证：

```python
if set(call) != {"name", "arguments"}:
    raise ToolValidationError("tool call must contain exactly name and arguments")

if name not in self._tools:
    raise ToolValidationError(f"tool is not allowlisted: {name!r}")

if set(arguments) != set(spec.required):
    raise ToolValidationError("argument fields mismatch")

for argument_name, expected_type in spec.required.items():
    if not isinstance(arguments[argument_name], expected_type):
        raise ToolValidationError("argument type mismatch")
```

这个顺序很重要：先验证，后执行。测试会让一个 `add(a, b)` 通过，并拒绝：

1. 白名单之外的 `delete_file`；
2. 把字符串 `"7"` 传给整数参数；
3. 在合法参数之外偷加 `extra` 字段。

预期输出：

```text
AGENT_03_TOOLS_OK accepted=1 rejected=3
```

它证明 executor 的硬边界存在，不证明模型总能选对工具。“选对工具”需要另外的 routing 评测。

## 第五步：将状态做成有界资源

运行：

```bash
./learn.sh 04-state-memory
cat reports/learner_state.json
```

`AgentState` 保存两类信息：

```python
@dataclass
class AgentState:
    goal: str = ""
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    max_turns: int = 4
```

当添加新对话时，代码只保留最近 4 轮：

```python
self.recent_turns.append({"question": question, "answer": answer})
self.recent_turns = self.recent_turns[-self.max_turns:]
```

保存时先写同目录临时文件，再用 `replace` 原子替换目标，避免程序中途崩溃留下半个 JSON。

为什么不保留全部历史？因为上下文会增长，模型延迟和显存会增加，过期信息还可能干扰当前任务。会话状态、长期事实和原始历史应该分开管理。

## 第六步：串成最小控制循环

运行：

```bash
./learn.sh 05-controller-loop
python3 - <<'PY'
import json
report = json.load(open("reports/05-controller-loop.json", encoding="utf-8"))
for event in report["result"]["trace"]:
    print(event["stage"])
PY
```

第二段 Python 从 JSON report 中读出 trace，应该看到：

```text
input
plan
tool_result
final
```

对“为什么不能直接执行模型生成的工具 JSON”这个问题，controller 的状态变化是：

1. `input`：收到学习者问题。
2. `plan`：构造 `search_notes(query)` 调用，没有直接执行 shell。
3. `tool_result`：通过 schema 验证后返回 `tool-boundary` 笔记。
4. `final`：用该笔记的文本合成回答，同时保留 source id。

此时还没有 LLM，但 Agent 的系统边界已经存在。下一步加入 Qwen 时，我们只用模型改写理解和生成层，不撤掉白名单、状态上限、trace 和 held-out 评测。

## 常见错误

1. **把 Agent 定义成聊天模型。** 模型是一个组件；Agent 还有工具、状态、证据、错误和控制流。
2. **只检查 JSON 语法。** 语法正确的工具调用仍可能越权、多字段或错类型。
3. **找到一篇文档就强行回答。** 普通词重叠会产生虚假命中，需要相关阈值和无证据拒答。
4. **无界保留全部消息。** 这会带来上下文成本、干扰和隐私问题。
5. **没有 trace。** 最终回答错了时，你将无法区分检索、路由、工具还是合成失败。

## 练习

1. 在 `knowledge.jsonl` 新增一条 CUDA 显存带宽笔记，再写一个不使用原文关键词的问题，观察 retrieval miss。
2. 新增 `multiply(a, b)` 工具和四个测试：合法、缺字段、错类型、多字段。
3. 把 `max_turns` 从 4 改为 2，运行状态步骤，核对哪些对话被删除。
4. 为 `LearningAgent.ask()` 增加未知笔记 ID 测试，要求错误进入 trace，而不是静默返回空字符串。

## 参考资料

- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Hugging Face Transformers：Tool use](https://huggingface.co/docs/transformers/en/chat_extras)
- [Hugging Face Transformers：Chat templates](https://huggingface.co/docs/transformers/en/chat_templating)
- [完整 lab README 和源码](/assets/labs/local-small-model-agent-course/README.md)

{% endraw %}
