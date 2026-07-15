#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

from rnn_hidden_state import build_probe, dumps_json


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def bool_word(value: bool) -> str:
    return "yes" if value else "no"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    probe = build_probe()
    (reports / "rnn_probe.json").write_text(dumps_json(probe) + "\n", encoding="utf-8")

    rows = probe["trace_rows"]
    with (reports / "trace_table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# RNN hidden-state mechanism probe report",
        "",
        f"- Train samples: {probe['train_samples']}",
        f"- Test samples: {probe['test_samples']}",
        f"- Sequence length: {probe['sequence_length']}",
        f"- Majority baseline accuracy: {percent(probe['majority_baseline_accuracy'])}",
        f"- Last-token baseline accuracy: {percent(probe['last_token_accuracy'])}",
        f"- Suffix-bag baseline accuracy: {percent(probe['suffix_bag_accuracy'])}",
        f"- No-recurrence final-state accuracy: {percent(probe['no_recurrence_accuracy'])}",
        f"- Recurrent hidden-state accuracy: {percent(probe['rnn_memory_accuracy'])}",
        f"- Memory gain over best baseline: {percent(probe['memory_gain_over_best_baseline'])}",
        f"- Hidden sign stable: {bool_word(probe['hidden_sign_stable'])}",
        "",
        "| sample | sequence | label | last token | suffix bag | no recurrence | recurrent | h after first | final h |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['name']} | `{row['sequence']}` | {row['label']} | "
            f"{row['last_token_prediction']} | {row['suffix_bag_prediction']} | "
            f"{row['no_recurrence_prediction']} | {row['rnn_prediction']} | "
            f"{row['hidden_after_first']} | {row['final_hidden']} |"
        )
    lines += ["", f"Boundary: {probe['boundary']}", ""]
    (reports / "rnn_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"TRAIN_SAMPLES={probe['train_samples']}")
    print(f"TEST_SAMPLES={probe['test_samples']}")
    print(f"SEQUENCE_LENGTH={probe['sequence_length']}")
    print(f"MAJORITY_BASELINE_ACC={probe['majority_baseline_accuracy']:.3f}")
    print(f"LAST_TOKEN_ACC={probe['last_token_accuracy']:.3f}")
    print(f"SUFFIX_BAG_ACC={probe['suffix_bag_accuracy']:.3f}")
    print(f"NO_RECURRENCE_ACC={probe['no_recurrence_accuracy']:.3f}")
    print(f"RNN_MEMORY_ACC={probe['rnn_memory_accuracy']:.3f}")
    print(f"MEMORY_GAIN_OVER_BEST_BASELINE={probe['memory_gain_over_best_baseline']:.3f}")
    print(f"HIDDEN_SIGN_STABLE={bool_word(probe['hidden_sign_stable'])}")
    print(f"RUN_STATUS={probe['run_status']}")
    return 0 if probe["run_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
