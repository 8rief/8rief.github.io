---
layout: post
title: "C++ 程序如何从源码变成可执行文件"
date: 2026-06-24 22:10:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
tags: [cpp, linux, compiler, linker, reproducible]
---

> 主题：Linux C++ 工程开发 / 编译链接 / 可复现实验  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0 环境下本地执行验证。不同发行版、编译器版本或安全加固选项会让部分输出略有差异，但观察方法和概念边界相同。

学 C++ 时，如果只把注意力放在语法上，很快会遇到一类看起来“不像语法问题”的错误：头文件明明包含了，为什么还是 `undefined reference`？程序能编译，为什么运行时找不到动态库？`g++ main.cpp -o app` 成功了，背后到底生成了什么？

这篇文章解决第一个基础问题：**一个 C++ 源文件如何经过预处理、编译、汇编和链接，变成 Linux 上可以运行的 ELF 可执行文件**。理解这条链路之后，后面的 CMake、库依赖、调试符号、ABI、sanitizer 和部署问题才有共同语言。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 把 `g++ main.cpp -o app` 拆成预处理、编译、汇编和链接四步。
2. 区分 `.cpp`、`.ii`、`.s`、`.o` 和可执行文件。
3. 用 `file`、`nm -C`、`ldd`、`readelf` 观察目标文件和可执行文件。
4. 解释一个最小的 `undefined reference` 链接错误。
5. 明白为什么“有声明”不等于“链接器能找到定义”。

## 先修知识

你只需要会基本 Linux 命令，并安装了 C++ 工具链：

```bash
sudo apt update
sudo apt install -y build-essential binutils
```

检查版本：

```bash
g++ --version
```

本文实验环境输出为：

```text
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

如果你的版本不同，不必追求逐字一致。教学重点是每一步产物的类型和含义。

## 核心模型：C++ 构建不是一步

平时写的命令通常是：

```bash
g++ -std=c++20 main.cpp -o app
```

这条命令把多个阶段合并执行了。拆开看，它至少包含：

1. **预处理**：处理 `#include`、宏、条件编译，生成展开后的翻译单元。
2. **编译**：把预处理后的 C++ 翻译成汇编。
3. **汇编**：把汇编变成目标文件，目标文件里有机器码和符号表，但还不是最终程序。
4. **链接**：把多个目标文件和库拼成可执行文件，并解析符号引用。
5. **加载运行**：程序启动时，动态加载器再装入需要的共享库。

![C++ 构建流水线](/assets/diagrams/cpp-build-pipeline.svg)

这条流水线最重要的分界是：**编译器只需要看见声明就能生成调用代码；链接器必须找到定义才能生成最终可执行文件**。很多 C++ 工程错误都发生在这个分界处。

## 建立实验目录

先创建一个干净目录：

```bash
mkdir -p cpp-build-pipeline/src cpp-build-pipeline/build
cd cpp-build-pipeline
```

写一个最小程序：

```bash
cat > src/main.cpp <<'CPP'
#include <iostream>
#include <string>

std::string make_message(const std::string& name) {
    return "hello, " + name;
}

int main() {
    std::cout << make_message("cpp") << '\n';
    return 0;
}
CPP
```

这个例子故意用了 `iostream` 和 `string`。它比 `printf("hello")` 更适合观察 C++ 构建过程，因为标准库会带出更多符号和动态库依赖。

## 第一步：预处理

执行：

```bash
g++ -std=c++20 -Wall -Wextra -pedantic -E src/main.cpp -o build/main.ii
```

参数含义：

- `-std=c++20`：显式指定 C++20，不依赖编译器默认值。
- `-Wall -Wextra -pedantic`：打开常用警告，尽早暴露问题。
- `-E`：只运行预处理阶段，不继续编译。
- `-o build/main.ii`：把输出写入文件。

观察输出行数和开头：

```bash
wc -l build/main.ii
sed -n '1,8p' build/main.ii
```

本地实验输出节选：

```text
43177 build/main.ii
# 0 "src/main.cpp"
# 0 "<built-in>"
# 0 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 0 "<command-line>" 2
# 1 "src/main.cpp"
# 1 "/usr/include/c++/13/iostream" 1 3
```

只有十来行的源码，预处理后变成四万多行。原因是 `#include <iostream>` 和 `#include <string>` 会把相关头文件内容展开进这个翻译单元。这里要建立一个重要认识：**头文件参与编译，不是运行时才去找**。头文件越复杂，单个翻译单元越大，编译成本通常也越高。

## 第二步：编译成汇编

执行：

```bash
g++ -std=c++20 -Wall -Wextra -pedantic -S src/main.cpp -o build/main.s
```

`-S` 表示生成汇编后停止。查看我们写的函数名是否出现在汇编中：

```bash
grep -n "make_message" build/main.s | head
```

本地实验输出节选：

```text
209:    .globl  _Z12make_messageRKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE
210:    .type   _Z12make_messageRKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE, @function
211:_Z12make_messageRKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE:
284:    call    _Z12make_messageRKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE
```

