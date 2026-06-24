---
layout: post
title: "头文件、源文件和 undefined reference：C++ 多文件构建的真实边界"
date: 2026-06-24 08:30:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
tags: [cpp, linux, linker, headers, cmake]
---

> 主题：Linux C++ 工程开发 / 头文件 / 源文件 / 链接错误  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3 环境下本地执行验证。不同系统的临时文件名、路径和诊断格式可能略有差异，但符号关系和错误类型应保持一致。

上一篇文章把 `g++ main.cpp -o app` 拆成预处理、编译、汇编和链接。现在进入 C++ 工程里更常见的问题：文件多了以后，头文件、源文件和链接器到底各自负责什么？为什么包含了头文件仍然会出现 `undefined reference`？为什么把函数体写进头文件有时又会变成 `multiple definition`？

这篇文章的核心结论是：**头文件主要让编译器看见声明；源文件编译出的目标文件提供定义；链接器负责把引用解析到定义。** 只要把这三层混在一起，C++ 多文件项目就会开始出现看似矛盾的错误。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 区分 declaration、definition、translation unit 和 object file。
2. 用 `nm -C` 判断一个目标文件是在定义符号还是引用符号。
3. 复现并解释 `undefined reference`。
4. 复现并解释头文件普通函数定义导致的 `multiple definition`。
5. 说明 `inline` 和 `static` 为什么能让头文件里的函数通过链接，但语义并不相同。
6. 用最小 CMake target 表达“库提供实现，程序链接库”。

## 先修知识

需要已经理解：

- `.cpp` 可以单独编译成 `.o`；
- 链接器把多个 `.o` 和库合成可执行文件；
- `nm -C` 能查看目标文件符号，`T` 常表示当前目标文件提供的代码符号，`U` 表示当前目标文件引用但未定义的符号。

如果这些概念还不清楚，可以先读上一篇：

- [C++ 程序如何从源码变成可执行文件](/computer-science-teaching/2026/06/24/cpp-build-pipeline-source-to-executable.html)

## 核心模型

一个典型多文件 C++ 项目里，头文件和源文件的关系可以这样理解：

![C++ 头文件、源文件和链接器关系](/assets/diagrams/cpp-headers-linking.svg)

`math_utils.hpp` 被 `main.cpp` 和 `math_utils.cpp` 同时包含。对编译器来说，头文件让两个翻译单元都看见同一组函数声明：

```cpp
int add(int a, int b);
int multiply(int a, int b);
```

`main.cpp` 只调用这些函数，所以它编译出来的 `main.o` 里会有 `U add(int, int)` 和 `U multiply(int, int)`。`U` 可以读成 unresolved reference：当前目标文件知道要调用谁，但自己没有函数体。

`math_utils.cpp` 提供函数体，所以它编译出的 `math_utils.o` 里会有 `T add(int, int)` 和 `T multiply(int, int)`。链接时，链接器把 `main.o` 里的 `U` 解析到 `math_utils.o` 里的 `T`，可执行文件才成立。

这也是 GNU `ld` 文档中“链接器组合目标文件、重定位数据并绑定符号引用”这句话在 C++ 项目里的具体表现。GCC 手册也把编译过程分为 preprocessing、compilation、assembly 和 linking，并说明 `-c` 会生成目标文件而不执行链接。

## 建立实验目录

创建目录：

```bash
mkdir -p cpp-headers-linking/{include,src,build/manual,build/cmake,reports}
cd cpp-headers-linking
```

写头文件，只放声明：

```bash
cat > include/math_utils.hpp <<'CPP'
#pragma once

int add(int a, int b);
int multiply(int a, int b);
CPP
```

写实现文件，放定义：

```bash
cat > src/math_utils.cpp <<'CPP'
#include "math_utils.hpp"

int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}
CPP
```

写主程序：

```bash
cat > src/main.cpp <<'CPP'
#include "math_utils.hpp"
#include <iostream>

int main() {
    std::cout << "add=" << add(2, 3) << '\n';
    std::cout << "multiply=" << multiply(4, 5) << '\n';
    return 0;
}
CPP
```

这里有一个有意安排：`main.cpp` 只包含头文件，不直接包含 `math_utils.cpp`。真实 C++ 项目应该编译每个 `.cpp`，再链接目标文件或库；把 `.cpp` 互相 `#include` 通常会制造更混乱的构建边界。

