---
layout: post
title: "C++ CMake FetchContent：把第三方库纳入可复现项目"
date: 2026-04-08 18:00:00 +0800
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

## 为什么需要 FetchContent 依赖边界

一个可以展示的 C++ 项目通常会同时用到命令行解析、JSON、日志、HTTP 服务和测试框架。把这些库只写进 README，读者需要手工安装，复现实验时很容易卡在版本差异、头文件路径和链接顺序上。

`FetchContent` 的作用是把依赖解析写进构建图：配置阶段下载指定版本，生成阶段产生可链接的 target，构建阶段把它们和自己的库、可执行程序、测试放进同一条 Ninja 图。这样做的好处有三个。

1. **复现路径短**：读者执行同一组 `cmake` 命令，就能得到一致的依赖版本。
2. **边界可检查**：核心库只链接自己真正需要的库，入口层再承担 CLI、日志和 HTTP。
3. **失败位置清楚**：下载、配置、编译、链接和测试都出现在 transcript 里，定位问题时不用猜。

这个项目的关键判断是：核心 `file_indexer` 只需要 JSON 表达报告结构；CLI 和 API 是外层接口，应该独立链接 CLI11、spdlog 和 cpp-httplib。


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

## 输出怎么读

配置阶段出现 `Populating nlohmann_json`、`Populating cli11`、`Populating spdlog`、`Populating cpp_httplib` 和 `Populating catch2`，说明 CMake 正在按声明的依赖图准备第三方源码。这里要关注两类信息：版本标签是否符合预期，以及最终导出的 target 是否能被自己的目标链接。

```text
-- Build spdlog: 1.15.3
-- Configuring done
-- Generating done
-- Build files have been written to: .../build
```

`Build files have been written` 只证明生成了构建图，还没有证明项目可以运行。后面必须继续看到：

```text
[122/122] Linking CXX executable file-indexer
100% tests passed, 0 tests failed out of 3
```

`122/122` 表示所有库、测试目标和 CLI 目标都完成编译链接。`CTest` 通过表示核心库的文件遍历、JSON/CSV 输出和报告写入行为被测试覆盖。最后的 CLI 和 API smoke 才证明这些 target 被实际使用，而不只是能编译。

如果配置阶段失败，先看网络和 Git tag；如果编译阶段失败，优先看 include 路径和 target 链接关系；如果测试失败，再回到核心库的输入 fixture 和报告字段。


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
