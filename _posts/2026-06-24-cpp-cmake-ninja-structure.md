---
layout: post
title: "CMake 和 Ninja：把 C++ 项目结构变成可验证的构建图"
date: 2026-06-24 11:20:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
tags: [cpp, linux, cmake, ninja, build-system]
---

> 主题：Linux C++ 工程开发 / CMake / Ninja / 项目结构  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下本地执行验证。实验覆盖 Debug/Release 两个构建树、CTest、`compile_commands.json` 检查、Ninja 目标查看、增量构建，以及一个预期失败的漏链接例子。

前几篇文章分别讲了编译链接、RAII 和所有权。它们解决的是单个程序或局部代码的边界。项目变大后，真正容易失控的地方会变成另一类问题：头文件目录到处手写，编译选项散落在命令里，库和可执行文件之间靠手工顺序链接，测试程序与业务程序使用的编译条件不一致。

CMake 的价值在这里体现出来：它把项目拆成 target，并用 target 之间的依赖关系描述 include 目录、语言标准、编译选项、链接关系和测试入口。Ninja 则根据 CMake 生成的构建图执行具体构建，并在文件变化后只重建受影响的部分。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 区分 source tree、build tree、configure、generate 和 build 几个阶段。
2. 用 `add_library()`、`add_executable()` 和 `target_link_libraries()` 组织一个小型 C++ 项目。
3. 解释 `target_include_directories(... PUBLIC ...)` 和 `target_compile_features(... PUBLIC ...)` 如何传播到依赖方。
4. 使用 `cmake -S`、`cmake -B`、`cmake --build`、`ctest` 和 Ninja target 工具完成构建检查。
5. 观察增量构建：修改 app 源文件和 library 源文件时，Ninja 重建的目标不同。
6. 复现漏掉 `target_link_libraries()` 时的链接错误，并把它和前面的 `undefined reference` 知识连接起来。

## 先修知识

建议先读：

- [C++ 程序如何从源码变成可执行文件](/computer-science-teaching/2026/06/24/cpp-build-pipeline-source-to-executable.html)
- [头文件、源文件和 undefined reference：C++ 多文件构建的真实边界](/computer-science-teaching/2026/06/24/cpp-headers-source-linking-undefined-reference.html)

你需要知道：

- `.cpp` 会先编译成目标文件，再由链接器合成库或可执行文件；
- 头文件只提供声明，函数实现必须进入最终链接；
- Debug 和 Release 经常需要不同编译选项，因此应该放在不同 build 目录。

## 核心模型：CMake 描述 target，Ninja 执行构建图

CMake 官方文档把 `add_library()`、`add_executable()`、`target_include_directories()`、`target_link_libraries()` 作为 target 化构建的基本命令。工程上应先想清楚 target：哪个 target 产出库，哪个 target 产出可执行文件，哪些 include 目录和语言标准属于库的公共接口，哪些编译选项只是库自己的实现细节。

本文项目结构如下：

```text
cpp-cmake-ninja-structure/
├── CMakeLists.txt
├── include/qcalc/calculator.hpp
├── src/
│   ├── CMakeLists.txt
│   └── calculator.cpp
├── app/
│   ├── CMakeLists.txt
│   └── main.cpp
├── tests/
│   ├── CMakeLists.txt
│   └── calculator_tests.cpp
├── tools/inspect_compile_commands.py
└── bad_missing_link/CMakeLists.txt
```

构建关系可以画成一张图：

![CMake Ninja 构建图](/assets/diagrams/cpp-cmake-ninja-structure.svg)

图里的主线是：`qcalc` 是库 target，它公开自己的头文件目录和 C++20 需求；`qcalc_cli` 和 `qcalc_tests` 通过 `target_link_libraries()` 依赖 `qcalc`，因此自动获得这些公共使用需求。CMake configure/generate 后，Ninja 读取生成的 `build.ninja` 执行编译和链接。

## 建立项目目录

创建目录：

```bash
mkdir -p cpp-cmake-ninja-structure/{include/qcalc,src,app,tests,tools,bad_missing_link,reports}
cd cpp-cmake-ninja-structure
```