## 只编译主程序：声明足够让编译通过

执行：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/main.cpp -o build/manual/main.o
```

参数说明：

- `-Iinclude` 把 `include/` 加入头文件搜索路径。
- `-c` 只生成目标文件，不链接。GCC 官方手册对 `-c` 的定义正是“编译或汇编源文件，但不链接”。

查看 `main.o` 的关键符号：

```bash
nm -C build/manual/main.o | grep -E " main$| add\(int, int\)| multiply\(int, int\)"
```

本地实验输出：

```text
                 U add(int, int)
                 U multiply(int, int)
0000000000000000 T main
```

这说明三件事：

1. `main` 的函数体在 `main.o` 里，所以是 `T main`。
2. `add` 和 `multiply` 只有声明可见，没有定义进入这个目标文件，所以是 `U`。
3. 编译器允许这种状态存在，因为 `-c` 不要求最终解析所有外部符号。

这一步是理解 `undefined reference` 的关键：**编译通过只说明当前翻译单元内部的语法、类型和声明可见性基本成立；它不证明整个程序已经有所有函数定义。**

## 忘记链接实现文件：`undefined reference`

现在故意只拿 `main.o` 链接：

```bash
g++ build/manual/main.o -o build/manual/missing_math
```

本地实验输出节选：

```text
/usr/bin/ld: build/manual/main.o: in function `main':
main.cpp:(.text+0x34): undefined reference to `add(int, int)'
/usr/bin/ld: main.cpp:(.text+0x76): undefined reference to `multiply(int, int)'
collect2: error: ld returned 1 exit status
```

这个错误来自链接阶段。它不是说头文件没被包含，也不是说 `add` 的声明错了。恰恰相反，编译器已经根据声明生成了对 `add(int, int)` 和 `multiply(int, int)` 的调用。链接器失败的原因是：当前参与链接的输入里没有任何目标文件提供这两个函数的定义。

可以把这句话压缩成一个排错规则：

> 如果错误是 `undefined reference to f(...)`，先问：哪个 `.o` 或库应该提供 `f(...)` 的定义？它是否真的参加了这次链接？

## 编译实现文件：定义出现在另一个目标文件里

编译实现文件：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/math_utils.cpp -o build/manual/math_utils.o
```

查看符号：

```bash
nm -C build/manual/math_utils.o | grep -E " add\(int, int\)| multiply\(int, int\)"
```

本地实验输出：

```text
0000000000000000 T add(int, int)
0000000000000018 T multiply(int, int)
```

现在 `math_utils.o` 提供了强定义。把两个目标文件一起链接：

```bash
g++ build/manual/main.o build/manual/math_utils.o -o build/manual/math_app
./build/manual/math_app
```

输出：

```text
add=5
multiply=20
```

此时链接器完成了最基本的符号解析：

| 目标文件 | 符号状态 | 含义 |
|---|---|---|
| `main.o` | `U add`、`U multiply` | 调用这些函数，但不提供函数体 |
| `math_utils.o` | `T add`、`T multiply` | 提供函数体 |
| 链接结果 | 可执行文件 | `U` 被解析到对应 `T` |

## 为什么头文件通常只放声明

如果普通函数定义写在头文件里，会发生什么？先写一个错误示例：

```bash
cat > include/bad_math.hpp <<'CPP'
#pragma once

int bad_add(int a, int b) {
    return a + b;
}
CPP
```

再写两个不同源文件，都包含这个头文件：

```bash
cat > src/use_bad_a.cpp <<'CPP'
#include "bad_math.hpp"

int value_a() {
    return bad_add(1, 2);
}
CPP

cat > src/use_bad_b.cpp <<'CPP'
#include "bad_math.hpp"

int value_b() {
    return bad_add(3, 4);
}
CPP
```

写一个主程序调用它们：

```bash
cat > src/bad_main.cpp <<'CPP'
#include <iostream>

int value_a();
int value_b();

int main() {
    std::cout << value_a() + value_b() << '\n';
}
CPP
```

分别编译三个源文件：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/use_bad_a.cpp -o build/manual/use_bad_a.o
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/use_bad_b.cpp -o build/manual/use_bad_b.o
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/bad_main.cpp -o build/manual/bad_main.o
```

查看 `bad_add`：

