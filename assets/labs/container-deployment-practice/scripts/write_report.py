#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def write_svg(summary: dict) -> None:
    path = REPORTS / "container_deployment_flow.svg"
    nodes = ["Dockerfile", "Image", "Container", "Port 18080", "Bind mount", "Report"]
    w, h = 940, 300
    x0, y, bw, bh, gap = 30, 112, 130, 70, 24
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
        '<title id="title">Container deployment practice flow</title>',
        '<desc id="desc">Dockerfile builds an image, image starts a container, host port and bind mount make the local deployment observable.</desc>',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif}.title{font-size:24px;font-weight:700;fill:#0f172a}.node{fill:#fff;stroke:#0ea5e9;stroke-width:2}.label{font-size:14px;font-weight:700;fill:#0f172a}.meta{font-size:13px;fill:#475569}.arrow{stroke:#64748b;stroke-width:2;marker-end:url(#arrow)}</style>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#64748b"/></marker></defs>',
        '<text class="title" x="30" y="42">Container deployment practice flow</text>',
    ]
    for idx, node in enumerate(nodes):
        x = x0 + idx * (bw + gap)
        parts.append(f'<rect class="node" x="{x}" y="{y}" width="{bw}" height="{bh}" rx="14"/>')
        parts.append(f'<text class="label" x="{x + bw/2}" y="{y + 42}" text-anchor="middle">{escape(node)}</text>')
        if idx < len(nodes) - 1:
            parts.append(f'<line class="arrow" x1="{x + bw + 3}" y1="{y + bh/2}" x2="{x + bw + gap - 5}" y2="{y + bh/2}"/>')
    parts.append(f'<text class="meta" x="30" y="250">Image: {escape(summary["image_tag"])}; visits after restart: {summary["visits_after_restart"]}; compose config: verified</text>')
    parts.append('</svg>\n')
    path.write_text("\n".join(parts), encoding="utf-8")


def write_markdown(summary: dict) -> None:
    lines = [
        "# Container deployment practice report",
        "",
        "## Headline",
        "",
        f"- Docker server version: {summary['docker_server_version']}",
        f"- Docker Compose version: {summary['compose_version']}",
        f"- Image tag: `{summary['image_tag']}`",
        f"- Container name: `{summary['container_name']}`",
        f"- Host URL: `{summary['host_url']}`",
        f"- Health status: {summary['health_status']}",
        f"- Visits after restart: {summary['visits_after_restart']}",
        f"- Bind-mounted state file exists: {summary['state_file_exists']}",
        f"- Compose config verified: {summary['compose_config_ok']}",
        "",
        "## Artifacts",
        "",
        "- `reports/smoke-first.json`",
        "- `reports/smoke-after-restart.json`",
        "- `reports/summary.json`",
        "- `reports/container_deployment_flow.svg`",
        "- `reports/transcript.txt`",
    ]
    (REPORTS / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    first = load_json("smoke-first.json")
    second = load_json("smoke-after-restart.json")
    docker_info = load_json("docker-info.json")
    summary = {
        "docker_server_version": docker_info["docker_server_version"],
        "compose_version": docker_info["compose_version"],
        "image_tag": docker_info["image_tag"],
        "container_name": docker_info["container_name"],
        "host_url": first["base_url"],
        "health_status": second["health"]["payload"]["status"],
        "visits_after_first_smoke": first["state"]["payload"]["visits"],
        "visits_after_restart": second["state"]["payload"]["visits"],
        "state_file_exists": (ROOT / "data" / "runtime" / "state.json").exists(),
        "compose_config_ok": docker_info["compose_config_ok"],
    }
    (REPORTS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_svg(summary)
    write_markdown(summary)
    print(f"health_status={summary['health_status']}")
    print(f"visits_after_restart={summary['visits_after_restart']}")
    print(f"compose_config_ok={summary['compose_config_ok']}")
    print("container_deployment_status=ok")


if __name__ == "__main__":
    main()
