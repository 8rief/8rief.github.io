#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

from position_mask import build_probe, dumps_json


def fmt(value: float) -> str:
    return f"{value:.3f}"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("trace rows must not be empty")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, probe: dict[str, object]) -> None:
    lines = [
        "# Transformer position and mask probe",
        "",
        "## Position task",
        "",
        "| Method | Test accuracy | Meaning |",
        "| --- | ---: | --- |",
        f"| Bag baseline | {fmt(float(probe['position_bag_baseline_accuracy']))} | Sees token multiset but loses order |",
        f"| No-position attention | {fmt(float(probe['no_position_attention_accuracy']))} | Attention without position cannot ask for slot 0 |",
        f"| Positional attention | {fmt(float(probe['positional_attention_accuracy']))} | Position key lets query select slot 0 |",
        "",
        f"Minimum top position weight: `{fmt(float(probe['position_min_top_weight']))}`.",
        f"Top position matches query: `{probe['positional_top_matches_query']}`.",
        "",
        "## Mask task",
        "",
        "| Method | Test accuracy | Meaning |",
        "| --- | ---: | --- |",
        f"| Unmasked future lookup | {fmt(float(probe['unmasked_future_lookup_accuracy']))} | Reads the future label position and leaks the answer |",
        f"| Causal masked lookup | {fmt(float(probe['causal_masked_lookup_accuracy']))} | Future position is blocked, so no future label can be read |",
        "",
        f"Mask blocks future: `{probe['mask_blocks_future']}`.",
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
    (reports / "position_mask_probe.json").write_text(dumps_json(probe) + "\n", encoding="utf-8")
    write_csv(reports / "order_trace_table.csv", list(probe["order_trace_rows"]))
    write_csv(reports / "future_trace_table.csv", list(probe["future_trace_rows"]))
    write_report(reports / "position_mask_report.md", probe)

    print(f"ORDER_TEST_SAMPLES={probe['order_test_samples']}")
    print(f"FUTURE_TEST_SAMPLES={probe['future_test_samples']}")
    print(f"POSITION_BAG_BASELINE_ACC={fmt(float(probe['position_bag_baseline_accuracy']))}")
    print(f"NO_POSITION_ATTENTION_ACC={fmt(float(probe['no_position_attention_accuracy']))}")
    print(f"POSITIONAL_ATTENTION_ACC={fmt(float(probe['positional_attention_accuracy']))}")
    print(f"POSITION_GAIN_OVER_BEST_BASELINE={fmt(float(probe['position_gain_over_best_baseline']))}")
    print(f"POSITION_MIN_TOP_WEIGHT={fmt(float(probe['position_min_top_weight']))}")
    print(f"POSITION_TOP_MATCHES_QUERY={'yes' if probe['positional_top_matches_query'] else 'no'}")
    print(f"UNMASKED_FUTURE_LOOKUP_ACC={fmt(float(probe['unmasked_future_lookup_accuracy']))}")
    print(f"CAUSAL_MASKED_LOOKUP_ACC={fmt(float(probe['causal_masked_lookup_accuracy']))}")
    print(f"MASK_BLOCKS_FUTURE={'yes' if probe['mask_blocks_future'] else 'no'}")
    print(f"RUN_STATUS={probe['run_status']}")
    if probe["run_status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