这里出现的长名字是 C++ name mangling 的结果。C++ 支持函数重载、命名空间、类成员函数和模板，链接器需要一个能区分这些信息的符号名，所以源码里的 `make_message` 会被编码成更长的符号。后面使用 `nm -C` 时，`-C` 会把这种符号反解成人更容易读的形式。

## 第三步：生成目标文件

执行：

```bash
g++ -std=c++20 -Wall -Wextra -pedantic -c src/main.cpp -o build/main.o
```

`-c` 表示只编译/汇编成目标文件，不链接。先看文件类型：

```bash
file build/main.o
```

本地实验输出：

```text
build/main.o: ELF 64-bit LSB relocatable, x86-64, version 1 (SYSV), not stripped
```

关键词是 `relocatable`。它说明 `main.o` 是一个**可重定位目标文件**，里面已经有机器码，但地址和外部符号还没有完全确定。

再看符号表：

```bash
nm -C build/main.o
```

输出很多，先抓住两类符号：

```text
0000000000000000 T make_message(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&)
                 U std::cout
                 U operator new(unsigned long)
0000000000000057 T main
```

`nm` 左侧的字母很关键：

| 标记 | 含义 | 在这里怎么理解 |
|---|---|---|
| `T` | 当前目标文件里定义的 text/code 符号 | `main` 和 `make_message` 是我们这个文件提供的函数 |
| `U` | undefined，当前目标文件引用但没有定义的符号 | `std::cout`、`operator new` 需要从标准库等外部对象中解析 |
| `W` | weak symbol，弱符号 | 常见于模板、inline 或标准库实现细节 |

这一步解释了为什么目标文件还不是最终程序：它还带着一批 `U` 符号，等待链接器去库或其他目标文件中寻找定义。

## 第四步：链接成可执行文件

执行：

```bash
g++ build/main.o -o build/hello_cpp
./build/hello_cpp
```

输出：

```text
hello, cpp
```

再看文件类型：

```bash
file build/hello_cpp
```

本地实验输出节选：

```text
build/hello_cpp: ELF 64-bit LSB pie executable, x86-64, dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, not stripped
```

几个关键词：

- `ELF`：Linux 常见的可执行/目标文件格式。
- `pie executable`：位置无关可执行文件，现代发行版通常默认启用，有利于地址空间随机化。
- `dynamically linked`：程序依赖动态库，不是把所有库代码都塞进一个文件。
- `interpreter /lib64/ld-linux-x86-64.so.2`：运行时由动态加载器装入共享库。

查看动态库依赖：

```bash
ldd build/hello_cpp | sed -n '1,8p'
```

本地实验输出节选：

```text
linux-vdso.so.1
libstdc++.so.6 => /lib/x86_64-linux-gnu/libstdc++.so.6
libgcc_s.so.1 => /lib/x86_64-linux-gnu/libgcc_s.so.1
libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6
libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6
/lib64/ld-linux-x86-64.so.2
```

这解释了另一个常见现象：一个 C++ 程序即使只有一个 `.cpp` 文件，最终也可能依赖 `libstdc++`、`libgcc_s`、`libc`、`libm` 等共享库。部署时如果目标机器上的库版本、ABI 或搜索路径不兼容，就可能出现运行时问题。

还可以查看 ELF 头：

```bash
readelf -h build/hello_cpp
```

输出节选：

```text
Class:                             ELF64
Data:                              2's complement, little endian
Type:                              DYN (Position-Independent Executable file)
Machine:                           Advanced Micro Devices X86-64
Entry point address:               0x21e0
```

这里的 `Entry point address` 不是 `main` 的源码地址。程序启动会先经过运行时入口，完成 C/C++ 运行时初始化后再调用 `main`。因此，不要把“程序入口”和“你写的 `main` 函数”简单等同。

## 链接错误实验：只有声明，没有定义

现在构造一个常见错误。先写一个只声明函数、不提供定义的文件：

```bash
cat > src/use_math.cpp <<'CPP'
#include <iostream>

int add(int a, int b); // declaration only

int main() {
    std::cout << add(2, 3) << '\n';
    return 0;
}
CPP
```

编译链接：

```bash
g++ -std=c++20 -Wall -Wextra -pedantic src/use_math.cpp -o build/use_math_missing
```

本地实验得到的错误节选：

```text
/usr/bin/ld: ... in function `main':
use_math.cpp:(.text+0x13): undefined reference to `add(int, int)'
collect2: error: ld returned 1 exit status
```

这个错误不是说 `add` 的声明语法错了。编译器已经接受了 `int add(int a, int b);`，并生成了“调用某个 `add(int, int)` 函数”的目标代码。问题发生在链接阶段：链接器找遍当前参与链接的目标文件和默认库，仍然找不到 `add(int, int)` 的函数体。

补上定义：

```bash
cat > src/math.cpp <<'CPP'
int add(int a, int b) {
    return a + b;
}
CPP
```

把两个源文件一起交给链接器：

```bash
g++ -std=c++20 -Wall -Wextra -pedantic src/use_math.cpp src/math.cpp -o build/use_math_ok
./build/use_math_ok
```