```bash
nm -C build/manual/use_bad_a.o build/manual/use_bad_b.o | grep "bad_add"
```

本地实验输出：

```text
0000000000000000 T bad_add(int, int)
0000000000000000 T bad_add(int, int)
```

两个目标文件都出现了 `T bad_add(int, int)`。原因很直接：头文件内容会被复制进每个包含它的翻译单元，所以 `use_bad_a.cpp` 和 `use_bad_b.cpp` 都各自生成了一个外部可见的强定义。

链接：

```bash
g++ build/manual/bad_main.o build/manual/use_bad_a.o build/manual/use_bad_b.o -o build/manual/bad_header_app
```

本地实验输出节选：

```text
/usr/bin/ld: build/manual/use_bad_b.o: in function `bad_add(int, int)':
use_bad_b.cpp:(.text+0x0): multiple definition of `bad_add(int, int)'; build/manual/use_bad_a.o:use_bad_a.cpp:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

这就是头文件普通函数定义的风险。编译阶段可以分别通过；到了链接阶段，每个翻译单元都已经编译出一份同名强定义，链接器无法决定最终程序里应该保留哪一个。

## `inline` 修复的是什么

把函数写成 `inline`：

```bash
cat > include/good_inline_math.hpp <<'CPP'
#pragma once

inline int good_add(int a, int b) {
    return a + b;
}
CPP
```

写两个源文件：

```bash
cat > src/use_good_a.cpp <<'CPP'
#include "good_inline_math.hpp"

int good_value_a() {
    return good_add(1, 2);
}
CPP

cat > src/use_good_b.cpp <<'CPP'
#include "good_inline_math.hpp"

int good_value_b() {
    return good_add(3, 4);
}
CPP
```

主程序：

```bash
cat > src/good_main.cpp <<'CPP'
#include <iostream>

int good_value_a();
int good_value_b();

int main() {
    std::cout << good_value_a() + good_value_b() << '\n';
}
CPP
```

编译链接：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/use_good_a.cpp -o build/manual/use_good_a.o
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/use_good_b.cpp -o build/manual/use_good_b.o
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/good_main.cpp -o build/manual/good_main.o
g++ build/manual/good_main.o build/manual/use_good_a.o build/manual/use_good_b.o -o build/manual/good_inline_app
./build/manual/good_inline_app
```

输出：

```text
10
```

查看符号：

```bash
nm -C build/manual/use_good_a.o build/manual/use_good_b.o | grep "good_add" || true
```

本地实验输出：

```text
0000000000000000 W good_add(int, int)
0000000000000000 W good_add(int, int)
```

这里 `W` 是 weak symbol。直观理解是：`inline` 允许相同定义出现在多个翻译单元中，链接器可以合并或选择合适的一份。它解决的是“头文件中定义函数会被多个翻译单元看到”的链接问题。

但要注意：`inline` 的现代语义不是“强制内联优化”。编译器是否真的把调用展开成内联机器码，是优化器的决定。`inline` 在工程边界上更重要的含义是允许符合规则的多处定义。

## `static` 也能通过链接，但语义不同

再看另一个写法：

```bash
cat > include/static_math.hpp <<'CPP'
#pragma once

static int local_add(int a, int b) {
    return a + b;
}
CPP
```

如果这个头文件被多个 `.cpp` 包含，每个翻译单元都会得到一个内部链接的 `local_add`。实验：

```bash
cat > src/use_static_a.cpp <<'CPP'
#include "static_math.hpp"

int static_value_a() {
    return local_add(10, 1);
}
CPP

cat > src/use_static_b.cpp <<'CPP'
#include "static_math.hpp"

int static_value_b() {
    return local_add(20, 2);
}
CPP
```

主程序：

```bash
cat > src/static_main.cpp <<'CPP'
#include <iostream>

int static_value_a();
int static_value_b();

int main() {
    std::cout << static_value_a() + static_value_b() << '\n';
}
CPP
```

