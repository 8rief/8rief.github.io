from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_core import (  # noqa: E402
    AgentState,
    LexicalRetriever,
    LearningAgent,
    ToolSpec,
    ToolValidationError,
    ToolRegistry,
    read_jsonl,
)


class AgentCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notes = read_jsonl(ROOT / "data" / "knowledge.jsonl")

    def test_retrieval_returns_expected_lora_note(self) -> None:
        retriever = LexicalRetriever(self.notes, expand_aliases=True)
        hits = retriever.search("低秩适配器为什么省显存？")
        self.assertEqual(hits[0].note_id, "lora-boundary")

    def test_retrieval_cache_is_observable(self) -> None:
        retriever = LexicalRetriever(self.notes)
        retriever.search("LoRA")
        retriever.search("LoRA")
        self.assertEqual((retriever.cache_misses, retriever.cache_hits), (1, 1))

    def test_unknown_tool_is_rejected(self) -> None:
        registry = ToolRegistry()
        registry.register(ToolSpec("ok", {"value": str}, 10, lambda value: value))
        with self.assertRaises(ToolValidationError):
            registry.execute({"name": "delete_file", "arguments": {"path": "/tmp/x"}})

    def test_extra_tool_argument_is_rejected(self) -> None:
        registry = ToolRegistry()
        registry.register(ToolSpec("ok", {"value": str}, 10, lambda value: value))
        with self.assertRaises(ToolValidationError):
            registry.execute({"name": "ok", "arguments": {"value": "x", "extra": 1}})

    def test_state_round_trip_and_bound(self) -> None:
        state = AgentState(goal="learn")
        for index in range(8):
            state.remember_turn(str(index), str(index))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state.save(path)
            restored = AgentState.load(path)
        self.assertEqual(restored.goal, "learn")
        self.assertEqual(len(restored.recent_turns), 4)

    def test_agent_cites_source(self) -> None:
        agent = LearningAgent(LexicalRetriever(self.notes))
        reply = agent.ask("vector_add_ok 能证明性能吗？")
        self.assertTrue(reply.ok)
        self.assertEqual(reply.sources, ["vector-add-proof"])

    def test_agent_refuses_without_evidence(self) -> None:
        agent = LearningAgent(LexicalRetriever(self.notes))
        reply = agent.ask("火星气象实时数据")
        self.assertEqual(reply.sources, [])
        self.assertIn("证据不足", reply.answer)

    def test_controller_trace_has_expected_stages(self) -> None:
        agent = LearningAgent(LexicalRetriever(self.notes))
        reply = agent.ask("为什么需要冻结评测？")
        self.assertEqual(
            [item["stage"] for item in reply.trace],
            ["input", "plan", "tool_result", "final"],
        )


if __name__ == "__main__":
    unittest.main()
