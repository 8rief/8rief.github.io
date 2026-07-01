---
layout: post
title: "信号和 IPC：用 SIGUSR1、pipe 组织父子进程"
date: 2026-07-01 21:06:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个父进程通知子进程、子进程通过 pipe 回复的实验解释异步事件和进程通信。"
tags: [systems, signals, ipc, teaching]
---
{% raw %}
> 主题：计算机系统 / signal / IPC
> 本文 lab 已验证：父进程发送 `SIGUSR1`，子进程通过 pipe 回复 `signal-ok`，退出码为 `0`。

进程之间默认内存隔离。要让一个进程通知另一个进程，可以使用 signal；要传递数据，可以使用 pipe、socket、共享内存等 IPC 机制。本文用最小父子进程实验把通知和数据回复分开。

## 学习目标

1. 理解 signal 是异步通知机制。
2. 使用 `sigaction` 安装简单 handler。
3. 使用 pipe 在父子进程之间传递消息。
4. 知道 signal handler 内能安全做的事情很有限。

## 先修知识

需要理解父子进程和 pipe 的基本读写模型。

## 核心模型

![信号和 IPC：用 SIGUSR1、pipe 组织父子进程](/assets/diagrams/systems-signals-ipc-parent-child.svg)

父进程等待子进程准备好，再用 `kill(pid, SIGUSR1)` 发送通知。子进程的 handler 只设置标志位，主循环醒来后通过 pipe 写回普通消息。

## 逐步实现

handler 摘要：

```c
static volatile sig_atomic_t got_usr1 = 0;
static void usr1_handler(int signo) {
    got_usr1 = 1;
}
```

父进程通知子进程：

```c
kill(child, SIGUSR1);
read(msg_pipe[0], msg, sizeof(msg));
```

lab 输出摘录：

```text
signal_ready_byte=R
signal_ipc_message=signal-ok
signal_child_exit_code=0
```

## 常见错误

1. **在 signal handler 里做复杂逻辑。** handler 应尽量短，复杂工作放回主流程。
2. **没有准备同步。** 父进程太早发 signal，子进程可能还没安装 handler。
3. **把 signal 当数据通道。** signal 适合通知，数据传输应使用 IPC。
4. **忽略子进程退出状态。** 父进程仍需 `waitpid` 回收并检查结果。

## 练习或延伸

把 `SIGUSR1` 改成 `SIGTERM`，设计一个优雅停止流程：handler 设置标志，主循环清理资源后退出。

## 参考资料
- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- MIT OpenCourseWare：[6.1810 Operating System Engineering](https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/)
- Linux man-pages：[sigaction(2)](https://man7.org/linux/man-pages/man2/sigaction.2.html)
- Linux man-pages：[kill(2)](https://man7.org/linux/man-pages/man2/kill.2.html)
- Linux man-pages：[pipe(2)](https://man7.org/linux/man-pages/man2/pipe.2.html)

{% endraw %}
