#!/usr/bin/env python3
"""Verify that the course's primary references are reachable."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def main() -> int:
    references = json.loads((ROOT / "references.json").read_text(encoding="utf-8"))
    rows = []
    failed = 0
    for reference in references:
        request = urllib.request.Request(
            reference["url"], headers={"User-Agent": "local-agent-course-reference-check/1.0"}
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                status = response.status
                final_url = response.url
        except (urllib.error.URLError, TimeoutError) as exc:
            status = 0
            final_url = ""
            error = f"{type(exc).__name__}: {exc}"
        else:
            error = ""
        ok = 200 <= status < 400
        failed += not ok
        rows.append({**reference, "ok": ok, "status": status, "final_url": final_url, "error": error})
        print(f"{'ok' if ok else 'FAIL'}\t{status}\t{reference['title']}\t{reference['url']}")
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "reference_check.json").write_text(
        json.dumps({"ok": failed == 0, "count": len(rows), "rows": rows}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    if failed:
        print(f"AGENT_REFERENCE_CHECK_FAILED failed={failed} total={len(rows)}")
        return 1
    print(f"AGENT_REFERENCE_CHECK_OK refs={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
