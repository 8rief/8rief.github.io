---
layout: post
title: "GoogleTest 和可复现实验：让 C++ 测试能被定位、复跑和审计"
date: 2026-06-24 12:20:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 GoogleTest、CTest、过滤运行、随机种子和 sanitizer，把 C++ 测试组织成可定位、可复跑、可审计的验证流。"
tags: [cpp, linux, googletest, testing, cmake, reproducibility]
---
{% raw %}

> 主题：Linux C++ 工程开发 / GoogleTest / CTest / 可复现实验  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下本地执行验证。实验使用 CMake `FetchContent` 固定 GoogleTest v1.17.0，并用 SHA256 校验下载内容。

前一篇文章把 CMake/Ninja 项目结构整理成 target 图。项目能稳定构建之后，下一步是让行为也能被稳定验证。真正有用的 C++ 测试要能回答几个工程问题：失败是哪一个测试？用什么输入失败？如何只复跑这个失败？测试数据从哪里来？随机过程是否可重复？能否在 sanitizer 下再跑一遍？

GoogleTest 适合放在这个位置：它提供 `TEST`、`TEST_F`、参数化测试、断言输出和过滤运行；CMake 的 `GoogleTest` 模块可以把 GoogleTest 用例发现成 CTest 测试；CTest 再负责统一执行、筛选和输出失败信息。这样，测试从一个可执行文件变成了可定位、可复跑、可进入 CI 的检查网。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 用 CMake `FetchContent` 固定 GoogleTest 版本和下载哈希。
2. 写 `TEST`、`TEST_F` 和 `TEST_P`，覆盖普通输入、异常路径、临时文件和参数化样例。
3. 用 `gtest_discover_tests()` 把 GoogleTest 用例注册成 CTest 测试。
4. 用 `--gtest_filter`、`--gtest_repeat`、`--gtest_shuffle`、`--gtest_random_seed` 定位和复跑测试。
5. 阅读一个预期失败的 GoogleTest 输出，理解 expected/actual 如何帮助定位问题。
6. 在 ASan/UBSan 构建下复跑同一组测试，形成更强的验证证据。

## 先修知识

建议先读：

- [CMake 和 Ninja：把 C++ 项目结构变成可验证的构建图](/computer-science-teaching/2026/06/24/cpp-cmake-ninja-structure.html)
- [unique_ptr、shared_ptr 和 raw pointer：把所有权写进类型](/computer-science-teaching/2026/06/24/cpp-ownership-smart-pointers.html)

你需要知道：

- CMake target、CTest 和 out-of-source build 的基本概念；
- C++ 异常和临时文件的基本用法；
- Debug 构建和 sanitizer 构建应该放在不同 build tree。

## 核心模型：测试也是可审计的构建产物

GoogleTest 官方快速开始文档推荐用 CMake 配置一个测试可执行文件，并链接 `GTest::gtest_main`。GoogleTest Primer 说明了 `TEST()`、fixture、断言和测试过滤等基本机制。CMake 的 `GoogleTest` 模块提供 `gtest_discover_tests()`，可以在构建后运行测试可执行文件并发现其中的 GoogleTest 用例，再注册成 CTest 测试。

本文实验采用这条结构：

![GoogleTest 可复现实验流程](/assets/diagrams/cpp-googletest-reproducible-tests.svg)

核心思想是：

1. 业务代码在 `qstats` 库 target 中；
2. GoogleTest 测试链接 `qstats::qstats` 和 `GTest::gtest_main`；
3. CMake 在构建后发现 GoogleTest 用例；
4. CTest 把每个用例当成可独立定位的测试；
5. 失败输出、过滤命令、固定种子和 sanitizer 构成复现实验证据。

## 建立实验目录

创建目录：

```bash
mkdir -p cpp-googletest-reproducible-tests/{include/qstats,src,tests,reports}
cd cpp-googletest-reproducible-tests
```

先写一个小型统计库。它包含均值、中位数、文件读取，以及一个固定算法的带种子数据划分函数。

```bash
cat > include/qstats/statistics.hpp <<'CPP'
#pragma once

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <span>
#include <utility>
#include <vector>

namespace qstats {

double mean(std::span<const double> values);
double median(std::vector<double> values);
std::vector<double> read_values(const std::filesystem::path& path);
std::vector<std::size_t> shuffled_indices(std::size_t size, std::uint64_t seed);
std::pair<std::vector<double>, std::vector<double>> split_train_test(
    std::span<const double> values,
    std::size_t train_count,
    std::uint64_t seed);

}  // namespace qstats
CPP
```

