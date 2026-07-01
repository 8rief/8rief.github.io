---
layout: post
title: "管道入门：用 grep、sort、uniq、wc 把日志变成问题答案"
date: 2026-07-01 09:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 16 行日志里数出错误请求、状态码分布和最常见结果。"
tags: [linux, pipe, grep, coreutils, teaching]
---
{% raw %}
> 主题：Linux CLI 与 Shell 自动化 / pipe / grep / sort / uniq / wc
> 本文 lab 已验证：`manual_error_count=5`，状态码 `200` 出现 8 次。

文本管道解决的问题很朴素：已有一堆文本，想快速回答一个具体问题。先不要写完整程序，先让每条命令只做一个小转换，然后用管道把转换串起来。

## 学习目标

1. 理解标准输出如何进入下一条命令的标准输入。
2. 用 `grep` 过滤行，用 `sort | uniq -c` 计数，用 `wc -l` 数行。
3. 能从日志中得到错误数和状态码分布。

## 先修知识

读完上一篇，已经知道命令有工作目录、输入、输出和退出状态。

## 核心模型

![文本管道把日志转成统计结果](/assets/diagrams/linux-cli-pipe-grep-sort-uniq.svg)

管道适合线性问题：过滤、抽取、排序、聚合、展示。每一步都能单独运行和检查，这让命令行调试比一上来写大脚本更容易。

## 可信资料的关键结论

- GNU grep 手册的核心行为是按模式查找匹配行；默认输出匹配行。
- GNU Coreutils 中 `sort` 负责排序，`uniq` 只合并相邻重复行，所以通常先 `sort` 再 `uniq -c`。
- `wc -l` 数的是换行分隔的行数，适合统计日志记录数。

## 逐步实现

完整 lab 已经把日志放在 `.lab_tmp/logs/`。先看总行数：

```bash
wc -l .lab_tmp/logs/*.log
```

预期输出：

```text
8 .lab_tmp/logs/app 2026-07-02.log
8 .lab_tmp/logs/app-2026-07-01.log
16 total
```

过滤错误日志：

```bash
grep -h ' level=ERROR ' .lab_tmp/logs/*.log
```

`-h` 的作用是多个文件输入时不显示文件名前缀，后续统计更干净。数错误行：

```bash
grep -h ' level=ERROR ' .lab_tmp/logs/*.log | wc -l
```

预期是 `5`。接着统计状态码：

```bash
awk '{ for (i=1; i<=NF; i++) { split($i, kv, "="); if (kv[1] == "status") print kv[2] } }' .lab_tmp/logs/*.log \
  | sort \
  | uniq -c \
  | sort -k1,1nr -k2,2
```

预期结果的第一行是：

```text
8 200
```

这条管道从日志中抽出 status 值，排序，让相同值相邻，再计数。最后一次排序按计数倒序输出。

## 常见错误

1. **忘记 `sort` 直接用 `uniq -c`。** `uniq` 只处理相邻重复行，输入不排序会漏计。
2. **模式太宽。** `ERROR` 可能出现在路径或用户字段里，用 ` level=ERROR ` 更明确。
3. **管道太长后无法调试。** 每加一段就运行一次，确认中间输出符合预期。
4. **把管道当成脚本替代品。** 管道适合探索；可复用、可测试的流程应收进脚本。

## 练习或延伸

1. 把 `level=ERROR` 改成 `status=500`，数出 500 错误数量。
2. 把状态码统计命令拆成 3 次运行，每次只增加一段管道，观察输出变化。

## 参考资料

- GNU grep：[GNU grep manual](https://www.gnu.org/software/grep/manual/grep.html)
- GNU Coreutils：[sort invocation](https://www.gnu.org/software/coreutils/manual/html_node/sort-invocation.html)
- GNU Coreutils：[uniq invocation](https://www.gnu.org/software/coreutils/manual/html_node/uniq-invocation.html)
- GNU Coreutils：[wc invocation](https://www.gnu.org/software/coreutils/manual/html_node/wc-invocation.html)

{% endraw %}