先写库的头文件：

```bash
cat > include/qcalc/calculator.hpp <<'CPP'
#pragma once

#include <span>
#include <string>
#include <string_view>

namespace qcalc {

int add(int left, int right) noexcept;
int multiply(int left, int right) noexcept;
double average(std::span<const int> values);
std::string format_result(std::string_view operation, int value);

}  // namespace qcalc
CPP
```

这里故意使用 `std::span`，因为它需要 C++20。这样后面就能验证 `target_compile_features(qcalc PUBLIC cxx_std_20)` 是否传播到了 app 和 tests。

写库实现：

```bash
cat > src/calculator.cpp <<'CPP'
#include "qcalc/calculator.hpp"

#include <numeric>
#include <stdexcept>

namespace qcalc {

int add(int left, int right) noexcept {
    return left + right;
}

int multiply(int left, int right) noexcept {
    return left * right;
}

double average(std::span<const int> values) {
    if (values.empty()) {
        throw std::invalid_argument("average requires at least one value");
    }
    const int sum = std::accumulate(values.begin(), values.end(), 0);
    return static_cast<double>(sum) / static_cast<double>(values.size());
}

std::string format_result(std::string_view operation, int value) {
    return std::string(operation) + "=" + std::to_string(value);
}

}  // namespace qcalc
CPP
```

写命令行程序：

```bash
cat > app/main.cpp <<'CPP'
#include "qcalc/calculator.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: " << argv[0] << " <left> <right>\n";
        return EXIT_FAILURE;
    }

    const int left = std::stoi(argv[1]);
    const int right = std::stoi(argv[2]);
    const std::vector<int> values{left, right, qcalc::add(left, right)};

    std::cout << qcalc::format_result("add", qcalc::add(left, right)) << '\n';
    std::cout << qcalc::format_result("multiply", qcalc::multiply(left, right)) << '\n';
    std::cout << "average=" << qcalc::average(values) << '\n';
    return EXIT_SUCCESS;
}
CPP
```

写一个不依赖第三方框架的测试程序：

```bash
cat > tests/calculator_tests.cpp <<'CPP'
#include "qcalc/calculator.hpp"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <vector>

void expect(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAILED: " << message << '\n';
        std::exit(EXIT_FAILURE);
    }
}

int main() {
    expect(qcalc::add(2, 5) == 7, "add should sum two integers");
    expect(qcalc::multiply(3, 4) == 12, "multiply should multiply two integers");

    const std::vector<int> values{2, 4, 6};
    expect(std::abs(qcalc::average(values) - 4.0) < 1e-9, "average should compute arithmetic mean");
    expect(qcalc::format_result("add", 7) == "add=7", "format_result should produce key=value text");

    bool threw = false;
    try {
        qcalc::average(std::span<const int>{});
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    expect(threw, "average should reject empty input");

    std::cout << "calculator tests passed\n";
    return EXIT_SUCCESS;
}
CPP
```

这四个文件体现了最常见的 C++ 项目切分：`include/` 放公共头文件，`src/` 放库实现，`app/` 放最终用户入口，`tests/` 放测试入口。关键是 app 和 tests 不直接知道库实现文件在哪里，它们只依赖库 target。

## 写 CMakeLists.txt

顶层 `CMakeLists.txt` 负责声明项目和子目录：

```bash
cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.20)
project(qcalc LANGUAGES CXX)

set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(src)
add_subdirectory(app)

include(CTest)
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()
CMAKE
```

`include(CTest)` 会引入 CTest 支持，并提供 `BUILD_TESTING` 选项。默认开启时，项目会进入 `tests/` 子目录。

库 target 写在 `src/CMakeLists.txt`：

```bash
cat > src/CMakeLists.txt <<'CMAKE'
add_library(qcalc STATIC calculator.cpp)
add_library(qcalc::qcalc ALIAS qcalc)

target_compile_features(qcalc PUBLIC cxx_std_20)
target_include_directories(qcalc
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
)
target_compile_options(qcalc PRIVATE -Wall -Wextra -Wpedantic)
CMAKE
```

