#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

from attention_lookup import build_probe, dumps_json


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
        "# Attention key-value lookup probe",
        "",
        "## Metrics",
        "",
        "| Method | Test accuracy | What it can use |",
        "| --- | ---: | --- |",
        f"| Majority baseline | {fmt(float(probe['majority_baseline_accuracy']))} | Only label frequency |",
        f"| Last-value baseline | {fmt(float(probe['last_value_accuracy']))} | Only the final memory slot value |",
        f"| Bag-of-values baseline | {fmt(float(probe['bag_of_values_accuracy']))} | The multiset of values, not their keys |",
        f"| Fixed summary baseline | {fmt(float(probe['fixed_summary_accuracy']))} | Average of all value vectors |",
        f"| Attention lookup | {fmt(float(probe['attention_lookup_accuracy']))} | Query-key match followed by weighted value read |",
        "",
        "## Interpretation",
        "",
        "Every sample contains the same four keys and the same four values, only paired differently. A fixed summary or value bag loses the binding between a key and its value. Scaled dot-product attention keeps separate key and value paths, so a query can put most weight on the matching key and read the associated value.",
        "",
        f"Minimum top attention weight: `{fmt(float(probe['attention_min_top_weight']))}`.",
        f"All top keys match query: `{probe['all_top_keys_match_query']}`.",
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
    (reports / "attention_probe.json").write_text(dumps_json(probe) + "\n", encoding="utf-8")
    write_trace_csv(reports / "trace_table.csv", list(probe["trace_rows"]))
    write_report(reports / "attention_report.md", probe)

    print(f"TRAIN_SAMPLES={probe['train_samples']}")
    print(f"TEST_SAMPLES={probe['test_samples']}")
    print(f"MEMORY_SLOTS={probe['memory_slots']}")
    print(f"KEY_DIM={probe['key_dim']}")
    print(f"VALUE_DIM={probe['value_dim']}")
    print(f"MAJORITY_BASELINE_ACC={fmt(float(probe['majority_baseline_accuracy']))}")
    print(f"LAST_VALUE_ACC={fmt(float(probe['last_value_accuracy']))}")
    print(f"BAG_OF_VALUES_ACC={fmt(float(probe['bag_of_values_accuracy']))}")
    print(f"FIXED_SUMMARY_ACC={fmt(float(probe['fixed_summary_accuracy']))}")
    print(f"ATTENTION_LOOKUP_ACC={fmt(float(probe['attention_lookup_accuracy']))}")
    print(f"ATTENTION_GAIN_OVER_BEST_BASELINE={fmt(float(probe['attention_gain_over_best_baseline']))}")
    print(f"ATTENTION_MIN_TOP_WEIGHT={fmt(float(probe['attention_min_top_weight']))}")
    print(f"TOP_KEYS_MATCH_QUERY={'yes' if probe['all_top_keys_match_query'] else 'no'}")
    print(f"RUN_STATUS={probe['run_status']}")
    if probe["run_status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
