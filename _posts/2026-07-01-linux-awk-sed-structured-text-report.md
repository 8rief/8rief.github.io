---
layout: post
title: "awk 和 sed 实战：从半结构化文本生成可读报告"
date: 2026-07-01 09:35:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 key=value 日志解释 awk 的字段处理、聚合统计和 sed 的轻量文本转换。"
tags: [linux, awk, sed, text-processing, teaching]
---
{% raw %}
> 主题：Linux CLI 与 Shell 自动化 / awk / sed / structured text
> 本文 lab 已验证：`path_latency.tsv` 中 `/jobs/payment` 的平均延迟为 `570.0`。

`grep` 适合回答“哪些行匹配”。当问题变成“每个状态码多少次”“每条路径平均耗时多少”，就需要按字段解析和聚合。`awk` 的优势正好在这里：逐行读取文本，按规则抽字段、计算、输出。`sed` 更适合做轻量替换、删除和格式调整。

## 学习目标

1. 用 `awk` 从 `key=value` 日志中抽取字段。
2. 用关联数组做分组计数和平均值。
3. 知道 `sed` 适合流式替换，不适合承载复杂业务逻辑。

## 先修知识

已经会用 `grep` 过滤行，用 `sort | uniq -c` 做简单计数。

## 核心模型

![awk sed 文本报告流程](/assets/diagrams/linux-awk-sed-report-flow.svg)

`awk` 面向记录和字段：每行是一条记录，每个字段都能被拆开并参与计算。`sed` 面向流式编辑：读一行、按规则改写、输出一行。

## 可信资料的关键结论

- GNU awk 手册把 awk 描述为 pattern-action 语言：匹配记录后执行动作，直到输入结束。
- GNU sed 手册把 sed 定义为 stream editor：对输入流做基本文本转换，适合管道中的轻量编辑。
- 实战中，涉及分组、求和、平均值时优先考虑 awk；涉及简单替换、删除、格式清理时考虑 sed。

## 逐步实现

状态码计数的核心 awk：

```bash
awk '
{
  delete f
  for (i = 1; i <= NF; i++) {
    split($i, kv, "=")
    f[kv[1]] = kv[2]
  }
  status[f["status"]]++
}
END {
  for (s in status) print s "\t" status[s]
}
' reports/all.log | sort -k2,2nr -k1,1
```

每行先拆成 `key=value`，再把字段放进数组 `f`。`END` 块在所有输入处理完后输出汇总。

平均延迟的版本多了两个数组：

```bash
latency[path] += f["latency_ms"] + 0
count[path]++
```

运行后查看：

```bash
cat reports/path_latency.tsv
```

预期第一行：

```text
/jobs/payment	570.0	2
```

`sed` 可以做输出整理，例如把制表符换成更适合阅读的分隔符：

```bash
sed 's/\t/  /g' reports/status_counts.tsv
```

这类转换不改变统计逻辑，只改变展示。

## 常见错误

1. **把 awk 写成难读的一行。** 学习阶段用多行脚本，先保证可解释。
2. **忘记清理每行字段数组。** `delete f` 可以避免上一行字段残留。
3. **把 sed 用成通用编程语言。** 复杂聚合交给 awk、Python 或数据库更清楚。
4. **排序键写错。** `sort -k2,2nr` 表示按第二列数值倒序。

## 练习或延伸

1. 在 `service_level_counts.tsv` 基础上，找出错误最多的 service。
2. 修改 awk，让 `path_latency.tsv` 额外输出最大延迟。
3. 用 sed 把 `status_counts.tsv` 转成 Markdown 表格的前两列。

## 参考资料

- GNU awk：[The GNU Awk User's Guide](https://www.gnu.org/software/gawk/manual/gawk.html)
- GNU awk：[Getting Started](https://www.gnu.org/software/gawk/manual/html_node/Getting-Started.html)
- GNU sed：[sed manual](https://www.gnu.org/software/sed/manual/sed.html)
- man7：[sed(1)](https://man7.org/linux/man-pages/man1/sed.1.html)

{% endraw %}
