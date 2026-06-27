---
layout: post
title: "Linux 进程模型：程序文件、PID、父子进程和 /proc"
date: 2026-06-28 00:03:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从可执行文件到运行中的进程，用 ps 和 /proc 观察 PID、PPID、状态和命令名。"
tags: [linux, process, procfs, ps, teaching]
---
{% raw %}

> 主题：操作系统与 Linux 基础 / 进程模型
> 本文是 OS/Linux 进程与文件基础包的第三篇。实验只观察当前 shell 和 lab 创建的短生命周期进程。

一个程序文件放在磁盘上时只是数据；运行之后，内核为它创建进程，分配 PID、地址空间、文件描述符表、环境和调度状态。很多命令行问题本质上都是进程问题：程序是否启动，父进程是谁，当前状态是什么，打开了哪些文件，为什么结束。

## 学习目标

1. 区分可执行文件、进程和命令行文本。
2. 解释 PID、PPID、进程状态和命令名。
3. 用 `ps` 和 `/proc/<pid>/status` 观察当前进程。
4. 建立 `fork`、`exec`、`wait` 的基本心智模型。

## 先修知识

需要会运行 shell 命令，知道一个命令会启动程序。

## 核心模型

![程序文件到 Linux 进程模型](/assets/diagrams/linux-process-pid-proc-ps.svg)

shell 读入命令后，通常创建子进程，子进程再用目标程序替换自己的程序映像。父进程可以等待子进程结束并读取退出状态。`/proc` 是内核暴露进程和系统状态的伪文件系统，`ps` 等工具会读取这些状态并整理成人能读的表格。

## 逐步实现

观察当前 shell：

```bash
ps -o pid,ppid,stat,comm -p $$
```

本地 transcript 中类似：

```text
    PID    PPID STAT COMMAND
2038474 1952450 Ss   bash
```

`PID` 是当前 shell 的进程号，`PPID` 是父进程号，`STAT` 表示状态，`COMMAND` 是命令名。`S` 常见于可中断睡眠，`s` 表示会话首进程。

lab 程序也读取了自己的 `/proc/<pid>/status`：

```text
Name:	python3
State:	R (running)
Pid:	2038547
PPid:	2038474
Threads:	1
```

这说明 `/proc` 中的文件是内核根据当前进程状态生成的视图。进程结束后，对应的 `/proc/<pid>` 目录通常也会消失。

## 从命令到进程

当你输入：

```bash
python3 src/system_observer.py --workspace workspace --outdir reports
```

可以按四步理解：

1. shell 解析命令行，找到 `python3`。
2. shell 创建子进程。
3. 子进程执行 Python 解释器，参数传入 `argv`。
4. 父进程等待或继续执行，取决于是否放到后台。

真实系统调用细节会因 shell 和平台而异，但这个模型足以解释大多数脚本和服务启动问题。

## 常见错误

1. **把命令名当作唯一身份。** 同一个命令可以同时有多个进程，PID 才是一次运行的身份。
2. **忘记父进程。** 子进程继承环境、工作目录和部分文件描述符，这些都来自父进程的启动上下文。
3. **把 `/proc` 当普通目录备份。** 它是内核视图，内容随进程和系统状态变化。
4. **只看是否有输出。** 没有输出不代表进程没运行，要结合 `ps`、日志和退出码判断。

## 练习或延伸

1. 运行 `sleep 30 & echo $!`，用 `ps -p <pid>` 观察后台进程。
2. 查看 `/proc/$$/status` 中的 `Name`、`State`、`Pid`、`PPid`。
3. 用 `pstree -p $$` 观察当前 shell 附近的父子关系，如果系统安装了 `pstree`。

## 参考资料

- Linux man-pages：[proc(5)](https://man7.org/linux/man-pages/man5/proc.5.html)
- Linux man-pages：[fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)
- Linux man-pages：[execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html)

{% endraw %}
