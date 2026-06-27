---
layout: post
title: "文本处理流水线：用 grep、awk、sort、uniq 把日志变成报告"
date: 2026-06-28 00:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从一份本地日志出发，拆解过滤、投影、排序、聚合和报告生成的命令流水线。"
tags: [linux, text-processing, grep, awk, pipeline, teaching]
---
{% raw %}

> 主题：操作系统与 Linux 基础 / 文本流水线
> 本文是 OS/Linux 进程与文件基础包的第七篇。实验只处理 lab 创建的本地日志。

Linux 命令行强大的地方不在单个命令参数多，而在于小工具之间有稳定的数据边界：文本进来，文本出去，错误走 `stderr`。把过滤、投影、排序、聚合拆开，很多临时分析任务就能在不写完整程序的情况下完成，并且可以保存为可复现命令。

## 学习目标

1. 把文本处理拆成过滤、投影、排序、聚合四步。
2. 解释 `grep`、`awk`、`sort`、`uniq -c` 在流水线中的职责。
3. 理解为什么聚合前常常需要排序。
4. 生成一份可复查的本地统计结果。

## 先修知识

需要理解标准输入输出和管道。建议先阅读本系列第二篇。

## 核心模型

![文本处理流水线模型](/assets/diagrams/linux-text-pipeline-grep-awk-sort.svg)

每一步只做一件事：`grep` 过滤行，`awk` 选择字段或计算，`sort` 把相同键放到一起，`uniq -c` 统计相邻重复项。这样拆分后，任何一步出错都可以单独打印中间结果检查。

## 逐步实现

lab 日志内容类似：

```text
INFO checkout user=alice
WARN retry user=bob
INFO checkout user=alice
ERROR timeout user=carol
INFO login user=bob
WARN retry user=bob
```

统计日志级别：

```bash
grep -E '^(INFO|WARN|ERROR)' workspace/logs/events.log \
  | awk '{print $1}' \
  | sort \
  | uniq -c
```

本地 transcript 得到：

```text
      1 ERROR
      3 INFO
      2 WARN
```

统计用户字段：

```bash
awk '{print $3}' workspace/logs/events.log | sort | uniq -c
```

输出：

```text
      2 user=alice
      3 user=bob
      1 user=carol
```

这里 `uniq -c` 只统计相邻重复行，所以前面要先 `sort`。如果直接对原始日志运行 `uniq -c`，同一个用户分散在不同位置时不会被合并。

## 如何检查流水线

调试流水线时不要一次盯着最终结果。可以逐段截断：

```bash
grep -E '^(INFO|WARN|ERROR)' workspace/logs/events.log

grep -E '^(INFO|WARN|ERROR)' workspace/logs/events.log | awk '{print $1}'

grep -E '^(INFO|WARN|ERROR)' workspace/logs/events.log | awk '{print $1}' | sort
```

每一段都应该有明确含义。中间结果正确，最终聚合才有解释价值。

## 常见错误

1. **聚合前没有排序。** `uniq` 只合并相邻重复项。
2. **字段假设没有写清楚。** `awk '{print $3}'` 默认按空白切分，日志格式变化会影响结果。
3. **把错误输出混进数据。** 诊断信息进入管道会污染统计。
4. **命令不可复现。** 临时敲出的命令应保存到脚本或报告，方便以后重跑。

## 练习或延伸

1. 修改日志，增加一个新用户，重新运行两条统计命令。
2. 用 `awk '{print $2}'` 统计动作字段，如 `checkout`、`retry`、`login`。
3. 把最终结果重定向到 `reports/log-summary.txt`，并记录生成命令。

## 参考资料

- GNU grep Manual：[grep Programs](https://www.gnu.org/software/grep/manual/grep.html)
- GNU Awk User's Guide：[Getting Started with awk](https://www.gnu.org/software/gawk/manual/gawk.html)
- GNU coreutils：[sort invocation](https://www.gnu.org/software/coreutils/manual/html_node/sort-invocation.html)

{% endraw %}
