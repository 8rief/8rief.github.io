---
layout: post
title: "CTest 回归测试：让修复能被重复定位"
date: 2026-06-29 20:05:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 CTest、测试命名和 output-on-failure 把 C++ 修复变成可复跑证据。"
tags: [ctest, testing, cpp, regression, teaching]
---
{% raw %}

> 主题：调试与构建工具基础 / CTest / regression
> 本文 lab 已验证：`debug_lab_tests` 通过，CTest 输出 `100% tests passed`。

调试不是只把当前错误改没。真正可靠的修复要能被重复验证：以后同样路径再坏，测试应该失败并指出位置。CTest 是 CMake 生态里的基础测试入口，适合把 C++ 小项目的测试命令统一起来。

## 学习目标

1. 用 CMake 注册一个 CTest 测试。
2. 理解测试名和失败输出对定位的重要性。
3. 用 `ctest --output-on-failure` 保存失败证据。
4. 区分单元测试、集成测试和命令行 smoke test。

## 先修知识

需要能构建 CMake 项目，理解函数输入输出和断言。

## 核心模型

![CTest 回归测试模型](/assets/diagrams/debug-ctest-regression-failure-localization.svg)

测试可执行文件包含多个断言。CTest 负责注册和运行测试，并把测试名、通过/失败状态和输出集中记录。失败时，`--output-on-failure` 把相关输出展示出来，便于定位。

## 逐步实现

CMake 注册测试：

```cmake
include(CTest)
if(BUILD_TESTING)
  add_test(NAME debug_lab_tests COMMAND debug_lab_tests)
endif()
```

执行：

```bash
ctest --test-dir .lab_tmp/build-debug --output-on-failure
```

lab 输出：

```text
Test #1: debug_lab_tests ..................   Passed
100% tests passed, 0 tests failed out of 1
```

测试可执行文件内部输出了摘要：

```text
tests_passed=10
parsed_values=2 parse_errors=2
shrunk_size=1 trigger=50
```

## 常见错误

1. **测试名没有语义。** 失败时只看到 `test1` 很难定位。
2. **只测成功路径。** 输入错误、空输入、边界值同样要测试。
3. **断言实现细节。** 测试应该验证行为契约，而不是临时变量名。
4. **不保存失败输出。** CI 或本地 transcript 应保留失败上下文。

## 练习或延伸

1. 故意让 `running_mean({})` 不抛异常，观察测试如何失败。
2. 增加一个 CLI smoke test，用 CTest 调用 `debug_lab_cli parse 10 5`。
3. 把测试输出写成更适合机器读取的 JSON 摘要。

## 参考资料

- CMake 文档：[CTest](https://cmake.org/cmake/help/latest/manual/ctest.1.html)
- CMake 文档：[add_test](https://cmake.org/cmake/help/latest/command/add_test.html)
- Google Testing Blog：[Testing on the Toilet: Flaky Tests](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html)

{% endraw %}
