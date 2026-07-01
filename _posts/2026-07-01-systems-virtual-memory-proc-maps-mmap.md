---
layout: post
title: "虚拟内存观察：/proc/maps、mmap 和 copy-on-write"
date: 2026-07-01 21:04:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 page size、mmap 和 fork 后写入解释进程看到的地址空间。"
tags: [systems, virtual-memory, mmap, teaching]
---
{% raw %}
> 主题：计算机系统 / 虚拟内存 / mmap
> 本文 lab 已验证：page size 为 `4096` byte；fork 后子进程把映射页写成 `99`，父进程仍读到 `7`。

进程看到的是虚拟地址空间。虚拟地址给程序一个连续、隔离的视角，内核和硬件负责把它映射到物理内存、文件或匿名页。`mmap` 和 `/proc/<pid>/maps` 是观察这个模型的直接入口。

## 学习目标

1. 理解 page 是虚拟内存管理的基本单位。
2. 使用 `mmap` 创建匿名可写映射。
3. 观察 copy-on-write 的父子进程隔离效果。
4. 知道 `/proc/<pid>/maps` 能展示地址区间和权限。

## 先修知识

需要知道进程拥有自己的地址空间，并已经理解 `fork` 会创建子进程。

## 核心模型

![虚拟内存观察：/proc/maps、mmap 和 copy-on-write](/assets/diagrams/systems-virtual-memory-proc-maps-mmap.svg)

虚拟地址空间由多个映射区间组成。`mmap` 可以创建一个匿名页。`fork` 后父子起初看起来共享内容；当子进程写入时，系统给它准备独立副本，父进程看到的值保持不变。

## 逐步实现

实验摘要：

```c
long page_size = sysconf(_SC_PAGESIZE);
int *page = mmap(NULL, page_size, PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
*page = 7;
```

fork 后子进程写入：

```c
if (fork() == 0) {
    *page = 99;
    _exit(0);
}
```

lab 输出摘录：

```text
vm_page_size=4096
vm_mmap_initial_value=7
vm_cow_child_value=99
vm_cow_parent_value=7
vm_cow_parent_unchanged=true
```

## 常见错误

1. **把虚拟地址当物理地址。** 程序打印出来的是虚拟地址。
2. **以为 fork 后所有写入都互相可见。** 私有映射会触发 copy-on-write。
3. **只看 malloc，不看 maps。** `/proc/<pid>/maps` 能看到更完整的映射区间。
4. **忽略页大小。** 内存保护和映射通常按 page 粒度工作。

## 练习或延伸

在程序运行时读取 `/proc/<pid>/maps`，找到可执行文件、heap、stack 和匿名映射。记录每段权限中的 `r/w/x` 分别表示什么。

## 参考资料
- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- MIT OpenCourseWare：[6.1810 Operating System Engineering](https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/)
- Linux man-pages：[mmap(2)](https://man7.org/linux/man-pages/man2/mmap.2.html)
- Linux man-pages：[/proc/pid/maps](https://man7.org/linux/man-pages/man5/proc_pid_maps.5.html)

{% endraw %}
