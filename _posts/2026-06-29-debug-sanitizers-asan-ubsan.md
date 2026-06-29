---
layout: post
title: "Sanitizer 入门：把内存越界和未定义行为变成证据"
date: 2026-06-29 20:04:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 AddressSanitizer 和 UndefinedBehaviorSanitizer 捕获越界访问和有符号整数溢出。"
tags: [cpp, asan, ubsan, sanitizer, teaching]
---
{% raw %}

> 主题：调试与构建工具基础 / ASan / UBSan
> 本文 lab 已验证：ASan 捕获 heap-buffer-overflow，UBSan 捕获 signed integer overflow。

C++ 程序里最危险的问题常常不会稳定崩溃：越界访问可能读到看似合理的值，有符号整数溢出属于未定义行为。Sanitizer 的价值是把这些隐蔽问题变成可定位的运行时证据，给出文件、行号和错误类别。

## 学习目标

1. 知道 ASan 和 UBSan 分别解决什么问题。
2. 用 CMake 增加 sanitizer 编译和链接选项。
3. 读懂 sanitizer 输出中的错误类别、源码位置和退出状态。
4. 理解 sanitizer 构建和发布构建应分开。

## 先修知识

需要会配置 CMake Debug 构建，并知道数组越界和整数溢出的基本含义。

## 核心模型

![Sanitizer 运行时证据模型](/assets/diagrams/debug-sanitizers-asan-ubsan.svg)

sanitizer 构建会在编译和链接时插入额外检查。程序运行到危险行为时，运行时库输出错误类别、调用位置和源码行。这个构建适合调试和 CI，不适合作为普通发布二进制。

## 逐步实现

CMake 选项：

```cmake
option(ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
if(ENABLE_SANITIZERS)
  target_compile_options(debuglab PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(debuglab PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
endif()
```

配置 sanitizer 构建：

```bash
cmake -S . -B .lab_tmp/build-sanitize -G Ninja -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON
cmake --build .lab_tmp/build-sanitize
```

触发越界：

```cpp
int unsafe_index_demo() {
    vector<int> values{1, 2, 3};
    return values[3];
}
```

transcript 中的证据：

```text
asan_status=1 ubsan_status=1
ERROR: AddressSanitizer: heap-buffer-overflow
runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
```

## 常见错误

1. **只给编译加 sanitizer，忘记链接。** 运行时库需要链接选项。
2. **把 sanitizer 当性能测试环境。** 插桩会改变速度和内存使用。
3. **只看退出码，不保存报告。** 错误类别和源码行才是关键证据。
4. **发布时保留调试插桩。** 发布构建应有独立配置和检查清单。

## 练习或延伸

1. 把 `values[3]` 改成 `values.at(3)`，比较异常和 ASan 的差异。
2. 给除零或空指针访问写一个 sanitizer demo。
3. 在 CI 中增加一个 sanitizer job，但不要替代普通测试 job。

## 参考资料

- GCC 文档：[Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)
- Clang 文档：[AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)
- Clang 文档：[UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)

{% endraw %}
