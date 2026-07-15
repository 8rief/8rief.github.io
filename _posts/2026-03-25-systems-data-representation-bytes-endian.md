---
layout: post
title: "数据表示第一课：bytes、整数宽度和 endian"
date: 2026-03-25 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从二进制文件和网络字段的解释问题出发，用一个 uint32_t 的四个字节讲清整数宽度、有符号解释和机器字节序。"
tags: [systems, data-representation, c, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/computer-systems-os-foundations/README.md`](/assets/labs/computer-systems-os-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：计算机系统 / 数据表示 / bytes  
> 本文实验已验证：`uint32_t` 大小为 `4` byte；当前环境观察到 little-endian 为 `true`。

先看一个很实际的问题：你从文件里读到 4 个 byte，内容是 `78 56 34 12`。它到底表示整数 `0x78563412`，还是 `0x12345678`？如果另一个程序把同样 4 个 byte 当成有符号整数，又会不会变成负数？

数据表示就是为了解决这个问题。计算机内存里保存的是 byte；“整数”“字符”“图片像素”“网络包字段”都是程序附加在 byte 上的解释规则。只要解释规则没有写清楚，跨语言、跨机器、跨文件格式就会出错。

## 这篇文章要解决什么

1. byte、bit、整数宽度分别是什么，为什么二进制协议不能只写 `int`。
2. `0x12345678` 这个数在内存里为什么可能按 `78 56 34 12` 排列。
3. 同一串 bit 按 `uint32_t` 和 `int32_t` 解释时，为什么数值范围不同。
4. 写文件格式或网络协议时，应该固定哪些规则，避免“在我机器上能跑”的隐患。

## 为什么要引入 byte、宽度和 endian

只在一个程序内部计算时，很多细节被编译器和运行时隐藏了。问题出现在边界处：

- **文件边界**：程序 A 写入 4 个 byte，程序 B 以后读取。B 不知道 A 当时用的是几 byte 整数、什么 byte 顺序，就无法稳定还原。
- **网络边界**：两台机器可能有不同字节序。协议必须规定字段宽度和顺序，否则包能收到，值却会被读错。
- **语言边界**：C、Python、Go、Java 都能处理整数，但默认类型、溢出规则、序列化方式不同。

所以我们需要三个基本词：

- **bit**：最小二进制位，只能是 0 或 1。
- **byte**：通常是 8 bit，是内存和文件里最常用的寻址/读写单位。
- **整数宽度**：这个整数占多少 bit，例如 `uint32_t` 固定占 32 bit，即 4 byte。
- **endianness**：多 byte 数值放入连续内存时，最高有效 byte 和最低有效 byte 的排列顺序。

## 机制图：数学值、内存 byte、解释规则

![数据表示第一课：bytes、整数宽度和 endian](/assets/diagrams/systems-data-representation-bytes-endian.svg)

把 `0x12345678` 拆成 4 个 byte，可以写成：

```text
数学书写：0x12 34 56 78
最高有效 byte：0x12
最低有效 byte：0x78
```

在 little-endian 机器上，低地址先放最低有效 byte，所以内存从低地址到高地址看起来是：

```text
地址递增方向：  +0    +1    +2    +3
内存内容：     78    56    34    12
```

在 big-endian 机器上，低地址先放最高有效 byte，内存顺序会是：

```text
地址递增方向：  +0    +1    +2    +3
内存内容：     12    34    56    78
```

注意这里有三层对象：

1. **数学值**：`0x12345678`，十进制是 `305419896`。
2. **内存 byte**：连续 4 个可观察 byte。
3. **解释规则**：把这 4 个 byte 按 unsigned、signed、little-endian 或 big-endian 解释。

很多 bug 的根源就是把这三层混成一层。

## 可复现实验

实验包里有一个最小 C 程序。你可以在实验目录运行：

```bash
bash run_lab.sh
```

单独看数据表示部分，核心代码是：

```c
uint32_t value = 0x12345678U;
unsigned char *bytes = (unsigned char *)&value;
bool little = bytes[0] == 0x78U;
int32_t negative_one = -1;

printf("data_uint32_decimal=%" PRIu32 "
", value);
printf("data_byte0_hex=%02x
", bytes[0]);
printf("data_little_endian=%s
", little ? "true" : "false");
printf("data_signed_minus_one_as_uint32=%" PRIu32 "
", (uint32_t)negative_one);
printf("data_uint32_size=%zu
", sizeof(uint32_t));
```

这段代码故意只做一件事：把一个 32 bit 整数的地址转成 `unsigned char *`，逐 byte 观察内存。C 语言允许用 character type 查看对象表示，这很适合作为入门实验。

## 输出怎么读

本次实验输出摘录：

```text
data_uint32_decimal=305419896
data_byte0_hex=78
data_little_endian=true
data_signed_minus_one_as_uint32=4294967295
data_uint32_size=4
```

逐行解释：

- `data_uint32_decimal=305419896`：`0x12345678` 的十进制值。这个值本身不说明内存顺序。
- `data_byte0_hex=78`：对象起始地址处的第一个 byte 是 `0x78`。因为 `0x78` 是最低有效 byte，所以当前机器表现为 little-endian。
- `data_little_endian=true`：程序用 `bytes[0] == 0x78` 得到的判断。
- `data_signed_minus_one_as_uint32=4294967295`：`-1` 的 32 bit 补码表示全是 1，按无符号 32 bit 解释就是 `2^32 - 1`。
- `data_uint32_size=4`：`uint32_t` 固定 32 bit，所以是 4 byte。写协议时应优先用这种固定宽度类型描述字段。

## 状态变化：从值到 byte

以 little-endian 环境为例，状态变化可以这样看：

```text
1. 源码写下 value = 0x12345678U
2. 编译器知道 value 是 uint32_t，占 4 byte
3. 运行时把 value 放到某个地址 A
4. A+0 保存 0x78，A+1 保存 0x56，A+2 保存 0x34，A+3 保存 0x12
5. unsigned char* 从 A 开始逐 byte 读取，所以 bytes[0] 是 0x78
```

如果你把这些 byte 写进文件，再让另一个程序读取，就必须把第 4 步的规则写进文件格式。否则对方只能猜。

## 实际开发里怎么用

设计一个二进制记录时，可以这样明确格式：

```text
magic:       4 bytes, ASCII "QLOG"
version:     1 byte, unsigned
item_count:  4 bytes, uint32, little-endian
payload_len: 4 bytes, uint32, little-endian
payload:     payload_len bytes
```

然后读取代码就不应该直接把文件内容强转成结构体，因为结构体可能有 padding、对齐和本机 endian 问题。更稳妥的做法是逐 byte 组装：

```c
uint32_t read_u32_le(const unsigned char b[4]) {
    return ((uint32_t)b[0]) |
           ((uint32_t)b[1] << 8) |
           ((uint32_t)b[2] << 16) |
           ((uint32_t)b[3] << 24);
}
```

这段代码把 little-endian 写成了显式规则，不依赖当前机器的默认字节序。

## 常见错误

1. **把十六进制书写顺序当内存顺序。** `0x12345678` 是人读的数值写法；内存第一个 byte 在 little-endian 上是 `78`。
2. **协议里写 `int` 而不写宽度。** `int` 的大小和溢出行为涉及语言和平台；协议字段应写 `uint32`、`int64` 这类明确宽度。
3. **把 signed 和 unsigned 混用后只看输出。** `-1` 转成 `uint32_t` 得到 `4294967295` 并不神秘，是同一串 bit 换了数值范围。
4. **直接序列化结构体内存。** 结构体 padding、对齐、endianness 都可能让文件在另一台机器上读错。
5. **用一次本机实验推断所有机器。** 本文实验说明当前环境是 little-endian，不代表所有架构都如此。

## 练习

1. 把实验里的 `0x12345678` 改成 `0x01020304`，先预测 `bytes[0]`，再运行验证。
2. 写一个 `read_u32_be`，让 byte 顺序 `12 34 56 78` 被解释成 `0x12345678`。
3. 设计一个 12 byte 的二进制头部，写清每个字段的宽度、endianness 和含义。

## 参考资料

- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- cppreference：[Fixed width integer types](https://en.cppreference.com/w/c/types/integer)
- CS:APP Labs：[Data Lab](https://csapp.cs.cmu.edu/3e/labs.html)

{% endraw %}
