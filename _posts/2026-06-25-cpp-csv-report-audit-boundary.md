---
layout: post
title: "C++ CSV 报告：把文件明细做成可打开、可审计的表格"
date: 2026-06-25 21:03:00 +0800
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

## 核心模型

JSON 负责结构，CSV 负责明细表。

![C++ CSV 审计边界](/assets/diagrams/cpp-csv-report-audit-boundary.svg)

读者在浏览器或表格工具里打开 CSV，可以逐行核对每个文件的 bytes、lines、words。

## 逐步实现

CSV 写入函数很短：

```cpp
output << "path,bytes,lines,words
";
for (const auto& entry : result.files) {
    output << entry.path << ',' << entry.bytes << ','
           << entry.lines << ',' << entry.words << '
';
}
```

实验输出是：

```text
path,bytes,lines,words
intro.txt,91,2,13
network.md,92,2,15
notes.txt,121,3,17
```

CSV 的价值不在于表达复杂层级，而在于让明细可以排序、筛选、导入。比如按 `words` 排序，能马上看到哪个样例文件内容最多。

测试只检查 CSV header 和文件存在还不够。这个 lab 至少验证 header 稳定，CLI smoke 又把真实输出写入 transcript。后续可以继续检查每一行的字段数。

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
