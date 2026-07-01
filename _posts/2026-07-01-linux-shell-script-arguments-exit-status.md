---
layout: post
title: "把命令收进脚本：参数、退出状态和可复用边界"
date: 2026-07-01 09:21:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把一次性管道整理成 report.sh，让输入目录、输出目录和失败条件变清楚。"
tags: [linux, bash, shell-script, automation, teaching]
---
{% raw %}
> 主题：Linux CLI 与 Shell 自动化 / script contract / arguments / exit status
> 本文 lab 已验证：`scripts/report.sh .lab_tmp/logs reports` 生成 `summary.txt`、`status_counts.tsv`、`path_latency.tsv`。

管道能快速探索问题，但团队协作和反复运行需要脚本。把命令收进脚本时，关键是明确脚本的契约：需要哪些参数，读取哪些文件，写出哪些结果，什么情况算失败。

## 学习目标

1. 会用 `$#` 检查参数个数，用 `$1`、`$2` 读取参数。
2. 理解 `set -euo pipefail` 的收益和边界。
3. 能把一个文本管道整理成可复跑报告脚本。

## 先修知识

知道管道可以得到错误数和状态码分布。

## 核心模型

![Shell 脚本的输入输出契约](/assets/diagrams/linux-shell-script-contract.svg)

脚本是稳定接口：输入目录和输出目录由参数给出，内部可以调整实现，但对外产物和退出状态应该稳定。

## 可信资料的关键结论

- Bash 手册定义 positional parameters：`$1`、`$2` 等来自脚本或函数调用参数。
- Bash 的 exit status 是自动化判断成功/失败的基础，`0` 表示成功，非零表示失败。
- `pipefail` 是 Bash 扩展，能让管道中较早失败的命令被整体感知；可移植 POSIX sh 脚本不能直接假设它存在。

## 逐步实现

`report.sh` 的入口先检查参数：

```bash
if (($# != 2)); then
  printf 'usage: %s LOG_DIR REPORT_DIR\n' "$0" >&2
  exit 2
fi

log_dir=$1
report_dir=$2
mkdir -p "$report_dir"
```

这段代码做了三件事：参数数量不对就给出 usage，错误信息写到标准错误，退出状态为 `2`。

然后收集输入文件：

```bash
mapfile -d '' logs < <(find "$log_dir" -type f -name '*.log' -print0 | sort -z)
if ((${#logs[@]} == 0)); then
  printf 'no .log files found under %s\n' "$log_dir" >&2
  exit 1
fi
```

这里输出目录、输入文件列表、失败条件都很清楚。运行：

```bash
bash scripts/report.sh .lab_tmp/logs reports
cat reports/summary.txt
```

预期结果：

```text
total_requests=16
error_requests=5
slow_requests_ge_400ms=4
top_status=200	8
source_files=2
```

## 常见错误

1. **脚本没有 usage。** 参数错了只能猜，后续维护成本很高。
2. **错误信息写到标准输出。** 自动化调用时，标准输出应尽量保留给正常结果。
3. **没有检查空输入。** 没有日志文件时继续生成空报告，会制造假成功。
4. **滥用 strict mode。** `set -euo pipefail` 能暴露错误，但仍要主动处理允许失败的命令，例如 `grep -c ... || true`。

## 练习或延伸

1. 运行 `bash scripts/report.sh`，确认 usage 和退出状态。
2. 新建空目录，运行 `bash scripts/report.sh empty reports`，观察失败信息。
3. 给 `summary.txt` 增加一个 `warn_requests=2` 字段，并补充测试。

## 参考资料

- GNU Bash：[Shell Parameters](https://www.gnu.org/software/bash/manual/html_node/Shell-Parameters.html)
- GNU Bash：[Exit Status](https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html)
- GNU Bash：[The Set Builtin](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html)

{% endraw %}
