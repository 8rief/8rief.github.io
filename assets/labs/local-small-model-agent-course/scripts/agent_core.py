#!/usr/bin/env python3
"""Small, inspectable Agent building blocks used by the learner course.

The deterministic controller is intentional: it lets a learner verify
retrieval, tool validation, state, traces, and evaluation before adding an LLM.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable


class AgentError(RuntimeError):
    """Base error for an expected Agent boundary failure."""


class ToolValidationError(AgentError):
    """Raised before execution when a model-proposed tool call is invalid."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AgentError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise AgentError(f"{path}:{line_number}: expected a JSON object")
        rows.append(row)
    return rows


ALIASES: dict[str, tuple[str, ...]] = {
    "显卡": ("gpu", "nvidia"),
    "编译器": ("nvcc", "compiler"),
    "运行库": ("runtime",),
    "低秩适配器": ("lora", "adapter"),
    "知识库": ("rag", "检索"),
    "外部动作": ("tool", "工具"),
    "回归集": ("held-out", "eval", "评测"),
}


def tokenize(text: str, *, expand_aliases: bool) -> list[str]:
    low = text.lower()
    tokens = re.findall(r"[a-z0-9_+.-]+", low)
    cjk = [ch for ch in low if "\u4e00" <= ch <= "\u9fff"]
    tokens.extend(cjk)
    tokens.extend("".join(cjk[i : i + 2]) for i in range(max(0, len(cjk) - 1)))
    if expand_aliases:
        for phrase, aliases in ALIASES.items():
            if phrase in low:
                tokens.extend(aliases)
    return tokens


@dataclass(frozen=True)
class RetrievalHit:
    note_id: str
    title: str
    text: str
    score: float


class LexicalRetriever:
    """A compact BM25-style retriever with an optional domain alias layer."""

    def __init__(self, notes: list[dict[str, Any]], *, expand_aliases: bool = True):
        if not notes:
            raise AgentError("knowledge base is empty")
        self._notes = notes
        self._expand_aliases = expand_aliases
        self._docs: list[tuple[dict[str, Any], Counter[str], int]] = []
        document_frequency: defaultdict[str, int] = defaultdict(int)
        for note in notes:
            for field_name in ("id", "title", "text"):
                if not isinstance(note.get(field_name), str) or not note[field_name].strip():
                    raise AgentError(f"knowledge note is missing non-empty {field_name}: {note!r}")
            counts = Counter(tokenize(f"{note['title']} {note['text']}", expand_aliases=False))
            length = sum(counts.values()) or 1
            self._docs.append((note, counts, length))
            for token in counts:
                document_frequency[token] += 1
        count = len(self._docs)
        self._idf = {
            token: math.log((count - frequency + 0.5) / (frequency + 0.5) + 1.0)
            for token, frequency in document_frequency.items()
        }
        self._average_length = sum(length for _, _, length in self._docs) / count
        self._cache: dict[tuple[str, int, float], tuple[RetrievalHit, ...]] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def search(self, query: str, *, top_k: int = 3, min_score: float = 7.0) -> list[RetrievalHit]:
        query = query.strip()
        if not query:
            raise AgentError("query must not be empty")
        if top_k < 1 or top_k > 10:
            raise AgentError("top_k must be between 1 and 10")
        if min_score < 0:
            raise AgentError("min_score must be non-negative")
        key = (query, top_k, min_score)
        if key in self._cache:
            self.cache_hits += 1
            return list(self._cache[key])
        self.cache_misses += 1
        query_counts = Counter(tokenize(query, expand_aliases=self._expand_aliases))
        scored: list[RetrievalHit] = []
        for note, counts, length in self._docs:
            score = 0.0
            for token, query_frequency in query_counts.items():
                term_frequency = counts.get(token, 0)
                if not term_frequency:
                    continue
                denominator = term_frequency + 1.2 * (
                    1 - 0.75 + 0.75 * length / self._average_length
                )
                score += self._idf.get(token, 0.0) * term_frequency * 2.2 / denominator * query_frequency
            if score >= min_score:
                scored.append(
                    RetrievalHit(
                        note_id=note["id"],
                        title=note["title"],
                        text=note["text"],
                        score=round(score, 6),
                    )
                )
        scored.sort(key=lambda hit: (-hit.score, hit.note_id))
        result = tuple(scored[:top_k])
        self._cache[key] = result
        return list(result)

    def note(self, note_id: str) -> dict[str, Any] | None:
        return next((note for note in self._notes if note["id"] == note_id), None)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    required: dict[str, type]
    max_string_length: int
    handler: Callable[..., Any]


