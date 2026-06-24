---
layout: post
title: "unique_ptr、shared_ptr 和 raw pointer：把所有权写进类型"
date: 2026-06-24 10:20:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
tags: [cpp, linux, ownership, smart-pointers, memory]
---

> 主题：Linux C++ 工程开发 / 所有权 / 智能指针  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3 环境下本地执行验证。实验包含 CTest、一个预期失败的编译例子，以及 ASan/UBSan 对非泄漏路径的检查。

前一篇文章讲 RAII：把资源释放动作放进析构函数，让作用域结束时自动释放资源。这篇继续回答更具体的问题：**当资源是一块动态分配的对象时，谁负责释放它？**

C++ 里经常同时看到 `T*`、`T&`、`std::unique_ptr<T>`、`std::shared_ptr<T>` 和 `std::weak_ptr<T>`。如果只把它们理解成“都能访问对象的东西”，代码很快会失去边界：一个函数拿到指针后该不该 `delete`？一个对象传给另一个对象后原来的持有者还能不能继续用？两个对象相互指向时会不会释放不了？这些问题不应靠注释和口头约定解决，应该尽量写进类型。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 区分 owning pointer、observer pointer 和 reference 的语义。
2. 用 `std::unique_ptr` 表示独占所有权，并解释为什么它不能拷贝、只能移动。
3. 用 `std::shared_ptr` 表示共享所有权，并观察 `use_count()` 如何随拷贝和销毁变化。
4. 用 `std::weak_ptr` 观察共享对象，并解释它为什么可以打断 `shared_ptr` 环。
5. 说明 raw pointer 适合表达可空观察，不适合表达所有权转移。
6. 用 CTest 和 sanitizer 验证所有权实验的正常路径。

## 先修知识

需要知道：

- 栈对象离开作用域会自动析构；
- `new`/`delete` 会手动管理堆对象；
- `std::move` 表示允许资源从一个对象转移到另一个对象；
- RAII 的基本思想：构造获得资源，析构释放资源。

建议先读：

- [RAII 和资源生命周期：让 C++ 对象负责释放资源](/computer-science-teaching/2026/06/24/cpp-raii-resource-lifetime.html)

## 核心模型：指针类型表达生命周期合同

C++ Core Guidelines 的智能指针规则给出了一条清晰主线：用 `unique_ptr` 或 `shared_ptr` 表达所有权；除非确实需要共享所有权，否则优先使用 `unique_ptr`；需要打断 `shared_ptr` 环时使用 `weak_ptr`。cppreference 对这几个类型的定义也围绕生命周期展开：`unique_ptr` 拥有并管理对象，离开作用域或重置时释放对象；`shared_ptr` 通过控制块共享所有权，最后一个共享拥有者消失时释放对象；`weak_ptr` 只观察由 `shared_ptr` 管理的对象，访问前需要 `lock()` 成临时 `shared_ptr`。

可以把选择规则压缩成这张图：

![C++ 所有权模型](/assets/diagrams/cpp-ownership-smart-pointers.svg)

更实用的判断方式是：

| 形式 | 语义 | 适合场景 | 退出时谁释放 |
| --- | --- | --- | --- |
| `std::unique_ptr<T>` | 独占所有权 | 工厂函数返回对象、容器持有多态对象、成员独占资源 | 当前唯一拥有者 |
| `std::shared_ptr<T>` | 共享所有权 | 对象生命周期确实由多个模块共同延长 | 最后一个共享拥有者 |
| `std::weak_ptr<T>` | 弱观察 | 缓存、回调、父指针、打断共享环 | 不释放，只尝试临时锁定 |
| `T*` | 可空观察或底层接口 | 可选参数、C API、临时查看对象 | 不释放 |
| `T&` | 必有观察 | 参数不能为空且不转移所有权 | 不释放 |

关键点在最后一列。代码审查时先问“谁释放”，再看类型是否把答案写清楚。

## 建立实验目录

创建目录：

```bash
mkdir -p cpp-ownership-smart-pointers/{src,compile_fail,reports}
cd cpp-ownership-smart-pointers
```