编译链接：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/use_static_a.cpp -o build/manual/use_static_a.o
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/use_static_b.cpp -o build/manual/use_static_b.o
g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/static_main.cpp -o build/manual/static_main.o
g++ build/manual/static_main.o build/manual/use_static_a.o build/manual/use_static_b.o -o build/manual/static_header_app
./build/manual/static_header_app
```

输出：

```text
33
```

查看符号：

```bash
nm -C build/manual/use_static_a.o build/manual/use_static_b.o | grep "local_add"
```

本地实验输出：

```text
0000000000000000 t local_add(int, int)
0000000000000000 t local_add(int, int)
```

小写 `t` 通常表示局部代码符号。也就是说，两个目标文件各自有一份只在本翻译单元内部可见的 `local_add`。链接器不会把它们当作冲突的全局强定义。

这和 `inline` 的语义不同：

| 写法 | 是否能放头文件 | 符号直觉 | 适合场景 |
|---|---|---|---|
| 普通非 `inline` 函数定义 | 不适合被多个 `.cpp` 包含 | 多个 `T`，可能 multiple definition | 放 `.cpp` 中 |
| `inline` 函数定义 | 可以 | 多个弱定义或可合并定义 | 小函数、模板相关头文件实现、header-only 接口 |
| `static` 函数定义 | 可以通过链接 | 每个翻译单元一份内部符号 | 只想要本翻译单元私有 helper；头文件中要谨慎 |

## 用 CMake 表达正确关系

手写 `g++ main.o math_utils.o -o app` 能帮助理解链接边界，但真实项目应该让构建系统表达依赖关系。最小 CMake 写法：

```bash
cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.20)
project(cpp_headers_linking LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(math_utils src/math_utils.cpp)
target_include_directories(math_utils PUBLIC include)
target_compile_options(math_utils PRIVATE -Wall -Wextra -Wpedantic)

add_executable(math_app src/main.cpp)
target_link_libraries(math_app PRIVATE math_utils)
target_compile_options(math_app PRIVATE -Wall -Wextra -Wpedantic)
CMAKE
```

构建：

```bash
cmake -S . -B build/cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build/cmake
./build/cmake/math_app
```

本地实验输出节选：

```text
[1/4] Building CXX object CMakeFiles/math_utils.dir/src/math_utils.cpp.o
[2/4] Linking CXX static library libmath_utils.a
[3/4] Building CXX object CMakeFiles/math_app.dir/src/main.cpp.o
[4/4] Linking CXX executable math_app
add=5
multiply=20
```

这个 CMake 片段表达了两个事实：

1. `math_utils` 是一个库 target，它由 `src/math_utils.cpp` 编译产生实现。
2. `math_app` 链接 `math_utils`，因此最终链接时会拿到 `add` 和 `multiply` 的定义。

`target_include_directories(math_utils PUBLIC include)` 的 `PUBLIC` 也有意义：使用 `math_utils` 的目标需要看见它的公共头文件，所以 include 目录是 usage requirement，会传递给链接这个库的目标。CMake 官方文档也强调 `target_include_directories` 是给目标指定 include 目录，并用 `PRIVATE`、`PUBLIC`、`INTERFACE` 区分作用域。

## 排错顺序

遇到 `undefined reference`，不要先乱改 include。按这个顺序查：

1. **确认错误阶段**：错误里是否出现 `/usr/bin/ld`、`collect2`、`undefined reference`？如果是，就是链接阶段。
2. **确认符号名**：错误里缺的是哪个函数或变量？签名是否和你以为的一样？
3. **确认定义存在**：用 `rg "函数名" src include` 找定义；只有声明不够。
4. **确认定义被编译**：对应 `.cpp` 是否真的生成了 `.o`？
5. **确认参与链接**：对应 `.o`、静态库或动态库是否在链接命令里？
6. **确认 CMake target 关系**：应该 `target_link_libraries` 的库是否真的被链接？include 目录不是链接库。
7. **确认签名一致**：命名空间、`const`、参数类型、重载、C/C++ linkage 都可能让你以为是同一个函数，但符号名并不相同。

这个顺序的重点是先定位边界：**头文件解决声明可见性；链接输入解决定义可达性。**

## 常见误解

### 误解 1：`#include` 会把库链接进来

`#include` 只是文本层面的包含，让当前翻译单元看见声明、类型、模板或 inline 定义。它不会自动把某个 `.cpp`、`.o`、`.a` 或 `.so` 加入链接命令。

### 误解 2：头文件里写函数体更方便，所以总是可以这么做

模板、`inline` 函数和 header-only 设计确实会把定义放在头文件里。但普通外部链接函数如果被多个 `.cpp` 包含，就容易制造多个强定义。

### 误解 3：`inline` 就是性能优化

`inline` 不等于强制优化器展开调用。它的工程语义是允许函数定义出现在多个翻译单元中，只要这些定义满足规则。是否真的内联展开由编译器优化决定。

### 误解 4：`static` 只是旧式写法，可以随便替代 `inline`

`static` 在命名空间作用域给函数内部链接。多个翻译单元会各自拥有一份本地函数。这可能能通过链接，但会改变符号可见性和对象身份；它不是 `inline` 的同义词。

### 误解 5：CMake 里 include 目录写对了就不会 undefined reference

include 目录只影响编译器找头文件。链接器需要目标文件或库。CMake 里通常要用 `target_link_libraries` 表达链接关系。

## 一次性复现实验命令

下面是压缩版复现流程。为了篇幅，省略了前面所有解释文字：

```bash
mkdir -p cpp-headers-linking/{include,src,build/manual,build/cmake,reports}
cd cpp-headers-linking

cat > include/math_utils.hpp <<'CPP'
#pragma once
int add(int a, int b);
int multiply(int a, int b);
CPP

cat > src/math_utils.cpp <<'CPP'
#include "math_utils.hpp"
int add(int a, int b) { return a + b; }
int multiply(int a, int b) { return a * b; }
CPP

cat > src/main.cpp <<'CPP'
#include "math_utils.hpp"
#include <iostream>
int main() {
    std::cout << "add=" << add(2, 3) << '\n';
    std::cout << "multiply=" << multiply(4, 5) << '\n';
}
CPP

g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/main.cpp -o build/manual/main.o
nm -C build/manual/main.o | grep -E " main$| add\(int, int\)| multiply\(int, int\)"

g++ build/manual/main.o -o build/manual/missing_math
# 预期：undefined reference to `add(int, int)' 和 `multiply(int, int)'

g++ -std=c++20 -Wall -Wextra -Wpedantic -Iinclude -c src/math_utils.cpp -o build/manual/math_utils.o
nm -C build/manual/math_utils.o | grep -E " add\(int, int\)| multiply\(int, int\)"

g++ build/manual/main.o build/manual/math_utils.o -o build/manual/math_app
./build/manual/math_app
```

如果你想完整复现 `multiple definition`、`inline` 和 `static` 三个头文件实验，可以按正文分段执行。建议不要只复制最后的命令块，因为每个错误的价值在于观察它发生在哪个阶段。

## 练习

1. 把 `multiply` 的声明从头文件删除，但保留 `main.cpp` 的调用。观察这是编译错误还是链接错误。
2. 把 `math_utils.cpp` 里的 `multiply(int, int)` 改成 `multiply(long, long)`，观察 `nm -C` 和链接错误如何变化。
3. 在 `bad_math.hpp` 中把 `bad_add` 改成 `inline`，重新编译链接，确认 `multiple definition` 消失。
4. 用 CMake 构建后，运行 `nm -C build/cmake/libmath_utils.a`，观察静态库里是否有 `add` 和 `multiply`。
5. 把 CMake 中的 `target_link_libraries(math_app PRIVATE math_utils)` 删除，只保留 include 目录，观察错误信息。

## 参考资料与阅读顺序

1. **GCC Overall Options**：理解 `-c`、`-S`、`-E`、`-o` 这些选项如何控制编译阶段。  
   https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html
2. **GNU nm manual**：理解 `nm` 如何显示目标文件符号，以及符号类型字母的大致含义。  
   https://sourceware.org/binutils/docs/binutils/nm.html
3. **GNU ld manual page**：理解链接器组合目标文件、重定位并绑定符号引用的职责。  
   https://man7.org/linux/man-pages/man1/ld.1.html
4. **CMake `target_include_directories`**：理解 include 目录如何绑定到 target，以及 `PRIVATE`、`PUBLIC`、`INTERFACE` 的传播语义。  
   https://cmake.org/cmake/help/latest/command/target_include_directories.html
5. **CMake `add_library`**：理解库 target、object library 和 interface library 的边界。  
   https://cmake.org/cmake/help/latest/command/add_library.html

这篇文章只解决 C++ 多文件项目的第一层边界：声明、定义、目标文件和链接输入。下一步进入 RAII 和资源生命周期时，我们会把注意力从“函数体在哪里”转到“资源由谁拥有，什么时候释放”。