这里最重要的是三行：

- `add_library(qcalc STATIC calculator.cpp)` 定义库 target；
- `target_include_directories(qcalc PUBLIC ${PROJECT_SOURCE_DIR}/include)` 表示 `include/` 是库的公共使用需求；
- `target_compile_features(qcalc PUBLIC cxx_std_20)` 表示使用这个库的 target 也需要 C++20。

`PUBLIC` 的意思是：这个属性既用于编译 `qcalc` 自己，也会传播给链接到 `qcalc` 的依赖方。头文件里出现 `std::span`，所以 C++20 属于公共接口要求。

app target 写在 `app/CMakeLists.txt`：

```bash
cat > app/CMakeLists.txt <<'CMAKE'
add_executable(qcalc_cli main.cpp)
target_link_libraries(qcalc_cli PRIVATE qcalc::qcalc)
target_compile_options(qcalc_cli PRIVATE -Wall -Wextra -Wpedantic)
CMAKE
```

测试 target 写在 `tests/CMakeLists.txt`：

```bash
cat > tests/CMakeLists.txt <<'CMAKE'
add_executable(qcalc_tests calculator_tests.cpp)
target_link_libraries(qcalc_tests PRIVATE qcalc::qcalc)
target_compile_options(qcalc_tests PRIVATE -Wall -Wextra -Wpedantic)

add_test(NAME qcalc_tests COMMAND qcalc_tests)
CMAKE
```

`target_link_libraries(qcalc_cli PRIVATE qcalc::qcalc)` 有两个作用：

1. 把 `qcalc` 的库文件链接进 `qcalc_cli`；
2. 把 `qcalc` 的公共使用需求传递给 `qcalc_cli`，包括 include 目录和 C++20 要求。

`PRIVATE` 表示 `qcalc_cli` 自己依赖 `qcalc`，但 `qcalc_cli` 不再把这个依赖继续传播给别的 target。可执行文件通常就是这样。

## 配置、生成、构建

执行 Debug 构建：

```bash
cmake -S . -B build/ninja -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build/ninja --parallel
```

这两个命令对应两个阶段：

- `cmake -S . -B build/ninja -G Ninja ...` 读取 source tree 中的 CMakeLists，配置项目，并生成 Ninja 能读取的构建文件；
- `cmake --build build/ninja --parallel` 调用 build tree 中记录的生成器执行构建，这里实际执行的是 Ninja。

本地构建摘要：

```text
[1/6] Building CXX object src/CMakeFiles/qcalc.dir/calculator.cpp.o
[2/6] Building CXX object app/CMakeFiles/qcalc_cli.dir/main.cpp.o
[3/6] Linking CXX static library src/libqcalc.a
[4/6] Building CXX object tests/CMakeFiles/qcalc_tests.dir/calculator_tests.cpp.o
[5/6] Linking CXX executable app/qcalc_cli
[6/6] Linking CXX executable tests/qcalc_tests
```

这能看出 target 图转成了具体构建动作：先编译源文件，再生成静态库，最后链接 app 和 tests。

运行测试和程序：

```bash
ctest --test-dir build/ninja --output-on-failure
build/ninja/app/qcalc_cli 7 8
```

本地输出摘要：

```text
100% tests passed, 0 tests failed out of 1
add=15
multiply=56
average=10
```

## 验证 PUBLIC 使用需求是否传播

打开 `compile_commands.json` 可以看到每个源文件实际使用的编译命令。为了避免靠肉眼看长命令，写一个小脚本检查三件事：库、app、tests 都获得了项目 include 目录，并且都处在 C++20 编译模式下。

