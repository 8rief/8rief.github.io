#!/usr/bin/env python3
"""Exercise atomic publication, cleanup, idempotence, and manifest checks."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
WORK = Path("/tmp/project-data-boundary-lab")
APP = ROOT / "src" / "artifact_pipeline.py"


@dataclass(frozen=True)
class CaseResult:
    name: str
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


def execute(name: str, argv: list[str]) -> CaseResult:
    proc = subprocess.run(
        argv,
        cwd=WORK,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return CaseResult(name, argv, proc.returncode, proc.stdout, proc.stderr)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_command(argv: list[str]) -> str:
    replacements = {
        str(APP): "src/artifact_pipeline.py",
        str(WORK): "$LAB",
    }
    rendered = shlex.join(argv)
    for source, target in replacements.items():
        rendered = rendered.replace(source, target)
    return rendered


def portable_case(result: CaseResult) -> dict[str, object]:
    return {
        "name": result.name,
        "argv": [
            "python3" if item == sys.executable else display_command([item])
            for item in result.argv
        ],
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> None:
    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "input").mkdir(parents=True)
    (WORK / "config").mkdir()
    (WORK / "cache").mkdir()
    (WORK / "temp").mkdir()
    (WORK / "output").mkdir()
    REPORTS.mkdir(parents=True, exist_ok=True)

    input_path = WORK / "input" / "orders.jsonl"
    config_path = WORK / "config" / "pipeline.json"
    output_path = WORK / "output" / "summary.json"
    manifest_path = WORK / "output" / "manifest.json"
    shutil.copyfile(ROOT / "fixtures" / "orders.jsonl", input_path)
    shutil.copyfile(ROOT / "config" / "pipeline.json", config_path)
    (WORK / "cache" / "orders.cache").write_text("disposable-cache\n", encoding="utf-8")

    old_bytes = b'{"sentinel":"old-output"}\n'
    output_path.write_bytes(old_bytes)
    old_hash = sha256_file(output_path)

    base_argv = [
        sys.executable,
        str(APP),
        "--input",
        str(input_path),
        "--config",
        str(config_path),
        "--output",
        str(output_path),
        "--manifest",
        str(manifest_path),
    ]
    failed = execute("forced-before-replace", base_argv + ["--fail-before-replace"])
    if failed.returncode != 70:
        raise AssertionError(f"expected forced failure rc=70, got {failed.returncode}")
    if output_path.read_bytes() != old_bytes:
        raise AssertionError("forced failure changed the published output")
    temp_after_failure = list(output_path.parent.glob(".summary.json.*.tmp"))
    if temp_after_failure:
        raise AssertionError(f"temporary files leaked: {temp_after_failure}")
    if manifest_path.exists():
        raise AssertionError("manifest must not exist when output publication fails")

    first = execute("first-success", base_argv)
    if first.returncode != 0:
        raise AssertionError(first.stderr)
    first_output = output_path.read_bytes()
    first_manifest = manifest_path.read_bytes()
    first_hash = sha256_file(output_path)
    summary = json.loads(first_output)
    manifest = json.loads(first_manifest)
    if summary["selected_order_count"] != 3 or summary["total_amount_cents"] != 4500:
        raise AssertionError(summary)
    if manifest["output_sha256"] != first_hash:
        raise AssertionError("manifest hash does not match output bytes")

    shutil.rmtree(WORK / "cache")
    second = execute("second-success-after-cache-delete", base_argv)
    if second.returncode != 0:
        raise AssertionError(second.stderr)
    rerun_identical = (
        output_path.read_bytes() == first_output
        and manifest_path.read_bytes() == first_manifest
    )
    if not rerun_identical:
        raise AssertionError("same input and config did not reproduce identical artifacts")
    if sha256_file(output_path) != first_hash:
        raise AssertionError("output hash drifted after rerun")

    report = {
        "directory_model": ["source", "config", "input", "cache", "temp", "output"],
        "old_output_sha256": old_hash,
        "published_output_sha256": first_hash,
        "failed_write_rc": failed.returncode,
        "output_preserved_after_failure": True,
        "temp_files_after_failure": len(temp_after_failure),
        "cache_deleted_before_rerun": True,
        "rerun_byte_identical": rerun_identical,
        "manifest_output_hash_match": manifest["output_sha256"] == first_hash,
        "summary": summary,
        "manifest": manifest,
        "run_status": "ok",
        "cases": [portable_case(failed), portable_case(first), portable_case(second)],
    }
    (REPORTS / "data_boundary_probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (REPORTS / "artifact_manifest.json").write_bytes(first_manifest)

    transcript = dedent(
        f"""
        # Project data/temp/atomic-write transcript

        ## Forced failure before replace

        ```bash
        {display_command(failed.argv)}
        # rc={failed.returncode}
        ```

        ```text
        OUTPUT_PRESERVED_AFTER_FAILURE=yes
        TEMP_FILES_AFTER_FAILURE={len(temp_after_failure)}
        OLD_OUTPUT_SHA256={old_hash}
        ```

        ## First successful publication

        ```bash
        {display_command(first.argv)}
        # rc={first.returncode}
        ```

        ```text
        SELECTED_ORDER_COUNT={summary['selected_order_count']}
        TOTAL_AMOUNT_CENTS={summary['total_amount_cents']}
        PUBLISHED_OUTPUT_SHA256={first_hash}
        MANIFEST_OUTPUT_HASH_MATCH=yes
        ```

        ## Delete cache and rerun

        ```bash
        rm -rf "$LAB/cache"
        {display_command(second.argv)}
        # rc={second.returncode}
        ```

        ```text
        RERUN_BYTE_IDENTICAL=yes
        RUN_STATUS=ok
        ```
        """
    ).lstrip()
    (REPORTS / "transcript.md").write_text(transcript, encoding="utf-8")

    summary_markdown = dedent(
        f"""
        # Atomic publication lab summary

        - Directory model: `source, config, input, cache, temp, output`.
        - Forced failure return code: `{failed.returncode}`.
        - Previous output preserved after failure: `yes`.
        - Temporary candidates after failure: `{len(temp_after_failure)}`.
        - Published output SHA-256: `{first_hash}`.
        - Cache deletion changed output: `no`.
        - Same-input rerun byte-identical: `yes`.
        - Manifest output hash matches: `yes`.
        """
    ).lstrip()
    (REPORTS / "atomic_write_summary.md").write_text(summary_markdown, encoding="utf-8")

    print("DIRECTORY_MODEL=source,config,input,cache,temp,output")
    print(f"FAILED_WRITE_RC={failed.returncode}")
    print("OUTPUT_PRESERVED_AFTER_FAILURE=yes")
    print(f"TEMP_FILES_AFTER_FAILURE={len(temp_after_failure)}")
    print(f"PUBLISHED_OUTPUT_SHA256={first_hash}")
    print("RERUN_BYTE_IDENTICAL=yes")
    print("MANIFEST_OUTPUT_HASH_MATCH=yes")
    print("RUN_STATUS=ok")


if __name__ == "__main__":
    main()
