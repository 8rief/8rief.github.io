---
layout: post
title: "内存布局：stack、heap、global 和对象生命周期"
date: 2026-06-30 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从返回局部变量地址、忘记 free、全局状态污染这些常见错误出发，解释 stack、heap、global 的生命周期边界。"
tags: [systems, memory, c, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/computer-systems-os-foundations/README.md`](/assets/labs/computer-systems-os-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：计算机系统 / 内存布局 / 生命周期  
> 本文实验已验证：stack、heap、global 三类对象地址不同，heap 对象需要显式释放。

写 C/C++ 时，很多内存错误的根源并不是“地址”本身难懂，而在于对象生命周期没有讲清楚：局部变量出了函数还能不能用？`malloc` 出来的对象谁负责释放？全局变量为什么会让测试和并发变复杂？

内存布局的第一课不应该背地址从高到低怎么画，而应该回答三个工程问题：对象在哪里，活多久，谁负责结束它的生命。

## 这篇文章要解决什么

1. stack、heap、global 各自适合保存什么对象。
2. 为什么返回局部变量地址会出错，而返回堆对象指针在释放前可以继续用。
3. 为什么具体地址不稳定，但地址差异和生命周期关系值得观察。
4. 后续学习虚拟内存、线程共享状态、sanitizer 调试时，需要怎样的基础模型。

## 为什么要引入不同内存区域

程序运行时需要处理不同寿命的对象：

- 函数内部的临时变量，只在这次函数调用期间存在。
- 运行时才知道大小的数据，例如读取文件后创建的缓冲区。
- 整个程序都需要访问的状态，例如配置表、统计计数器。

如果所有对象都用同一种方式管理，程序要么浪费内存，要么无法表达“这个对象什么时候失效”。于是运行时和操作系统给了我们几类常见区域：

| 区域 | 典型对象 | 生命周期 | 谁负责结束 |
|---|---|---|---|
| stack | 普通局部变量、函数参数 | 函数调用进入到返回 | 编译器生成的调用/返回逻辑 |
| heap | `malloc/new` 创建的对象 | 从分配成功到 `free/delete` | 程序员或资源管理对象 |
| global/static | 全局变量、静态变量 | 程序启动到结束 | 运行时/操作系统 |

这张表比具体地址更重要。地址每次运行都可能变，生命周期规则才是写代码时要遵守的契约。

## 机制图：地址空间里的几类对象

![内存布局：stack、heap、global 和对象生命周期](/assets/diagrams/systems-memory-layout-stack-heap.svg)

一个进程看到的是虚拟地址空间。stack、heap、global 都在这个地址空间里，但它们服务不同的管理策略：

- **stack** 跟函数调用栈绑定。函数返回后，对应栈帧就不再属于那个局部变量。
- **heap** 跟显式分配绑定。只要没有释放，其他函数仍可以通过指针访问它。
- **global/static** 跟程序生命周期绑定。它们方便共享，也容易形成隐式依赖。

## 可复现实验

运行实验：

```bash
bash run_lab.sh
```

内存布局部分的核心代码：

```c
static int global_value = 17;

static void demo_memory(void) {
    int stack_value = 23;
    int *heap_value = malloc(sizeof(*heap_value));
    if (heap_value == NULL) {
        perror("malloc");
        exit(1);
    }
    *heap_value = 29;

    uintptr_t stack_addr = (uintptr_t)&stack_value;
    uintptr_t heap_addr = (uintptr_t)heap_value;
    uintptr_t global_addr = (uintptr_t)&global_value;

    printf("memory_stack_value=%d
", stack_value);
    printf("memory_heap_value=%d
", *heap_value);
    printf("memory_global_value=%d
", global_value);
    printf("memory_stack_heap_distinct=%s
", stack_addr != heap_addr ? "true" : "false");
    printf("memory_stack_global_distinct=%s
", stack_addr != global_addr ? "true" : "false");
    printf("memory_heap_global_distinct=%s
", heap_addr != global_addr ? "true" : "false");

    free(heap_value);
}
```

这里没有把具体地址公开成教学结论，因为 ASLR、编译选项、运行时库都会改变地址。实验只验证三件事：值写入成功、三类对象不是同一个位置、堆对象最后被释放。

## 输出怎么读

本次输出摘录：

```text
memory_stack_value=23
memory_heap_value=29
memory_global_value=17
memory_stack_heap_distinct=true
memory_stack_global_distinct=true
memory_heap_global_distinct=true
```

解释如下：

- `memory_stack_value=23`：`stack_value` 是本次函数调用里的局部变量。
- `memory_heap_value=29`：`heap_value` 指向 `malloc` 返回的堆对象。
- `memory_global_value=17`：`global_value` 在函数外定义，程序整个运行期间存在。
- 三个 `distinct=true`：它们是不同对象，不能把一个区域的生命周期规则套到另一个区域。

## 状态变化：一次函数调用里发生了什么

以 `demo_memory()` 为例：

```text
1. 进入 demo_memory，运行时为这次调用准备栈帧
2. stack_value 出现在栈帧中，值为 23
3. malloc 向堆申请 sizeof(int) byte，成功后返回地址
4. *heap_value = 29 把 29 写进堆对象
5. global_value 从程序启动时就已经存在，当前读到 17
6. free(heap_value) 归还堆对象；此后 heap_value 保存的旧地址不再可解引用
7. 函数返回，stack_value 的生命周期结束
```

第 6 步和第 7 步是很多 bug 的来源。指针变量本身只是一个地址值，它不会自动告诉你“这个地址还是否有效”。

## 两个典型错误案例

### 返回局部变量地址

```c
int *bad_pointer(void) {
    int x = 42;
    return &x;
}
```

`x` 在函数返回时生命周期结束。调用者拿到的地址曾经指向 `x`，但现在已经没有权利再按 `int` 使用它。这个错误叫 dangling pointer，表现可能是偶尔正确、偶尔崩溃、偶尔污染别的数据。

### 分配后忘记释放

```c
char *load_buffer(size_t n) {
    char *p = malloc(n);
    if (p == NULL) return NULL;
    return p;
}
```

这段代码本身可以成立，但调用者必须知道自己拿到了所有权，最后要 `free(p)`。如果接口文档没有说明所有权，泄漏就很容易发生。C++ 常用 RAII 和智能指针把这类责任绑定到对象析构上，减少人工遗漏。

## 常见错误

1. **返回局部变量地址。** 局部变量离开作用域后生命周期结束，旧地址不能继续用。
2. **`malloc` 成功后没有对应释放路径。** 错误分支、提前 return、循环中分配都要检查。
3. **释放后继续使用指针。** `free(p)` 后，`p` 的数值还在，但它不再代表一个可用对象。
4. **把全局变量当临时捷径。** 全局状态会隐藏依赖，单元测试、并发访问、重入调用都会更难推理。
5. **把地址差异当绝对布局。** “这次 stack 地址比 heap 大”不能写成跨平台规律。

## 练习

1. 增加一个 `static int local_static = 31;`，打印它和 global、stack、heap 的地址是否不同，并解释它的生命周期和可见性。
2. 故意写一个返回局部变量地址的小程序，用编译器 warning 或 sanitizer 观察报错。
3. 把 `malloc/free` 改成 C++ 的 `std::unique_ptr<int>`，比较所有权表达方式。

## 参考资料

- MIT Missing Semester：[The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)
- CS:APP：[Computer Systems: A Programmer's Perspective](https://csapp.cs.cmu.edu/)
- MIT OpenCourseWare：[6.1810 Operating System Engineering](https://ocw.mit.edu/courses/6-1810-operating-system-engineering-fall-2023/)

{% endraw %}
