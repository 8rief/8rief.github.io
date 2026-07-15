#!/usr/bin/env python3
"""Train and evaluate a tiny, transparent domain LoRA on Qwen3-0.6B."""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

from agent_core import read_jsonl
from local_qwen import (
    DATA,
    MODEL_ID,
    MODEL_REVISION,
    REPORTS,
    SYSTEM,
    build_context,
    chat_text,
    generate,
    require_cuda,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ADAPTER = ARTIFACTS / "qwen3-0.6b-agent-course-lora"
SEED = int(os.environ.get("AGENT_LORA_SEED", "20260706"))
EPOCHS = int(os.environ.get("AGENT_LORA_EPOCHS", "2"))
MAX_LENGTH = int(os.environ.get("AGENT_LORA_MAX_LENGTH", "256"))
LR = float(os.environ.get("AGENT_LORA_LR", "2e-4"))
GRAD_ACCUM = int(os.environ.get("AGENT_LORA_GRAD_ACCUM", "2"))
EVAL_LIMIT = int(os.environ.get("AGENT_LORA_EVAL_LIMIT", "6"))
MAX_NEW_TOKENS = int(os.environ.get("AGENT_LORA_MAX_NEW_TOKENS", "64"))


def seed_everything(torch: Any) -> None:
    random.seed(SEED)
    os.environ.setdefault("PYTHONHASHSEED", str(SEED))
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)


def training_text(tokenizer: Any, instruction: str, output: str) -> tuple[list[int], list[int]]:
    prompt = tokenizer.apply_chat_template(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": instruction}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    answer_ids = tokenizer(output + (tokenizer.eos_token or ""), add_special_tokens=False)["input_ids"]
    if len(answer_ids) >= MAX_LENGTH:
        raise RuntimeError("an answer is longer than AGENT_LORA_MAX_LENGTH")
    prompt_ids = prompt_ids[-(MAX_LENGTH - len(answer_ids)) :]
    input_ids = prompt_ids + answer_ids
    labels = [-100] * len(prompt_ids) + answer_ids
    return input_ids, labels


def target_loss(torch: Any, tokenizer: Any, model: Any, row: dict[str, Any], *, rag: bool) -> float:
    context = build_context(row["question"])[0] if rag else ""
    prompt = chat_text(tokenizer, row["question"], context)
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    answer_ids = tokenizer(row["answer"] + (tokenizer.eos_token or ""), add_special_tokens=False)["input_ids"]
    if len(answer_ids) >= MAX_LENGTH:
        answer_ids = answer_ids[: MAX_LENGTH - 1]
        prompt_ids = []
    else:
        prompt_ids = prompt_ids[-(MAX_LENGTH - len(answer_ids)) :]
    input_ids = torch.tensor([prompt_ids + answer_ids], dtype=torch.long, device="cuda")
    labels = torch.tensor([[-100] * len(prompt_ids) + answer_ids], dtype=torch.long, device="cuda")
    attention_mask = torch.ones_like(input_ids)
    with torch.inference_mode():
        loss = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels).loss
    return float(loss.detach().cpu())


def keyword_coverage(answer: str, keywords: list[str]) -> float:
    low = answer.lower()
    return sum(keyword.lower() in low for keyword in keywords) / max(1, len(keywords))


