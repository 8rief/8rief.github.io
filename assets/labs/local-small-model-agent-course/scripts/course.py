#!/usr/bin/env python3
"""Learner runner for deterministic Agent foundations."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from agent_core import (
    AgentState,
    LexicalRetriever,
    LearningAgent,
    ToolValidationError,
    ToolRegistry,
    ToolSpec,
    read_jsonl,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Step:
    step_id: str
    title: str
    command: str
    does: tuple[str, ...]
    expected: str
    proves: str
    does_not_prove: str
    troubleshoot: tuple[str, ...]
    runner: Callable[[], dict[str, Any]]


def write_report(step: Step, result: dict[str, Any], elapsed: float) -> None:
    payload = {
        "step": {
            "id": step.step_id,
            "title": step.title,
            "command": step.command,
            "does": step.does,
            "expected": step.expected,
            "proves": step.proves,
            "does_not_prove": step.does_not_prove,
            "troubleshoot": step.troubleshoot,
        },
        "result": result,
        "elapsed_seconds": round(elapsed, 6),
    }
    (REPORTS / f"{step.step_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def make_agent(*, expand_aliases: bool = True) -> LearningAgent:
    notes = read_jsonl(DATA / "knowledge.jsonl")
    return LearningAgent(LexicalRetriever(notes, expand_aliases=expand_aliases))


def step_environment() -> dict[str, Any]:
    commands = {}
    for command in ("nvidia-smi", "nvcc"):
        proc = subprocess.run(
            ["bash", "-lc", f"command -v {command} || true"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        commands[command] = proc.stdout.strip() or "not-found"
    marker = "AGENT_00_ENV_OK python=yes cpu_foundations=yes"
    return {
        "marker": marker,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "optional_gpu_commands": commands,
    }


def step_contract() -> dict[str, Any]:
    contract = {
        "task": "Answer CUDA/local-model course questions with cited local evidence.",
        "inputs": ["learner question", "local knowledge notes", "allowlisted tools"],
        "outputs": ["answer", "source ids", "trace", "error type"],
        "success": ["supported answer", "valid tool call", "bounded state"],
        "refusal": "No supporting note -> state that evidence is insufficient.",
    }
    required = {"task", "inputs", "outputs", "success", "refusal"}
    assert set(contract) == required
    return {"marker": "AGENT_01_CONTRACT_OK fields=5", "contract": contract}


def step_retrieval() -> dict[str, Any]:
    agent = make_agent()
    question = "低秩适配器为什么省训练显存？"
    hits = agent.retriever.search(question, top_k=3)
    assert hits and hits[0].note_id == "lora-boundary"
    return {
        "marker": f"AGENT_02_RAG_OK top1={hits[0].note_id} hits={len(hits)}",
        "question": question,
        "hits": [asdict(hit) for hit in hits],
    }


def step_tools() -> dict[str, Any]:
    registry = ToolRegistry()
    registry.register(ToolSpec("add", {"a": int, "b": int}, 0, lambda a, b: a + b))
    accepted = registry.execute({"name": "add", "arguments": {"a": 7, "b": 5}})
    rejected: list[str] = []
    invalid_calls = [
        {"name": "delete_file", "arguments": {"path": "/tmp/x"}},
        {"name": "add", "arguments": {"a": "7", "b": 5}},
        {"name": "add", "arguments": {"a": 7, "b": 5, "extra": True}},
    ]
    for call in invalid_calls:
        try:
            registry.execute(call)
        except ToolValidationError as exc:
            rejected.append(str(exc))
    assert accepted == 12 and len(rejected) == 3
    return {
        "marker": "AGENT_03_TOOLS_OK accepted=1 rejected=3",
        "accepted_result": accepted,
        "rejections": rejected,
    }


def step_state() -> dict[str, Any]:
    agent = make_agent()
    state_path = REPORTS / "learner_state.json"
    first = agent.ask("记住当前目标：完成 Agent 评测")
    agent.state.save(state_path)
    restored = LearningAgent(agent.retriever, AgentState.load(state_path))
    second = restored.ask("当前目标是什么？")
    for index in range(7):
        restored.state.remember_turn(f"q{index}", f"a{index}")
    assert second.answer == "完成 Agent 评测"
    assert len(restored.state.recent_turns) == restored.state.max_turns == 4
    return {
        "marker": "AGENT_04_STATE_OK restored=yes recent_turns=4",
        "write_reply": first.answer,
        "read_reply": second.answer,
        "state_file": state_path.name,
    }


def step_controller() -> dict[str, Any]:
    agent = make_agent()
    reply = agent.ask("模型生成了工具 JSON，为什么不能直接执行？")
    stages = [item["stage"] for item in reply.trace]
    assert reply.ok and reply.sources == ["tool-boundary"]
    assert stages == ["input", "plan", "tool_result", "final"]
    return {
        "marker": f"AGENT_05_LOOP_OK source={reply.sources[0]} stages={len(stages)}",
        "answer": reply.answer,
        "trace": reply.trace,
    }


def evaluate(*, expand_aliases: bool) -> tuple[list[dict[str, Any]], Counter[str]]:
    agent = make_agent(expand_aliases=expand_aliases)
    rows = []
    failures: Counter[str] = Counter()
    for case in read_jsonl(DATA / "eval_cases.jsonl"):
        reply = agent.ask(case["question"])
        source_ok = case["expected_source"] is None or case["expected_source"] in reply.sources
        keyword_ok = all(keyword.lower() in reply.answer.lower() for keyword in case["keywords"])
        if case["expected_source"] is None:
            source_ok = not reply.sources
        passed = source_ok and keyword_ok
        if not passed:
            failures[case["failure_type"]] += 1
        rows.append(
            {
                "id": case["id"],
                "passed": passed,
                "expected_source": case["expected_source"],
                "actual_sources": reply.sources,
                "keyword_ok": keyword_ok,
                "failure_type": None if passed else case["failure_type"],
            }
        )
    return rows, failures


def step_evaluation() -> dict[str, Any]:
    rows, failures = evaluate(expand_aliases=True)
    passed = sum(row["passed"] for row in rows)
    assert passed == len(rows), (rows, failures)
    return {
        "marker": f"AGENT_06_EVAL_OK passed={passed} total={len(rows)} failures=0",
        "rows": rows,
        "failure_counts": failures,
    }


def step_optimization() -> dict[str, Any]:
    baseline_rows, baseline_failures = evaluate(expand_aliases=False)
    improved_rows, improved_failures = evaluate(expand_aliases=True)
    baseline_passed = sum(row["passed"] for row in baseline_rows)
    improved_passed = sum(row["passed"] for row in improved_rows)
    agent = make_agent()
    queries = [case["question"] for case in read_jsonl(DATA / "eval_cases.jsonl")]
    start = time.perf_counter()
    for _ in range(20):
        for query in queries:
            agent.retriever.search(query, top_k=3)
    elapsed = time.perf_counter() - start
    assert improved_passed == len(improved_rows)
    assert improved_passed >= baseline_passed
    assert agent.retriever.cache_hits == len(queries) * 19
    return {
        "marker": (
            f"AGENT_07_OPTIMIZE_OK baseline={baseline_passed}/{len(baseline_rows)} "
            f"improved={improved_passed}/{len(improved_rows)} cache_hits={agent.retriever.cache_hits}"
        ),
        "baseline_failures": baseline_failures,
        "improved_failures": improved_failures,
        "cache_misses": agent.retriever.cache_misses,
        "cache_hits": agent.retriever.cache_hits,
        "timing_observation_seconds": round(elapsed, 6),
        "timing_boundary": "Timing is observational only; correctness and exact cache counters are the acceptance evidence.",
    }


STEPS = [
    Step(
        "00-environment",
        "确认 CPU 基础路线可运行，并区分可选 GPU 工具",
        "./learn.sh 00-environment",
        ("读取 Python/操作系统信息", "检查 nvidia-smi 和 nvcc 是否在 PATH"),
        "AGENT_00_ENV_OK",
        "不依赖模型的 Agent 基础实验可以开始",
        "不证明本地 Qwen/LoRA 环境已完成",
        ("Python 失败先确认 python3 >= 3.10", "GPU 工具缺失不影响 00--07"),
        step_environment,
    ),
    Step(
        "01-task-contract",
        "先定义 Agent 的任务、输入输出和拒答边界",
        "./learn.sh 01-task-contract",
        ("构建五字段任务契约", "把成功和无证据拒答变成可检查条件"),
        "AGENT_01_CONTRACT_OK fields=5",
        "Agent 优化已有明确对象",
        "不证明检索或模型质量",
        ("任务无法写成输入输出时先不要选模型",),
        step_contract,
    ),
    Step(
        "02-rag-retrieval",
        "用 BM25 风格词法检索建立 RAG 证据边界",
        "./learn.sh 02-rag-retrieval",
        ("对中英文 token 计数", "计算文档分数", "返回 top-k 来源"),
        "AGENT_02_RAG_OK top1=lora-boundary",
        "查询能找到预期领域笔记",
        "不证明最终生成回答正确",
        ("top1 错误时检查分词、同义词和语料重复",),
        step_retrieval,
    ),
    Step(
        "03-tool-validation",
        "在执行前验证模型提议的工具调用",
        "./learn.sh 03-tool-validation",
        ("执行一个合法 add 调用", "拒绝未知工具、错类型和额外字段"),
        "AGENT_03_TOOLS_OK accepted=1 rejected=3",
        "工具白名单和参数边界实际生效",
        "不证明模型会选对工具",
        ("如果错误调用进入 handler，先修执行器而不是 prompt",),
        step_tools,
    ),
    Step(
        "04-state-memory",
        "区分有界会话状态和持久文件",
        "./learn.sh 04-state-memory",
        ("写入当前目标", "原子保存 JSON", "重载目标并裁剪最近对话"),
        "AGENT_04_STATE_OK restored=yes recent_turns=4",
        "状态可恢复且不会无界增长",
        "不证明哪些事实应进入长期记忆",
        ("JSON 损坏时不要静默忽略，应保留错误并重建",),
        step_state,
    ),
    Step(
        "05-controller-loop",
        "串起输入、规划、工具、证据和最终回答",
        "./learn.sh 05-controller-loop",
        ("记录四阶段 trace", "通过检索工具获取来源", "用证据合成回答"),
        "AGENT_05_LOOP_OK source=tool-boundary stages=4",
        "最小 Agent 控制循环可观测",
        "不证明大模型的规划能力",
        ("trace 缺阶段时先修控制器可观测性",),
        step_controller,
    ),
    Step(
        "06-held-out-eval",
        "在冻结问题上检查来源、关键事实和拒答",
        "./learn.sh 06-held-out-eval",
        ("运行 10 个未作为回答索引的评测样例", "记录每题来源和失败类型"),
        "AGENT_06_EVAL_OK passed=10 total=10 failures=0",
        "当前确定性 Agent 通过这组有限回归集",
        "不证明对开放世界问题有通用能力",
        ("失败时先看 failure_type，不要立即换大模型",),
        step_evaluation,
    ),
    Step(
        "07-failure-driven-optimize",
        "用失败类型改检索，再测缓存边界",
        "./learn.sh 07-failure-driven-optimize",
        ("对比无同义词和有同义词检索", "重跑同一评测", "验证缓存命中计数"),
        "AGENT_07_OPTIMIZE_OK",
        "优化由具体失败驱动，且性能缓存不改变结果",
        "观测到的 wall-clock 时间不是稳定性能结论",
        ("优化后出现回归时撤回该改动并扩充失败样例",),
        step_optimization,
    ),
]


def print_step(step: Step) -> None:
    print(f"\n=== {step.step_id}: {step.title} ===")
    print(f"[Run in WSL] {step.command}")
    print("[What it does]")
    for item in step.does:
        print(f"- {item}")
    print(f"[Expected] {step.expected}")
    print(f"[Proves] {step.proves}")
    print(f"[Does not prove] {step.does_not_prove}")
    print("[Troubleshooting]")
    for item in step.troubleshoot:
        print(f"- {item}")


def run_step(step: Step) -> dict[str, Any]:
    print_step(step)
    started = time.perf_counter()
    result = step.runner()
    elapsed = time.perf_counter() - started
    marker = result.get("marker")
    if not isinstance(marker, str) or not marker.startswith("AGENT_"):
        raise RuntimeError(f"step {step.step_id} did not produce a stable marker")
    write_report(step, result, elapsed)
    print(f"[Observed] {marker}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Local small-model Agent learner course")
    parser.add_argument("step", nargs="?", default="all")
    args = parser.parse_args()
    if args.step == "list":
        for step in STEPS:
            print(f"{step.step_id}\t{step.title}")
        print("08-local-qwen\t可选 GPU：本地 Qwen baseline")
        print("09-domain-lora\t可选 GPU：领域 LoRA 训练与评测")
        return 0
    selected = STEPS if args.step == "all" else [step for step in STEPS if step.step_id == args.step]
    if not selected:
        parser.error(f"unknown CPU step: {args.step}; use ./learn.sh list")
    results = [run_step(step) for step in selected]
    if args.step == "all":
        summary = {"ok": True, "step_count": len(results), "markers": [item["marker"] for item in results]}
        (REPORTS / "cpu_course_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"AGENT_CPU_COURSE_OK steps={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
