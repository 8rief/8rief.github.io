---
layout: post
title: "环境变量和 PATH：shell 如何找到命令，子进程如何继承上下文"
date: 2026-06-28 00:04:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 env、PATH、which/type 和子进程继承实验解释命令查找与环境边界。"
tags: [linux, shell, environment, path, teaching]
---
{% raw %}

> 主题：操作系统与 Linux 基础 / 环境变量
> 本文是 OS/Linux 进程与文件基础包的第四篇。实验只设置临时环境变量，不修改 shell 配置文件。

很多“命令找不到”“脚本在终端能跑，在任务里不能跑”的问题，都和环境有关。环境变量是父进程交给子进程的一组字符串键值。`PATH` 是其中最常见的一项，它告诉 shell 和相关执行逻辑到哪些目录中查找可执行文件。

## 学习目标

1. 说明环境变量是进程启动上下文的一部分。
2. 解释 `PATH` 如何影响命令查找。
3. 区分 shell 变量、导出的环境变量和一次性命令前缀。
4. 用子进程实验验证环境继承边界。

## 先修知识

需要知道 shell 会执行命令，知道路径可以写成 `/usr/bin/python3` 这样的形式。

## 核心模型

![环境变量和 PATH 继承模型](/assets/diagrams/linux-environment-path-child-process.svg)

父进程创建子进程时，可以传入环境。子进程收到的是一份启动时的环境快照。子进程修改自己的环境不会自动反向影响父进程。`PATH` 是查找可执行文件时使用的目录列表，目录之间用冒号分隔。

## 逐步实现

先观察 `PATH`：

```bash
printf '%s\n' "$PATH" | tr ':' '\n'
type python3
command -v python3
```

`type` 是 shell 视角，可以告诉你命令是内建命令、函数、别名还是磁盘文件；`command -v` 更适合脚本中确认命令是否可用。

再做一次子进程继承实验：

```bash
OS_LAB_DEMO=visible python3 -c 'import os; print(os.environ.get("OS_LAB_DEMO"))'
```

本地 transcript 中输出：

```text
visible
```

这里的 `OS_LAB_DEMO=visible` 只作用于这一次命令启动的子进程。命令结束后，当前 shell 不会因此长期多出这个变量。

如果想让当前 shell 后续启动的子进程都看到变量，需要导出：

```bash
export OS_LAB_DEMO=visible
python3 -c 'import os; print(os.environ.get("OS_LAB_DEMO"))'
unset OS_LAB_DEMO
```

## 如何解释命令查找问题

遇到“找不到命令”时，建议按顺序检查：

1. 你输入的是命令名还是路径。
2. `type <name>` 看到的是内建、别名、函数还是文件。
3. `command -v <name>` 是否能找到可执行文件。
4. 当前执行环境的 `PATH` 是否和交互终端一致。
5. 脚本、服务、定时任务是否使用了更小的环境。

这套检查尤其适合排查 Python、Java、Go、Rust、CMake 等工具链版本不一致的问题。

## 常见错误

1. **只在交互 shell 中配置。** 服务、CI、定时任务可能不会读取你的交互配置文件。
2. **修改子进程环境后期待父进程变化。** 环境继承是向下的，不能自动向上回写。
3. **把当前目录放进 `PATH` 前面。** 这会增加误执行同名脚本的风险，学习阶段也容易混淆来源。
4. **混用 `which` 和 shell 内建语义。** `type` 更能说明 shell 实际会执行什么。

## 练习或延伸

1. 比较 `type cd`、`type python3`、`command -v python3` 的输出。
2. 在一条命令前设置临时变量，命令结束后用 `printenv` 检查是否仍存在。
3. 写一个脚本，打印 `PATH` 和 `sys.executable`，分别从终端和另一个脚本中调用。

## 参考资料

- Linux man-pages：[environ(7)](https://man7.org/linux/man-pages/man7/environ.7.html)
- Linux man-pages：[execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html)
- GNU Bash Manual：[Command Search and Execution](https://www.gnu.org/software/bash/manual/html_node/Command-Search-and-Execution.html)

{% endraw %}
