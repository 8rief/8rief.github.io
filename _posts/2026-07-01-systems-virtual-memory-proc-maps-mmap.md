---
layout: post
title: "虚拟内存观察：/proc/maps、mmap 和 copy-on-write"
date: 2026-07-01 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从两个进程能否使用同一地址说起，用 page、mmap、/proc/maps 和 copy-on-write 解释虚拟地址空间。"
tags: [systems, virtual-memory, mmap, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/computer-systems-os-foundations/README.md`](/assets/labs/computer-systems-os-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：计算机系统 / 虚拟内存 / mmap  
> 本文实验已验证：page size 为 `4096` byte；fork 后子进程把映射页写成 `99`，父进程仍读到 `7`。

两个进程都可以打印出类似 `0x7ffd...` 的地址。问题是：如果地址数值看起来一样，它们访问的是同一块物理内存吗？为什么一个进程崩溃通常不会把另一个进程的内存一起写坏？

虚拟内存就是为了解释这类问题的核心抽象。程序看到的是虚拟地址；内核和硬件负责把虚拟地址翻译到物理页、文件页或匿名页，并用权限位控制能读、能写、能执行。

## 这篇文章要解决什么

1. page 为什么是虚拟内存管理的基本粒度。
2. `mmap` 如何创建一段匿名可写映射。
3. `/proc/<pid>/maps` 能看到什么，不能看到什么。
4. fork 后 copy-on-write 为什么能让父子进程起初共享、写入后隔离。

## 为什么要引入虚拟内存

如果程序直接使用物理地址，会有几个严重问题：

- 程序必须知道机器当前有哪些物理内存空闲，开发难度很高。
- 一个程序可能误写另一个程序的内存，隔离性很差。
- 文件映射、按需加载、共享库、内存保护都很难统一表达。

虚拟内存把这些问题分开：

```text
程序：使用虚拟地址
CPU/MMU：按页表把虚拟地址翻译成物理位置
内核：维护页表、权限、映射来源和异常处理
```

程序员平时看到的指针值是虚拟地址。它只在当前进程的地址空间里有意义。

## 机制图：映射区间、page、COW

![虚拟内存观察：/proc/maps、mmap 和 copy-on-write](/assets/diagrams/systems-virtual-memory-proc-maps-mmap.svg)

一个进程的虚拟地址空间由很多映射区间组成：可执行文件代码段、共享库、heap、stack、匿名映射、文件映射等。`/proc/<pid>/maps` 展示的是这些区间的范围和权限，例如：

```text
address-range          perms  offset  dev   inode  pathname
00400000-00452000      r-xp   ...                 /path/to/program
...
```

`perms` 中常见字母含义：

- `r`：可读。
- `w`：可写。
- `x`：可执行。
- `p`：private，私有映射，写入时通常不影响其他进程。
- `s`：shared，共享映射，写入可能对共享者可见。

## 可复现实验

运行实验：

```bash
bash run_lab.sh
```

虚拟内存部分的核心代码：

```c
long page_size = sysconf(_SC_PAGESIZE);
int *page = mmap(NULL, (size_t)page_size,
                 PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS,
                 -1, 0);
if (page == MAP_FAILED) {
    perror("mmap");
    exit(1);
}
*page = 7;
```

这里创建的是一页匿名私有映射：

- `NULL`：让内核选择虚拟地址。
- `page_size`：映射大小按页粒度申请。
- `PROT_READ | PROT_WRITE`：允许读写。
- `MAP_PRIVATE | MAP_ANONYMOUS`：不绑定文件，私有映射。
- `-1, 0`：匿名映射不需要文件 fd 和文件偏移。

fork 后子进程写入：

```c
pid_t child = fork();
if (child == 0) {
    *page = 99;
    _exit(0);
}
waitpid(child, &status, 0);
printf("parent=%d
", *page);
```

## 输出怎么读

本次输出摘录：

```text
vm_page_size=4096
vm_mmap_initial_value=7
vm_cow_child_value=99
vm_cow_parent_value=7
vm_cow_parent_unchanged=true
```

逐行解释：

- `vm_page_size=4096`：当前环境页大小是 4096 byte。很多映射和保护操作按页对齐。
- `vm_mmap_initial_value=7`：父进程在匿名映射页里写入初始值 7。
- `vm_cow_child_value=99`：子进程 fork 后把自己看到的那页写成 99。
- `vm_cow_parent_value=7`：父进程等待子进程结束后，自己仍然读到 7。
- `vm_cow_parent_unchanged=true`：私有映射的写入隔离成立。

这不是说 fork 时一定立刻复制了整页。更准确的理解是：父子进程起初可以共享物理页；当其中一方写入时，内核通过页表和缺页异常为写入方准备副本。这就是 copy-on-write。

## 状态变化：一次 COW 写入

```text
1. 父进程 mmap 一页匿名私有映射，写入 7
2. fork 创建子进程，父子虚拟地址空间看起来都有这段映射
3. 内核把相关页标记为适合 COW 的状态
4. 子进程执行 *page = 99，触发写入路径
5. 内核给子进程准备独立物理页或独立页表映射
6. 子进程读到 99，父进程仍读到 7
```

入门时不要把 COW 想成“fork 立即复制所有内存”。现代系统这样做会太慢，也浪费内存。COW 的价值就在于推迟复制，直到真的发生写入。

## 如何观察 /proc/maps

你可以让程序暂停，然后在另一个终端查看：

```bash
cat /proc/<pid>/maps | head
```

观察时重点看三列：

1. 地址区间：这段虚拟地址从哪里到哪里。
2. 权限：是否可读、可写、可执行，是 private 还是 shared。
3. pathname：映射来自可执行文件、共享库、heap、stack，还是匿名区域。

`maps` 能告诉你虚拟地址布局，不会直接告诉你物理地址。普通用户程序通常也不应该依赖物理地址。

## 常见错误

1. **把虚拟地址当物理地址。** 程序打印出的指针值属于当前进程地址空间，不是裸物理位置。
2. **以为 fork 后所有写入都互相可见。** 私有映射和普通进程内存通常通过 COW 隔离写入。
3. **只看 malloc，不看 maps。** `malloc` 可能使用 heap，也可能通过 `mmap` 获取大块内存；`maps` 能看到更完整的区间。
4. **忽略页大小和对齐。** `mprotect`、`mmap` 等操作常按 page 粒度工作。
5. **把 private/shared 权限理解成变量级别。** 共享与私有通常是映射和页级别的概念，不是某个 C 变量自带的属性。

## 练习

1. 在程序中打印 `page` 地址，再运行时查看 `/proc/<pid>/maps`，找到它落在哪个区间。
2. 把 `MAP_PRIVATE` 改成文件相关映射，比较 private 和 shared 写入行为。
3. 用 `mprotect` 把一页改成只读，然后尝试写入，观察程序如何失败。

## 参考资料

- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- MIT OpenCourseWare：[6.1810 Operating System Engineering](https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/)
- Linux man-pages：[mmap(2)](https://man7.org/linux/man-pages/man2/mmap.2.html)
- Linux man-pages：[/proc/pid/maps](https://man7.org/linux/man-pages/man5/proc_pid_maps.5.html)

{% endraw %}
