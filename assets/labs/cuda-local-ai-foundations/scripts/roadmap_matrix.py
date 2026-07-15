#!/usr/bin/env python3
"""Emit the need -> principle -> method -> lab roadmap for the first package."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROADMAP = [
    {
        "need": "知道本机与任意目标机器能跑哪些GPU/AI实验",
        "principle": "先验证硬件、driver、toolkit和Python包，再讨论性能或模型效果",
        "why": "没有环境证据时，失败可能来自工具链而非概念；教学文章也不能把单机配置写成通用结论",
        "first_lab": "gpu_env_probe.py 生成 GPU、nvcc、PyTorch 和依赖状态报告",
        "rtx5070_mapping": "作为12GB/sm_120验证机；缺nvcc和PyTorch时先记录gap，不伪装为已就绪",
    },
    {
        "need": "理解什么时候GPU会比CPU快",
        "principle": "GPU适合大量相似、独立或弱耦合的工作；性能通常受并行度、访存和同步限制",
        "why": "把小任务强行搬到GPU会被数据传输和kernel launch开销淹没",
        "first_lab": "CPU loop vs CUDA vector add；记录规模变化时的时间曲线",
        "rtx5070_mapping": "用5070测本地曲线，同时解释8GB/24GB/40GB机器只改变可承载规模，不改变判断逻辑",
    },
    {
        "need": "读懂N-Queens这类真实CUDA搜索代码",
        "principle": "先把搜索状态压缩成bitmask，再把搜索树切成大量子问题，最后处理负载不均衡",
        "why": "不规则搜索不是矩阵乘法；难点在分支、栈、任务分配和访存，而不是单个算术操作",
        "first_lab": "bitmask_state_demo.py 解释 valid mask 和 lowbit；后续接入CUDA子问题kernel",
        "rtx5070_mapping": "编译目标用sm_120；源码精读不把5070当知识边界，只当实测平台",
    },
    {
        "need": "让本地小模型适配专业领域任务",
        "principle": "先定义任务和评价集；用RAG解决可变知识，用LoRA/QLoRA改变稳定行为和格式",
        "why": "盲目微调会把事实更新、格式控制和推理能力混在一起，无法判断结果为什么变化",
        "first_lab": "base model/RAG/LoRA三方baseline；先从0.6B或1.7B开始",
        "rtx5070_mapping": "12GB适合0.6B/1.7B LoRA，4B QLoRA作为挑战；更大显存只扩大模型和上下文空间",
    },
    {
        "need": "做能实际完成任务的本地agent",
        "principle": "agent是检索、工具、状态、模型和评估组成的系统，不是单个聊天模型",
        "why": "小模型靠系统补足可变知识和工具能力；微调主要服务输出格式和稳定行为",
        "first_lab": "本地资料检索 + 工具schema + 失败样例回放",
        "rtx5070_mapping": "5070用于本地推理与小adapter实验；CPU/磁盘/检索索引同样是系统瓶颈",
    },
]

TIERS = [
    {"tier": "CPU-only", "role": "概念和baseline", "boundary": "不做真实LLM微调验收"},
    {"tier": "6-8GB GPU", "role": "CUDA基础、小模型LoRA", "boundary": "短上下文、小batch"},
    {"tier": "10-12GB GPU", "role": "本地小模型主线；RTX 5070属于此层", "boundary": "4B QLoRA需谨慎，7B训练只作挑战"},
    {"tier": "16-24GB GPU", "role": "4B/7B QLoRA更稳，较长上下文", "boundary": "仍需baseline和显存预算"},
    {"tier": "40GB+ GPU", "role": "多模型/长上下文/更大adapter实验", "boundary": "不等于可以跳过任务定义和评估"},
]


def markdown() -> str:
    lines = ["# CUDA 与本地小模型工程路线矩阵", "", "## 需求到实验", ""]
    lines.append("| 需求 | 原理 | 为什么 | 第一实验 | RTX 5070落地 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in ROADMAP:
        lines.append(f"| {row['need']} | {row['principle']} | {row['why']} | {row['first_lab']} | {row['rtx5070_mapping']} |")
    lines += ["", "## 硬件层级", "", "| 层级 | 角色 | 边界 |", "| --- | --- | --- |"]
    for row in TIERS:
        lines.append(f"| {row['tier']} | {row['role']} | {row['boundary']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    args.json.write_text(json.dumps({"roadmap": ROADMAP, "hardware_tiers": TIERS}, ensure_ascii=False, indent=2), encoding="utf-8")
    args.markdown.write_text(markdown(), encoding="utf-8")
    print(f"roadmap_items={len(ROADMAP)}")
    print(f"hardware_tiers={len(TIERS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
