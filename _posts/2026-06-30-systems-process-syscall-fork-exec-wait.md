---
layout: post
title: "进程和系统调用：fork、exec、wait 如何把程序跑起来"
date: 2026-06-30 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 Shell 执行一条命令的过程出发，讲清 program、process、PID、系统调用、fork、exec 和 wait 的分工。"
tags: [systems, process, syscall, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/computer-systems-os-foundations/README.md`](/assets/labs/computer-systems-os-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：计算机系统 / 进程 / 系统调用  
> 本文实验已验证：父进程创建子进程，子进程退出码为 `42`。

你在 Shell 里输入：

```bash
ls -l
```

屏幕上出现文件列表后，Shell 又回到提示符。这个过程中至少发生了几件事：Shell 没有把自己变成 `ls` 后消失；`ls` 得到了参数 `-l`；命令结束后 Shell 知道它成功还是失败。

进程模型就是用来解释这件事的。程序文件在磁盘上，进程是程序运行起来后的实例。系统调用是用户程序请求内核服务的边界，`fork`、`exec`、`waitpid` 则构成了理解命令执行的最小骨架。

## 这篇文章要解决什么

1. program 和 process 的区别。
2. PID、父子进程、退出码分别解决什么问题。
3. `fork`、`exec`、`waitpid` 在 Shell 执行命令时怎样配合。
4. 为什么自动化脚本不能只看输出文本，还要检查退出码。

## 为什么要引入进程

操作系统需要同时运行很多程序，并且要隔离它们的资源。浏览器崩溃不应该直接破坏编辑器的数据；一个普通程序也不能随便读写另一个进程的内存。进程提供了几个关键能力：

- **独立地址空间**：每个进程看到自己的虚拟内存。
- **资源归属**：打开的文件、当前工作目录、环境变量、权限都挂在进程上下文上。
- **调度单位**：内核可以暂停一个进程，切换到另一个进程执行。
- **退出状态**：父进程或调用者可以知道任务如何结束。

程序文件只是静态内容。双击同一个浏览器图标两次，或从同一个可执行文件启动多个 worker，都会得到多个进程实例。

## 机制图：fork、exec、wait 的分工

![进程和系统调用：fork、exec、wait 如何把程序跑起来](/assets/diagrams/systems-process-syscall-fork-exec-wait.svg)

典型 Shell 执行外部命令的流程是：

```text
1. Shell 进程读取命令行
2. Shell 调用 fork，得到一个子进程
3. 子进程设置重定向、环境变量等执行上下文
4. 子进程调用 exec，把自己的程序映像替换成目标程序
5. 父进程 Shell 调用 waitpid，等待子进程结束并读取退出状态
6. Shell 根据退出码设置 $?，然后显示下一次提示符
```

几个词要分清：

- `fork`：复制出一个新的进程。父子进程从同一个返回点继续执行，但 `fork` 返回值不同。
- `exec`：不创建新进程，而是把当前进程的程序映像替换成另一个程序。
- `waitpid`：父进程等待指定子进程状态变化，读取退出码，并回收内核记录。

## 可复现实验

运行实验：

```bash
bash run_lab.sh
```

本文的最小实验先不调用 `exec`，只观察父子进程和退出码：

```c
pid_t child = fork();
if (child < 0) {
    perror("fork");
    exit(1);
}

if (child == 0) {
    _exit(42);
}

int status = 0;
if (waitpid(child, &status, 0) < 0) {
    perror("waitpid");
    exit(1);
}

int exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
printf("process_child_exit_code=%d
", exit_code);
```

为什么用 `_exit(42)` 而不是 `return 42`？在 fork 后的子进程里，直接 `_exit` 可以避免重复刷新父进程继承来的 stdio 缓冲区。入门阶段先记住：fork 后子进程如果只是结束，`_exit` 更贴近系统调用层面的退出。

## 输出怎么读

本次输出摘录：

```text
process_parent_pid_positive=true
process_child_pid_positive=true
process_child_exit_code=42
```

解释如下：

- `process_parent_pid_positive=true`：父进程有有效 PID。
- `process_child_pid_positive=true`：在父进程看来，`fork` 返回的子进程 PID 是正数。
- `process_child_exit_code=42`：父进程通过 `waitpid` 读到了子进程 `_exit(42)` 设置的退出码。

这三个输出对应了进程模型的三个基本事实：进程有身份，父子关系可观察，结束状态可回收。

## 状态变化：fork 后到底有几条执行路径

`fork` 之后，父子进程都从 `fork` 返回后的下一行继续执行，但返回值不同：

```text
父进程：child = 子进程 PID，进入 waitpid 分支
子进程：child = 0，进入 _exit(42) 分支
失败时：child = -1，只有原进程继续，进入错误处理
```

这就是 fork 代码容易写错的原因。你写在 `fork` 后面的普通语句，默认会被父子进程都执行，除非你用返回值把路径分开。

## exec 放在哪里

如果要把子进程变成 `/bin/echo`，子进程分支可以写成：

```c
if (child == 0) {
    execl("/bin/echo", "echo", "hello", (char *)NULL);
    _exit(127);
}
```

`execl` 成功时不会返回，因为当前进程映像已经被新程序替换。只有失败时才执行后面的 `_exit(127)`。Shell 里常见的 `127` 通常表示命令找不到或无法执行一类错误。`execl` 属于 `exec` 系列函数，底层语义见 `execve`。

## 常见错误

1. **把程序文件和进程混为一谈。** 同一个可执行文件可以对应多个运行中的进程。
2. **fork 后没有区分父子路径。** 普通代码会被父子都执行，写文件、打印、网络请求都可能重复。
3. **父进程不 wait。** 子进程退出后，退出状态需要被父进程回收，否则会暂时留下僵尸进程记录。
4. **exec 失败后继续跑子进程逻辑。** `execve` 失败要立刻处理并退出，不能让子进程误执行父进程代码。
5. **只看 stdout，不看退出码。** 自动化脚本判断成败主要靠退出码；输出文本可能为空，也可能只是日志。

## 练习

1. 把子进程退出码改成 `0`、`1`、`127`，运行后观察父进程读到的值。
2. 在 Shell 里运行 `false; echo $?` 和 `sh -c 'exit 42'; echo $?`，把结果和本文实验对上。
3. 尝试在子进程中调用 `execl("/bin/echo", "echo", "hello", NULL)`，观察 `waitpid` 读到的退出码。

## 参考资料

- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- MIT OpenCourseWare：[6.1810 Operating System Engineering](https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/)
- Linux man-pages：[fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html)
- Linux man-pages：[execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html)
- Linux man-pages：[waitpid(2)](https://man7.org/linux/man-pages/man2/waitpid.2.html)

{% endraw %}
