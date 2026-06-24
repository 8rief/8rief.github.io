---
layout: post
title: "RAII 和资源生命周期：让 C++ 对象负责释放资源"
date: 2026-06-24 08:40:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
tags: [cpp, linux, raii, lifetime, resource-management]
---

> 主题：Linux C++ 工程开发 / RAII / 资源生命周期  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3 环境下本地执行验证。实验使用 Linux 的 `/proc/self/fd` 观察进程内文件描述符数量，因此在非 Linux 系统上需要替换观察方式。

前两篇文章解决了 C++ 程序如何构建，以及头文件、源文件和链接器的边界。这篇进入 C++ 工程开发里更重要的一条线：**资源生命周期**。真实程序不只管理内存，还会管理文件、socket、锁、线程、临时目录、数据库连接和 GPU 句柄。只要资源需要释放，就必须回答两个问题：谁拥有它？什么时候释放？

RAII 的作用就是把这两个问题绑定到对象生命周期上：对象构造时获得资源，对象析构时释放资源。这样，正常返回、提前返回和异常路径都能走到同一个释放动作。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释 RAII 中 acquire、invariant、destructor 和 scope exit 的关系。
2. 用 Linux 文件描述符复现手动资源管理在提前返回时的泄漏。
3. 实现一个最小 `unique_fd`，用析构函数关闭文件描述符。
4. 观察异常路径下 RAII 对象如何释放资源。
5. 说明同一作用域内对象按构造逆序析构。
6. 区分 RAII、`std::ofstream` 和 `std::unique_ptr` 各自管理的资源形态。

## 先修知识

需要知道：

- 函数作用域和局部变量；
- 构造函数与析构函数；
- 文件描述符是 Linux 进程持有的资源；
- `open()` 返回文件描述符，`close()` 释放文件描述符。

如果你还不熟悉 C++ 多文件构建，可以先读：

- [C++ 程序如何从源码变成可执行文件](/computer-science-teaching/2026/06/24/cpp-build-pipeline-source-to-executable.html)
- [头文件、源文件和 undefined reference：C++ 多文件构建的真实边界](/computer-science-teaching/2026/06/24/cpp-headers-source-linking-undefined-reference.html)

## 核心模型

C++ Core Guidelines 把 resource 定义得很宽：内存、文件句柄、socket 和锁都属于资源；资源管理的目标是避免泄漏，也避免持有时间超过需要。cppreference 对 RAII 的总结更接近工程实现：把资源封装进类，构造函数获取资源并建立不变量，析构函数释放资源且不抛异常。

可以把它压缩成一条工程规则：

> 只要某个动作需要成对释放，就让对象析构函数负责释放；不要让每条控制流分支手工记住释放。

![RAII 生命周期](/assets/diagrams/cpp-raii-lifetime.svg)

图里的区别在于释放动作和控制流的关系。手动路径里，`close(fd)` 是一条普通语句；提前返回或异常可能绕开它。RAII 路径里，`close(fd)` 放进析构函数；离开作用域时，析构函数由语言规则触发。

## 建立实验目录

创建目录：

```bash
mkdir -p cpp-raii-lifetime/{include,src,build/manual,build/cmake,reports}
cd cpp-raii-lifetime
```

我们先写一个最小 `unique_fd`。它只做一件事：拥有一个 Linux 文件描述符，并在析构时调用 `close()`。

```bash
cat > include/unique_fd.hpp <<'CPP'
#pragma once

#include <unistd.h>
#include <utility>

class unique_fd {
public:
    explicit unique_fd(int fd = -1) noexcept : fd_(fd) {}

    unique_fd(const unique_fd&) = delete;
    unique_fd& operator=(const unique_fd&) = delete;

    unique_fd(unique_fd&& other) noexcept : fd_(std::exchange(other.fd_, -1)) {}

    unique_fd& operator=(unique_fd&& other) noexcept {
        if (this != &other) {
            reset();
            fd_ = std::exchange(other.fd_, -1);
        }
        return *this;
    }

    ~unique_fd() noexcept {
        reset();
    }

    int get() const noexcept { return fd_; }
    explicit operator bool() const noexcept { return fd_ >= 0; }

    int release() noexcept {
        return std::exchange(fd_, -1);
    }

    void reset(int next = -1) noexcept {
        if (fd_ >= 0) {
            ::close(fd_);
        }
        fd_ = next;
    }

private:
    int fd_ = -1;
};
CPP
```

这段代码体现了 RAII wrapper 的几个基本设计点：

