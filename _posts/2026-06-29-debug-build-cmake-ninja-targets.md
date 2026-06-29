---
layout: post
title: "CMake 和 Ninja 排错：先看 target、缓存和构建图"
date: 2026-06-29 20:02:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 CMake 配置、Ninja targets 和构建目录边界定位 C++ 项目为什么没有按预期构建。"
tags: [cmake, ninja, build-system, cpp, teaching]
---
{% raw %}

> 主题：调试与构建工具基础 / CMake / Ninja
> 本文 lab 已验证：`ninja -t targets` 输出了 `debuglab`、`debug_lab_cli`、`debug_lab_tests` 和 CTest 相关目标。

构建问题常见症状是“我改了代码但没重新编译”“测试没有被发现”“链接到了旧库”。排查这类问题时，重点在 target、缓存、构建目录和生成文件的边界。CMake 负责生成构建系统，Ninja 负责执行具体构建图。

## 学习目标

1. 区分 source tree、build tree 和 install/output tree。
2. 用 CMake target 理解库、CLI、测试之间的依赖。
3. 用 `ninja -t targets` 查看可构建目标。
4. 知道什么时候需要重新 configure，什么时候只需要 rebuild。

## 先修知识

需要知道 C++ 工程通常由库、可执行文件和测试组成。建议先读上一篇编译告警和构建类型。

## 核心模型

![CMake 和 Ninja 构建图模型](/assets/diagrams/debug-build-cmake-ninja-targets.svg)

CMake 读取 `CMakeLists.txt`，生成 Ninja 的构建图。构建图中每个 target 有输入源文件、编译选项、链接依赖和输出文件。Ninja 根据文件时间戳和依赖关系决定哪些步骤需要重跑。

## 逐步实现

lab 中的核心 target：

```cmake
add_library(debuglab src/debug_lab.cpp)
add_executable(debug_lab_cli src/debug_lab_cli.cpp)
target_link_libraries(debug_lab_cli PRIVATE debuglab)
add_executable(debug_lab_tests tests/test_debug_lab.cpp)
target_link_libraries(debug_lab_tests PRIVATE debuglab)
```

查看 Ninja 目标：

```bash
ninja -C .lab_tmp/build-debug -t targets
```

transcript 中可以看到：

```text
debuglab: phony
all: phony
build.ninja: RERUN_CMAKE
clean: CLEAN
help: HELP
```

如果你新增源文件但没有写进 target，Ninja 不会知道它。排错时先问：这个文件属于哪个 target？target 是否依赖它？构建目录是不是当前正在使用的目录？

## 常见错误

1. **在 source tree 里混入生成文件。** 建议使用 `.lab_tmp/build-debug` 这类独立构建目录。
2. **改 CMakeLists 后只 rebuild。** CMake 通常会自动 rerun，但生成异常时应主动重新 configure。
3. **把 include path 写成全局变量。** 优先用 `target_include_directories`。
4. **多个 build 目录混用。** Debug、Release、sanitizer 构建应分目录，避免缓存污染。

## 练习或延伸

1. 删除 `.lab_tmp/build-debug` 后重新 configure，观察输出差异。
2. 给项目增加一个新 `.cpp`，故意不加入 target，解释为什么不会参与构建。
3. 用 `ninja -t graph debug_lab_cli` 生成构建图并观察依赖。

## 参考资料

- CMake 文档：[add_library](https://cmake.org/cmake/help/latest/command/add_library.html)
- CMake 文档：[add_executable](https://cmake.org/cmake/help/latest/command/add_executable.html)
- Ninja 手册：[Ninja manual](https://ninja-build.org/manual.html)

{% endraw %}
