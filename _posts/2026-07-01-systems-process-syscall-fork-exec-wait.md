---
layout: post
title: "进程和系统调用：fork、exec、wait 如何把程序跑起来"
date: 2026-07-01 21:02:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用父子进程和退出码解释 program、process、PID 与系统调用边界。"
tags: [systems, process, syscall, teaching]
---
{% raw %}
> 主题：计算机系统 / 进程 / 系统调用
> 本文 lab 已验证：父进程创建子进程，子进程退出码为 `42`。

程序文件放在磁盘上，进程是正在运行的实例。Shell 输入一条命令后，系统需要创建进程、装载程序、传入参数、等待退出状态。`fork`、`exec` 和 `wait` 是理解这个过程的关键入口。

## 学习目标

1. 区分 program 和 process。
2. 理解 PID、父子进程和退出码。
3. 知道系统调用是用户程序请求内核服务的边界。
4. 能解释 Shell 为什么可以知道命令成功或失败。

## 先修知识

需要会在终端运行命令，知道退出码 0 通常表示成功。这里不要求写完整 shell。

## 核心模型

![进程和系统调用：fork、exec、wait 如何把程序跑起来](/assets/diagrams/systems-process-syscall-fork-exec-wait.svg)

`fork` 创建一个子进程，`exec` 用新的程序映像替换当前进程内容，`waitpid` 让父进程取得子进程退出状态。Shell 执行外部命令时会组合这些动作。

## 逐步实现

最小父子进程实验：

```c
pid_t child = fork();
if (child == 0) {
    _exit(42);
}
int status = 0;
waitpid(child, &status, 0);
printf("exit=%d\n", WEXITSTATUS(status));
```

lab 输出摘录：

```text
process_parent_pid_positive=true
process_child_pid_positive=true
process_child_exit_code=42
```

这个实验没有调用 `exec`，因为目标是先看清父子进程和退出状态。读懂后，可以把子进程里的 `_exit(42)` 换成 `execve` 或用 Python `subprocess.run()` 观察同一模型。

## 常见错误

1. **把程序文件和进程混为一谈。** 同一个可执行文件可以同时有多个进程实例。
2. **父进程不 wait。** 子进程退出状态需要被回收，否则会留下僵尸状态。
3. **在 fork 后重复执行父子都不该执行的代码。** `fork` 后父子都从返回点继续运行，要分支清楚。
4. **只看 stdout，不看退出码。** 自动化脚本判断成败主要依赖退出码。

## 练习或延伸

把子进程退出码改成 0、1、127，观察父进程读取到的状态。再用 Shell 运行 `false; echo $?` 对比。

## 参考资料
- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- MIT OpenCourseWare：[6.1810 Operating System Engineering](https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/)
- Linux man-pages：[fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)
- Linux man-pages：[execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html)
- Linux man-pages：[waitpid(2)](https://man7.org/linux/man-pages/man2/waitpid.2.html)

{% endraw %}
