---
layout: post
title: "Linux CLI 入门：先把工作目录、命令和输出边界跑通"
date: 2026-03-27 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 pwd、ls、mkdir、printf、tee 和 exit status 建立命令行的最小心智模型。"
tags: [linux, cli, shell, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/linux-cli-shell-automation/README.md`](/assets/labs/linux-cli-shell-automation/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Linux CLI 与 Shell 自动化 / 工作目录 / 命令契约
> 本文 lab 已验证：生成 2 个日志文件、16 行请求记录，并输出 `report_ready=reports/summary.txt`。

很多初学者第一次打开终端时会卡在同一个地方：命令看起来像咒语，失败后不知道该看哪里。先把 CLI 看成一个简单契约：你在某个工作目录里运行一个程序，程序读取参数、文件或标准输入，写出标准输出或标准错误，最后返回一个退出状态。

## 学习目标

1. 知道 `pwd`、`ls`、`cd`、`mkdir` 解决的都是工作区定位问题。
2. 知道一个命令至少有三类结果：输出内容、写出的文件、退出状态。
3. 能运行本包 lab，并确认第一个可见结果已经生成。

## 先修知识

只需要能打开 Linux shell。WSL、Ubuntu 虚拟机、Docker 容器里的 Bash 都可以。

## 核心模型

![CLI 工作区和命令契约](/assets/diagrams/linux-cli-workspace-contract.svg)

命令行学习先分清四件事：当前位置、要运行的程序、传给程序的参数、程序产生的结果。路径错误、参数错误、输出被重定向到文件，是最常见的三个初学者问题。

## 为什么需要先学命令契约

很多 Linux 教程从一串命令开始，这对已经有经验的人很快，对零基础学习者却容易形成机械记忆。命令真正要解决的核心问题是：让一个可执行程序在一个明确上下文里完成一次可复查的动作。只要上下文不明确，后面的 `grep`、`awk`、脚本参数、重定向都会变成猜测。

本系列把每条命令都拆成五个问题：

1. 我现在在哪个目录？
2. 我要运行哪个程序？
3. 这个程序收到哪些参数？
4. 正常结果写到屏幕还是文件？
5. 失败时有没有非零退出状态和错误信息？

这五个问题能直接解释日常开发里的大多数命令行故障。比如 `cat reports/summary.txt` 失败时，先查 `pwd` 和 `ls reports`，再判断是目录错、文件没生成，还是命令本身写错。命令行不需要靠感觉排错，先把输入、输出和状态边界固定下来。

## 可信资料的关键结论

- POSIX Shell Command Language 把 shell 定义为命令语言解释器，重点是命令、参数、重定向、管道和退出状态。
- GNU Bash 手册给出 Bash 的扩展能力；写个人自动化脚本时可以用 Bash，但需要知道哪些写法不是 POSIX sh。
- GNU Coreutils 覆盖 `pwd`、`ls`、`mkdir`、`cat`、`wc` 等基础工具；这些工具组合起来构成多数命令行工作流。

## 逐步实现

先进入 lab 目录，运行：

```bash
bash run_lab.sh
```

第一段输出会告诉你当前工作区和工具版本：

```text
lab=linux-cli-shell-automation
pwd=...
bash_version=5.2.21(1)-release
grep_version=grep (GNU grep) 3.11
```

这里不要急着看脚本内部。先检查命令产生了什么：

```bash
ls reports
cat reports/summary.txt
```

预期能看到：

```text
total_requests=16
error_requests=5
slow_requests_ge_400ms=4
top_status=200	8
source_files=2
```

这就是第一个可见结果：一个自动生成的报告文件。之后所有文章都围绕这个报告继续拆开。

## 输出怎么读

这份输出可以当作一个最小报告契约来读：

- `total_requests=16` 说明输入日志一共包含 16 条请求记录。
- `error_requests=5` 说明其中 5 条带有 `level=ERROR`。
- `slow_requests_ge_400ms=4` 说明 4 条请求的 `latency_ms` 大于等于 400。
- `top_status=200	8` 说明最常见状态码是 200，出现 8 次。
- `source_files=2` 说明本次报告读取了 2 个 `.log` 文件。

把这些字段写成一行一个键值，是为了让人和脚本都能读。人可以直接打开文件确认结果；测试脚本可以搜索 `total_requests=16` 这样的稳定标记。后面做脚本质量检查时，这些字段会成为回归测试的断言。

如果想确认退出状态，运行：

```bash
bash run_lab.sh
echo $?
```

输出 `0` 表示脚本正常结束。非零值通常表示某条命令失败、参数缺失、文件不存在或测试没有通过。

## 一个最小排错顺序

如果你跟着运行却没有看到报告，按这个顺序排查：

```bash
pwd
ls
ls scripts reports
bash run_lab.sh
echo $?
```

第一步确认工作目录，第二步确认仓库文件存在，第三步确认脚本和报告目录是否存在，第四步重新运行，最后一步读退出状态。这个顺序看起来慢，但它把“不知道哪里错了”压缩成几个明确问题。

## 常见错误

1. **不知道自己在哪个目录。** 先用 `pwd`，再用 `ls` 看当前文件。
2. **把屏幕输出当成唯一结果。** 很多命令的真正产物是写到文件里的报告。
3. **忽略退出状态。** 自动化脚本靠退出状态判断下一步能不能继续。
4. **复制命令时漏掉路径。** 初学阶段建议每次都确认输入文件和输出目录。

## 练习或延伸

1. 修改 `scripts/generate_logs.sh`，再增加一行 `level=ERROR` 日志，重新运行 lab，观察 `error_requests` 是否变化。
2. 运行 `bash scripts/report.sh .lab_tmp/logs reports`，比较直接跑报告脚本和跑完整 `run_lab.sh` 的区别。

## 参考资料

- POSIX：[Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)
- GNU Bash：[Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html)
- GNU Coreutils：[Coreutils Manual](https://www.gnu.org/software/coreutils/manual/coreutils.html)

{% endraw %}
