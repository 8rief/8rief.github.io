---
layout: post
title: "Shell 脚本质量：语法检查、测试脚本和可复跑 transcript"
date: 2026-07-01 09:42:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 bash -n、测试脚本和 transcript 把一次成功运行变成可复查证据。"
tags: [linux, shell, testing, shellcheck, teaching]
---
{% raw %}
> 主题：Linux CLI 与 Shell 自动化 / quality gates / tests / transcript
> 本文 lab 已验证：`bash -n scripts/*.sh` 通过，`shell_lab_tests=ok`。

脚本能在自己电脑上跑一次，只能说明当时没有明显失败。可复查的自动化需要三类证据：语法检查、行为测试、运行 transcript。这样以后改脚本时，能快速知道自己是否破坏了原有结果。

## 学习目标

1. 用 `bash -n` 检查脚本语法。
2. 写一个小测试脚本验证关键输出。
3. 保存 transcript，让别人知道命令、环境和结果。

## 先修知识

已经能运行 `report.sh` 并理解输出报告。

## 核心模型

![Shell 脚本质量门槛](/assets/diagrams/linux-shell-quality-gates.svg)

质量门槛从低到高是：脚本能解析，脚本能运行，结果符合预期，证据能被复查。每一层都能捕获不同类型的问题。

## 可信资料的关键结论

- Bash 的 `-n` 选项会读取命令但不执行，用于发现语法错误。
- ShellCheck 的规则库适合发现引用、未定义变量、不可达分支和常见脚本陷阱。
- 测试脚本不需要一开始很复杂；先断言最关键的输出，再逐步增加覆盖。

## 逐步实现

语法检查：

```bash
bash -n scripts/*.sh
```

这一步不会执行脚本，只检查 Bash 是否能解析。行为测试在 `scripts/test_report.sh` 中：

```bash
require_line 'total_requests=16' "$report_dir/summary.txt"
require_line 'error_requests=5' "$report_dir/summary.txt"
require_line $'200\t8' "$report_dir/status_counts.tsv"
require_line $'app 2026-07-02.log\t8\t3' "$report_dir/batch-summary.tsv"
```

这些断言对应最重要的结果：总量、错误数、状态码分布、带空格文件名是否被正确处理。

完整 lab 会把全部过程写入：

```text
reports/transcript.txt
```

这份 transcript 记录了环境版本、手工命令、报告脚本、批处理脚本和测试结果。它让“我跑过”变成“可以复查”。

如果系统安装了 ShellCheck，lab 会自动运行：

```bash
shellcheck run_lab.sh scripts/*.sh
```

当前环境没有安装时，transcript 会明确记录 `shellcheck=skipped_not_installed`，避免把未验证说成已验证。

## 常见错误

1. **只看脚本退出码。** 退出码为 0 仍可能生成错误报告，需要断言具体内容。
2. **测试只检查文件存在。** 文件存在不代表内容正确。
3. **没有保存环境信息。** Bash、awk、grep 版本差异会影响复现。
4. **跳过工具却不记录。** 未安装 ShellCheck 时要明确写出 skipped。

## 练习或延伸

1. 故意把 `error_requests=5` 改成 `error_requests=4`，运行测试观察失败信息。
2. 安装 ShellCheck 后重新运行 lab，比较 transcript 中的变化。
3. 给 `path_latency.tsv` 增加一个测试断言。

## 参考资料

- GNU Bash：[Invoking Bash](https://www.gnu.org/software/bash/manual/html_node/Invoking-Bash.html)
- ShellCheck：[ShellCheck Wiki](https://www.shellcheck.net/wiki/)
- ShellCheck：[SC2086](https://www.shellcheck.net/wiki/SC2086)

{% endraw %}
