---
layout: post
title: "结课项目：做一个可复跑的本地日志报告自动化"
date: 2026-07-01 09:49:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把工作目录、管道、引用、find、awk、测试和 transcript 合成一个可展示小项目。"
tags: [linux, shell, automation, capstone, teaching]
---
{% raw %}
> 主题：Linux CLI 与 Shell 自动化 / capstone / log report
> 本文 lab 已验证：总请求 16、错误请求 5、慢请求 4、测试通过并生成 transcript。

这个结课项目把前七篇合起来：生成示例日志，手工探索问题，把管道收进脚本，安全批量处理文件，用 awk 生成统计报告，用测试和 transcript 保存证据。最终结果是一个可以展示、可以复跑、可以继续扩展的小型自动化项目。

## 学习目标

1. 从零运行一个 Shell 自动化项目并看到报告。
2. 解释每个脚本负责的边界。
3. 用测试和 transcript 证明结果可信。
4. 知道下一步如何把脚本发展成更完整的工具。

## 先修知识

建议按顺序读完本包前七篇。

## 核心模型

![Shell 自动化结课项目](/assets/diagrams/linux-shell-automation-capstone.svg)

一个可展示的自动化项目需要四层闭环：输入可生成，处理可解释，输出可阅读，验证可复跑。只要这四层稳定，后续换成真实日志、增加图表或接入 CI 都有基础。

## 可信资料的关键结论

- Bash 适合把命令行工具组合成自动化流程，但要认真处理引用、退出状态和错误边界。
- GNU Coreutils、grep、findutils、awk、sed 已经覆盖大量日常文本处理需求；先用它们构建可见结果，再判断是否需要 Python、数据库或专用日志系统。
- 自动化项目的可信度来自可复现证据：命令、输入、输出、测试和环境记录。

## 逐步实现

运行完整项目：

```bash
bash run_lab.sh
```

核心产物：

```text
reports/transcript.txt
reports/summary.txt
reports/status_counts.tsv
reports/path_latency.tsv
reports/service_level_counts.tsv
reports/batch-summary.tsv
```

`summary.txt` 是最容易展示的结果：

```text
total_requests=16
error_requests=5
slow_requests_ge_400ms=4
top_status=200	8
source_files=2
```

`batch-summary.tsv` 证明批处理能处理带空格文件名：

```text
file	lines	errors
app 2026-07-02.log	8	3
app-2026-07-01.log	8	2
```

测试结尾应出现：

```text
shell_lab_tests=ok
test_status=ok
```

这时你已经完成了一个最小但完整的 Shell 自动化项目。它的价值不在功能多，而在边界清楚：输入在哪里，脚本怎么处理，结果写到哪里，如何判断结果没有坏。

## 常见错误

1. **结课项目没有固定输入。** 没有固定输入，就很难复现和测试。
2. **只展示最终文件，不展示生成过程。** transcript 才能说明结果从哪里来。
3. **把所有逻辑塞进一个长脚本。** 当前 lab 把数据生成、报告、批处理、测试拆开，便于替换和调试。
4. **过早接入真实生产日志。** 先用合成数据验证流程，再处理真实数据的隐私和规模问题。

## 练习或延伸

1. 新增 `reports/errors_by_service.tsv`，统计每个 service 的错误数量。
2. 用 Python 读取 `path_latency.tsv` 生成一个柱状图。
3. 把 `run_lab.sh` 加进 GitHub Actions 或本地 CI，让每次修改自动运行。
4. 把输入目录改成命令行参数，让项目能处理任意日志目录。

## 参考资料

- GNU Bash：[Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html)
- GNU Coreutils：[Coreutils Manual](https://www.gnu.org/software/coreutils/manual/coreutils.html)
- GNU grep：[GNU grep manual](https://www.gnu.org/software/grep/manual/grep.html)
- GNU findutils：[Finding Files](https://www.gnu.org/software/findutils/manual/html_mono/find.html)
- GNU awk：[The GNU Awk User's Guide](https://www.gnu.org/software/gawk/manual/gawk.html)
- GNU sed：[sed manual](https://www.gnu.org/software/sed/manual/sed.html)

{% endraw %}
