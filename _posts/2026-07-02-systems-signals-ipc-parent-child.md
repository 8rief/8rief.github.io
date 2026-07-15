---
layout: post
title: "信号和 IPC：用 SIGUSR1、pipe 组织父子进程"
date: 2026-07-02 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从进程间如何通知和传数据出发，用 SIGUSR1 与 pipe 区分异步事件、同步准备和普通消息传递。"
tags: [systems, signals, ipc, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/computer-systems-os-foundations/README.md`](/assets/labs/computer-systems-os-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：计算机系统 / signal / IPC  
> 本文实验已验证：父进程发送 `SIGUSR1`，子进程通过 pipe 回复 `signal-ok`，退出码为 `0`。

父进程想让子进程“现在停一下”或“该开始处理了”，可以发 signal。父进程想把一段文本、一个 JSON 或一批 byte 交给子进程，应该用 pipe、socket、共享内存等 IPC。

把 signal 当数据通道，是很多初学者会踩的坑。signal 更像门铃：它适合通知有事发生；真正要说什么，最好走清晰的数据通道。

## 这篇文章要解决什么

1. signal 为什么是异步通知机制，不适合承载复杂数据。
2. `sigaction` 安装 handler 时，handler 里应该少做什么。
3. pipe 如何负责普通消息传递。
4. 父子进程之间为什么要先同步“handler 已准备好”，再发送 signal。

## 为什么要引入 signal 和 IPC

进程之间默认内存隔离。一个进程不能直接改另一个进程的局部变量。操作系统因此提供两类能力：

- **事件通知**：告诉目标进程发生了某个事件，例如终止、用户中断、定时器、子进程状态变化。signal 属于这一类。
- **数据传输**：把 byte 从一个进程传给另一个进程，例如 pipe、socket、共享内存、消息队列。

这两类能力解决的问题不同。通知要求及时、轻量；数据传输要求有明确内容、边界、缓冲和错误处理。

## 机制图：signal 只敲门，pipe 传消息

![信号和 IPC：用 SIGUSR1、pipe 组织父子进程](/assets/diagrams/systems-signals-ipc-parent-child.svg)

本文实验使用两个 pipe：

```text
ready_pipe：子进程 -> 父进程，告诉父进程 handler 已安装
msg_pipe：  子进程 -> 父进程，收到 signal 后回复普通消息
```

流程是：

```text
1. 父进程创建 ready_pipe 和 msg_pipe
2. fork 子进程
3. 子进程安装 SIGUSR1 handler
4. 子进程向 ready_pipe 写入 'R'
5. 父进程读到 'R' 后，调用 kill(child, SIGUSR1)
6. 子进程 handler 设置标志位
7. 子进程主流程观察到标志位，通过 msg_pipe 写回 signal-ok
8. 父进程读取消息并 waitpid 回收子进程
```

第 4 步很关键。如果父进程太早发送 signal，而子进程还没安装 handler，结果可能完全不同。

## 可复现实验

运行实验：

```bash
bash run_lab.sh
```

handler 非常短，只设置一个标志位：

```c
static volatile sig_atomic_t got_usr1 = 0;

static void usr1_handler(int signo) {
    (void)signo;
    got_usr1 = 1;
}
```

子进程安装 handler 并通知父进程：

```c
struct sigaction action;
memset(&action, 0, sizeof(action));
action.sa_handler = usr1_handler;
sigemptyset(&action.sa_mask);
sigaction(SIGUSR1, &action, NULL);

write(ready_pipe[1], "R", 1);
while (!got_usr1) {
    pause();
}
write(msg_pipe[1], "signal-ok", 9);
```

父进程等待 ready，再发送 signal：

```c
char ready = 0;
read(ready_pipe[0], &ready, 1);
kill(child, SIGUSR1);
read(msg_pipe[0], msg, sizeof(msg) - 1);
waitpid(child, &status, 0);
```

## 输出怎么读

本次输出摘录：

```text
signal_ready_byte=R
signal_ipc_message=signal-ok
signal_child_exit_code=0
```

解释如下：

- `signal_ready_byte=R`：子进程已经完成 handler 安装，父进程此时发送 `SIGUSR1` 才有可预期行为。
- `signal_ipc_message=signal-ok`：signal 触发后，普通消息通过 pipe 返回。
- `signal_child_exit_code=0`：子进程正常结束，父进程用 `waitpid` 回收到了状态。

这组输出刻意把“通知”和“数据”拆开。`SIGUSR1` 不携带字符串 `signal-ok`；字符串来自 pipe。

## 状态变化：handler 为什么不能写复杂逻辑

signal 可能打断进程正在执行的任意位置。如果 handler 里调用复杂函数，可能碰到重入问题。例如主程序正在 `printf`，handler 里又 `printf`，内部锁和缓冲状态可能不安全。

所以入门阶段采用稳妥模式：

```text
handler：只设置 sig_atomic_t 标志位
主循环：看到标志位后，在正常上下文里做复杂工作
```

这就是本文代码用 `got_usr1` 的原因。

## 常见错误

1. **在 signal handler 里做复杂逻辑。** handler 应尽量短；复杂工作回到主流程处理。
2. **没有 ready 同步。** 父进程太早发 signal，子进程可能还没安装 handler。
3. **把 signal 当数据通道。** signal 适合通知，数据应通过 pipe、socket 等 IPC 传递。
4. **忽略系统调用被 signal 打断。** 真实项目要处理 `EINTR` 等中断情况。
5. **忘记回收子进程。** 父进程仍需 `waitpid` 检查退出状态。

## 练习

1. 把 `SIGUSR1` 改成 `SIGTERM`，实现“收到终止请求后清理资源再退出”。
2. 删除 ready_pipe 同步，重复运行，观察行为是否稳定，并解释为什么不可靠。
3. 把 pipe 消息改成一段带长度前缀的 payload，练习处理 read 的 byte 边界。

## 参考资料

- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- MIT OpenCourseWare：[6.1810 Operating System Engineering](https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/)
- Linux man-pages：[sigaction(2)](https://man7.org/linux/man-pages/man2/sigaction.2.html)
- Linux man-pages：[kill(2)](https://man7.org/linux/man-pages/man2/kill.2.html)
- Linux man-pages：[pipe(2)](https://man7.org/linux/man-pages/man2/pipe.2.html)

{% endraw %}
