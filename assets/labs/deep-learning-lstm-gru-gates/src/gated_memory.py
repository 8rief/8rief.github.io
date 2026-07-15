#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, NamedTuple

Sequence = tuple[str, ...]
Label = str

LABEL_A = "topic_a"
LABEL_B = "topic_b"
VANILLA_RECURRENT_WEIGHT = 0.2
VANILLA_INPUT_WEIGHT = 1.4


@dataclass(frozen=True)
class Sample:
    name: str
    sequence: Sequence
    label: Label


class LstmStep(NamedTuple):
    token: str
    forget_gate: float
    input_gate: float
    candidate: float
    output_gate: float
    cell: float
    hidden: float


class GruStep(NamedTuple):
    token: str
    reset_gate: float
    update_gate: float
    candidate: float
    hidden: float


def label_from_cue(cue: str) -> Label:
    if cue == "A":
        return LABEL_A
    if cue == "B":
        return LABEL_B
    raise ValueError("cue must be A or B")


def make_sample(split: str, cue: str, suffix: str, index: int) -> Sample:
    if cue not in {"A", "B"}:
        raise ValueError("cue must be A or B")
    if len(suffix) != 12:
        raise ValueError("suffix must contain exactly 12 distractor tokens")
    if any(token not in {"x", "y"} for token in suffix):
        raise ValueError("suffix tokens must be x/y")
    return Sample(
        name=f"{split}-{index}-{cue}-{suffix}",
        sequence=tuple(cue + suffix),
        label=label_from_cue(cue),
    )


def make_dataset() -> tuple[list[Sample], list[Sample]]:
    train_suffixes = [
        "xyxyxyxyxyxy",
        "yxyxyxyxyxyx",
        "xxyyxyxyyxxy",
        "yyxxyxyxxyyx",
        "xyyxxxyyxyyx",
        "yxxyyyxxyxxy",
        "xxxyyyxyxyyx",
        "yyyxxxyxyxxy",
    ]
    test_suffixes = [
        "xxyxyyxyxyxy",
        "yyxyxxyxyxyx",
        "xyxxyyxyxyyx",
        "yxyyxxxyxyxy",
        "xxxyxyyyxxyx",
        "yyyxyxxxxyxy",
        "xyxyxxyyxyyx",
        "yxyxyyxxxyxy",
    ]
    train: list[Sample] = []
    test: list[Sample] = []
    for index, suffix in enumerate(train_suffixes):
        train.append(make_sample("train", "A", suffix, index))
        train.append(make_sample("train", "B", suffix, index))
    for index, suffix in enumerate(test_suffixes):
        test.append(make_sample("test", "A", suffix, index))
        test.append(make_sample("test", "B", suffix, index))
    return train, test


def token_signal(token: str) -> float:
    if token in {"A", "x"}:
        return 1.0
    if token in {"B", "y"}:
        return -1.0
    raise ValueError(f"unknown token {token}")


def cue_candidate(token: str) -> float:
    if token == "A":
        return 1.0
    if token == "B":
        return -1.0
    if token in {"x", "y"}:
        return 0.0
    raise ValueError(f"unknown token {token}")


def vanilla_rnn_step(previous_hidden: float, token: str) -> float:
    return math.tanh(VANILLA_RECURRENT_WEIGHT * previous_hidden + VANILLA_INPUT_WEIGHT * token_signal(token))


def vanilla_rnn_trace(sequence: Sequence) -> list[float]:
    hidden = 0.0
    trace: list[float] = []
    for token in sequence:
        hidden = vanilla_rnn_step(hidden, token)
        trace.append(hidden)
    return trace


def predict_vanilla_rnn(sequence: Sequence) -> Label:
    return LABEL_A if vanilla_rnn_trace(sequence)[-1] >= 0.0 else LABEL_B


def lstm_gate_step(previous_cell: float, token: str) -> LstmStep:
    if token in {"A", "B"}:
        forget_gate = 0.0
        input_gate = 1.0
        candidate = cue_candidate(token)
    elif token in {"x", "y"}:
        forget_gate = 1.0
        input_gate = 0.0
        candidate = token_signal(token)
    else:
        raise ValueError(f"unknown token {token}")
    output_gate = 1.0
    cell = forget_gate * previous_cell + input_gate * candidate
    hidden = output_gate * math.tanh(cell)
    return LstmStep(token, forget_gate, input_gate, candidate, output_gate, cell, hidden)


def lstm_trace(sequence: Sequence) -> list[LstmStep]:
    cell = 0.0
    trace: list[LstmStep] = []
    for token in sequence:
        step = lstm_gate_step(cell, token)
        trace.append(step)
        cell = step.cell
    return trace


def predict_lstm_gate(sequence: Sequence) -> Label:
    return LABEL_A if lstm_trace(sequence)[-1].hidden >= 0.0 else LABEL_B


def gru_gate_step(previous_hidden: float, token: str) -> GruStep:
    if token in {"A", "B"}:
        reset_gate = 1.0
        update_gate = 0.0
        candidate = math.tanh(cue_candidate(token))
    elif token in {"x", "y"}:
        reset_gate = 0.0
        update_gate = 1.0
        candidate = math.tanh(token_signal(token))
    else:
        raise ValueError(f"unknown token {token}")
    hidden = (1.0 - update_gate) * candidate + update_gate * previous_hidden
    return GruStep(token, reset_gate, update_gate, candidate, hidden)


