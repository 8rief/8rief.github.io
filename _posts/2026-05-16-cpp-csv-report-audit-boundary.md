---
layout: post
title: "C++ CSV 报告：把文件明细做成可打开、可审计的表格"
date: 2026-05-16 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, csv, report, teaching]
---

## 学习目标

这一篇讲 CSV 明细报告。读完以后，你应该能说明：

1. 为什么 JSON 汇总之外还需要 CSV 明细；
2. 如何用标准库输出简单、稳定的 CSV；
3. 哪些字段适合放进表格，哪些字段应该留在 JSON。

## 先修知识

需要知道 CSV 是按行和列组织的文本格式，适合表格工具打开。当前样例文件名不包含逗号，所以可以用最小输出；真实项目要补充转义。

## 为什么需要 CSV 审计报告

JSON 很适合表达层级结构，但人类排查明细时经常需要排序、筛选和逐行核对。文件索引器的 summary 只能告诉你总共有 3 个文件、304 字节、7 行和 45 个词；它不能直接回答“哪个文件贡献了最多单词”或“某个文件的行数为什么改变”。

CSV 把每个 `FileEntry` 展开成一行，读者可以用表格工具、`cut`、`sort` 或脚本检查。它是审计边界，不承担复杂对象表达。

这个边界能让报告职责变清楚。JSON 负责机器接口和完整结构，CSV 负责扁平明细和人工检查。后续如果字段增加，先判断这个字段是否适合逐行比较，再决定放进 CSV。


## 核心模型

JSON 负责结构，CSV 负责明细表。

![C++ CSV 审计边界](/assets/diagrams/cpp-csv-report-audit-boundary.svg)

读者在浏览器或表格工具里打开 CSV，可以逐行核对每个文件的 bytes、lines、words。

## 逐步实现

CSV 写入函数很短：

```cpp
output << "path,bytes,lines,words\n";
for (const auto& entry : result.files) {
    output << entry.path << ',' << entry.bytes << ','
           << entry.lines << ',' << entry.words << '\n';
}
```

实验输出是：

```text
path,bytes,lines,words
intro.txt,91,2,13
network.md,92,2,15
notes.txt,121,3,17
```

CSV 的主要价值是让明细可以排序、筛选、导入。比如按 `words` 排序，能马上看到哪个样例文件内容最多。

测试只检查 CSV header 和文件存在还不够。这个 lab 至少验证 header 稳定，CLI smoke 又把真实输出写入 transcript。后续可以继续检查每一行的字段数。

## 输出怎么读

CSV 第一行是 schema：

```text
path,bytes,lines,words
```

后面的每一行对应一个 `FileEntry`。以 `notes.txt,121,3,17` 为例：`path` 是相对路径，`bytes` 是文件大小，`lines` 是逐行读取次数，`words` 是按空白切出的词数。

读 CSV 时先检查三件事。

1. header 是否完全等于预期，避免下游脚本读错列。
2. 行数是否等于 JSON 里的 `summary.files`。
3. 数值累计是否等于 JSON 里的 summary。

可以用最小命令做一次人工核对：

```bash
awk -F, 'NR>1 {files++; bytes += $2; lines += $3; words += $4} END {print files, bytes, lines, words}' reports/index.csv
```

预期结果应接近：

```text
3 304 7 45
```

当前样例文件名没有逗号和换行，所以最小输出足够教学。真实项目要按 RFC 4180 处理双引号、逗号、换行和编码问题。


## 什么时候继续扩展 CSV

CSV 字段不要随着内部结构无限增加。判断一个字段是否应该进入 CSV，可以问三个问题。

1. 这个字段能否被表格工具逐行排序或筛选？
2. 这个字段是否来自单个文件，而不是跨文件汇总？
3. 这个字段是否足够稳定，适合作为下游脚本输入？

例如 `path`、`bytes`、`lines`、`words` 都满足这些条件。`summary.files` 是汇总字段，已经可以从 CSV 行数推导，放进每一行会产生重复。

如果后续要加入 `extension`，CSV 会更方便筛选：

```text
path,extension,bytes,lines,words
intro.txt,.txt,91,2,13
```

对应测试也要升级：除了检查 header，还要检查每一行字段数和扩展名值。

## 常见错误

1. **把嵌套对象硬塞进 CSV**：复杂结构应放 JSON，CSV 保持扁平。
2. **报告里写绝对路径**：相对路径更适合公开 demo 和跨机器复现。
3. **不说明 CSV 转义边界**：当前样例安全，但真实文件名含逗号时要使用成熟 CSV 库或完整转义。

## 练习或延伸

- 增加一个文件名含逗号的测试样例，然后修复 CSV 转义。
- 把 CSV 输出改成按 `words` 降序，说明排序规则应在 README 里写清楚。

## 参考资料

- [RFC 4180: Common Format and MIME Type for CSV Files](https://www.rfc-editor.org/rfc/rfc4180)
- [std::ofstream](https://en.cppreference.com/w/cpp/io/basic_ofstream)
- [C++ string streams](https://en.cppreference.com/w/cpp/io/basic_istringstream)