def generation_rows(tokenizer: Any, model: Any, eval_rows: list[dict[str, Any]], *, rag: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    model.config.use_cache = True
    model.eval()
    for row in eval_rows:
        generated = generate(
            tokenizer,
            model,
            row["question"],
            rag=rag,
            max_new_tokens=MAX_NEW_TOKENS,
        )
        coverage = keyword_coverage(generated["answer"], row["keywords"])
        rows.append(
            {
                "id": row["id"],
                "rag": rag,
                "answer": generated["answer"],
                "sources": generated["sources"],
                "keyword_coverage": coverage,
                "passed": coverage >= 0.5,
            }
        )
    model.config.use_cache = False
    return rows


def main() -> int:
    report: dict[str, Any] = {
        "ok": False,
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "seed": SEED,
        "epochs": EPOCHS,
        "max_length": MAX_LENGTH,
        "learning_rate": LR,
        "gradient_accumulation": GRAD_ACCUM,
        "eval_limit": EVAL_LIMIT,
    }
    try:
        torch = require_cuda()
        seed_everything(torch)
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer

        train_rows = read_jsonl(DATA / "train_sft.jsonl")
        eval_rows = read_jsonl(DATA / "eval_cases.jsonl")[:EVAL_LIMIT]
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            revision=MODEL_REVISION,
            dtype=torch.float16,
            low_cpu_mem_usage=True,
        ).to("cuda")
        model.config.use_cache = False

        baseline_losses = [target_loss(torch, tokenizer, model, row, rag=False) for row in eval_rows]
        baseline_generation = generation_rows(tokenizer, model, eval_rows, rag=False)

        config = LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        )
        model = get_peft_model(model, config)
        trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
        optimizer = torch.optim.AdamW(trainable, lr=LR)
        optimizer.zero_grad(set_to_none=True)
        losses: list[float] = []
        optimizer_steps = 0
        started = time.perf_counter()
        for epoch in range(EPOCHS):
            order = list(range(len(train_rows)))
            random.Random(SEED + epoch).shuffle(order)
            model.train()
            for position, index in enumerate(order):
                input_ids, labels = training_text(
                    tokenizer,
                    train_rows[index]["instruction"],
                    train_rows[index]["output"],
                )
                input_tensor = torch.tensor([input_ids], dtype=torch.long, device="cuda")
                label_tensor = torch.tensor([labels], dtype=torch.long, device="cuda")
                output = model(
                    input_ids=input_tensor,
                    attention_mask=torch.ones_like(input_tensor),
                    labels=label_tensor,
                )
                if not math.isfinite(float(output.loss.detach().cpu())):
                    raise RuntimeError("training loss became non-finite")
                losses.append(float(output.loss.detach().cpu()))
                (output.loss / GRAD_ACCUM).backward()
                if (position + 1) % GRAD_ACCUM == 0 or position == len(order) - 1:
                    torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)
                    optimizer_steps += 1
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started

        lora_losses = [target_loss(torch, tokenizer, model, row, rag=False) for row in eval_rows]
        rag_lora_losses = [target_loss(torch, tokenizer, model, row, rag=True) for row in eval_rows]
        lora_generation = generation_rows(tokenizer, model, eval_rows, rag=False)
        rag_lora_generation = generation_rows(tokenizer, model, eval_rows, rag=True)

        ADAPTER.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(ADAPTER)
        tokenizer.save_pretrained(ADAPTER)
        report.update(
            {
                "ok": True,
                "device": torch.cuda.get_device_name(0),
                "train_count": len(train_rows),
                "eval_count": len(eval_rows),
                "trainable_params": sum(parameter.numel() for parameter in trainable),
                "all_params": sum(parameter.numel() for parameter in model.parameters()),
                "optimizer_steps": optimizer_steps,
                "train_losses": losses,
                "train_initial_loss": losses[0],
                "train_final_loss": losses[-1],
                "baseline_eval_loss_mean": sum(baseline_losses) / len(baseline_losses),
                "lora_eval_loss_mean": sum(lora_losses) / len(lora_losses),
                "rag_lora_eval_loss_mean": sum(rag_lora_losses) / len(rag_lora_losses),
                "baseline_pass_count": sum(row["passed"] for row in baseline_generation),
                "lora_pass_count": sum(row["passed"] for row in lora_generation),
                "rag_lora_pass_count": sum(row["passed"] for row in rag_lora_generation),
                "baseline_generation": baseline_generation,
                "lora_generation": lora_generation,
                "rag_lora_generation": rag_lora_generation,
                "elapsed_seconds": round(elapsed, 3),
                "max_memory_allocated_mib": round(torch.cuda.max_memory_allocated() / 1024**2, 1),
                "adapter_dir": str(ADAPTER.relative_to(ROOT)),
                "claim_boundary": (
                    "This tiny run proves the local training/evaluation pipeline and records a finite held-out comparison. "
                    "It does not establish general professional competence."
                ),
            }
        )
        (REPORTS / "domain_lora_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            "AGENT_09_DOMAIN_LORA_OK "
            f"steps={optimizer_steps} loss={losses[0]:.4f}->{losses[-1]:.4f} "
            f"passes={report['baseline_pass_count']}/{report['lora_pass_count']}/{report['rag_lora_pass_count']} "
            f"memory_mib={report['max_memory_allocated_mib']}"
        )
        return 0
    except Exception as exc:
        report.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        (REPORTS / "domain_lora_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"AGENT_09_DOMAIN_LORA_FAILED {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
