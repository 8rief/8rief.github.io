---
layout: post
title: "C++ Catch2 测试：用 fixture 锁住文件索引器行为"
date: 2026-06-25 21:05:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, catch2, testing, teaching]
---

## 学习目标

这一篇讲 C++ 项目的回归验证。读完以后，你应该能解释：

1. 为什么文件索引器需要 fixture；
2. Catch2 如何通过 CTest 集成到 CMake；
3. 测试应该锁住哪些用户可见行为。

## 先修知识

需要知道 CTest 是 CMake 的测试运行器，Catch2 是 C++ 单元测试框架。前面 GoogleTest 文章讲过测试思想，这里重点看项目化 fixture。

## 核心模型

测试链路是：样例目录作为 fixture，核心库生成 `IndexResult`，测试断言汇总、JSON 和 CSV。

![C++ Catch2 fixture 测试](/assets/diagrams/cpp-catch2-fixtures-regression-tests.svg)

fixture 要小、稳定、能解释。这个项目用三个文本文件，覆盖 `.txt`、`.md` 和多行内容。

## 逐步实现

CMake 里给测试目标链接 Catch2：

```cmake
add_executable(file_indexer_tests tests/test_indexer.cpp)
target_link_libraries(file_indexer_tests PRIVATE file_indexer Catch2::Catch2WithMain)
include(Catch)
catch_discover_tests(file_indexer_tests)
```

测试样例断言汇总：

```cpp
TEST_CASE("build_index summarizes sample files") {
    std::vector<std::string> extensions{".txt", ".md"};
    file_indexer::IndexerConfig config{fixture_root(), extensions};
    const auto result = file_indexer::build_index(config);
    REQUIRE(result.summary.files == 3);
    REQUIRE(result.summary.lines == 7);
    REQUIRE(result.summary.words >= 40);
}
```

JSON 测试检查字段结构：

```cpp
const auto value = file_indexer::to_json_value(result);
REQUIRE(value.at("summary").at("files").get<std::size_t>() == 2);
REQUIRE(value.at("files").is_array());
```

报告测试检查文件和 CSV header：

```cpp
file_indexer::write_json_report(json_path, result);
file_indexer::write_csv_report(csv_path, result);
REQUIRE(std::filesystem::exists(json_path));
REQUIRE(header == "path,bytes,lines,words");
```

实验输出：

```text
3/3 Test #3: write reports creates JSON and CSV files ... Passed
100% tests passed, 0 tests failed out of 3
```

## 常见错误

1. **测试真实大目录**：大目录不稳定，也可能暴露本机路径。fixture 应该小而可解释。
2. **只检查进程退出码**：测试要检查汇总数值、文件存在和字段结构。
3. **测试依赖当前工作目录**：用 CMake 注入 source root，避免从不同目录运行时找不到 fixture。

## 练习或延伸

- 增加一个空文件 fixture，检查 lines 和 words 是否为 0。
- 增加一个扩展名过滤测试，只允许 `.md` 时应只有一个文件。

## 参考资料

- [Catch2 documentation](https://github.com/catchorg/Catch2/blob/devel/docs/Readme.md)
- [CTest manual](https://cmake.org/cmake/help/latest/manual/ctest.1.html)
- [Catch2 CMake integration](https://github.com/catchorg/Catch2/blob/devel/docs/cmake-integration.md)
