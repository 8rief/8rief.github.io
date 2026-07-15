---
layout: post
title: "文件描述符：open、read、write、pipe 和 inode 边界"
date: 2026-07-01 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 Shell 管道和重定向出发，把普通文件、pipe、inode 与进程内 fd 表放到同一个 I/O 模型里。"
tags: [systems, file-descriptor, filesystem, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/computer-systems-os-foundations/README.md`](/assets/labs/computer-systems-os-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：计算机系统 / 文件描述符 / 文件系统  
> 本文实验已验证：文件写入 `8` byte、读回 `8` byte，pipe 传回消息 `pipe-ok`。

Shell 里的这条命令很普通：

```bash
printf 'hello
' | wc -c > count.txt
```

但它背后包含三个关键动作：`printf` 的标准输出被接到一个 pipe，`wc` 的标准输入从 pipe 读取，`wc` 的标准输出又被重定向到文件。进程并不知道“左边命令”“右边命令”这些 Shell 语法；它只知道自己手里有一些文件描述符。

文件描述符是 Linux I/O 模型的入口。理解它之后，普通文件、终端、pipe、socket、重定向会变成同一套语言。

## 这篇文章要解决什么

1. fd 为什么只是进程内的小整数，却能代表文件、pipe、socket。
2. `open/read/write` 如何以 byte 为边界操作普通文件。
3. `pipe` 如何把一个进程的写端连接到另一个进程的读端。
4. 路径名、目录项、inode、打开文件描述之间有什么区别。

## 为什么要引入文件描述符

程序需要访问很多 I/O 对象：磁盘文件、终端输入、网络连接、匿名管道。若每种对象都设计一套完全不同的 API，Shell 就很难统一实现重定向和管道。

Linux 的做法是把这些对象统一成“可读写的 byte 流或 byte 序列”，进程通过 fd 访问它们：

```text
进程中的 fd 表
fd 0 -> 标准输入
fd 1 -> 标准输出
fd 2 -> 标准错误
fd 3 -> open 打开的文件
fd 4 -> pipe 的读端或写端
```

fd 本身只是进程 fd 表里的索引。真正的文件偏移、访问模式、pipe 缓冲区等状态由内核维护。

## 机制图：进程 fd 表、打开文件、inode

![文件描述符：open、read、write、pipe 和 inode 边界](/assets/diagrams/systems-file-descriptor-pipe-inode.svg)

需要区分四层：

1. **路径名**：例如 `data/a.txt`，是人和程序用来定位文件的字符串。
2. **目录项**：把路径中的名字映射到 inode。
3. **inode**：文件系统里的文件对象身份，保存权限、大小、数据块位置等元数据。
4. **fd / open file description**：进程打开文件后得到的访问句柄，包含当前偏移、读写模式等运行时状态。

删除路径名不一定立刻删除数据；只要还有进程打开着对应文件，内核仍可以通过打开文件描述访问它。这就是“路径不是文件身份”的实际含义。

## 可复现实验

运行实验：

```bash
bash run_lab.sh
```

普通文件读写部分：

```c
int fd = open(".lab_tmp/fd-demo.txt", O_CREAT | O_TRUNC | O_RDWR, 0644);
const char *payload = "systems
";
ssize_t written = write(fd, payload, strlen(payload));

lseek(fd, 0, SEEK_SET);
char buffer[32] = {0};
ssize_t read_bytes = read(fd, buffer, sizeof(buffer) - 1);

struct stat st;
fstat(fd, &st);
close(fd);
```

pipe 部分：

```c
int pipefd[2];
pipe(pipefd);

write(pipefd[1], "pipe-ok", 7);
close(pipefd[1]);

char pipe_buffer[32] = {0};
ssize_t pipe_read = read(pipefd[0], pipe_buffer, sizeof(pipe_buffer) - 1);
close(pipefd[0]);
```

`pipefd[0]` 是读端，`pipefd[1]` 是写端。这个约定很重要，写反后程序不是读不到，就是直接报错。

## 输出怎么读

本次输出摘录：

```text
fd_file_bytes_written=8
fd_file_bytes_read=8
fd_file_inode_positive=true
fd_pipe_bytes_read=7
fd_pipe_message=pipe-ok
```

解释如下：

- `fd_file_bytes_written=8`：`systems
` 一共 8 个 byte，`write` 返回真实写入数量。
- `fd_file_bytes_read=8`：`lseek` 回到文件开头后，`read` 读回同样 8 个 byte。
- `fd_file_inode_positive=true`：`fstat` 能读到有效 inode 号，说明 fd 背后确实关联到文件系统对象。
- `fd_pipe_bytes_read=7`：`pipe-ok` 是 7 个 byte，不包含 C 字符串末尾的 `\0`。
- `fd_pipe_message=pipe-ok`：读端收到写端放入内核 pipe 缓冲区的内容。

重点是 `read` 和 `write` 的返回值。它们不承诺“一次调用处理完你想要的全部内容”，尤其在 socket、pipe、大文件、信号中断场景下更要写循环。

## 状态变化：一次文件读写发生了什么

```text
1. open 创建或截断文件，进程得到 fd
2. write 把 8 个 byte 从用户态缓冲区交给内核
3. 文件偏移随写入向后移动 8
4. lseek 把当前偏移重新设为 0
5. read 从当前偏移读出最多 sizeof(buffer)-1 个 byte
6. fstat 通过 fd 查询 inode 等元数据
7. close 释放当前进程持有的 fd
```

pipe 的状态变化不同：

```text
1. pipe 创建一对 fd：读端和写端
2. 写端 write，把 byte 放入内核 pipe 缓冲区
3. 关闭写端，读端在读完已有数据后能看到 EOF
4. 读端 read，取出缓冲区里的 byte
5. 关闭读端
```

如果第 3 步不关闭写端，读端可能继续等待，因为它还不能判断以后不会再有数据。

## Shell 管道如何对应到 fd

`printf 'a
' | wc -c` 可以粗略理解为：

```text
1. Shell 创建 pipe，得到 r/w 两个 fd
2. fork 第一个子进程，把它的 fd 1 复制到 pipe 写端
3. fork 第二个子进程，把它的 fd 0 复制到 pipe 读端
4. 两个子进程分别 exec printf 和 wc
5. 父进程关闭自己不需要的 pipe 端，并 wait 两个子进程
```

所以管道的本质不是 Shell 在用户态搬运字符串；内核提供 pipe 缓冲区，两个进程通过 fd 连接到这个缓冲区。

## 常见错误

1. **忘记检查 `read/write` 返回值。** 返回值才说明真实处理了多少 byte；生产代码需要处理短读、短写和错误。
2. **把路径当文件身份。** 路径是名字，inode 更接近文件对象身份，fd 是一次打开后的访问句柄。
3. **pipe 写端不关闭。** 读端可能一直等不到 EOF，程序表现为卡住。
4. **把文本行当系统调用边界。** `read` 和 `write` 处理 byte；行、JSON、消息帧都是上层协议。
5. **混淆 fd 的进程局部性。** 不同进程里的 fd 3 不一定指向同一个对象。

## 练习

1. 把 pipe 的 `close(pipefd[1])` 注释掉，观察读端是否会等待。给程序加超时，避免一直挂住。
2. 在 Shell 里运行 `printf 'a
' | wc -c`，解释 `wc` 为什么输出 2。
3. 写一个循环 `read_all(fd, buf, n)`，直到读够 n 个 byte、遇到 EOF 或出错。

## 参考资料

- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- Linux man-pages：[open(2)](https://man7.org/linux/man-pages/man2/open.2.html)
- Linux man-pages：[read(2)](https://man7.org/linux/man-pages/man2/read.2.html)
- Linux man-pages：[write(2)](https://man7.org/linux/man-pages/man2/write.2.html)
- Linux man-pages：[pipe(2)](https://man7.org/linux/man-pages/man2/pipe.2.html)

{% endraw %}