实现文件：

```bash
cat > src/statistics.cpp <<'CPP'
#include "qstats/statistics.hpp"

#include <algorithm>
#include <fstream>
#include <numeric>
#include <stdexcept>
#include <string>

namespace qstats {
namespace {

std::uint64_t next_state(std::uint64_t state) noexcept {
    return state * 6364136223846793005ULL + 1442695040888963407ULL;
}

}  // namespace

double mean(std::span<const double> values) {
    if (values.empty()) {
        throw std::invalid_argument("mean requires at least one value");
    }
    const double sum = std::accumulate(values.begin(), values.end(), 0.0);
    return sum / static_cast<double>(values.size());
}

double median(std::vector<double> values) {
    if (values.empty()) {
        throw std::invalid_argument("median requires at least one value");
    }
    std::sort(values.begin(), values.end());
    const std::size_t middle = values.size() / 2;
    if (values.size() % 2 == 1) {
        return values[middle];
    }
    return (values[middle - 1] + values[middle]) / 2.0;
}

std::vector<double> read_values(const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("cannot open values file: " + path.string());
    }

    std::vector<double> values;
    std::string line;
    while (std::getline(input, line)) {
        if (line.empty()) {
            continue;
        }
        std::size_t parsed = 0;
        double value = 0.0;
        try {
            value = std::stod(line, &parsed);
        } catch (const std::exception&) {
            throw std::runtime_error("invalid numeric line: " + line);
        }
        if (parsed != line.size()) {
            throw std::runtime_error("trailing characters in numeric line: " + line);
        }
        values.push_back(value);
    }

    if (values.empty()) {
        throw std::runtime_error("values file is empty: " + path.string());
    }
    return values;
}

std::vector<std::size_t> shuffled_indices(std::size_t size, std::uint64_t seed) {
    std::vector<std::size_t> indices(size);
    std::iota(indices.begin(), indices.end(), 0);
    std::uint64_t state = seed;
    for (std::size_t i = size; i > 1; --i) {
        state = next_state(state);
        const std::size_t j = static_cast<std::size_t>(state % i);
        std::swap(indices[i - 1], indices[j]);
    }
    return indices;
}

std::pair<std::vector<double>, std::vector<double>> split_train_test(
    std::span<const double> values,
    std::size_t train_count,
    std::uint64_t seed) {
    if (train_count > values.size()) {
        throw std::invalid_argument("train_count cannot exceed values.size()");
    }

    const auto order = shuffled_indices(values.size(), seed);
    std::vector<double> train;
    std::vector<double> test;
    train.reserve(train_count);
    test.reserve(values.size() - train_count);

    for (std::size_t pos = 0; pos < order.size(); ++pos) {
        if (pos < train_count) {
            train.push_back(values[order[pos]]);
        } else {
            test.push_back(values[order[pos]]);
        }
    }
    return {train, test};
}

}  // namespace qstats
CPP
```

这里的 `shuffled_indices()` 没有使用平台库中的随机分布，而是写了一个固定的线性同余状态推进和 Fisher-Yates shuffle。这样测试里的种子输出由本文代码决定，不依赖标准库随机分布实现细节。它不是密码学随机数，也不适合安全场景；这里只用于可复现实验。

## CMake：固定 GoogleTest 版本

顶层 `CMakeLists.txt`：

```bash
cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.20)
project(qstats_reproducible_tests LANGUAGES CXX)

set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)
FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.17.0.zip
    URL_HASH SHA256=40d4ec942217dcc84a9ebe2a68584ada7d4a33a8ee958755763278ea1c5e18ff
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_subdirectory(src)

include(CTest)
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()
CMAKE
```

这里有三个关键点：

- `FetchContent_Declare()` 固定 GoogleTest v1.17.0 的 URL；
- `URL_HASH` 校验下载内容，避免静默使用错误包；
- `DOWNLOAD_EXTRACT_TIMESTAMP TRUE` 避免 URL 下载包解压时间戳导致的增量构建歧义。

库 target：

```bash
mkdir -p src
cat > src/CMakeLists.txt <<'CMAKE'
add_library(qstats STATIC statistics.cpp)
add_library(qstats::qstats ALIAS qstats)

target_compile_features(qstats PUBLIC cxx_std_20)
target_include_directories(qstats
    PUBLIC
        ${PROJECT_SOURCE_DIR}/include
)
target_compile_options(qstats PRIVATE -Wall -Wextra -Wpedantic)
CMAKE
```

测试 target：

