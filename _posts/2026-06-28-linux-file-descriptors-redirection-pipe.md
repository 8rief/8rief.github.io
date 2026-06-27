---
layout: post
title: "文件描述符和重定向：stdin、stdout、stderr 到底指向哪里"
date: 2026-06-28 00:02:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用受控实验解释文件描述符、标准流、重定向、dup 和 pipe 的关系。"
tags: [linux, file-descriptor, shell, pipe, teaching]
---
{% raw %}

> 主题：操作系统与 Linux 基础 / 文件描述符
> 本文是 OS/Linux 进程与文件基础包的第二篇。实验只写入 lab 目录下的临时文件。

命令行里的 `>`、`2>`、`|` 看似是 shell 语法，底层连接的是进程的文件描述符表。理解这个表之后，很多现象会变得直接：为什么 `stdout` 和 `stderr` 可以分开保存，为什么管道只连接前一个命令的输出和后一个命令的输入，为什么一个文件可以被两个描述符连续写入。

## 学习目标

1. 说明文件描述符是进程内的整数句柄。
2. 区分 `0`、`1`、`2` 对应的标准输入、标准输出、标准错误。
3. 解释 shell 重定向和管道在启动进程前做了什么。
4. 用 `dup` 示例理解两个描述符指向同一个打开文件描述的情况。

## 先修知识

需要知道进程会读写文件，知道 shell 命令可以用 `>` 保存输出。

## 核心模型

![文件描述符、重定向和管道模型](/assets/diagrams/linux-file-descriptors-redirection-pipe.svg)

进程通过文件描述符访问已经打开的对象。默认情况下，`0` 连接键盘或上游管道，`1` 连接终端或下游管道，`2` 连接终端错误输出。shell 解析重定向后，在执行程序前调整这些连接。

## 逐步实现

先把标准输出和标准错误分开：

```bash
python3 -c 'import sys; print("stdout line"); print("stderr line", file=sys.stderr)' \
  > workspace/generated/stdout.txt \
  2> workspace/generated/stderr.txt
printf 'stdout=' && cat workspace/generated/stdout.txt
printf 'stderr=' && cat workspace/generated/stderr.txt
```

本地 transcript 中看到：

```text
stdout=stdout line
stderr=stderr line
```

这说明 `>` 只改了描述符 `1`，`2>` 改了描述符 `2`。如果只写 `>`，错误信息仍会出现在终端。

再看两个描述符写同一个文件的实验。lab 程序打开一个文件，复制文件描述符，然后分别通过原描述符和副本写入：

```text
written through original fd
written through duplicated fd
```

这对应系统调用层面的 `open` 和 `dup`。复制出来的描述符沿用同一个打开文件描述，因此写入会落在同一个文件中，并共享文件偏移位置。

最后看管道：

```bash
grep -E '^(INFO|WARN|ERROR)' workspace/logs/events.log | awk '{print $1}' | sort | uniq -c
```

管道把 `grep` 的 `stdout` 接到 `awk` 的 `stdin`，再把 `awk` 的 `stdout` 接到 `sort` 的 `stdin`。每个程序只知道自己在读标准输入、写标准输出，不需要知道上下游是谁。

## 如何解释输出

读一条 shell 命令时，可以先标出数据边界：

1. 哪些内容来自标准输入。
2. 哪些内容写到标准输出。
3. 哪些诊断写到标准错误。
4. 哪一步把输出改写到文件或管道。

这个习惯能减少脚本调试中的混乱。例如测试命令失败时，应同时保存 `stderr` 和 `stdout`，再判断哪一部分属于数据、哪一部分属于诊断。

## 常见错误

1. **把 shell 语法和程序逻辑混在一起。** `>` 和 `|` 通常由 shell 处理，程序看到的是已经连接好的文件描述符。
2. **把错误输出也当普通数据处理。** 很多工具把诊断写到 `stderr`，它不应该进入数据管道。
3. **忘记追加和覆盖的区别。** `>` 会截断文件，`>>` 会追加。
4. **在复杂命令里丢失退出码。** 管道中的每个命令都可能失败，后续文章会专门讨论退出状态。

## 练习或延伸

1. 去掉 `2>` 后重复实验，观察错误输出出现在哪里。
2. 把 `>` 改成 `>>` 连续运行两次，检查文件内容。
3. 用 `cat < file` 和 `cat file` 比较标准输入和路径参数的差异。

## 参考资料

- Linux man-pages：[open(2)](https://man7.org/linux/man-pages/man2/open.2.html)
- Linux man-pages：[dup(2)](https://man7.org/linux/man-pages/man2/dup.2.html)
- GNU Bash Manual：[Redirections](https://www.gnu.org/software/bash/manual/html_node/Redirections.html)

{% endraw %}