```bash
cat > tools/inspect_compile_commands.py <<'PY'
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('build/ninja')
compile_commands = root / 'compile_commands.json'
rows = json.loads(compile_commands.read_text(encoding='utf-8'))
summary = {}
for row in rows:
    file_name = Path(row['file']).name
    command = row.get('command', '')
    summary[file_name] = {
        'has_project_include': '/include' in command,
        'uses_cxx20': '-std=c++20' in command or '-std=gnu++20' in command,
    }

required = ['calculator.cpp', 'main.cpp', 'calculator_tests.cpp']
for name in required:
    if name not in summary:
        raise SystemExit(f'missing compile command for {name}')
    if not summary[name]['has_project_include']:
        raise SystemExit(f'{name} did not receive the public include directory')
    if not summary[name]['uses_cxx20']:
        raise SystemExit(f'{name} did not receive a C++20 compile mode')

for name in required:
    item = summary[name]
    print(f"{name}: include={item['has_project_include']} cxx20={item['uses_cxx20']}")
PY
```

执行：

```bash
python3 tools/inspect_compile_commands.py build/ninja
```

本地输出：

```text
calculator.cpp: include=True cxx20=True
main.cpp: include=True cxx20=True
calculator_tests.cpp: include=True cxx20=True
```

这就是 target 化写法比手写 `g++ -I... -std=...` 更可靠的地方。公共接口要求被放在库 target 上，依赖方通过 `target_link_libraries()` 自动获得它们，app 和 tests 不需要复制同一组 include 路径和语言标准。

## 查看 Ninja target 和增量构建

可以查看 Ninja 看到的目标：

```bash
ninja -C build/ninja -t targets | grep -E '^(qcalc|qcalc_cli|qcalc_tests|libqcalc.a|all|test):'
```

本地可以看到 `qcalc`、`qcalc_cli`、`qcalc_tests`、`libqcalc.a`、`all`、`test` 等目标。它们来自 CMake 生成的 `build.ninja`。

现在观察增量构建。先只改 app 源文件：

```bash
touch app/main.cpp
cmake --build build/ninja --parallel
```

本地输出：

```text
[1/2] Building CXX object app/CMakeFiles/qcalc_cli.dir/main.cpp.o
[2/2] Linking CXX executable app/qcalc_cli
```

因为只改了 app 源文件，库 `qcalc` 和测试程序不需要重建。

再改库实现：

```bash
touch src/calculator.cpp
cmake --build build/ninja --parallel
```

本地输出：

```text
[1/4] Building CXX object src/CMakeFiles/qcalc.dir/calculator.cpp.o
[2/4] Linking CXX static library src/libqcalc.a
[3/4] Linking CXX executable tests/qcalc_tests
[4/4] Linking CXX executable app/qcalc_cli
```

这次库被重新编译和归档，依赖库的 app 和 tests 需要重新链接。增量构建会沿依赖图找到受影响的输出，而不是重新跑所有命令。

## Debug 和 Release 分开 build tree

对于单配置生成器 Ninja，`CMAKE_BUILD_TYPE` 在配置阶段决定。不要在同一个 build 目录里来回改 Debug/Release。创建单独目录更清晰：

```bash
cmake -S . -B build/release -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/release --parallel
ctest --test-dir build/release --output-on-failure
```

本地 Release 测试同样通过：

```text
100% tests passed, 0 tests failed out of 1
```

这种做法也方便保留 `build/ninja` 的 Debug 编译数据库给编辑器、clangd 或静态分析工具使用。

## 漏掉 target_link_libraries 会发生什么

为了把 CMake target 边界和链接错误联系起来，写一个故意错误的项目：

```bash
cat > bad_missing_link/CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.20)
project(qcalc_bad_missing_link LANGUAGES CXX)

set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(qcalc_bad ../app/main.cpp)
target_compile_features(qcalc_bad PRIVATE cxx_std_20)
target_include_directories(qcalc_bad PRIVATE ../include)
# This project intentionally omits target_link_libraries(qcalc_bad PRIVATE qcalc).
CMAKE
```

这个项目给了 include 目录，所以 `main.cpp` 能找到头文件；但它没有链接 `qcalc`，因此函数实现不会进入最终可执行文件。

运行：

```bash
cmake -S bad_missing_link -B build/bad -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/bad --parallel
```

本地得到预期链接错误：