这次实验用一个 `Trace` 类记录构造和析构，再用不同指针类型驱动对象生命周期。下面代码可以直接复制成 `src/ownership_lab.cpp`。

```bash
cat > src/ownership_lab.cpp <<'CPP'
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

class Trace {
public:
    explicit Trace(std::string name) : id_(++next_id_), name_(std::move(name)) {
        ++live_count_;
        std::cout << "+ Trace#" << id_ << " " << name_ << " live=" << live_count_ << '\n';
    }

    Trace(const Trace&) = delete;
    Trace& operator=(const Trace&) = delete;

    ~Trace() noexcept {
        std::cout << "- Trace#" << id_ << " " << name_ << " live=" << (live_count_ - 1) << '\n';
        --live_count_;
    }

    const std::string& name() const noexcept { return name_; }
    int id() const noexcept { return id_; }

    static int live_count() noexcept { return live_count_; }

private:
    inline static int next_id_ = 0;
    inline static int live_count_ = 0;

    int id_ = 0;
    std::string name_;
};

void expect(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error("expectation failed: " + message);
    }
}

void inspect_optional(const Trace* ptr, const std::string& label) {
    if (ptr == nullptr) {
        std::cout << label << ": optional view is empty\n";
        return;
    }
    std::cout << label << ": observing Trace#" << ptr->id() << " " << ptr->name() << '\n';
}

void inspect_required(const Trace& item, const std::string& label) {
    std::cout << label << ": required view observes Trace#" << item.id() << " " << item.name() << '\n';
}

void take_unique(std::unique_ptr<Trace> owned) {
    std::cout << "take_unique: got owner for " << owned->name() << '\n';
    inspect_required(*owned, "take_unique");
}

int mode_raw_observer() {
    std::cout << "[raw-observer] raw pointer/reference as views, not owners\n";
    auto owner = std::make_unique<Trace>("owned-by-unique_ptr");
    Trace* optional_view = owner.get();
    inspect_optional(optional_view, "raw pointer view");
    inspect_required(*owner, "reference view");
    inspect_optional(nullptr, "nullable raw pointer view");
    expect(Trace::live_count() == 1, "observer functions must not create or destroy owners");
    owner.reset();
    expect(Trace::live_count() == 0, "owner reset destroys the object");
    std::cout << "raw pointer/reference did not own the object\n";
    return EXIT_SUCCESS;
}

int mode_unique() {
    std::cout << "[unique] exclusive ownership and move transfer\n";
    auto owner = std::make_unique<Trace>("single-owner");
    Trace* old_view = owner.get();
    inspect_optional(old_view, "before move raw view");
    take_unique(std::move(owner));
    expect(owner == nullptr, "moved-from unique_ptr should be empty after ownership transfer");
    expect(Trace::live_count() == 0, "callee-owned unique_ptr should destroy object before returning");
    std::cout << "old raw address after transfer is only an address value: " << old_view << '\n';
    std::cout << "do not dereference it after the owner is gone\n";
    return EXIT_SUCCESS;
}

int mode_shared() {
    std::cout << "[shared] shared ownership and weak observation\n";
    std::weak_ptr<Trace> weak_view;
    {
        auto owner = std::make_shared<Trace>("shared-object");
        weak_view = owner;
        Trace* raw_view = owner.get();
        std::cout << "after make_shared use_count=" << owner.use_count() << '\n';
        inspect_optional(raw_view, "raw view from shared_ptr");
        expect(owner.use_count() == 1, "raw view must not change shared ownership count");
        {
            auto second_owner = owner;
            std::cout << "after copy use_count=" << owner.use_count() << '\n';
            expect(owner.use_count() == 2, "copying shared_ptr adds a shared owner");
            if (auto pinned = weak_view.lock()) {
                std::cout << "weak lock succeeded, pinned use_count=" << pinned.use_count() << '\n';
                expect(pinned.use_count() == 3, "weak lock creates temporary shared ownership");
            } else {
                throw std::runtime_error("weak view unexpectedly expired");
            }
        }
        std::cout << "after inner copy scope use_count=" << owner.use_count() << '\n';
        expect(owner.use_count() == 1, "inner shared_ptr copy was destroyed");
    }
    std::cout << "after owner scope weak expired=" << std::boolalpha << weak_view.expired() << '\n';
    expect(weak_view.expired(), "weak_ptr should expire after last shared owner is destroyed");
    expect(Trace::live_count() == 0, "shared object should be destroyed after last owner");
    return EXIT_SUCCESS;
}

struct SharedNode {
    explicit SharedNode(std::string name) : name(std::move(name)) {
        ++live_count;
        std::cout << "+ SharedNode " << this->name << " live=" << live_count << '\n';
    }

    ~SharedNode() noexcept {
        --live_count;
        std::cout << "- SharedNode " << name << " live=" << live_count << '\n';
    }

    inline static int live_count = 0;
    std::string name;
    std::shared_ptr<SharedNode> peer;
};

struct WeakBackNode {
    explicit WeakBackNode(std::string name) : name(std::move(name)) {
        ++live_count;
        std::cout << "+ WeakBackNode " << this->name << " live=" << live_count << '\n';
    }

    ~WeakBackNode() noexcept {
        --live_count;
        std::cout << "- WeakBackNode " << name << " live=" << live_count << '\n';
    }

    inline static int live_count = 0;
    std::string name;
    std::shared_ptr<WeakBackNode> child;
    std::weak_ptr<WeakBackNode> parent;
};

int mode_shared_cycle() {
    std::cout << "[shared-cycle] two shared_ptr edges keep each other alive\n";
    {
        auto left = std::make_shared<SharedNode>("left");
        auto right = std::make_shared<SharedNode>("right");
        left->peer = right;
        right->peer = left;
        std::cout << "inside scope left.use_count=" << left.use_count()
                  << " right.use_count=" << right.use_count() << '\n';
        expect(left.use_count() == 2 && right.use_count() == 2,
               "cycle should produce two owners for each node");
    }
    std::cout << "after scope SharedNode::live_count=" << SharedNode::live_count << '\n';
    expect(SharedNode::live_count == 2,
           "shared_ptr cycle intentionally remains alive for this demonstration");
    std::cout << "this mode intentionally demonstrates a leak; sanitizer runs skip it\n";
    return EXIT_SUCCESS;
}

int mode_weak_breaks_cycle() {
    std::cout << "[weak-cycle] weak_ptr breaks the back edge\n";
    {
        auto parent = std::make_shared<WeakBackNode>("parent");
        auto child = std::make_shared<WeakBackNode>("child");
        parent->child = child;
        child->parent = parent;
        std::cout << "parent.use_count=" << parent.use_count()
                  << " child.use_count=" << child.use_count() << '\n';
        expect(parent.use_count() == 1, "weak parent edge must not add a shared owner");
        expect(child.use_count() == 2, "parent owns child and local variable also owns child");
        if (auto locked_parent = child->parent.lock()) {
            std::cout << "child can temporarily lock parent: " << locked_parent->name << '\n';
        } else {
            throw std::runtime_error("parent expired inside scope");
        }
    }
    std::cout << "after scope WeakBackNode::live_count=" << WeakBackNode::live_count << '\n';
    expect(WeakBackNode::live_count == 0, "weak back edge allows both nodes to be destroyed");
    return EXIT_SUCCESS;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: " << argv[0]
                  << " raw|unique|shared|cycle|weak-cycle\n";
        return EXIT_FAILURE;
    }

    const std::string mode = argv[1];
    try {
        if (mode == "raw") return mode_raw_observer();
        if (mode == "unique") return mode_unique();
        if (mode == "shared") return mode_shared();
        if (mode == "cycle") return mode_shared_cycle();
        if (mode == "weak-cycle") return mode_weak_breaks_cycle();
        std::cerr << "unknown mode: " << mode << '\n';
        return EXIT_FAILURE;
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << '\n';
        return EXIT_FAILURE;
    }
}
CPP
```

