---
layout: post
title: "Agent 评测与优化：从 held-out 失败分类到检索缓存"
date: 2026-04-20 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 10 条冻结样例定位 retrieval、tool、state 和 unsupported claim 失败；先把检索从 8/10 修到 10/10，再加入不改变结果的 cache。"
tags: [agent, evaluation, rag, optimization, failure-taxonomy, cache, teaching]
---
{% raw %}

一个 Agent 演示能回答一个问题，只说明这次输入没有让它失败。要做优化，首先需要一组在修改前就冻结的问题，然后把失败归因到具体边界。否则，“改了 prompt 后感觉更好”只是一个无法复核的主观判断。

本文使用前一课的确定性 Agent，先构建 held-out 评测，再故意运行一个没有领域同义词的检索基线。基线得到 8/10，失败定位到 retrieval；加入可审计的同义词扩展后得到 10/10。只有正确性稳定后，才增加 query cache，并用精确命中计数而不是某一次 wall-clock 时间验收。

## 学习目标

1. 为 Agent 定义可执行的 held-out 样例，不把评测答案喂回优化过程。
2. 将失败分为 retrieval、routing/tool、arguments、state 和 unsupported claim。
3. 用逐题来源和关键事实检查代替单一平均分。
4. 只修复当前主要失败层，然后重跑全部回归。
5. 在正确性不变的前提下增加 cache，并说清计时边界。

## 先修知识

请先完成 [Agent 第一课](/computer-science-teaching/2026/04/18/local-rag-agent-tool-eval-loop.html)，或至少理解 `LexicalRetriever`、`ToolRegistry`、`AgentState` 和 `LearningAgent.ask()` 的职责。本文的 06--07 不需要 GPU。

## 第一步：复跑评测和优化步骤

```bash
cd ~/8rief.github.io/assets/labs/local-small-model-agent-course
./learn.sh 06-held-out-eval
./learn.sh 07-failure-driven-optimize
```

预期：

```text
AGENT_06_EVAL_OK passed=10 total=10 failures=0
AGENT_07_OPTIMIZE_OK baseline=8/10 improved=10/10 cache_hits=190
```

第一个 marker 使用已开启领域同义词扩展的当前 Agent，验证它没有回归。第二个 marker 内部同时跑基线和改进版，用同一组数据比较。

## 第二步：为什么需要逐题失败证据

`data/eval_cases.jsonl` 的一行包含：

```json
{
  "id": "eval-006",
  "question": "模型输出了 JSON 工具参数，为什么还不能直接执行？",
  "answer": "模型输出是不可信输入……",
  "expected_source": "tool-boundary",
  "keywords": ["白名单", "类型"],
  "failure_type": "bad_arguments"
}
```

这五类信息分别解决不同问题：

- `question`：真正交给 Agent 的输入。
- `answer`：用于小模型 held-out loss 的参考目标，确定性 Agent 不会把它放入检索索引。
- `expected_source`：检查系统是否真的用了正确证据。
- `keywords`：第一轮机器可判断的最小事实覆盖。
- `failure_type`：失败时应该先检查的边界。

对“火星实时气象”，`expected_source` 是 `null`，关键词是“证据不足”。这条样例不要求 Agent 知道火星气象，而是检查它没有来源时能否拒答。

## 第三步：评估逻辑不只看答案字符串

简化后的评估代码：

```python
reply = agent.ask(case["question"])

source_ok = case["expected_source"] in reply.sources
keyword_ok = all(
    keyword.lower() in reply.answer.lower()
    for keyword in case["keywords"]
)
passed = source_ok and keyword_ok
```

对无证据样例，则要求 `reply.sources` 为空。这个规则比只看关键词多一层保护：Agent 不能从错误来源中碰巧拼出正确词。

但它仍然有边界：

1. 关键词存在不证明句子逻辑正确。
2. 一条 source id 正确不证明回答每个断言都被原文支持。
3. 开放式答案可能有多种等价表达，全部用子串会有误判。

所以这是回归门，不是最终质量证明。真实专业 Agent 还需要结构化事实检查、工具实际成功率和人工失败审阅。

## 第四步：失败分类要指向可操作修复

| failure type | 意义 | 先检查 | 不要第一步做什么 |
| --- | --- | --- | --- |
| `retrieval_miss` | 没找到应有证据 | 分词、同义词、chunk、top-k、阈值 | 换大模型 |
| `wrong_tool` | 路由到错误工具 | tool description、routing examples、权限 | 放开全部工具 |
| `bad_arguments` | 字段、类型或长度错 | schema、parser、validator | 让 handler 容忍任意输入 |
| `unsupported_claim` | 没证据仍断言 | 检索阈值、拒答规则、citation check | 只在 prompt 中写“不要幻觉” |
| `state_error` | 目标或最近上下文丢失 | 状态写入、裁剪、恢复和并发边界 | 无界保留全部历史 |

有用的 failure type 应将修复范围缩小到一个边界，“答案不好”这种描述无法指导下一步。

## 第五步：为什么无同义词基线只有 8/10

基线检索使用英文 token、中文单字和二元组，但不知道领域同义词。两个典型问法是：

