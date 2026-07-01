---
layout: post
title: "数据表示第一课：bytes、整数宽度和 endian"
date: 2026-07-01 21:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个 uint32_t 的四个字节解释整数宽度、有符号解释和机器字节序。"
tags: [systems, data-representation, c, teaching]
---
{% raw %}
> 主题：计算机系统 / 数据表示 / bytes
> 本文 lab 已验证：`uint32_t` 大小为 `4` byte；当前环境观察到 little-endian 为 `true`。

程序处理的整数、字符、图片和网络消息最终都会落到 byte。学习数据表示的目标是知道同一段 byte 在不同解释规则下会变成什么。

## 学习目标

1. 解释 byte、bit、整数宽度和 endian 的关系。
2. 观察 `uint32_t` 在内存中的 byte 顺序。
3. 区分数值、二进制表示和有符号解释。
4. 知道为什么跨文件、网络和二进制协议时必须固定格式。

## 先修知识

需要会运行一个 C 程序，知道十六进制的 `0x` 前缀表示法。没有 C 基础也可以先把代码当成可观察实验。

## 核心模型

![数据表示第一课：bytes、整数宽度和 endian](/assets/diagrams/systems-data-representation-bytes-endian.svg)

一个 `uint32_t` 有 32 bit，也就是 4 byte。数值 `0x12345678` 写在纸上是一种数学值；放进内存后，四个 byte 的排列顺序由机器字节序决定。同样的 32 bit 若按 `int32_t` 或 `uint32_t` 解释，得到的数值也可能不同。

## 逐步实现

最小实验代码：

```c
uint32_t value = 0x12345678U;
unsigned char *bytes = (unsigned char *)&value;
printf("byte0=%02x\n", bytes[0]);
```

本次 lab 输出摘录：

```text
data_uint32_decimal=305419896
data_byte0_hex=78
data_little_endian=true
data_signed_minus_one_as_uint32=4294967295
```

`byte0_hex=78` 说明当前机器把最低有效 byte 放在低地址处。`-1` 转成 `uint32_t` 后显示为 `4294967295`，说明同一串 bit 可以被解释成不同数值范围。

## 常见错误

1. **把十六进制文本当内存顺序。** `0x12345678` 是书写形式，内存第一个 byte 可能是 `78`。
2. **忽略整数宽度。** `int` 在不同平台上可能有差异，二进制协议要用固定宽度类型。
3. **把 signed overflow 当普通数学。** C 里有符号整数溢出有严格边界，工程代码应避免依赖它。
4. **文件格式不写 endian。** 文件和网络数据需要约定 byte order，不能依赖本机默认。

## 练习或延伸

把 `0x12345678` 改成 `0x01020304`，预测 `byte0` 的值，再运行 lab 验证。然后解释为什么网络协议常规定固定 byte order。

## 参考资料
- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- cppreference：[Fixed width integer types](https://en.cppreference.com/w/c/types/integer)
- CS:APP Labs：[Data Lab](https://csapp.cs.cmu.edu/3e/labs.html)

{% endraw %}