- `fd_` 是被拥有的资源句柄；
- 拷贝被删除，因为两个对象同时拥有同一个 fd 会导致重复关闭；
- move 构造和 move 赋值转移所有权；
- 析构函数调用 `reset()`，最终执行 `close()`；
- 析构函数标成 `noexcept`，因为析构阶段抛异常会让错误处理复杂化。

`release()` 是一个例外通道：它把 fd 交出去，并让当前对象不再负责关闭。真实项目里要谨慎使用，因为它会把资源管理责任重新交给调用者。

## 实验程序

写实验源文件：

```bash
cat > src/raii_lifetime.cpp <<'CPP'
#include "unique_fd.hpp"

#include <fcntl.h>
#include <unistd.h>

#include <cerrno>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace fs = std::filesystem;

int count_fds() {
    int count = 0;
    for (const auto& entry : fs::directory_iterator("/proc/self/fd")) {
        (void)entry;
        ++count;
    }
    return count;
}

int open_report_file() {
    int fd = ::open("reports/raii_demo.txt", O_CREAT | O_RDWR | O_APPEND, 0644);
    if (fd < 0) {
        throw std::runtime_error(std::string("open failed: ") + std::strerror(errno));
    }
    return fd;
}

void write_line(int fd, const std::string& line) {
    std::string data = line + "\n";
    if (::write(fd, data.data(), data.size()) < 0) {
        throw std::runtime_error(std::string("write failed: ") + std::strerror(errno));
    }
}

void manual_leak_on_early_return() {
    int fd = open_report_file();
    write_line(fd, "manual path opened a file descriptor");
    return; // close(fd) is skipped: this is the bug we want to observe.
}

void raii_close_on_early_return() {
    unique_fd fd(open_report_file());
    write_line(fd.get(), "raii path opened a file descriptor");
    return; // unique_fd::~unique_fd closes the descriptor here.
}

void raii_close_on_exception() {
    unique_fd fd(open_report_file());
    write_line(fd.get(), "exception path opened a file descriptor");
    throw std::runtime_error("simulated failure after acquisition");
}
CPP
```

这三个函数分别对应三条控制流：

1. `manual_leak_on_early_return()`：手工管理 fd，提前返回时没有执行 `close(fd)`。
2. `raii_close_on_early_return()`：用 `unique_fd` 接管 fd，提前返回也会析构。
3. `raii_close_on_exception()`：抛异常时发生栈展开，`unique_fd` 仍会析构。

继续追加一个构造/析构顺序实验，以及标准库 `std::ofstream` 的 RAII 示例：

```bash
cat >> src/raii_lifetime.cpp <<'CPP'

struct Tracer {
    explicit Tracer(std::string name) : name_(std::move(name)) {
        std::cout << "construct " << name_ << '\n';
    }

    ~Tracer() noexcept {
        std::cout << "destruct " << name_ << '\n';
    }

    std::string name_;
};

void show_reverse_destruction() {
    Tracer first("first");
    Tracer second("second");
    Tracer third("third");
    std::cout << "leaving scope\n";
}

void ofstream_raii_demo() {
    {
        std::ofstream out("reports/ofstream_raii.txt");
        out << "fstream also closes at scope exit\n";
    }

    std::ifstream in("reports/ofstream_raii.txt");
    std::string line;
    std::getline(in, line);
    std::cout << "fstream readback: " << line << '\n';
}

int main() {
    fs::create_directories("reports");

    std::cout << "fd count at start: " << count_fds() << '\n';

    for (int i = 0; i < 3; ++i) {
        manual_leak_on_early_return();
    }
    std::cout << "fd count after 3 manual leaks: " << count_fds() << '\n';

    for (int i = 0; i < 3; ++i) {
        raii_close_on_early_return();
    }
    std::cout << "fd count after 3 RAII early returns: " << count_fds() << '\n';

    try {
        raii_close_on_exception();
    } catch (const std::exception& e) {
        std::cout << "caught: " << e.what() << '\n';
    }
    std::cout << "fd count after RAII exception: " << count_fds() << '\n';

    show_reverse_destruction();
    ofstream_raii_demo();
}
CPP
```

`count_fds()` 通过 `/proc/self/fd` 统计当前进程打开的文件描述符数量。这个数字不是跨环境固定值；我们关注的是变化趋势：手工泄漏后计数增长，RAII 路径不继续增长。

## 编译并运行

