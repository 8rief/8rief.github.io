#!/usr/bin/env python3
"""Run a pinned local Qwen model with optional local RAG and LoRA adapter."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from agent_core import LexicalRetriever, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

MODEL_ID = os.environ.get("AGENT_MODEL_ID", "Qwen/Qwen3-0.6B")
MODEL_REVISION = os.environ.get(
    "AGENT_MODEL_REVISION", "c1899de289a04d12100db370d81485cdf75e47ca"
)
SYSTEM = (
    "你是 CUDA 与本地小模型学习助手。"
    "只根据给定证据回答；证据不足时明确说证据不足。"
    "先给结论，再说原因、边界和下一步。"
)


def require_cuda() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch is missing; run ./setup_gpu.sh first") from exc
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; GPU steps require a CUDA-capable PyTorch environment")
    return torch


def build_context(question: str, *, top_k: int = 2) -> tuple[str, list[dict[str, Any]]]:
    retriever = LexicalRetriever(read_jsonl(DATA / "knowledge.jsonl"), expand_aliases=True)
    hits = retriever.search(question, top_k=top_k)
    lines = [f"[{hit.note_id}] {hit.text}" for hit in hits]
    return "\n".join(lines), [asdict(hit) for hit in hits]


def chat_text(tokenizer: Any, question: str, context: str = "") -> str:
    if context:
        content = f"证据：\n{context}\n\n问题：{question}"
    else:
        content = question
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


def load_model(adapter: Path | None = None) -> tuple[Any, Any, Any]:
    torch = require_cuda()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("Transformers is missing; run ./setup_gpu.sh first") from exc
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        dtype=torch.float16,
        low_cpu_mem_usage=True,
    )
    if adapter is not None:
        if not adapter.is_dir():
            raise RuntimeError(f"adapter directory not found: {adapter}")
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter)
    model = model.to("cuda").eval()
    return torch, tokenizer, model


def generate(
    tokenizer: Any,
    model: Any,
    question: str,
    *,
    rag: bool,
    max_new_tokens: int,
) -> dict[str, Any]:
    torch = require_cuda()
    context, hits = build_context(question) if rag else ("", [])
    prompt = chat_text(tokenizer, question, context)
    encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to("cuda")
    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    torch.cuda.synchronize()
    new_tokens = generated[0, encoded["input_ids"].shape[1] :]
    answer = tokenizer.decode(new_tokens, skip_special_tokens=False)
    answer = re.sub(r"<think>\s*</think>", "", answer, flags=re.S).strip()
    return {
        "question": question,
        "answer": answer,
        "rag": rag,
        "sources": [hit["note_id"] for hit in hits],
        "retrieval": hits,
        "generated_tokens": int(new_tokens.numel()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    ask = subparsers.add_parser("ask")
    ask.add_argument("--question", required=True)
    ask.add_argument("--rag", action="store_true")
    ask.add_argument("--adapter", type=Path)
    ask.add_argument("--max-new-tokens", type=int, default=192)
    args = parser.parse_args()
    if args.max_new_tokens < 8 or args.max_new_tokens > 256:
        parser.error("--max-new-tokens must be between 8 and 256")

    try:
        torch, tokenizer, model = load_model(args.adapter)
        result = generate(
            tokenizer,
            model,
            args.question,
            rag=args.rag,
            max_new_tokens=args.max_new_tokens,
        )
        result.update(
            {
                "ok": True,
                "model": MODEL_ID,
                "revision": MODEL_REVISION,
                "adapter": str(args.adapter) if args.adapter else None,
                "device": torch.cuda.get_device_name(0),
                "max_memory_allocated_mib": round(torch.cuda.max_memory_allocated() / 1024**2, 1),
            }
        )
        (REPORTS / "local_qwen_ask.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(
            f"AGENT_08_LOCAL_QWEN_OK rag={'yes' if args.rag else 'no'} "
            f"sources={len(result['sources'])} generated_tokens={result['generated_tokens']}"
        )
        return 0
    except Exception as exc:
        print(f"AGENT_08_LOCAL_QWEN_FAILED {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
