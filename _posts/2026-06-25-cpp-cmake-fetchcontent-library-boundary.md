---
layout: post
title: "C++ CMake FetchContent：把第三方库纳入可复现项目"
date: 2026-06-25 21:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, cmake, fetchcontent, teaching]
---

## 学习目标

这一篇把前面 C++ 构建知识推进到真实项目：如何用 CMake 固定第三方库版本，并让 CLI、JSON、日志、HTTP API 和测试一起构建。读完以后，你应该能完成：

1. 用 `FetchContent` 固定 nlohmann/json、CLI11、spdlog、cpp-httplib 和 Catch2；
2. 理解库 target、include 目录和可执行程序之间的依赖边界；
3. 解释为什么 C++ 项目要把依赖下载、编译和测试纳入同一条 transcript。

## 先修知识

需要知道 CMake target、静态库、可执行程序、头文件路径和链接的基本概念。前面的 C++ CMake/Ninja 文章已经覆盖了这些基础。

## 核心模型

C++ 项目的依赖边界可以看成一张构建图。

![C++ FetchContent 构建图](/assets/diagrams/cpp-cmake-fetchcontent-library-boundary.svg)

核心库 `file_indexer` 只依赖 nlohmann/json；CLI 可执行程序再依赖 CLI11、spdlog 和 cpp-httplib；测试目标依赖 Catch2。这样划分后，核心逻辑不会被命令行和 HTTP 服务绑死。

## 逐步实现

CMake 先声明项目和 C++ 标准：

```cmake
cmake_minimum_required(VERSION 3.24)
project(cpp_file_indexer_service VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
```

依赖用 tag 固定：

```cmake
FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.12.0
)
FetchContent_Declare(
  CLI11
  GIT_REPOSITORY https://github.com/CLIUtils/CLI11.git
  GIT_TAG v2.5.0
)
```

核心库和入口程序分开：

```cmake
add_library(file_indexer src/indexer.cpp)
target_include_directories(file_indexer PUBLIC include)
target_link_libraries(file_indexer PUBLIC nlohmann_json::nlohmann_json)

add_executable(file-indexer src/main.cpp)
target_link_libraries(file-indexer PRIVATE file_indexer CLI11::CLI11 spdlog::spdlog)
```

cpp-httplib 作为 header-only 库手工加入 include 目录：

```cmake
target_include_directories(file-indexer PRIVATE ${cpp_httplib_SOURCE_DIR})
```

这是一次验证中得到的工程结论：直接链接 cpp-httplib 的 CMake target 会在当前 WSL 环境里带入 Windows MSYS include 路径，导致 Linux 编译器读取错误平台头文件。手工引用 header-only 目录能保持依赖边界更干净。

实验命令是：

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
```

transcript 证明 CTest 三个用例全部通过，CLI 和 API 也在同一构建产物上运行。

## 常见错误

1. **核心库直接依赖 CLI 和 HTTP server**：这样测试纯逻辑时也会被入口层拖住。
2. **依赖只写 README，不进 CMake**：读者无法一条命令复现环境。
3. **忽略平台 include 污染**：C++ 构建失败常常来自错误头文件路径，要看完整编译命令。

## 练习或延伸

- 给 `FetchContent_Declare` 增加 `GIT_SHALLOW TRUE`，比较首次下载时间。
- 把 cpp-httplib 的 include 目录错误地删掉，观察编译器如何定位缺失头文件。

## 参考资料

- [CMake FetchContent](https://cmake.org/cmake/help/latest/module/FetchContent.html)
- [CMake target_link_libraries](https://cmake.org/cmake/help/latest/command/target_link_libraries.html)
- [CLI11](https://github.com/CLIUtils/CLI11)
