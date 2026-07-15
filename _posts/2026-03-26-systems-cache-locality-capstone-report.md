---
layout: post
title: "结课项目：用 locality 测量生成系统证据报告"
date: 2026-03-26 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从同样 O(n^2) 的两段循环为什么速度差很多出发，用 row-major/column-major 扫描生成可复查的系统实验报告。"
tags: [systems, cache, performance, capstone, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/computer-systems-os-foundations/README.md`](/assets/labs/computer-systems-os-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：计算机系统 / cache locality / capstone  
> 本文实验已验证：row-major 扫描耗时 `872763` ns，column-major 扫描耗时 `14806693` ns，本次比值约 `16.965`。

两段代码都是双重循环，都是访问 `1024 x 1024` 个整数，算法复杂度都可以写成 `O(n^2)`。为什么一段可能明显更快？

复杂度只告诉你随着输入规模增长，大致操作次数如何变化。真实机器还关心数据怎样进入 cache、每次访问是否连续、TLB 是否频繁失效、编译器有没有优化掉循环。系统基础的结课项目应该把这些“机器层证据”收集起来，而不只给一个结论。

## 这篇文章要解决什么

1. locality 为什么会影响性能。
2. C 语言 row-major 数组布局怎样决定访问顺序。
3. `clock_gettime` 的测量边界该如何说明。
4. 怎样把实验变成可复查证据包：metrics、report、transcript、图示和测试。

## 为什么要引入 cache locality

CPU 执行加法很快，从内存拿数据相对慢。硬件 cache 利用一个经验：程序刚访问过的位置，附近位置很可能马上也会被访问。这叫空间局部性；同一个位置短时间内再次被访问，叫时间局部性。

矩阵扫描是最适合入门的例子。C 里的二维矩阵如果用一维数组 `matrix[i * n + j]` 表示，那么同一行的元素在内存里连续：

```text
matrix[0][0], matrix[0][1], matrix[0][2], ... matrix[0][n-1], matrix[1][0], ...
```

按行扫描会顺着内存走，按列扫描会跨行跳跃。两种方式求和结果一样，访问路径完全不同。

## 机制图：同样求和，不同访问路径

![结课项目：用 locality 测量生成系统证据报告](/assets/diagrams/systems-cache-locality-capstone-report.svg)

row-major 扫描：

```text
访问 matrix[0][0], matrix[0][1], matrix[0][2] ...
内存地址连续，cache line 里的相邻数据很快被用到
```

column-major 扫描：

```text
访问 matrix[0][0], matrix[1][0], matrix[2][0] ...
每次跨过一整行，cache line 里的相邻元素可能还没用就被替换
```

这就是“复杂度相同，实际耗时不同”的一个具体来源。

## 可复现实验

运行完整实验：

```bash
bash run_lab.sh
```

row-major 核心循环：

```c
for (int r = 0; r < repeat; r += 1) {
    for (int i = 0; i < n; i += 1) {
        for (int j = 0; j < n; j += 1) {
            row_sum += matrix[(size_t)i * (size_t)n + (size_t)j];
        }
    }
}
```

column-major 对比循环：

```c
for (int r = 0; r < repeat; r += 1) {
    for (int j = 0; j < n; j += 1) {
        for (int i = 0; i < n; i += 1) {
            col_sum += matrix[(size_t)i * (size_t)n + (size_t)j];
        }
    }
}
```

计时边界使用 `clock_gettime(CLOCK_MONOTONIC, ...)`：

```c
uint64_t row_start = now_ns();
/* row-major loop */
uint64_t row_ns = now_ns() - row_start;
```

实验还把 `row_sum + col_sum` 写入 `volatile` 全局变量，避免编译器判断结果无用后直接删除循环。

## 输出怎么读

本次输出摘录：

```text
cache_matrix_n=1024
cache_row_major_ns=872763
cache_column_major_ns=14806693
cache_column_to_row_ratio=16.965
cache_sums_equal=true
systems_os_status=ok
```

解释如下：

- `cache_matrix_n=1024`：矩阵规模是 `1024 x 1024`。
- `cache_row_major_ns=872763`：按行扫描在本次环境下耗时约 0.87 ms。
- `cache_column_major_ns=14806693`：按列扫描耗时约 14.81 ms。
- `cache_column_to_row_ratio=16.965`：本次按列扫描约为按行扫描的 16.965 倍。
- `cache_sums_equal=true`：两种访问顺序求出的和一致，说明比较的是访问路径，不是计算目标变化。
- `systems_os_status=ok`：整套系统实验和测试通过。

这个比值不是普遍常数。CPU、cache 层级、内存带宽、编译选项、系统负载、矩阵大小都会改变它。教学重点是建立测量方法和解释链条。

## 状态变化：从代码到证据包

一个合格的小型系统实验至少要留下这些材料：

```text
1. 输入和参数：n=1024，repeat=6，编译器版本，平台信息
2. 源代码：两段循环的唯一区别是访问顺序
3. 原始输出：stdout 中的 metrics
4. 结构化数据：reports/metrics.json
5. 人类可读报告：reports/report.md
6. 复跑记录：reports/transcript.txt
7. 图示：解释流程、内存访问路径、关键指标
8. 测试：至少检查关键指标存在和逻辑关系成立
```

本文实验已生成这些可展示产物：

```text
reports/metrics.json
reports/report.md
reports/transcript.txt
reports/systems_flow.svg
reports/memory_process_fd.svg
reports/cache_locality.svg
```

有了证据包，别人才能判断你的结论是否来自同一份代码、同一组参数和同一个测量边界。

## 如何写性能结论

不要写：

```text
column-major 慢 16.965 倍，所以它总是慢 16.965 倍。
```

应该写：

```text
在本次 WSL2/Linux 环境、n=1024、repeat=6、当前编译设置下，column-major 扫描耗时约为 row-major 的 16.965 倍。两者求和结果一致，主要差异来自内存访问局部性。这个数字需要在目标机器和目标数据规模上重新测量。
```

这类表述保留了可复查边界，也给后续优化留出了空间。

## 常见错误

1. **只报告性能数字。** 没有输入规模、编译参数和环境，数字无法解释。
2. **让编译器优化掉循环。** 如果结果完全不用，优化器可能删除计算路径。
3. **把一次测量当普遍规律。** 性能结论必须带机器、负载和参数边界。
4. **只留图，不留原始数据。** 图应该能从 metrics 重新生成，transcript 应能复跑。
5. **忽略正确性检查。** 两段代码的结果必须一致，否则速度比较没有意义。

## 练习

1. 把矩阵大小改成 `256`、`512`、`2048`，记录比值变化并解释趋势。
2. 把 `int` 改成 `double`，观察数据宽度变化对 cache 行利用率的影响。
3. 使用 `perf stat` 观察 cache miss 相关指标；如果环境不支持 perf，就记录原因，不要伪造数据。
4. 把报告整理成一页 README：问题、方法、参数、结果、限制、下一步。

## 参考资料

- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- Linux man-pages：[clock_gettime(2)](https://man7.org/linux/man-pages/man2/clock_gettime.2.html)
- CS:APP Labs：[Cache Lab](https://csapp.cs.cmu.edu/3e/labs.html)

{% endraw %}