```bash
mkdir -p tests
cat > tests/CMakeLists.txt <<'CMAKE'
add_executable(qstats_tests statistics_tests.cpp)
target_link_libraries(qstats_tests PRIVATE qstats::qstats GTest::gtest_main)
target_compile_options(qstats_tests PRIVATE -Wall -Wextra -Wpedantic)

include(GoogleTest)
gtest_discover_tests(qstats_tests DISCOVERY_TIMEOUT 30)

add_executable(qstats_failing_demo failing_demo.cpp)
target_link_libraries(qstats_failing_demo PRIVATE qstats::qstats GTest::gtest_main)
target_compile_options(qstats_failing_demo PRIVATE -Wall -Wextra -Wpedantic)
CMAKE
```

`gtest_discover_tests(qstats_tests ...)` 是连接 GoogleTest 和 CTest 的关键。它让 CTest 看见每一个 GoogleTest 用例，而不是只看见一个大测试可执行文件。

## 写普通测试、fixture 和参数化测试

测试文件：

```bash
cat > tests/statistics_tests.cpp <<'CPP'
#include "qstats/statistics.hpp"

#include <gtest/gtest.h>

#include <filesystem>
#include <fstream>
#include <ostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct MeanCase {
    std::vector<double> values;
    double expected;
};

void PrintTo(const MeanCase& value, std::ostream* os) {
    *os << "MeanCase{size=" << value.values.size()
        << ", expected=" << value.expected << "}";
}

std::string case_name(const testing::TestParamInfo<MeanCase>& info) {
    std::ostringstream out;
    out << "Case" << info.index;
    return out.str();
}

class MeanParamTest : public testing::TestWithParam<MeanCase> {};

TEST_P(MeanParamTest, ComputesExpectedMean) {
    const auto& param = GetParam();
    EXPECT_DOUBLE_EQ(qstats::mean(param.values), param.expected);
}

INSTANTIATE_TEST_SUITE_P(
    SmallSamples,
    MeanParamTest,
    testing::Values(
        MeanCase{{1.0, 2.0, 3.0}, 2.0},
        MeanCase{{-2.0, 2.0}, 0.0},
        MeanCase{{4.5}, 4.5}),
    case_name);

TEST(MeanTest, RejectsEmptyInput) {
    EXPECT_THROW(qstats::mean(std::span<const double>{}), std::invalid_argument);
}

TEST(MedianTest, HandlesOddEvenAndUnsortedInputs) {
    EXPECT_DOUBLE_EQ(qstats::median({5.0, 1.0, 3.0}), 3.0);
    EXPECT_DOUBLE_EQ(qstats::median({10.0, 2.0, 8.0, 4.0}), 6.0);
}

TEST(MedianTest, RejectsEmptyInput) {
    EXPECT_THROW(qstats::median({}), std::invalid_argument);
}

class ValuesFileTest : public testing::Test {
protected:
    void SetUp() override {
        const auto* info = testing::UnitTest::GetInstance()->current_test_info();
        root_ = std::filesystem::temp_directory_path() /
                (std::string("qstats_") + info->test_suite_name() + "_" + info->name());
        std::filesystem::remove_all(root_);
        std::filesystem::create_directories(root_);
    }

    void TearDown() override {
        std::filesystem::remove_all(root_);
    }

    std::filesystem::path write_file(const std::string& name, const std::string& text) const {
        const auto path = root_ / name;
        std::ofstream output(path);
        output << text;
        return path;
    }

private:
    std::filesystem::path root_;
};

TEST_F(ValuesFileTest, ReadsOneValuePerLine) {
    const auto path = write_file("values.txt", "1.5\n2.5\n\n4.0\n");
    EXPECT_EQ(qstats::read_values(path), (std::vector<double>{1.5, 2.5, 4.0}));
}

TEST_F(ValuesFileTest, RejectsInvalidLine) {
    const auto path = write_file("bad.txt", "1\nnot-a-number\n3\n");
    EXPECT_THROW(qstats::read_values(path), std::runtime_error);
}

TEST(SplitTest, UsesDeterministicSeed) {
    const std::vector<double> values{10.0, 20.0, 30.0, 40.0, 50.0};
    const auto [train, test] = qstats::split_train_test(values, 3, 20260624ULL);

    EXPECT_EQ(train, (std::vector<double>{20.0, 10.0, 40.0}));
    EXPECT_EQ(test, (std::vector<double>{50.0, 30.0}));
}

TEST(SplitTest, RejectsOversizedTrainingSet) {
    const std::vector<double> values{1.0, 2.0};
    EXPECT_THROW(qstats::split_train_test(values, 3, 1ULL), std::invalid_argument);
}

}  // namespace
CPP
```