```text
“能看到显卡就能编译 CUDA C++ 吗？”
“文档常变，先改知识库还是重训？”
```

文档中主要使用 `GPU/nvidia/nvcc` 和 `RAG/检索`，所以基线容易将第一问排到 `cuda-compiler`，将第二问排到评测相关文档。

改进版保留原检索器，只添加一张小而显式的 alias 表：

```python
ALIASES = {
    "显卡": ("gpu", "nvidia"),
    "编译器": ("nvcc", "compiler"),
    "运行库": ("runtime",),
    "低秩适配器": ("lora", "adapter"),
    "知识库": ("rag", "检索"),
    "回归集": ("held-out", "eval", "评测"),
}
```

扩展只用于 query token，原始文档不被改写。这使你能审计“哪个用户表达被映射到哪个领域词”。

重跑同一组评测后：

```text
without aliases = 8/10
with aliases    = 10/10
```

这证明两个已知 retrieval 失败在当前有限集上被修复。它不证明 alias 表对所有查询都有益；每添加一个同义词，都需重跑全集，防止错误扩展导致新的假命中。

## 第六步：正确性稳定后才加 cache

检索 cache 使用 `(query, top_k, min_score)` 作为 key：

```python
key = (query, top_k, min_score)
if key in self._cache:
    self.cache_hits += 1
    return list(self._cache[key])

self.cache_misses += 1
# 计算分数
self._cache[key] = result
```

为什么 key 不能只有 query？因为同一 query 在 `top_k=1` 和 `top_k=3` 下输出数量不同，`min_score` 不同也可能从有结果变成拒答。如果 key 忽略了这些语义参数，cache 会返回错的旧结果。

优化步骤对 10 个 query 重复 20 轮。第一轮是 10 次 miss，后面 19 轮应该是：

\[
10\times19=190
\]

次 cache hit。因此 marker 验收的是 `cache_hits=190`，而不是要求某台机器必须低于某个毫秒阈值。

运行时仍会记录 `timing_observation_seconds`，但它只是现象：WSL 调度、CPU 频率、后台进程和文件系统 cache 都会使数字波动。

## 第七步：小模型结果怎么进入同一优化逻辑

在领域 LoRA 课中，RTX 5070 实测前 6 题的生成 pass 是：

```text
base direct = 0/6
LoRA direct = 0/6
RAG + LoRA = 3/6
```

这里不应直接得出“LoRA 无用”或“RAG 足够”。应该打开：

```bash
python3 - <<'PY'
import json
r = json.load(open("reports/domain_lora_report.json", encoding="utf-8"))
for method in ("baseline_generation", "lora_generation", "rag_lora_generation"):
    print("\n", method)
    for row in r[method]:
        if not row["passed"]:
            print(row["id"], row["keyword_coverage"], row["sources"])
PY
```

这段命令不重新训练模型，只读取 JSON report，列出每种方法的失败 ID、关键词覆盖和来源。接下来的决策树是：

```text
来源错或空 -> 修 retrieval/chunk/threshold
来源对，回答没用 -> 改 prompt/context layout 或补 evidence-following 数据
直接 LoRA 缺固定格式 -> 补 SFT 格式样例
工具参数错 -> 先硬化 schema/executor，再评估 routing model
没证据仍猜 -> 增加 unsupported-claim 拒答样例和门控
上述都完成仍受限 -> 才比较更大模型
```

## 常见错误

1. **优化一题就只重跑该题。** 必须重跑全部冻结集，否则看不到新回归。
2. **把 eval answer 放进 RAG 索引。** 这会让评测变成答案检索，无法表示泛化。
3. **只报一个平均分。** 平均数不告诉你是 retrieval 错还是 tool 错。
4. **在正确性不稳定时先加 cache。** cache 会更快地复用错误。
5. **cache key 忽略语义参数。** `top_k` 和 `min_score` 不同时结果不可共用。
6. **用一次 wall-clock 比较声称加速。** 本 lab 只用精确 hit/miss 计数验收 cache 逻辑；真实性能实验还需 warmup、多轮、分位数和固定输入。

## 练习

1. 删掉 `ALIASES` 中的“知识库”，重跑 07，确认失败回到哪一题。
2. 故意将 `min_score` 调得很低，观察无证据样例为什么变成假命中。
3. 向 eval 新增一条未知工具调用，要求 `ToolRegistry` 拒绝且归类为 `wrong_tool`。
4. 为 cache 增加知识版本号；当 `knowledge.jsonl` 改变时，旧 cache 必须失效。
5. 对同一组 query 做 30 次 warmup 和 100 次测量，报告 p50/p90；不要只报最快一次。

## 参考资料

- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Hugging Face Transformers：Tool use](https://huggingface.co/docs/transformers/en/chat_extras)
- [Hugging Face Transformers：Generation strategies](https://huggingface.co/docs/transformers/generation_strategies)
- [PyTorch CUDA semantics](https://docs.pytorch.org/docs/stable/notes/cuda.html)
- [完整 Agent lab](/assets/labs/local-small-model-agent-course/README.md)

{% endraw %}