class ToolRegistry:
    """Allowlisted executor. Generated JSON never bypasses this validator."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise AgentError(f"duplicate tool: {spec.name}")
        self._tools[spec.name] = spec

    def execute(self, call: dict[str, Any]) -> Any:
        if set(call) != {"name", "arguments"}:
            raise ToolValidationError("tool call must contain exactly name and arguments")
        name = call["name"]
        arguments = call["arguments"]
        if not isinstance(name, str) or name not in self._tools:
            raise ToolValidationError(f"tool is not allowlisted: {name!r}")
        if not isinstance(arguments, dict):
            raise ToolValidationError("arguments must be an object")
        spec = self._tools[name]
        expected = set(spec.required)
        actual = set(arguments)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ToolValidationError(f"argument fields mismatch: missing={missing} extra={extra}")
        for argument_name, expected_type in spec.required.items():
            value = arguments[argument_name]
            if not isinstance(value, expected_type):
                raise ToolValidationError(
                    f"{argument_name} must be {expected_type.__name__}, got {type(value).__name__}"
                )
            if isinstance(value, str):
                if not value.strip():
                    raise ToolValidationError(f"{argument_name} must not be empty")
                if len(value) > spec.max_string_length:
                    raise ToolValidationError(f"{argument_name} exceeds {spec.max_string_length} characters")
        return spec.handler(**arguments)


@dataclass
class AgentState:
    goal: str = ""
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    max_turns: int = 4

    def remember_turn(self, question: str, answer: str) -> None:
        self.recent_turns.append({"question": question, "answer": answer})
        self.recent_turns = self.recent_turns[-self.max_turns :]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    @classmethod
    def load(cls, path: Path) -> "AgentState":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise AgentError("state file must contain an object")
        return cls(
            goal=str(data.get("goal", "")),
            recent_turns=list(data.get("recent_turns", []))[-4:],
            max_turns=4,
        )


@dataclass
class AgentReply:
    ok: bool
    answer: str
    sources: list[str]
    trace: list[dict[str, Any]]
    error_type: str | None = None


class LearningAgent:
    """Deterministic controller that exposes the same boundaries as an LLM Agent."""

    def __init__(self, retriever: LexicalRetriever, state: AgentState | None = None):
        self.retriever = retriever
        self.state = state or AgentState()
        self.tools = ToolRegistry()
        self.tools.register(
            ToolSpec("search_notes", {"query": str}, 200, self._search_notes)
        )
        self.tools.register(
            ToolSpec("read_note", {"note_id": str}, 80, self._read_note)
        )

    def _search_notes(self, query: str) -> list[dict[str, Any]]:
        return [asdict(hit) for hit in self.retriever.search(query, top_k=3)]

    def _read_note(self, note_id: str) -> dict[str, Any]:
        note = self.retriever.note(note_id)
        if note is None:
            raise AgentError(f"note not found: {note_id}")
        return note

    def ask(self, question: str) -> AgentReply:
        question = question.strip()
        if not question:
            raise AgentError("question must not be empty")
        trace: list[dict[str, Any]] = [{"stage": "input", "question": question}]

        if question.startswith("记住当前目标："):
            self.state.goal = question.split("：", 1)[1].strip()
            answer = f"已记住当前目标：{self.state.goal}"
            trace.append({"stage": "state_update", "goal": self.state.goal})
            self.state.remember_turn(question, answer)
            return AgentReply(True, answer, [], trace)
        if question == "当前目标是什么？":
            answer = self.state.goal or "尚未设置当前目标。"
            trace.append({"stage": "state_read", "goal": self.state.goal})
            self.state.remember_turn(question, answer)
            return AgentReply(True, answer, [], trace)

        if question.startswith("读取笔记："):
            call = {"name": "read_note", "arguments": {"note_id": question.split("：", 1)[1].strip()}}
        else:
            call = {"name": "search_notes", "arguments": {"query": question}}
        trace.append({"stage": "plan", "tool_call": call})

        try:
            result = self.tools.execute(call)
        except ToolValidationError as exc:
            trace.append({"stage": "tool_rejected", "error": str(exc)})
            return AgentReply(False, f"工具调用已拒绝：{exc}", [], trace, "bad_arguments")

        trace.append({"stage": "tool_result", "result": result})
        if call["name"] == "read_note":
            sources = [result["id"]]
            answer = result["text"]
        elif not result:
            sources = []
            answer = "证据不足：本地知识库没有找到能支持结论的内容。"
        else:
            best = result[0]
            sources = [best["note_id"]]
            answer = best["text"]
        trace.append({"stage": "final", "sources": sources})
        self.state.remember_turn(question, answer)
        return AgentReply(True, answer, sources, trace)


def build_agent(knowledge_path: Path, *, expand_aliases: bool = True) -> LearningAgent:
    notes = read_jsonl(knowledge_path)
    return LearningAgent(LexicalRetriever(notes, expand_aliases=expand_aliases))