这一个文件覆盖了三类测试需求。

第一类是普通输入输出和异常路径：

```cpp
TEST(MedianTest, HandlesOddEvenAndUnsortedInputs) {
    EXPECT_DOUBLE_EQ(qstats::median({5.0, 1.0, 3.0}), 3.0);
    EXPECT_DOUBLE_EQ(qstats::median({10.0, 2.0, 8.0, 4.0}), 6.0);
}

TEST(MedianTest, RejectsEmptyInput) {
    EXPECT_THROW(qstats::median({}), std::invalid_argument);
}
```

第二类是 fixture。`ValuesFileTest` 在 `SetUp()` 中创建临时目录，在 `TearDown()` 中清理。这样每个文件测试都有自己的环境，不共享隐藏状态。

第三类是参数化测试。`MeanParamTest` 把多组输入挂到同一个测试逻辑上，并用 `case_name()` 给每个参数生成稳定名称。`PrintTo()` 让 CTest 列表里的参数说明更可读。

再写一个预期失败的示例，它不注册到 CTest，只用于观察失败输出：

```bash
cat > tests/failing_demo.cpp <<'CPP'
#include "qstats/statistics.hpp"

#include <gtest/gtest.h>

TEST(FailingExample, ShowsExpectedAndActualValues) {
    EXPECT_DOUBLE_EQ(qstats::median({1.0, 2.0, 100.0}), 2.5);
}
CPP
```

这个测试故意把 `{1.0, 2.0, 100.0}` 的中位数期望写成 `2.5`。真实结果是 `2.0`，因此它应该失败。

## 构建和发现测试

执行 Debug 构建：

```bash
cmake -S . -B build/ninja -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build/ninja --parallel
```

本地构建会先下载并构建 GoogleTest，然后构建 `qstats`、`qstats_tests` 和 `qstats_failing_demo`。

查看 CTest 发现到的测试：

```bash
ctest --test-dir build/ninja -N
```

本地输出摘要：

```text
Test  #1: MeanTest.RejectsEmptyInput
Test  #2: MedianTest.HandlesOddEvenAndUnsortedInputs
Test  #3: MedianTest.RejectsEmptyInput
Test  #4: ValuesFileTest.ReadsOneValuePerLine
Test  #5: ValuesFileTest.RejectsInvalidLine
Test  #6: SplitTest.UsesDeterministicSeed
Test  #7: SplitTest.RejectsOversizedTrainingSet
Test  #8: SmallSamples/MeanParamTest.ComputesExpectedMean/Case0
Test  #9: SmallSamples/MeanParamTest.ComputesExpectedMean/Case1
Test #10: SmallSamples/MeanParamTest.ComputesExpectedMean/Case2
```

这说明 `gtest_discover_tests()` 已经把 GoogleTest 内部用例展开成 10 个 CTest 测试。CI 或本地脚本可以用 CTest 统一执行它们。

## 跑完整测试和局部复跑

完整测试：

```bash
ctest --test-dir build/ninja --output-on-failure
```

本地结果：

```text
100% tests passed, 0 tests failed out of 10
```

列出 GoogleTest 原生命名结构：

```bash
build/ninja/tests/qstats_tests --gtest_list_tests
```

局部复跑中位数相关测试：

```bash
build/ninja/tests/qstats_tests --gtest_filter=MedianTest.*
```

本地输出摘要：

```text
Note: Google Test filter = MedianTest.*
[ RUN      ] MedianTest.HandlesOddEvenAndUnsortedInputs
[       OK ] MedianTest.HandlesOddEvenAndUnsortedInputs
[ RUN      ] MedianTest.RejectsEmptyInput
[       OK ] MedianTest.RejectsEmptyInput
[  PASSED  ] 2 tests.
```

这就是测试命名的重要性。`MedianTest.HandlesOddEvenAndUnsortedInputs` 比 `Test1` 更容易定位问题，也更容易写过滤条件。

## 固定随机种子并重复运行

执行：

```bash
build/ninja/tests/qstats_tests --gtest_repeat=3 --gtest_shuffle --gtest_random_seed=123
```

本地三轮都通过。输出会显示每一轮使用的 seed：

```text
Repeating all tests (iteration 1) . . .
Note: Randomizing tests' orders with a seed of 123 .
[  PASSED  ] 10 tests.

Repeating all tests (iteration 2) . . .
Note: Randomizing tests' orders with a seed of 124 .
[  PASSED  ] 10 tests.

Repeating all tests (iteration 3) . . .
Note: Randomizing tests' orders with a seed of 125 .
[  PASSED  ] 10 tests.
```

