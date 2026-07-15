---
layout: post
title: "把命令收进脚本：参数、退出状态和可复用边界"
date: 2026-06-13 09:00:00 +0800
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

## 为什么需要脚本契约

一条手工管道能回答当下问题，但它不适合重复交付。第二天你可能忘记命令顺序，同伴可能不知道输入目录，自动化系统也无法判断失败路径。脚本契约用来解决这些问题：把输入、输出、失败条件和退出状态写成稳定接口。

`report.sh` 的核心问题是：给定一个日志目录和一个报告目录，生成固定格式的统计文件。如果参数缺失、日志目录里没有 `.log` 文件，脚本应该明确失败，而不是生成一份看似成功的空报告。

一个好的脚本入口至少要回答：

1. 需要几个参数？
2. 每个参数代表什么？
3. 成功时会写出哪些文件？
4. 失败时错误信息写在哪里？
5. 调用者如何用退出状态判断能否继续？

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

## 输出怎么读

这份摘要说明脚本完成了完整输入到输出的闭环：

- `source_files=2` 证明脚本发现并读取了两个日志文件。
- `total_requests=16` 与每个文件 8 行相互印证。
- `error_requests=5` 来自 `grep -c ' level=ERROR '`，但脚本对没有匹配的情况用了 `|| true`，避免“0 个错误”被当作命令失败。
- `slow_requests_ge_400ms=4` 来自 `awk` 对 `latency_ms` 字段的数值判断。
- `top_status=200	8` 来自 `status_counts.tsv` 的第一行。

这些字段都能被测试脚本复查。脚本输出不只给人看，也给后续自动化检查使用。

## 失败路径也要可解释

运行参数错误的版本：

```bash
bash scripts/report.sh
echo $?
```

预期会看到 usage，退出状态是 `2`。这个状态约定表示“调用方式错误”。如果输入目录存在但没有日志文件，脚本写出 `no .log files found under ...` 并退出 `1`。区分这两类失败，后续自动化才能给出更准确的提示。

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
