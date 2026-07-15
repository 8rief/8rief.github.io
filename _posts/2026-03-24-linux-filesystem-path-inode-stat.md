---
layout: post
title: "Linux 文件系统：路径、目录项、inode 和 stat 怎么连起来"
date: 2026-03-24 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从路径名进入文件系统，用目录项和 inode 理解 ls、find、stat 看到的元数据。"
tags: [linux, filesystem, inode, stat, teaching]
---
{% raw %}

> 主题：操作系统与 Linux 基础 / 文件系统模型
> 本文是 OS/Linux 进程与文件基础包的第一篇。实验只在本地 lab 自己创建的文件中进行。

很多人学 Linux 文件系统时先背 `ls` 参数，遇到问题却不知道该看路径、权限、文件类型还是挂载点。更稳的起点是把一次文件访问拆成三件事：路径名被逐段解析，目录把名字映射到文件对象，inode 保存对象的元数据。这样再看 `ls -li`、`stat` 和 `find`，输出就不再是零散字段。

## 学习目标

1. 区分路径字符串、目录项和 inode 元数据。
2. 解释 `ls -li`、`stat`、`find` 分别在观察什么。
3. 理解为什么同名文件移动后路径变了，但文件对象的元数据有连续性。
4. 识别 WSL、网络盘或特殊挂载点可能带来的权限显示差异。

## 先修知识

需要会进入目录、运行命令、阅读普通文本文件。本文不要求了解文件系统实现源码。

## 为什么需要路径与 inode 模型

构建脚本报“文件不存在”时，有几种完全不同的原因：当前工作目录错了，路径某一段没有搜索权限，符号链接的目标消失，或文件在检查后被重命名。只反复运行 `ls` 很难区分这些情况。

路径解析模型把问题拆成可验证的状态：从起点目录出发，逐段查目录项，最终到达一个文件对象。inode 号、文件类型和链接数帮助我们判断两个路径是否指向同一对象，以及一次重命名是否真的换了文件。

## 核心模型

![路径、目录项和 inode 模型](/assets/diagrams/linux-filesystem-path-inode-stat.svg)

路径是给人和程序使用的名字序列。目录保存名字到文件对象的映射。inode 记录文件类型、权限位、链接数、所有者、大小、时间戳和数据块位置等元数据。`stat` 主要展示 inode 相关信息，`ls` 把目录遍历和部分元数据压缩成一行，`find` 则沿目录树递归枚举路径。

## 逐步实现

先创建一组受控文件：

```bash
mkdir -p workspace/files workspace/logs
printf 'alpha one\nalpha two\n' > workspace/files/alpha.txt
printf 'beta one\nbeta two\nbeta three\n' > workspace/files/beta.txt
printf 'INFO login user=alice\n' > workspace/logs/events.log
```

观察目录项和 inode 号：

```bash
ls -li workspace/files
```

本地 transcript 中输出类似：

```text
1407374884264694 -rwxrwxrwx 1 brief brief 20 Jun 28 00:04 alpha.txt
1407374884264695 -rwxrwxrwx 1 brief brief 29 Jun 28 00:04 beta.txt
```

第一列是 inode 号，最后一列是当前目录项里的名字。中间的权限、链接数、用户、组、大小和时间来自文件元数据。inode 号只在对应文件系统的上下文中有意义，不能当作跨机器或跨文件系统的稳定标识。文章只关心同一轮观察中的字段关系。

再用 `stat` 展开一个文件：

```bash
stat -c '%n inode=%i type=%F mode=%A uid=%u gid=%g size=%s' \
  workspace/files/alpha.txt workspace/logs/events.log
```

输出示例：

```text
workspace/files/alpha.txt inode=1407374884264694 type=regular file mode=-rwxrwxrwx uid=1000 gid=1000 size=20
workspace/logs/events.log inode=1407374884264696 type=regular file mode=-rwxrwxrwx uid=1000 gid=1000 size=135
```

如果你在 WSL 的 Windows 挂载目录下实验，权限位可能来自挂载策略，和普通 Linux 文件系统上的创建权限存在差异。`stat` 展示的是当前挂载层呈现的元数据，所以解释结果时要同时看文件系统和挂载选项。

再用硬链接和同文件系统内重命名验证“名字”与“对象”的区别：

```bash
cp workspace/files/alpha.txt workspace/files/link-source.txt
ln workspace/files/link-source.txt workspace/files/link-alias.txt
stat -c 'inode=%i links=%h name=%n' workspace/files/link-*.txt
mv workspace/files/link-source.txt workspace/files/renamed.txt
stat -c 'inode=%i links=%h name=%n' \
  workspace/files/renamed.txt workspace/files/link-alias.txt
```

两次 `stat` 中，同一轮实验的两个路径应有相同 inode 号，`links=2`。`mv` 改变了一个目录项的名字，另一个硬链接仍然指向原对象。这个结论限定在同一文件系统；跨文件系统移动通常需要复制后删除，对象身份会变。

可能看到的输出形状如下，inode 数字以实际系统为准：

```text
inode=<same-number> links=2 name=workspace/files/renamed.txt
inode=<same-number> links=2 name=workspace/files/link-alias.txt
```

## 如何解释输出

看到一行文件信息时，建议按顺序读：

1. 文件类型：普通文件、目录、符号链接、设备文件的操作语义不同。
2. inode 号：同一文件系统内用于识别文件对象。
3. 权限和所有者：决定访问控制的第一层信息。
4. 大小和时间戳：用于判断数据是否符合预期。
5. 路径名：只是当前观察入口，不等同于文件对象本身。

这个顺序能帮助你在构建、日志、配置文件问题中先定位对象，再判断权限或内容。

`stat` 的输出是一次快照。读取元数据后，另一个进程可以立即重命名或替换路径指向的对象。因此对安全性或并发性要求高的程序，应尽量对已打开的文件描述符执行后续操作，避免把“先检查路径，再按路径打开”误当成一个原子步骤。

## 常见错误

1. **把路径当成文件对象。** 路径是入口，同一个文件对象可能通过硬链接有多个名字。
2. **只看文件名，不看文件类型。** 目录、普通文件和符号链接的行为不同。
3. **忽略挂载点。** WSL 的 `/mnt/c`、容器卷、网络盘可能让权限和时间戳表现不同。
4. **把 inode 当作跨机器稳定 ID。** inode 只在具体文件系统上下文中有意义。

## 练习或延伸

1. 对同一个文件运行 `stat` 和 `ls -li`，标出哪些字段对应。
2. 用 `find workspace -maxdepth 3 -type f -print` 枚举路径，再对每个路径运行 `stat`。
3. 在 Linux 原生目录和 WSL `/mnt/c` 目录分别创建文件，比较权限位差异。

## 参考资料

- Linux man-pages：[path_resolution(7)](https://man7.org/linux/man-pages/man7/path_resolution.7.html)
- Linux man-pages：[inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html)
- GNU coreutils：[stat invocation](https://www.gnu.org/software/coreutils/manual/html_node/stat-invocation.html)

{% endraw %}