这里有两个层面的可复现：GoogleTest 的测试顺序随机种子可记录；业务函数 `split_train_test()` 的数据划分种子也固定在测试里。若以后某轮失败，至少可以从命令、seed 和测试名恢复同样的检查条件。

## 观察一次失败输出

运行故意失败的示例：

```bash
build/ninja/tests/qstats_failing_demo --gtest_filter=FailingExample.ShowsExpectedAndActualValues
```

本地得到预期失败，关键输出如下：

```text
Expected equality of these values:
  qstats::median({1.0, 2.0, 100.0})
    Which is: 2
  2.5
[  FAILED  ] FailingExample.ShowsExpectedAndActualValues
```

这段输出把失败定位到表达式、实际值和期望值。写断言时应该让失败信息尽量指向具体差异：哪个输入、哪个条件、哪个边界。

## sanitizer 下复跑同一组测试

另建一个 sanitizer build tree：

```bash
cmake -S . -B build/sanitize -G Ninja -DCMAKE_BUILD_TYPE=Debug   -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer"
cmake --build build/sanitize --parallel
ctest --test-dir build/sanitize --output-on-failure
```

本地结果：

```text
100% tests passed, 0 tests failed out of 10
```

这一步不能证明程序没有任何内存或未定义行为问题，但它提供了比普通 Debug 测试更强的证据：同一组 GoogleTest 用例在 ASan/UBSan 插桩下也通过。

## 常见错误

### 1. 只测试正常输入

`mean()` 和 `median()` 的空输入必须测试。没有异常路径测试时，函数很容易在真实边界上返回错误值或触发未定义行为。

### 2. 测试共享临时文件或全局状态

文件测试应使用 fixture 创建独立临时目录，并在 `TearDown()` 清理。共享一个固定文件名会让测试顺序影响结果，尤其在并行测试或失败中断后更明显。

### 3. 让随机过程没有记录种子

如果测试依赖随机输入，必须记录 seed；如果函数本身做采样或划分，最好把 seed 作为显式参数传入。这样失败才能复跑。

### 4. 把所有用例藏在一个 CTest 测试里

如果 CTest 只看到一个大测试可执行文件，CI 报告会变粗。`gtest_discover_tests()` 可以把 GoogleTest 用例展开成独立 CTest 测试，失败时定位更直接。

### 5. 只看通过，不保存失败样例

失败输出是调试材料。本文故意保留一个不进入 CTest 的失败示例，是为了说明 expected/actual 的信息结构。真实项目里，修复 bug 后应把失败输入转成回归测试。

## 实践检查清单

为 C++ 项目添加 GoogleTest 时，可以按这个顺序检查：

1. GoogleTest 版本是否固定，下载内容是否有哈希或其他可审计来源？
2. 测试 target 是否通过链接业务库 target 复用实现？
3. 是否有普通输入、异常路径、边界输入和文件/状态类 fixture？
4. 参数化测试是否有稳定、可读的 case 名称？
5. CTest 是否能发现每个 GoogleTest 用例？
6. 是否能用 `--gtest_filter` 只复跑一个测试族？
7. 随机过程是否有固定 seed，并在输出或命令中可见？
8. 是否有 sanitizer build tree 复跑同一组测试？

## 练习

1. 给 `read_values()` 增加对行首行尾空白的处理，并增加对应 GoogleTest 用例。
2. 给 `split_train_test()` 增加 `train_count == 0` 和 `train_count == values.size()` 的边界测试。
3. 删除 `ValuesFileTest::TearDown()` 中的清理逻辑，观察重复运行或失败中断后临时目录如何残留，再恢复清理。
4. 把 `qstats_failing_demo` 的错误期望修正为 `2.0`，然后将它改造成一个正式回归测试。

## 参考资料

- [GoogleTest Quickstart: Building with CMake](https://google.github.io/googletest/quickstart-cmake.html)
- [GoogleTest Primer](https://google.github.io/googletest/primer.html)
- [GoogleTest Advanced: value-parameterized tests](https://google.github.io/googletest/advanced.html#value-parameterized-tests)
- [GoogleTest Advanced: running tests](https://google.github.io/googletest/advanced.html#running-tests)
- [CMake module: GoogleTest](https://cmake.org/cmake/help/latest/module/GoogleTest.html)
- [CMake module: FetchContent](https://cmake.org/cmake/help/latest/module/FetchContent.html)
{% endraw %}