这段程序包含五个实验模式：

- `raw`：`T*` 和 `T&` 只观察对象，不改变生命周期；
- `unique`：`unique_ptr` 被 `std::move` 转移后，原变量变空，接收者负责销毁对象；
- `shared`：拷贝 `shared_ptr` 会增加共享拥有者，`weak_ptr::lock()` 会临时延长生命周期；
- `cycle`：两个对象用 `shared_ptr` 相互指向，外部变量离开作用域后仍不能析构；
- `weak-cycle`：把反向边改成 `weak_ptr` 后，作用域结束时两个对象都能析构。

## CMake 和测试入口

写 `CMakeLists.txt`：

```bash
cat > CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.20)
project(cpp_ownership_smart_pointers LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(ownership_lab src/ownership_lab.cpp)
target_compile_options(ownership_lab PRIVATE -Wall -Wextra -Wpedantic)

enable_testing()
add_test(NAME raw_observer COMMAND ownership_lab raw)
add_test(NAME unique_owner COMMAND ownership_lab unique)
add_test(NAME shared_owner COMMAND ownership_lab shared)
add_test(NAME weak_breaks_cycle COMMAND ownership_lab weak-cycle)
CMAKE
```

这里没有引入 GoogleTest，因为本篇重点是所有权状态观察。`add_test()` 已经把正常路径纳入 CTest：raw observer、unique owner、shared owner、weak break cycle。`cycle` 是有意制造的共享环泄漏，所以只在普通命令里单独运行，不放进 sanitizer 验证路径。