```text
undefined reference to `qcalc::add(int, int)'
undefined reference to `qcalc::multiply(int, int)'
undefined reference to `qcalc::average(...)'
collect2: error: ld returned 1 exit status
ninja: build stopped: subcommand failed.
```

这和前面 `undefined reference` 文章中的结论一致：头文件让编译器知道函数声明，链接阶段仍然需要找到函数实现。CMake 的 `target_link_libraries()` 就是在 target 图里表达这条链接边。

## 常见错误

### 1. 把 include 目录写成全局变量

`include_directories()` 会把目录影响到后续很多 target，项目一大就难以判断某个头文件为什么能被找到。优先把 include 目录挂到真正拥有该接口的 target 上：

```cmake
target_include_directories(qcalc PUBLIC ${PROJECT_SOURCE_DIR}/include)
```

这样依赖关系清楚：谁链接 `qcalc`，谁获得 `qcalc` 的公共头文件目录。

### 2. 把编译命令当成构建系统

单文件练习可以手写：

```bash
g++ -std=c++20 -Iinclude app/main.cpp src/calculator.cpp -o qcalc_cli
```

项目化之后，这条命令会变成一串难以维护的路径、宏、库和平台差异。CMakeLists 应该保存构建知识，命令行只负责选择 source tree、build tree、生成器和配置类型。

### 3. 在 source tree 里生成构建文件

建议始终使用 out-of-source build：

```bash
cmake -S . -B build/ninja -G Ninja
```

这样源代码目录只放源码和 CMakeLists，生成的 `CMakeCache.txt`、`build.ninja`、目标文件、库和可执行文件都留在 `build/` 里。清理构建产物时删除 build 目录即可。

### 4. 用 `use_count` 式思维理解构建依赖

构建系统不关心“哪个文件看起来相关”，它只关心明确的输入输出和依赖边。CMake target 写得越清楚，Ninja 的增量构建越可靠。漏掉链接边时，编译阶段可能通过，链接阶段会暴露 `undefined reference`。

## 实践检查清单

为一个新的 C++ 小项目写 CMake 时，可以按这个顺序检查：

1. 每个库和可执行文件是否都是一个明确 target？
2. 公共头文件目录是否挂在库 target 的 `PUBLIC` 使用需求上？
3. C++ 标准要求是否由包含公共头文件语义的 target 传播？
4. 可执行文件和测试是否通过 `target_link_libraries()` 依赖库？
5. 是否启用 CTest 并能用 `ctest --test-dir ... --output-on-failure` 验证？
6. Debug 和 Release 是否使用不同 build tree？
7. 是否能解释一次 app 源文件修改和一次 library 源文件修改分别触发哪些重建？

## 练习

1. 把 `qcalc` 从 `STATIC` 改成默认库类型，配置时加 `-DBUILD_SHARED_LIBS=ON`，观察输出文件和链接命令变化。
2. 给库增加一个公共宏，例如 `QCALC_ENABLE_TRACE`，分别用 `PUBLIC` 和 `PRIVATE` 传播，检查 `compile_commands.json` 的差异。
3. 增加第二个库 target `qcalc_format`，让 app 同时链接两个库，观察 Ninja targets 和增量重建范围。
4. 把 `target_link_libraries(qcalc_tests PRIVATE qcalc::qcalc)` 删除，确认测试程序也会在链接阶段失败。

## 参考资料

- [CMake command: add_library](https://cmake.org/cmake/help/latest/command/add_library.html)
- [CMake command: add_executable](https://cmake.org/cmake/help/latest/command/add_executable.html)
- [CMake command: target_include_directories](https://cmake.org/cmake/help/latest/command/target_include_directories.html)
- [CMake command: target_link_libraries](https://cmake.org/cmake/help/latest/command/target_link_libraries.html)
- [CMake manual: cmake(1)](https://cmake.org/cmake/help/latest/manual/cmake.1.html)
- [CMake module: CTest](https://cmake.org/cmake/help/latest/module/CTest.html)
- [Ninja Manual](https://ninja-build.org/manual.html)
