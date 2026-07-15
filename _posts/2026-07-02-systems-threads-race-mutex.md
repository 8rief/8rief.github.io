---
layout: post
title: "线程同步：race、mutex 和可验证计数器"
date: 2026-07-02 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从两个线程各加一次却只得到 1 的实验出发，讲清共享内存、读改写、race condition 和 mutex。"
tags: [systems, threads, mutex, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/computer-systems-os-foundations/README.md`](/assets/labs/computer-systems-os-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：计算机系统 / 线程 / 同步  
> 本文实验已验证：受控 race 的期望值为 `2`、实际值为 `1`；mutex 计数器得到 `200000`。

`counter += 1` 看起来像一个动作，但机器执行时至少要读出旧值、计算新值、写回内存。两个线程同时做这件事时，期望值是 2，结果却可能只剩 1。

这不是玄学，也不是“电脑偶尔抽风”。它说明多个执行流共享同一块内存时，读改写必须有同步规则。线程带来的是共享内存的便利，以及共享状态的责任。

## 这篇文章要解决什么

1. 线程和进程在内存共享上的核心区别。
2. 为什么 `x = x + 1` 不是天然安全的并发操作。
3. race condition 如何由执行交错造成。
4. mutex 保护的到底是变量、代码，还是一段状态转换。

## 为什么要引入线程和同步

进程之间默认内存隔离，通信需要 pipe、socket、共享内存等 IPC。线程则运行在同一个进程里，天然共享地址空间：

- 共享全局变量、heap 对象、打开文件等资源。
- 每个线程有自己的栈和寄存器上下文。
- 切换成本通常比进程低，适合并发处理 I/O、后台任务、并行计算。

共享内存让通信变简单：一个线程写入对象，另一个线程可以直接读取。问题是，只要两个线程同时读写同一状态，并且至少一个是写操作，就需要明确同步，否则结果取决于不可控的调度交错。

## 机制图：lost update 是怎样发生的

![线程同步：race、mutex 和可验证计数器](/assets/diagrams/systems-threads-race-mutex.svg)

假设 `shared` 初始为 0，两个线程都执行一次加一：

```text
线程 A：读 shared -> 0
线程 B：读 shared -> 0
线程 A：计算 0 + 1 -> 1
线程 B：计算 0 + 1 -> 1
线程 A：写 shared = 1
线程 B：写 shared = 1
最终 shared = 1
```

期望值是 2，实际值是 1。丢掉的一次更新叫 lost update。它的核心原因是并发程序缺少互斥边界，概率只是它在某次运行里是否暴露出来的表象。

## 可复现实验

运行实验：

```bash
bash run_lab.sh
```

为了稳定展示 race，实验先让两个线程都读到旧值，再同时写回：

```c
static volatile long controlled_shared = 0;

static void *controlled_race_thread(void *arg) {
    long local = controlled_shared;
    barrier_wait_until_two_threads_read();
    controlled_shared = local + 1;
    return NULL;
}
```

这段代码里的 barrier 只用于教学：它强行制造“两个线程都先读到 0”的交错。真实项目里的 race 往往不会这么稳定出现，所以更难排查。

mutex 版本：

```c
static long mutex_counter = 0;
static pthread_mutex_t counter_mutex = PTHREAD_MUTEX_INITIALIZER;

pthread_mutex_lock(&counter_mutex);
mutex_counter += 1;
pthread_mutex_unlock(&counter_mutex);
```

mutex 保护的重点是“读取旧值、计算新值、写回”这整个状态转换。只保护写回、不保护读取和计算，仍然可能错。

## 输出怎么读

本次输出摘录：

```text
thread_controlled_race_expected=2
thread_controlled_race_actual=1
thread_mutex_expected=200000
thread_mutex_actual=200000
thread_mutex_correct=true
```

逐行解释：

- `thread_controlled_race_expected=2`：两个线程各自加一，逻辑期望是 2。
- `thread_controlled_race_actual=1`：两个线程读到同一个旧值后分别写回，丢了一次更新。
- `thread_mutex_expected=200000`：4 个线程，每个循环 50000 次，总计应为 200000。
- `thread_mutex_actual=200000`：加锁后结果与期望一致。
- `thread_mutex_correct=true`：本次实验的同步边界足够覆盖计数器更新。

## 状态变化：mutex 做了什么

一次受保护的计数器更新可以看成：

```text
1. 线程 A 请求 lock
2. 如果锁空闲，线程 A 进入关键区
3. 线程 B 请求同一把 lock，但必须等待
4. 线程 A 完成 read -> add -> write
5. 线程 A unlock
6. 线程 B 才能进入关键区，读取 A 写入后的新值
```

mutex 不会让 CPU 指令变少，它提供的是互斥顺序。代价是等待和上下文切换，所以锁范围要覆盖必要状态转换，同时避免把无关慢操作放进去。

## 如何判断一段代码是否需要锁

问三个问题：

1. 这个状态会不会被多个线程访问？
2. 是否至少有一个线程会写它？
3. 读写组合是否需要保持不变量，例如“读旧值后写新值”“检查后插入”“余额不能为负”？

三个答案都接近“是”时，就应该设计同步策略。策略不一定非要 mutex，也可能是原子变量、读写锁、消息队列、线程封闭、不可变数据结构。但必须有策略。

## 常见错误

1. **用一次运行正确证明没有 race。** 并发错误只在特定交错下出现；没复现不代表不存在。
2. **只保护写，不保护读改写整体。** `counter += 1` 的读、加、写要作为一个状态转换保护。
3. **锁范围过大。** 把 I/O、日志、网络请求放在锁里，会让其他线程无谓等待。
4. **错误路径忘记释放锁。** C 代码要有清晰的 unlock 路径；C++ 可用 RAII 管理锁。
5. **把 volatile 当线程同步。** `volatile` 不等于互斥，也不等于完整的内存同步工具。

## 练习

1. 删除 mutex 版本里的加锁，多运行几次，记录结果是否稳定等于 200000。
2. 把线程数改成 2、8、16，观察无锁版本错误概率和性能变化。
3. 用 C11 atomic 或 C++ `std::atomic<long>` 实现计数器，对比 mutex 版本的语义和适用范围。

## 参考资料

- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- Linux man-pages：[pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)
- POSIX man-pages：[pthread_mutex_lock(3p)](https://man7.org/linux/man-pages/man3/pthread_mutex_lock.3p.html)

{% endraw %}
