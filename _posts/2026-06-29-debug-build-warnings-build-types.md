---
layout: post
title: "编译告警和构建类型：先让问题在编译期暴露"
date: 2026-06-29 20:01:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 -Wall、-Wextra、-Wpedantic、-Werror、Debug/Release 和 compile_commands.json 建立第一层构建诊断。"
tags: [cpp, debugging, compiler-warnings, cmake, teaching]
---
{% raw %}

> 主题：调试与构建工具基础 / compiler warnings / build types
> 本文 lab 已验证：GCC 13.3.0 使用 `-Wall -Wextra -Wpedantic -Werror` 编译通过，并生成 `compile_commands.json`。

调试的第一层，是把明显问题尽早暴露在编译期。编译告警能发现未使用变量、隐式转换、可疑分支和接口不一致；构建类型决定是否带调试符号、是否优化、是否方便定位源码。把这些边界固定下来，后续测试、sanitizer 和性能观察才有稳定基础。

## 学习目标

1. 理解为什么要把告警当成构建门禁。
2. 区分 Debug 和 Release 构建的目的。
3. 用 CMake 给目标设置编译选项，而不是全局乱改环境。
4. 知道 `compile_commands.json` 在编辑器、静态分析和源码定位中的作用。

## 先修知识

需要会运行 `cmake`、`ninja` 和 C++ 编译命令。本文不要求会 gdb；本文 lab 环境未验证 gdb 单步调试。

## 核心模型

![编译告警和构建类型模型](/assets/diagrams/debug-build-warnings-build-types.svg)

源码先经过编译器检查。告警门禁负责拦下可疑写法；Debug 构建保留调试符号和更少优化；Release 构建面向最终性能；`compile_commands.json` 记录每个源文件的真实编译命令。

## 逐步实现

CMake 中为目标设置 C++ 标准和告警：

```cmake
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

target_compile_options(debuglab PRIVATE -Wall -Wextra -Wpedantic -Werror)
```

关键点是把选项挂在 target 上。这样库、CLI、测试可以分别声明自己的要求，避免某个目录里的临时变量影响整个工程。

lab 的 Debug 配置命令：

```bash
cmake -S . -B .lab_tmp/build-debug -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build .lab_tmp/build-debug
```

本地 transcript 显示：

```text
compiler=g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
cmake=cmake version 3.28.3
ninja=1.11.1
```

## 常见错误

1. **只在命令行临时加告警。** 下次构建容易丢失，应写进 CMake target。
2. **把 Release 当调试环境。** 优化会改变调用栈、变量可见性和单步观察效果。
3. **忽略告警。** 告警长期积累后，真正危险的告警会被淹没。
4. **没有 compile database。** 编辑器和静态分析工具会猜错 include path 或宏定义。

## 练习或延伸

1. 故意添加一个未使用变量，观察 `-Werror` 如何让构建失败。
2. 分别配置 Debug 和 Release，比较生成命令中的优化和调试符号选项。
3. 打开 `.lab_tmp/build-debug/compile_commands.json`，找到 `debug_lab.cpp` 的编译命令。

## 参考资料

- GCC 文档：[Warning Options](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html)
- CMake 文档：[CMAKE_BUILD_TYPE](https://cmake.org/cmake/help/latest/variable/CMAKE_BUILD_TYPE.html)
- CMake 文档：[CMAKE_EXPORT_COMPILE_COMMANDS](https://cmake.org/cmake/help/latest/variable/CMAKE_EXPORT_COMPILE_COMMANDS.html)

{% endraw %}
