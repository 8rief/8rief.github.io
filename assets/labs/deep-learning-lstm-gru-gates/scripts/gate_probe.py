#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

from gated_memory import build_probe, dumps_json


def fmt(value: float) -> str:
    return f"{value:.3f}"


def write_trace_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("trace rows must not be empty")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, probe: dict[str, object]) -> None:
    lines = [
        "# LSTM/GRU gate memory probe",
        "",
        "## Metrics",
        "",
        "| Method | Test accuracy | What it can see |",
        "| --- | ---: | --- |",
        f"| Majority baseline | {fmt(float(probe['majority_baseline_accuracy']))} | Only label frequency in training data |",
        f"| Last-token baseline | {fmt(float(probe['last_token_accuracy']))} | Only the final distractor token |",
        f"| Vanilla RNN | {fmt(float(probe['vanilla_rnn_accuracy']))} | Shared hidden state overwritten by distractors |",
        f"| Idealized LSTM gates | {fmt(float(probe['lstm_gate_accuracy']))} | Writes the cue once, then keeps the cell state |",
        f"| Idealized GRU update gate | {fmt(float(probe['gru_update_gate_accuracy']))} | Writes the cue once, then keeps hidden state |",
        "",
        "## Interpretation",
        "",
        "The label is determined by the first token. Later x/y tokens are distractors and are paired with both labels, so suffix-only rules stay at chance. The vanilla RNN update uses every later token as new input, while the idealized LSTM/GRU gates separate write and keep decisions.",
        "",
        f"LSTM cell stable: `{probe['lstm_cell_state_stable']}`.",
        f"GRU keep stable: `{probe['gru_keep_stable']}`.",
        "",
        "## Boundary",
        "",
        str(probe["boundary"]),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    probe = build_probe()
    (reports / "gate_probe.json").write_text(dumps_json(probe) + "\n", encoding="utf-8")
    write_trace_csv(reports / "trace_table.csv", list(probe["trace_rows"]))
    write_report(reports / "gate_report.md", probe)

    print(f"TRAIN_SAMPLES={probe['train_samples']}")
    print(f"TEST_SAMPLES={probe['test_samples']}")
    print(f"SEQUENCE_LENGTH={probe['sequence_length']}")
    print(f"MAJORITY_BASELINE_ACC={fmt(float(probe['majority_baseline_accuracy']))}")
    print(f"LAST_TOKEN_ACC={fmt(float(probe['last_token_accuracy']))}")
    print(f"VANILLA_RNN_ACC={fmt(float(probe['vanilla_rnn_accuracy']))}")
    print(f"LSTM_GATE_ACC={fmt(float(probe['lstm_gate_accuracy']))}")
    print(f"GRU_UPDATE_GATE_ACC={fmt(float(probe['gru_update_gate_accuracy']))}")
    print(f"GATE_GAIN_OVER_BEST_BASELINE={fmt(float(probe['gate_gain_over_best_baseline']))}")
    print(f"LSTM_CELL_STABLE={'yes' if probe['lstm_cell_state_stable'] else 'no'}")
    print(f"GRU_KEEP_STABLE={'yes' if probe['gru_keep_stable'] else 'no'}")
    print(f"RUN_STATUS={probe['run_status']}")
    if probe["run_status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