再写一个预期编译失败的小例子：

```bash
mkdir -p compile_fail
cat > compile_fail/copy_unique.cpp <<'CPP'
#include <memory>

int main() {
    auto owner = std::make_unique<int>(42);
    auto copy = owner; // expected compile error: std::unique_ptr is move-only.
    return *copy;
}
CPP
```

这段代码的意义是验证 `unique_ptr` 的独占语义由编译器规则保证，不只依赖注释约定。它尝试拷贝 `unique_ptr`，应当失败。

## 构建并运行正常路径

执行：

```bash
cmake -S . -B build/default -DCMAKE_BUILD_TYPE=Debug
cmake --build build/default --parallel
ctest --test-dir build/default --output-on-failure
```

本地输出的关键部分如下：

```text
Test #1: raw_observer ............ Passed
Test #2: unique_owner ............ Passed
Test #3: shared_owner ............ Passed
Test #4: weak_breaks_cycle ....... Passed
100% tests passed, 0 tests failed out of 4
```

这说明四条非泄漏路径都满足程序内部的 `expect()` 检查。接下来逐个看输出。

### raw pointer/reference：只观察，不拥有

```bash
build/default/ownership_lab raw
```

输出摘要：

```text
[raw-observer] raw pointer/reference as views, not owners
+ Trace#1 owned-by-unique_ptr live=1
raw pointer view: observing Trace#1 owned-by-unique_ptr
reference view: required view observes Trace#1 owned-by-unique_ptr
nullable raw pointer view is empty
- Trace#1 owned-by-unique_ptr live=0
raw pointer/reference did not own the object
```

`Trace` 的生命由 `unique_ptr` 控制。`Trace*` 可以为空，适合表达“可能没有对象”；`Trace&` 不能为空，适合表达“必须有对象”。两者都不负责释放对象。

这里最容易犯的错误是把 raw pointer 当成所有权标记。一个函数参数写成 `T*` 时，调用者无法从类型上知道函数会不会保存它、删除它、只读它，或者要求它指向数组。因此，现代 C++ 工程里通常把 raw pointer 限制为观察和底层接口，把拥有关系交给 RAII 类型表达。

### unique_ptr：独占所有权，只能移动

```bash
build/default/ownership_lab unique
```

输出摘要：

```text
[unique] exclusive ownership and move transfer
+ Trace#1 single-owner live=1
before move raw view: observing Trace#1 single-owner
take_unique: got owner for single-owner
take_unique: required view observes Trace#1 single-owner
- Trace#1 single-owner live=0
old raw address after transfer is only an address value: 0x...
do not dereference it after the owner is gone
```

