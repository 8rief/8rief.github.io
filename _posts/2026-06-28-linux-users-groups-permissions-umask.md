---
layout: post
title: "用户、用户组和权限位：从 chmod 到 umask 的基础模型"
date: 2026-06-28 00:05:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 user/group/other、rwx、chmod 和 umask 建立 Linux 文件权限的第一层模型。"
tags: [linux, permissions, chmod, umask, teaching]
---
{% raw %}

> 主题：操作系统与 Linux 基础 / 权限模型
> 本文是 OS/Linux 进程与文件基础包的第五篇。实验不需要 root，不修改系统目录。

Linux 权限模型的第一层并不复杂：每个进程带着用户和用户组身份，每个文件有所有者、所属组和权限位。读取、写入、执行是否允许，先由这些基础身份和位决定。学清这一层，后续再看 ACL、capability、容器用户映射才有支点。

## 学习目标

1. 解释 user、group、other 三组权限位。
2. 读懂 `-rwxr-x---` 这类符号权限。
3. 区分 `chmod` 修改已有权限和 `umask` 影响新文件默认权限。
4. 识别 WSL Windows 挂载目录上的权限显示差异。

## 先修知识

需要知道文件有所有者和权限，知道 `ls -l` 会显示文件详情。

## 核心模型

![Linux 权限和 umask 模型](/assets/diagrams/linux-users-groups-permissions-umask.svg)

权限字符串第一位表示文件类型，后九位分成三组：所有者、所属组、其他用户。每组三位分别表示读、写、执行。`chmod` 改变已有文件模式，`umask` 在创建新文件时屏蔽默认权限位。

## 逐步实现

先看当前身份：

```bash
id
```

输出会包含 uid、gid 和附加组。文件访问时，内核会结合进程凭据和文件元数据做判断。

再看一个普通文件：

```bash
ls -l workspace/files/alpha.txt
stat -c '%A %a %U %G %n' workspace/files/alpha.txt
```

`%A` 是符号权限，`%a` 是八进制权限。八进制更适合脚本和精确记录，符号权限更适合人工阅读。

lab 中的 `umask` 实验在 Linux `/tmp` 文件系统中创建文件：

```text
Requested mode 0o666 with umask 0o027 produced 0o640
```

这个结果来自按位屏蔽：普通文件默认请求 `666`，`umask 027` 会去掉组的写权限和其他用户的全部权限，得到 `640`。同一轮 lab 还记录了工作区路径的显示权限。如果工作区在 WSL 的 Windows 挂载目录下，可能显示为 `777`，这说明挂载层在呈现权限位，不适合作为 `umask` 教学证据。

## 如何解释权限字符串

以 `-rw-r-----` 为例：

1. `-` 表示普通文件。
2. `rw-` 表示所有者可读写。
3. `r--` 表示所属组只读。
4. `---` 表示其他用户没有权限。

目录的执行位表示能否穿过目录访问其中名字；普通文件的执行位表示能否作为程序执行。两者含义不同。

## 常见错误

1. **把 `777` 当成方便默认值。** 它扩大了写入和执行范围，也会掩盖权限设计问题。
2. **忽略目录执行位。** 文件本身可读，但父目录不可进入时，仍然访问不了。
3. **混淆 `chmod` 和 `umask`。** 前者改已有文件，后者影响后续创建。
4. **在特殊挂载点上验证权限规则。** 学习权限位时优先用 Linux 原生文件系统目录。

## 练习或延伸

1. 在 `/tmp` 下创建一个文件，分别用 `chmod 600`、`chmod 640`、`chmod 755` 观察变化。
2. 设置 `umask 077` 后创建文件，解释结果为什么更收紧。
3. 对目录和普通文件分别去掉执行位，比较访问行为。

## 参考资料

- Linux man-pages：[chmod(1)](https://man7.org/linux/man-pages/man1/chmod.1.html)
- Linux man-pages：[umask(2)](https://man7.org/linux/man-pages/man2/umask.2.html)
- Linux man-pages：[credentials(7)](https://man7.org/linux/man-pages/man7/credentials.7.html)

{% endraw %}
