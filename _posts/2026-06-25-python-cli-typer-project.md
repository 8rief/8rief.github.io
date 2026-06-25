---
layout: post
title: "Python CLI：用 Typer 把脚本变成可复用命令"
date: 2026-06-25 16:34:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 Typer 组织 scan 和 summary 两个命令，解释参数、选项、输出和命令入口的项目边界。"
tags: [python, typer, cli, command-line, project]
---
{% raw %}


> 主题：Python 从0到可运行项目 / CLI / Typer / 命令入口  
> 本文 lab 已执行 `scan` 和 `summary` 两个命令，并产出 JSON/CSV 报告。

脚本解决一次性问题，CLI 解决可重复问题。一个好用的 CLI 需要清楚的参数、稳定的输出、可测试的边界，以及从项目安装后也能找到的命令入口。本文用 Typer 把文件扫描逻辑包装成两个命令：`scan` 和 `summary`。

## 学习目标

1. 区分位置参数和选项参数。
2. 用 Typer 定义多命令 CLI。
3. 让 CLI 调用核心函数，避免把业务逻辑写进命令函数。
4. 把 JSON/CSV 导出路径作为可选输出。
5. 用 transcript 验证命令行为。

## 先修知识

需要会执行命令行程序，并理解上一讲中的 `build_manifest()`、`write_manifest_json()` 和 `write_manifest_csv()`。

## 核心模型

CLI 是用户输入和核心逻辑之间的适配层。

![CLI 命令到核心逻辑](/assets/diagrams/python-cli-typer-project.svg)

终端参数进入 Typer，Typer 负责解析类型和选项，核心函数负责扫描，存储模块负责写报告，CLI 最后打印短摘要。

## 定义 scan 命令

`scan` 命令接收一个目录，并可选导出 JSON/CSV：

```python
app = typer.Typer(help="Build and inspect local file evidence manifests.")

@app.command()
def scan(
    path: Path = typer.Argument(..., help="Directory to scan."),
    json_output: Optional[Path] = typer.Option(None, "--json", help="Write manifest JSON."),
    csv_output: Optional[Path] = typer.Option(None, "--csv", help="Write manifest CSV."),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level."),
) -> None:
    configure_logging(log_level)
    manifest = build_manifest(path)
    if json_output is not None:
        write_manifest_json(manifest, json_output)
    if csv_output is not None:
        write_manifest_csv(manifest, csv_output)
    typer.echo(f"scanned root={manifest.root_name} files={manifest.summary.file_count} bytes={manifest.summary.total_bytes}")
```

这里 `path` 是必填位置参数，`--json` 和 `--csv` 是可选输出。CLI 函数本身很薄：它解析参数、调用核心逻辑、输出结果。扫描、哈希、JSON、CSV 都放在独立模块中。

## 定义 summary 命令

`summary` 读取已保存的 JSON 清单，只打印 compact 摘要：

```python
@app.command()
def summary(manifest_json: Path = typer.Argument(..., help="Manifest JSON produced by scan.")) -> None:
    payload = read_manifest_json(manifest_json)
    summary_payload = payload["summary"]
    typer.echo(
        f"manifest root={payload['root_name']} files={summary_payload['file_count']} "
        f"bytes={summary_payload['total_bytes']}"
    )
```

这个命令说明 CLI 可以复用中间产物。一次扫描得到 JSON 后，后续命令可以基于报告继续处理，而不必每次重新扫描文件系统。

## 执行命令

lab 中使用模块方式执行，避免依赖 shell 是否已经刷新命令入口：

```bash
python -m local_evidence.cli scan sample_data --json reports/sample-manifest.json --csv reports/sample-manifest.csv
python -m local_evidence.cli summary reports/sample-manifest.json
```

输出为：

```text
scanned root=sample_data files=3 bytes=119
manifest root=sample_data files=3 bytes=119
```

如果通过 `pyproject.toml` 的 `[project.scripts]` 安装命令入口，也可以执行：

```bash
local-evidence scan sample_data --json reports/sample-manifest.json --csv reports/sample-manifest.csv
```

## 常见错误

1. **CLI 函数太厚。** 参数解析、业务处理、文件写入、网络请求全部写在一个函数里，后续很难测试。
2. **输出不稳定。** 面向脚本调用的 CLI 应该有简洁、可预测的文本输出。
3. **只支持当前目录运行。** 项目安装后仍应能找到包和命令入口。
4. **帮助信息缺失。** CLI 是用户界面，参数说明就是最基础的文档。

## 练习

1. 给 `scan` 增加 `--min-size` 选项，并把过滤逻辑放进扫描模块。
2. 给 `summary` 增加 `--json` 选项，让它输出机器可读摘要。
3. 执行 `python -m local_evidence.cli --help`，检查帮助文本是否能解释命令用途。

## 参考资料

- Typer 文档：[First Steps](https://typer.tiangolo.com/tutorial/first-steps/)
- PyPA docs source：[Creating command line tools](https://github.com/pypa/packaging.python.org/blob/main/source/guides/creating-command-line-tools.rst)
- Python 文档：[argparse](https://docs.python.org/3/library/argparse.html)


{% endraw %}
