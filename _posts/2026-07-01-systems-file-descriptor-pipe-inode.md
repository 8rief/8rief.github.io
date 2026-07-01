---
layout: post
title: "文件描述符：open、read、write、pipe 和 inode 边界"
date: 2026-07-01 21:03:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把文件、管道和 inode 放在同一个实验里，解释 fd 是进程访问 I/O 的句柄。"
tags: [systems, file-descriptor, filesystem, teaching]
---
{% raw %}
> 主题：计算机系统 / 文件描述符 / 文件系统
> 本文 lab 已验证：文件写入 `8` byte、读回 `8` byte，pipe 传回消息 `pipe-ok`。

Linux 把文件、管道、终端和 socket 都放进统一的 I/O 模型里。进程拿到的是一个小整数文件描述符，它指向内核维护的 I/O 对象。理解 fd 后，重定向、管道和网络连接会变得一致。

## 学习目标

1. 理解 fd 是进程内的 I/O 句柄。
2. 用 `open/read/write` 观察普通文件的字节边界。
3. 用 `pipe` 观察内核缓冲区如何连接写端和读端。
4. 区分路径名和 inode 所代表的文件对象。

## 先修知识

需要知道 Shell 中的 `>`、`|` 是重定向和管道。本文把它们还原成系统调用层面的模型。

## 核心模型

![文件描述符：open、read、write、pipe 和 inode 边界](/assets/diagrams/systems-file-descriptor-pipe-inode.svg)

fd 是进程表里的索引，指向内核维护的打开文件描述。普通文件背后有 inode，pipe 背后是内核缓冲区。`read` 和 `write` 面对的都是 byte 流。

## 逐步实现

文件读写摘要：

```c
int fd = open("fd-demo.txt", O_CREAT | O_TRUNC | O_RDWR, 0644);
write(fd, "systems\n", 8);
lseek(fd, 0, SEEK_SET);
read(fd, buffer, sizeof(buffer));
```

pipe 摘要：

```c
int pipefd[2];
pipe(pipefd);
write(pipefd[1], "pipe-ok", 7);
read(pipefd[0], buffer, sizeof(buffer));
```

lab 输出摘录：

```text
fd_file_bytes_written=8
fd_file_bytes_read=8
fd_file_inode_positive=true
fd_pipe_bytes_read=7
fd_pipe_message=pipe-ok
```

## 常见错误

1. **忘记检查 `read/write` 返回值。** 返回值才说明真实读写了多少 byte。
2. **把路径当文件身份。** 路径是目录项，inode 更接近文件对象身份。
3. **pipe 写端不关闭。** 读端可能一直等不到 EOF。
4. **把文本行当系统调用边界。** `read` 和 `write` 处理 byte，行是上层约定。

## 练习或延伸

把 pipe 的写端关闭语句删除，观察读端行为。再用 Shell 写一条 `printf 'a\n' | wc -c`，解释它背后的 fd 连接。

## 参考资料
- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- Linux man-pages：[open(2)](https://man7.org/linux/man-pages/man2/open.2.html)
- Linux man-pages：[read(2)](https://man7.org/linux/man-pages/man2/read.2.html)
- Linux man-pages：[write(2)](https://man7.org/linux/man-pages/man2/write.2.html)
- Linux man-pages：[pipe(2)](https://man7.org/linux/man-pages/man2/pipe.2.html)

{% endraw %}
