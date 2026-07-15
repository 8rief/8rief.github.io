---
layout: post
title: "用户、用户组和权限位：从 chmod 到 umask 的基础模型"
date: 2026-05-26 18:00:00 +0800
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

## 为什么需要权限与 umask

一个程序创建日志、配置或临时文件时，操作系统必须立即决定谁能读、谁能改、谁能执行。如果每次都要程序创建后再调用 `chmod`，中间会出现一个权限过宽的窗口。`umask` 用来给新对象设置进程级默认屏蔽规则，创建时就产生更窄的权限。

排查权限问题也需要这个模型。程序报 `Permission denied` 时，至少要同时核对进程的 uid/组身份、目标文件的所有者与模式位，以及路径上每一层目录的执行权限。只改最后一个文件并不一定能解决问题。

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

可以用一个最小 shell 实验复现这条状态变化：

```bash
tmp_dir=$(mktemp -d)
old_mask=$(umask)
umask 027
: > "$tmp_dir/demo.txt"
stat -c '%a %n' "$tmp_dir/demo.txt"
umask "$old_mask"
rm -rf "$tmp_dir"
```

在普通 Linux 文件系统上，关键输出应为：

```text
640 /tmp/tmp.<random>/demo.txt
```

`mktemp` 的后缀每次不同。稳定证据是第一列 `640`：所有者可读写，同组可读，其他用户无权限。脚本在结束前恢复原 `umask`，避免影响当前 shell 之后创建的文件。

## 如何解释权限字符串

以 `-rw-r-----` 为例：

1. `-` 表示普通文件。
2. `rw-` 表示所有者可读写。
3. `r--` 表示所属组只读。
4. `---` 表示其他用户没有权限。

目录的执行位表示能否穿过目录访问其中名字；普通文件的执行位表示能否作为程序执行。两者含义不同。

### 从创建请求到最终模式

可把新文件的基础计算记成 `requested_mode & ~umask`。例如 `0666 & ~0027 = 0640`。目录常以 `0777` 作为创建请求，因为目录需要执行位才能穿过；普通文件通常不默认请求执行位。应用程序还可以显式请求更窄的模式，`umask` 只负责去掉请求中的位，不会为请求补权限。

实际访问检查还受 ACL、capability、只读挂载和具体文件系统语义影响。本篇的 user/group/other 模型是排查起点，后续证据与它冲突时再查这些扩展机制。

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