输出：

```text
5
```

这就是声明和定义的边界：

- 声明告诉编译器“这个函数存在，签名长这样”。
- 定义提供函数体，让链接器能把调用指向真实代码。
- 头文件通常放声明，`.cpp` 文件通常放定义。
- 只有声明没有定义时，单个文件可以编译成 `.o`，但最终链接会失败。

## 为什么有时错误发生在编译期，有时发生在链接期

可以用一个简单判断：

| 阶段 | 它主要检查什么 | 常见错误 |
|---|---|---|
| 预处理 | include 路径、宏展开、条件编译 | 找不到头文件、宏展开异常 |
| 编译 | 语法、类型、声明可见性 | 类型不匹配、变量未声明、模板实例化错误 |
| 汇编 | 汇编到机器码 | 普通 C++ 开发较少直接接触 |
| 链接 | 符号定义是否齐全，库是否匹配 | `undefined reference`、重复定义、库顺序问题 |
| 运行 | 动态库加载、实际输入、运行时状态 | 找不到 `.so`、崩溃、未定义行为暴露 |

C++ 的复杂性来自这些阶段都可能失败，而且失败信息经常指向不同层次。排错时先判断“错误来自哪个阶段”，比直接搜索错误文本更可靠。

## 常见误解

### 误解 1：包含头文件就等于链接了实现

包含头文件只让声明进入当前翻译单元。除非函数定义也在头文件中，例如模板或 `inline` 函数，否则链接时仍需要对应的 `.o`、静态库或动态库。

### 误解 2：`.o` 文件已经是程序

`.o` 里有机器码，但还可能有未解析符号。只有链接后生成的可执行文件才能直接运行。

### 误解 3：`main` 是操作系统直接调用的第一行 C++ 代码

Linux 加载 ELF 后会进入运行时入口，完成动态链接、运行时初始化、全局对象初始化等动作，然后才调用 `main`。这就是为什么 `readelf` 看到的 entry point 不等于源码里的 `main`。

### 误解 4：编译器默认标准足够稳定

不同 GCC/Clang 版本的默认 C++ 标准可能不同。教学、项目和 CI 都应该显式写 `-std=c++20` 或在 CMake 中设置 `CMAKE_CXX_STANDARD`。

## 本文命令清单

如果你想一次性复现实验，可以按这个顺序执行：

```bash
mkdir -p cpp-build-pipeline/src cpp-build-pipeline/build
cd cpp-build-pipeline

cat > src/main.cpp <<'CPP'
#include <iostream>
#include <string>

std::string make_message(const std::string& name) {
    return "hello, " + name;
}

int main() {
    std::cout << make_message("cpp") << '\n';
    return 0;
}
CPP

g++ -std=c++20 -Wall -Wextra -pedantic -E src/main.cpp -o build/main.ii
wc -l build/main.ii

g++ -std=c++20 -Wall -Wextra -pedantic -S src/main.cpp -o build/main.s
grep -n "make_message" build/main.s | head

g++ -std=c++20 -Wall -Wextra -pedantic -c src/main.cpp -o build/main.o
file build/main.o
nm -C build/main.o | sed -n '1,40p'

g++ build/main.o -o build/hello_cpp
./build/hello_cpp
file build/hello_cpp
ldd build/hello_cpp | sed -n '1,8p'
readelf -h build/hello_cpp
```

## 练习

1. 把 `make_message` 移到 `src/message.cpp`，只在 `src/main.cpp` 中保留声明，分别观察“忘记链接 `message.cpp`”和“正确链接”的输出差异。
2. 用 `nm -C build/hello_cpp | grep make_message` 观察链接后的可执行文件里是否还能看到这个符号。再加 `-O2` 编译，比较符号和汇编变化。
3. 把 `-std=c++20` 改成 `-std=c++17`，观察本文代码是否还能通过。思考：什么时候标准版本会影响编译结果？
4. 运行 `g++ -v src/main.cpp -o build/verbose_app`，查看编译器实际调用了哪些子工具和搜索路径。

## 参考资料与阅读顺序

1. **GCC C++ standards support**：用于确认不同 GCC 版本对 C++ 标准的支持状态。  
   https://gcc.gnu.org/projects/cxx-status.html
2. **Clang C++ status**：如果使用 Clang，可用它核对标准特性支持。  
   https://clang.llvm.org/cxx_status.html
3. **C++ Core Guidelines**：后续写 RAII、所有权、资源管理和接口设计时会作为主要风格参考。  
   https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
4. **CMake 官方教程**：下一篇进入多文件项目和 CMake 时使用。  
   https://cmake.org/cmake/help/latest/guide/tutorial/index.html

本文不是编译器实现课程，也不试图解释所有 ELF 字段或 C++ ABI 细节。它先建立工程开发所需的最小模型：**源码不是直接运行；目标文件携带符号；链接器解析定义；运行时还要加载动态库**。这个模型足够支撑后续理解 CMake、库依赖、调试和 sanitizer。