执行：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude src/raii_lifetime.cpp -o build/manual/raii_lifetime
./build/manual/raii_lifetime
```

本地实验输出：

```text
fd count at start: 4
fd count after 3 manual leaks: 7
fd count after 3 RAII early returns: 7
caught: simulated failure after acquisition
fd count after RAII exception: 7
construct first
construct second
construct third
leaving scope
destruct third
destruct second
destruct first
fstream readback: fstream also closes at scope exit
```

逐行解释：

- `fd count at start: 4` 是进程初始状态，具体数值和环境有关。
- 手工路径调用 3 次后，计数从 4 增到 7，说明 3 个 fd 留在进程里。
- RAII 提前返回路径再调用 3 次，计数仍是 7，没有继续增长。
- 异常路径执行后，计数仍是 7，说明栈展开期间 `unique_fd` 析构并关闭 fd。
- `third`、`second`、`first` 的析构顺序和构造顺序相反。
- `std::ofstream` 在块作用域结束时关闭并刷新文件，随后 `ifstream` 能读回内容。

查看写入文件：

```bash
sed -n '1,20p' reports/raii_demo.txt
sed -n '1,5p' reports/ofstream_raii.txt
```

本地输出：

```text
manual path opened a file descriptor
manual path opened a file descriptor
manual path opened a file descriptor
raii path opened a file descriptor
raii path opened a file descriptor
raii path opened a file descriptor
exception path opened a file descriptor
```

```text
fstream also closes at scope exit
```

文件内容说明所有路径都实际写入了数据。文件描述符计数说明资源释放策略不同。

## 为什么 RAII 对异常路径重要

如果一个函数有多条返回路径，手工 `close()` 很容易漏掉一条。异常会让问题更明显：抛出异常后，普通语句级别的清理代码不会继续执行；局部对象析构会在栈展开过程中执行。

因此，RAII 的核心价值在于错误路径设计。它把资源释放从“程序员记得在每个分支写清理语句”改成“语言负责在作用域结束时调用析构函数”。这也是 C++ Core Guidelines 强调资源管理和 resource safety 的原因之一。

## 构造逆序析构的含义

实验输出：

```text
construct first
construct second
construct third
leaving scope
destruct third
destruct second
destruct first
```

这个顺序让后构造的对象可以安全依赖先构造的对象。假设 `third` 使用 `second`，`second` 使用 `first`，离开作用域时先销毁 `third`，再销毁 `second`，最后销毁 `first`，依赖方向就不会被提前破坏。

这条规则对锁、临时文件、事务和日志对象都很重要。你可以用局部变量顺序表达资源释放顺序，减少函数末尾手工 cleanup 的遗漏风险。

## `std::ofstream` 已经是 RAII 对象

示例中的 `ofstream_raii_demo()` 没有显式 `close()`：

```cpp
{
    std::ofstream out("reports/ofstream_raii.txt");
    out << "fstream also closes at scope exit\n";
}
```

块作用域结束时，`out` 析构。标准库文件流对象会管理关联文件，`close()` 是它的成员函数；在常规用法里，把文件流放进局部作用域就能让生命周期清晰可见。

这也是学习 RAII 的一个好起点：先识别标准库中已经替你做好的 RAII 类型，例如 `std::fstream`、`std::lock_guard`、`std::unique_ptr`。cppreference 对 `std::unique_ptr` 的说明也强调它拥有并管理对象，在 `unique_ptr` 销毁或重置时释放对象。

## 最小 CMake 构建

写 `CMakeLists.txt`：

```bash
cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.20)
project(cpp_raii_lifetime LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(raii_lifetime src/raii_lifetime.cpp)
target_include_directories(raii_lifetime PRIVATE include)
target_compile_options(raii_lifetime PRIVATE -Wall -Wextra -Wpedantic)
CMAKE
```

构建运行：

```bash
cmake -S . -B build/cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/cmake
./build/cmake/raii_lifetime
```

本地实验输出节选：

```text
[1/2] Building CXX object CMakeFiles/raii_lifetime.dir/src/raii_lifetime.cpp.o
[2/2] Linking CXX executable raii_lifetime
fd count at start: 4
fd count after 3 manual leaks: 7
fd count after 3 RAII early returns: 7
caught: simulated failure after acquisition
fd count after RAII exception: 7
```

## sanitizer 检查补充

这篇主要观察文件描述符，不是内存越界。但我们仍然可以用 AddressSanitizer 和 UndefinedBehaviorSanitizer 做基础运行检查：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic \
  -fsanitize=address,undefined \
  -fno-omit-frame-pointer -g \
  -Iinclude src/raii_lifetime.cpp \
  -o build/manual/raii_lifetime_asan

./build/manual/raii_lifetime_asan
```

本地运行没有报告 ASan/UBSan 错误，并输出同样的生命周期观察结果。注意这不是“没有 fd 泄漏”的证明；fd 泄漏是通过 `/proc/self/fd` 计数观察到的。不同工具覆盖不同错误类别，不能用一个绿色检查替代全部验证。

## 常见误解

### 误解 1：RAII 只是在说智能指针

智能指针是 RAII 的典型应用，但 RAII 管理的是资源，不只管理内存。文件描述符、socket、mutex、临时文件、事务句柄都可以用同一思路管理。

### 误解 2：程序退出时操作系统会回收资源，所以进程内泄漏无所谓

进程退出时，操作系统会回收文件描述符和内存等资源。但长时间运行的服务不会频繁退出。每次请求泄漏一个 fd，最终会耗尽进程或系统允许的文件描述符数量。

### 误解 3：析构函数里可以随便抛异常

RAII 的释放路径应该可靠。析构函数抛异常会和栈展开、错误处理交织，容易导致终止或隐藏真实错误。资源释放函数通常应设计成不抛异常；必要时记录错误或提供显式 `close()`/`commit()` 操作处理可恢复失败。

### 误解 4：`release()` 可以经常用

`release()` 会让 RAII 对象放弃所有权。如果调用者没有立刻把资源交给另一个 owner，泄漏风险又回来了。它适合边界转移，不适合日常使用。

### 误解 5：RAII 会让代码变慢

RAII 只是把获取和释放放进对象生命周期。`unique_fd` 的析构里调用一次 `close()`，这本来就是必须执行的操作。C++ Core Guidelines 的整体设计目标之一是使用合适抽象时保持零额外开销或接近零额外开销。

## 一次性复现实验命令

如果你想快速复现实验，可以把本文代码保存后运行：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude src/raii_lifetime.cpp -o build/manual/raii_lifetime
./build/manual/raii_lifetime

cmake -S . -B build/cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/cmake
./build/cmake/raii_lifetime

g++ -std=c++20 -Wall -Wextra -Wpedantic \
  -fsanitize=address,undefined \
  -fno-omit-frame-pointer -g \
  -Iinclude src/raii_lifetime.cpp \
  -o build/manual/raii_lifetime_asan
./build/manual/raii_lifetime_asan
```

建议你重点观察三处输出：

1. 手工路径后 fd 计数是否增长；
2. RAII 提前返回和异常路径是否继续增长 fd 计数；
3. 局部对象析构顺序是否和构造顺序相反。

## 练习

1. 给 `unique_fd` 加一个 `std::cerr << "close fd=" << fd_` 的日志，观察提前返回和异常路径是否都会打印关闭动作。
2. 删除 `unique_fd` 的 move 构造函数，再尝试写一个返回 `unique_fd` 的工厂函数，观察编译错误或行为变化。
3. 把 `release()` 调用加到 `raii_close_on_early_return()` 中，然后不手动关闭返回 fd，观察 fd 计数是否增长。
4. 用 `std::lock_guard<std::mutex>` 写一个类似示例：构造时加锁，析构时解锁。思考它和 `unique_fd` 的共同点。
5. 把 `open_report_file()` 改成打开不存在目录下的文件，观察构造前失败和构造后失败在资源管理上的差异。

## 参考资料与阅读顺序

1. **C++ Core Guidelines：P.8 和 R. Resource management**。先读 P.8，再读资源管理章节，理解“不要泄漏资源”和 owner 的概念。  
   https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-resource
2. **cppreference：RAII**。用于确认 RAII 的标准表述：构造获取资源并建立不变量，析构释放资源且不抛异常。  
   https://en.cppreference.com/w/cpp/language/raii
3. **cppreference：`std::unique_ptr`**。用于理解独占所有权、析构释放和 move-only 语义。  
   https://en.cppreference.com/w/cpp/memory/unique_ptr
4. **cppreference：`std::basic_fstream`**。用于理解标准库文件流对象的文件操作接口，例如 `open()`、`close()` 和 `is_open()`。  
   https://en.cppreference.com/w/cpp/io/basic_fstream

这篇文章建立了 RAII 的最小工程模型：资源必须有 owner，owner 的析构函数负责释放，作用域决定释放时机。下一篇进入 `unique_ptr`、`shared_ptr` 和 raw pointer 时，我们会把这个模型推广到动态对象所有权，并解释为什么 C++ 代码里“能拿到地址”不等于“拥有对象”。