`take_unique(std::move(owner))` 把所有权转移给函数参数。函数返回时，参数 `owned` 离开作用域，析构触发对象释放。原来的 `owner` 变成空 `unique_ptr`。

这条路径有两个重要结论：

1. `std::move` 不移动对象本身，它允许移动构造或移动赋值发生。这里移动的是 `unique_ptr` 的所有权状态。
2. 之前通过 `get()` 得到的 raw pointer 不会自动变空。所有者销毁对象后，它只剩一个地址值，不能再解引用。

编译器也会阻止拷贝 `unique_ptr`：

```bash
g++ -std=c++20 -Wall -Wextra -Wpedantic compile_fail/copy_unique.cpp -o build/default/copy_unique
```

本地得到预期错误：

```text
error: use of deleted function 'std::unique_ptr<...>::unique_ptr(const std::unique_ptr<...>&)'
note: declared here
  unique_ptr(const unique_ptr&) = delete;
```

这就是“把所有权写进类型”的实际效果。一个对象只能有一个 `unique_ptr` 拥有者；如果要交给别人，必须显式移动。

### shared_ptr：共享所有权有成本，也有边界

```bash
build/default/ownership_lab shared
```

输出摘要：

```text
[shared] shared ownership and weak observation
+ Trace#1 shared-object live=1
after make_shared use_count=1
raw view from shared_ptr: observing Trace#1 shared-object
after copy use_count=2
weak lock succeeded, pinned use_count=3
after inner copy scope use_count=1
- Trace#1 shared-object live=0
after owner scope weak expired=true
```

`std::make_shared<Trace>()` 创建对象和控制块。`owner` 是第一个共享拥有者，`use_count()` 为 1。复制成 `second_owner` 后，计数变成 2。`weak_view.lock()` 成功时会临时创建一个 `shared_ptr`，所以计数短暂变成 3。所有共享拥有者离开作用域后，对象析构，`weak_view.expired()` 变为 `true`。

这说明 `shared_ptr` 解决的是“多个地方都需要延长对象生命”的问题。它不应该作为默认指针类型滥用。单个函数内部创建、使用、销毁的对象，用 `unique_ptr` 更直接；`shared_ptr` 需要维护控制块和引用计数，还会让析构时机变得不如独占所有权明确。

### shared_ptr 环：引用计数不是垃圾回收

```bash
build/default/ownership_lab cycle
```

输出摘要：

```text
[shared-cycle] two shared_ptr edges keep each other alive
+ SharedNode left live=1
+ SharedNode right live=2
inside scope left.use_count=2 right.use_count=2
after scope SharedNode::live_count=2
this mode intentionally demonstrates a leak; sanitizer runs skip it
```

`left` 指向 `right`，`right` 又指向 `left`。局部变量离开作用域后，两个节点仍然各自被对方拥有，引用计数不能降到 0，析构函数没有执行。

这反映的是引用计数模型的边界。引用计数只能处理有向拥有图中可以从外部逐步释放的结构；一旦形成强引用环，计数本身无法判断这组对象已经不可达。

### weak_ptr：观察共享对象，打断拥有环

```bash
build/default/ownership_lab weak-cycle
```

输出摘要：

```text
[weak-cycle] weak_ptr breaks the back edge
+ WeakBackNode parent live=1
+ WeakBackNode child live=2
parent.use_count=1 child.use_count=2
child can temporarily lock parent: parent
- WeakBackNode parent live=1
- WeakBackNode child live=0
after scope WeakBackNode::live_count=0
```

父节点用 `shared_ptr` 拥有子节点，子节点用 `weak_ptr` 观察父节点。这样，父到子的边延长子对象生命，子到父的边不延长父对象生命。需要访问父节点时，调用 `lock()`；如果父节点还活着，就得到临时 `shared_ptr`，否则得到空指针。

父子关系、缓存、事件回调、观察者列表都经常需要这种设计。关键判断是：哪条边表达拥有，哪条边只表达访问关系。

## sanitizer 验证

`cycle` 模式故意保留强引用环，所以不放进 sanitizer 路径。对其他路径执行 ASan/UBSan：