def gru_trace(sequence: Sequence) -> list[GruStep]:
    hidden = 0.0
    trace: list[GruStep] = []
    for token in sequence:
        step = gru_gate_step(hidden, token)
        trace.append(step)
        hidden = step.hidden
    return trace


def predict_gru_gate(sequence: Sequence) -> Label:
    return LABEL_A if gru_trace(sequence)[-1].hidden >= 0.0 else LABEL_B


def majority_label(samples: Iterable[Sample]) -> Label:
    counts = Counter(sample.label for sample in samples)
    if not counts:
        raise ValueError("majority baseline needs samples")
    return sorted((-count, label) for label, count in counts.items())[0][1]


def train_lookup(
    samples: Iterable[Sample],
    key_fn: Callable[[Sequence], object],
    *,
    default_label: Label,
) -> dict[object, Label]:
    buckets: dict[object, Counter[Label]] = defaultdict(Counter)
    for sample in samples:
        buckets[key_fn(sample.sequence)][sample.label] += 1
    table: dict[object, Label] = {}
    for key, counts in buckets.items():
        table[key] = sorted((-count, label) for label, count in counts.items())[0][1]
    table["__default__"] = default_label
    return table


def predict_from_lookup(sequence: Sequence, table: dict[object, Label], key_fn: Callable[[Sequence], object]) -> Label:
    return table.get(key_fn(sequence), table["__default__"])


def accuracy(samples: Iterable[Sample], predict: Callable[[Sequence], Label]) -> float:
    rows = list(samples)
    if not rows:
        raise ValueError("accuracy needs at least one sample")
    return sum(1 for sample in rows if predict(sample.sequence) == sample.label) / len(rows)


def lstm_cell_state_stable(samples: Iterable[Sample]) -> bool:
    for sample in samples:
        trace = lstm_trace(sample.sequence)
        first_cell = trace[0].cell
        if first_cell == 0.0:
            return False
        if any(step.cell != first_cell for step in trace[1:]):
            return False
    return True


def gru_keep_stable(samples: Iterable[Sample]) -> bool:
    for sample in samples:
        trace = gru_trace(sample.sequence)
        first_hidden = trace[0].hidden
        if first_hidden == 0.0:
            return False
        if any(abs(step.hidden - first_hidden) > 1e-12 for step in trace[1:]):
            return False
    return True


def trace_rows(samples: Iterable[Sample], last_table: dict[object, Label]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sample in samples:
        vanilla_trace = vanilla_rnn_trace(sample.sequence)
        lstm_steps = lstm_trace(sample.sequence)
        gru_steps = gru_trace(sample.sequence)
        rows.append({
            "name": sample.name,
            "sequence": "".join(sample.sequence),
            "label": sample.label,
            "last_token_prediction": predict_from_lookup(sample.sequence, last_table, lambda seq: seq[-1]),
            "vanilla_rnn_prediction": predict_vanilla_rnn(sample.sequence),
            "lstm_gate_prediction": predict_lstm_gate(sample.sequence),
            "gru_gate_prediction": predict_gru_gate(sample.sequence),
            "vanilla_after_first": round(vanilla_trace[0], 4),
            "vanilla_final": round(vanilla_trace[-1], 4),
            "lstm_cell_after_first": round(lstm_steps[0].cell, 4),
            "lstm_cell_final": round(lstm_steps[-1].cell, 4),
            "gru_hidden_after_first": round(gru_steps[0].hidden, 4),
            "gru_hidden_final": round(gru_steps[-1].hidden, 4),
        })
    return rows


def build_probe() -> dict[str, object]:
    train, test = make_dataset()
    majority = majority_label(train)
    last_table = train_lookup(train, lambda seq: seq[-1], default_label=majority)
    majority_acc = accuracy(test, lambda _seq: majority)
    last_token_acc = accuracy(test, lambda seq: predict_from_lookup(seq, last_table, lambda item: item[-1]))
    vanilla_acc = accuracy(test, predict_vanilla_rnn)
    lstm_acc = accuracy(test, predict_lstm_gate)
    gru_acc = accuracy(test, predict_gru_gate)
    best_baseline = max(majority_acc, last_token_acc, vanilla_acc)
    cell_stable = lstm_cell_state_stable(train + test)
    gru_stable = gru_keep_stable(train + test)
    run_ok = (
        majority_acc == 0.5
        and last_token_acc == 0.5
        and vanilla_acc == 0.5
        and lstm_acc == 1.0
        and gru_acc == 1.0
        and cell_stable
        and gru_stable
    )
    return {
        "schema_version": 1,
        "train_samples": len(train),
        "test_samples": len(test),
        "sequence_length": len(train[0].sequence),
        "task": "Delayed-cue classification with suffix distractors.",
        "majority_baseline_accuracy": majority_acc,
        "last_token_accuracy": last_token_acc,
        "vanilla_rnn_accuracy": vanilla_acc,
        "lstm_gate_accuracy": lstm_acc,
        "gru_update_gate_accuracy": gru_acc,
        "gate_gain_over_best_baseline": lstm_acc - best_baseline,
        "lstm_cell_state_stable": cell_stable,
        "gru_keep_stable": gru_stable,
        "trace_rows": trace_rows(test, last_table),
        "boundary": "The LSTM and GRU gates are hand-set to expose the mechanism. This is a sequence-memory teaching probe, not a language-model benchmark.",
        "run_status": "ok" if run_ok else "failed",
    }


def dumps_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    print(dumps_json(build_probe()))
