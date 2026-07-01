---
layout: post
title: "内存布局：stack、heap、global 和对象生命周期"
date: 2026-07-01 21:01:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从三个变量的地址和生命周期出发，解释栈、堆、全局区各自解决的问题。"
tags: [systems, memory, c, teaching]
---
{% raw %}
> 主题：计算机系统 / 内存布局 / 生命周期
> 本文 lab 已验证：stack、heap、global 三类对象地址不同，heap 对象需要显式释放。

内存错误经常来自生命周期判断失败：局部变量已经离开作用域，堆对象忘记释放，全局状态被多个函数共享。学习内存布局，是为了让对象“在哪里、活多久、谁负责释放”变成可检查的问题。

## 学习目标

1. 区分 stack、heap、global 三类常见存储位置。
2. 理解局部变量、`malloc` 对象和全局变量的生命周期。
3. 观察地址差异只用于建立直观模型，不把具体地址当稳定结果。
4. 为后续虚拟内存、线程共享状态和调试 sanitizer 做准备。

## 先修知识

需要知道 C 里的局部变量、全局变量和 `malloc/free`。如果还不熟悉，可以先关注输出里的“distinct”检查。

## 核心模型

![内存布局：stack、heap、global 和对象生命周期](/assets/diagrams/systems-memory-layout-stack-heap.svg)

栈适合函数调用期间的临时对象，堆适合需要跨函数或动态大小的对象，全局区适合整个程序生命周期都存在的状态。虚拟地址空间把这些区域映射成进程能看到的地址。

## 逐步实现

实验代码摘要：

```c
static int global_value = 17;
int stack_value = 23;
int *heap_value = malloc(sizeof(*heap_value));
*heap_value = 29;
```

lab 输出摘录：

```text
memory_stack_value=23
memory_heap_value=29
memory_global_value=17
memory_stack_heap_distinct=true
memory_heap_global_distinct=true
```

输出不公布具体地址，因为地址会受 ASLR、系统和运行时影响。我们只验证不同存储区确实是不同对象，并把生命周期责任讲清楚。

## 常见错误

1. **返回局部变量地址。** 局部变量离开函数后生命周期结束。
2. **`malloc` 后忘记 `free`。** 堆对象需要明确释放或交给 RAII/智能指针管理。
3. **把全局变量当省事工具。** 全局状态会增加测试和并发推理难度。
4. **把地址大小当内存大小。** 地址只是位置标识，不等于对象占用空间。

## 练习或延伸

新增一个 `static` 局部变量，打印它和全局变量、普通局部变量的地址关系。解释它的生命周期和可见性分别是什么。

## 参考资料
- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- MIT OpenCourseWare：[6.1810 Operating System Engineering](https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/)

{% endraw %}
