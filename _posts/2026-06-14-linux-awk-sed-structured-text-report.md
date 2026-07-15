---
layout: post
title: "awk 和 sed 实战：从半结构化文本生成可读报告"
date: 2026-06-14 09:00:00 +0800
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

## 为什么需要 awk 和 sed

管道里的 `grep | sort | uniq` 能解决简单计数，但它不理解字段之间的关系。我们的日志每行都是若干 `key=value` 字段，问题一旦变成“每个 path 的平均耗时”或“每个 service 的 ERROR 数”，就需要一个能保存中间状态的工具。`awk` 用关联数组解决这个问题：用字段值作为键，把计数、求和、最大值等状态保留下来。

`sed` 的作用不同。它不适合维护复杂聚合状态，却很适合做流式文本改写，例如替换分隔符、删掉某类行、把输出整理成另一个轻量格式。把这两个工具分清楚，能避免把所有文本处理都塞进难维护的一行命令。

在本 lab 中，`awk` 负责三类状态：

1. `status[code]++`：每个状态码出现多少次。
2. `latency[path] += latency_ms` 与 `count[path]++`：每条路径的平均延迟。
3. `counts[service "\t" level]++`：每个服务和日志等级的组合数量。

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

## 输出怎么读

`path_latency.tsv` 的三列分别是路径、平均延迟和样本数。`/jobs/payment	570.0	2` 的含义是：`/jobs/payment` 出现 2 次，两次请求延迟分别是 310 ms 和 830 ms，平均值是 `(310+830)/2=570.0` ms。这个结果来自字段聚合，不是简单数行。

`status_counts.tsv` 使用同样的思路，但状态变量更简单：

```text
200	8
429	2
500	2
0	1
201	1
401	1
503	1
```

这里第一列是状态码，第二列是出现次数。`report.sh` 对它再取第一行，写入 `summary.txt` 的 `top_status=200	8`。最终摘要由同一份中间结果派生出来，避免手写统计数值。

## awk 脚本的状态变化

每处理一行日志，脚本都会临时构造一次字段表：

```text
f["service"]="api"
f["level"]="ERROR"
f["status"]="503"
f["latency_ms"]="650"
f["path"]="/api/report"
```

随后把这些字段写入长期聚合数组。`delete f` 的位置很关键：它让每一行都从空字段表开始，避免上一行残留字段污染当前记录。`END` 块只在输入全部结束后运行，因此适合输出总表和平均值。

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
