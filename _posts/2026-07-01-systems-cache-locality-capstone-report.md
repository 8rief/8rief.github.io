---
layout: post
title: "结课项目：用 locality 测量生成系统证据报告"
date: 2026-07-01 21:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把前面的系统观察合成一个报告，用 row-major 和 column-major 扫描看见缓存局部性。"
tags: [systems, cache, performance, capstone, teaching]
---
{% raw %}
> 主题：计算机系统 / cache locality / capstone
> 本文 lab 已验证：row-major 扫描耗时 `858687` ns，column-major 扫描耗时 `14639785` ns，本次比值约 `17.049`。

系统基础最终要落到证据。一个程序变慢，原因可能在算法复杂度、I/O、锁竞争、内存分配，也可能在缓存局部性。本文用矩阵扫描做一个小结课项目：同样的数据、同样的求和结果，只改变访问顺序，观察耗时差异。

## 学习目标

1. 理解 locality 为什么影响性能。
2. 用 `clock_gettime` 记录明确测量边界。
3. 同时保存 metrics、report、SVG 和 transcript。
4. 把系统实验整理成可复查证据包。

## 先修知识

需要理解数组按连续内存存放，也需要知道一次性能数字会受机器、负载和编译选项影响。

## 核心模型

![结课项目：用 locality 测量生成系统证据报告](/assets/diagrams/systems-cache-locality-capstone-report.svg)

row-major 扫描顺着 C 数组的内存布局连续访问，column-major 扫描跨行跳跃。两种方式求和结果相同，访问局部性不同。

## 逐步实现

核心循环：

```c
for (int i = 0; i < n; i++) {
    for (int j = 0; j < n; j++) {
        row_sum += matrix[i * n + j];
    }
}
```

对比循环：

```c
for (int j = 0; j < n; j++) {
    for (int i = 0; i < n; i++) {
        col_sum += matrix[i * n + j];
    }
}
```

运行完整 lab：

```bash
bash run_lab.sh
```

可展示产物：

```text
reports/metrics.json
reports/report.md
reports/transcript.txt
reports/systems_flow.svg
reports/memory_process_fd.svg
reports/cache_locality.svg
```

本次输出摘录：

```text
cache_matrix_n=1024
cache_row_major_ns=858687
cache_column_major_ns=14639785
cache_column_to_row_ratio=17.049
cache_sums_equal=true
systems_os_status=ok
```

比值是当前环境的观察结果，不能脱离机器和负载边界外推。真正可复查的是：输入规模、编译命令、计时边界、原始 metrics 和 transcript 都被保留下来。

## 常见错误

1. **只报告性能数字。** 没有输入规模和环境，数字无法解释。
2. **让编译器优化掉循环。** lab 使用汇总值保留计算路径。
3. **把一次测量当普遍规律。** 性能结论应保留机器和负载边界。
4. **只留图，不留数据。** 图应由 metrics 生成，transcript 应能复跑。

## 练习或延伸

把矩阵大小改成 256、512、2048，记录比值变化。再解释为什么 cache、TLB 和内存带宽都会影响结果。

## 参考资料
- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- Linux man-pages：[clock_gettime(2)](https://man7.org/linux/man-pages/man2/clock_gettime.2.html)
- CS:APP Labs：[Cache Lab](https://csapp.cs.cmu.edu/3e/labs.html)

{% endraw %}