```bash
cmake -S . -B build/sanitize -DCMAKE_BUILD_TYPE=Debug   -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer"
cmake --build build/sanitize --parallel
build/sanitize/ownership_lab raw
build/sanitize/ownership_lab unique
build/sanitize/ownership_lab shared
build/sanitize/ownership_lab weak-cycle
```

本地执行通过，未报告 sanitizer 错误。这里的验证边界很明确：它证明正常路径没有触发 ASan/UBSan 能检查到的内存错误；它不证明所有真实业务场景都安全，也不证明 `shared_ptr` 环不会泄漏。泄漏路径已经由 `cycle` 模式单独演示。

## 常见错误

### 1. 用 `shared_ptr` 作为默认选择

如果没有共享所有权，默认用 `unique_ptr`。共享所有权应该来自真实需求，例如多个异步任务都需要延长对象生命；如果只是“不确定谁释放”，应当先整理生命周期图。不确定所有权时应当先整理生命周期图，再选择类型。

### 2. 从 `shared_ptr::get()` 再构造一个 shared_ptr

`get()` 返回的是观察用 raw pointer。不要写这种代码：

```cpp
auto a = std::make_shared<Trace>("object");
std::shared_ptr<Trace> b(a.get()); // 错误：两个控制块会分别释放同一对象
```

两个 `shared_ptr` 必须通过拷贝、赋值、`make_shared` 或合理的别名构造共享同一个控制块。直接从已被管理的 raw pointer 再构造 `shared_ptr` 会造成未定义行为风险。

### 3. 保存 raw pointer 后忘记所有者可能消失

`T*` 不知道对象还活不活。它适合短时间观察，不能单独作为长期缓存。需要跨作用域观察共享对象时，用 `weak_ptr`；需要延长生命时，必须拿到 `shared_ptr`。

### 4. 把 `use_count()` 当成业务逻辑条件

`use_count()` 适合教学和调试，不适合驱动业务逻辑。真实工程里，一次函数调用、临时拷贝、`weak_ptr::lock()` 都可能改变计数。判断对象是否可访问，应使用所有权结构、作用域和 API 合同，而不是依赖某个瞬间的计数值。

## 选择指针类型的实践顺序

写 C++ 接口时，可以按这个顺序问：

1. 这个对象是否需要动态生命周期？如果不需要，直接用值对象或栈对象。
2. 谁负责释放？只有一个负责者时，用 `unique_ptr`。
3. 是否确实需要多个拥有者共同延长生命？需要时，用 `shared_ptr`。
4. 是否只需要观察共享对象，并且允许对象已经消失？用 `weak_ptr`。
5. 是否只是当前调用期间访问对象？非空用 `T&`，可空用 `T*`。
6. 是否面向 C API 或底层内存结构？可以用 raw pointer，但要把拥有边界包在更外层的 RAII 类型里。

这样写出来的代码更容易审查。类型本身会告诉读者：这里是拥有、共享拥有、弱观察，还是普通观察。

## 练习

1. 把 `take_unique(std::unique_ptr<Trace>)` 改成 `std::unique_ptr<Trace> pass_through(std::unique_ptr<Trace>)`，观察所有权如何返回给调用者。
2. 给 `WeakBackNode` 增加一个 `std::vector<std::shared_ptr<WeakBackNode>> children`，构造一个三节点树，验证析构顺序。
3. 把 `shared` 模式中的 `weak_view.lock()` 保存到外层变量，观察对象生命周期如何被延长。
4. 故意把 `weak-cycle` 的 `parent` 改成 `shared_ptr`，再运行 `cycle` 类似检查，确认强引用环会保留对象。

## 参考资料

- [C++ Core Guidelines: R.smart smart pointers](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rsmart-smart-pointers)
- [cppreference: std::unique_ptr](https://en.cppreference.com/cpp/memory/unique_ptr)
- [cppreference: std::shared_ptr](https://en.cppreference.com/cpp/memory/shared_ptr)
- [cppreference: std::weak_ptr](https://en.cppreference.com/cpp/memory/weak_ptr)
