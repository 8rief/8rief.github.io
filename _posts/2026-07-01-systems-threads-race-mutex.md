---
layout: post
title: "线程同步：race、mutex 和可验证计数器"
date: 2026-07-01 21:05:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个受控 race 和一个 mutex 计数器解释共享内存并发为什么需要同步。"
tags: [systems, threads, mutex, teaching]
---
{% raw %}
> 主题：计算机系统 / 线程 / 同步
> 本文 lab 已验证：受控 race 的期望值为 `2`、实际值为 `1`；mutex 计数器得到 `200000`。

线程共享同一个进程地址空间，这让通信很方便，也让错误更隐蔽。两个线程同时读写同一个变量时，结果取决于执行交错。mutex 的作用是把关键区变成一次只允许一个线程进入的区域。

## 学习目标

1. 理解线程共享内存带来的 race 条件。
2. 用受控实验观察 lost update。
3. 用 mutex 保护共享计数器。
4. 区分“程序偶尔看起来正确”和“同步规则保证正确”。

## 先修知识

需要知道变量读写并非天然原子地完成完整业务动作。`x = x + 1` 包含读、加、写多个步骤。

## 核心模型

![线程同步：race、mutex 和可验证计数器](/assets/diagrams/systems-threads-race-mutex.svg)

race 的关键在于多个线程对同一共享状态进行无保护读改写。mutex 给关键区建立互斥边界，让读改写成为可推理的串行步骤。

## 逐步实现

受控 race 摘要：

```c
long local = shared;
barrier_wait_until_two_threads_read();
shared = local + 1;
```

两个线程都先读到 0，再各自写回 1，所以最终值小于期望值 2。

mutex 计数器摘要：

```c
pthread_mutex_lock(&lock);
counter += 1;
pthread_mutex_unlock(&lock);
```

lab 输出摘录：

```text
thread_controlled_race_expected=2
thread_controlled_race_actual=1
thread_mutex_expected=200000
thread_mutex_actual=200000
thread_mutex_correct=true
```

## 常见错误

1. **用一次运行结果证明没有 race。** 并发错误可能只在特定交错下出现。
2. **只保护写，不保护读改写整体。** `counter += 1` 需要整体放进关键区。
3. **锁范围过大。** 锁住无关工作会降低并发度。
4. **忘记错误路径释放锁。** 复杂函数应使用清晰的资源管理结构。

## 练习或延伸

把 mutex 版本改成不加锁的循环计数器，多运行几次。记录它是否每次都失败，并解释为什么“偶尔正确”仍然不能接受。

## 参考资料
- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- Linux man-pages：[pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)
- POSIX man-pages：[pthread_mutex_lock(3p)](https://man7.org/linux/man-pages/man3/pthread_mutex_lock.3p.html)

{% endraw %}
