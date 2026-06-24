---
layout: post
title: "并查集：用森林维护动态连通性"
date: 2026-06-24 17:20:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用父指针森林、路径压缩和按大小合并实现并查集，并用朴素连通性模型做随机对照测试。"
tags: [algorithm, data-structure, dsu, union-find, cpp]
---
{% raw %}

> 主题：算法与数据结构 / 并查集 / union-find / C++ 实现  
> 本文命令已在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下本地执行验证。实验覆盖 Debug 构建、CTest、固定连通性测试、越界输入测试，以及不同规模下 200 步随机合并与朴素连通性实现对照。

并查集适合处理“元素会不断合并，之后反复询问两个元素是否在同一组”的问题。图论里这叫动态连通性的一种简化场景：边只增加，不删除。每次 `union(a,b)` 表示把包含 `a` 和 `b` 的两个组件合并；每次 `same(a,b)` 表示询问它们当前是否连通。

如果每次合并后都重新遍历图，成本很高。并查集的设计思路是把每个组件表示成一棵树，用根节点代表整个组件。`find(x)` 找到 `x` 所在树的根；`unite(a,b)` 把两棵树的根连起来。再加上 union by size 和 path compression，实际运行中查询会非常接近常数时间。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释并查集的父指针森林模型。
2. 说明根节点、组件大小、`find()` 和 `unite()` 的职责。
3. 实现带 union by size 和 path compression 的 C++ 并查集。
4. 用朴素连通性实现做随机对照测试。
5. 说明并查集适合边只增加的连通性问题，不直接支持普通删除边。

## 问题模型

输入：`n` 个元素，编号为 `0..n-1`，以及一串操作：

- `unite(a, b)`：把 `a` 和 `b` 所在组件合并；
- `same(a, b)`：判断两者是否在同一组件；
- `component_size(x)`：返回 `x` 所在组件的元素数量。

输出：每次查询的连通性或组件大小。

约束：本文只处理合并，不处理拆分。如果需要删除边、回滚或在线动态连通性，需要额外数据结构，例如 rollback DSU、link-cut tree 或离线算法。

## 核心不变量

并查集维护的是一片森林：

![并查集森林不变量](/assets/diagrams/algorithm-dsu-invariants.svg)

每个节点有一个 `parent`：

1. 如果 `parent[x] == x`，`x` 是所在组件的根。
2. 如果 `parent[x] != x`，沿着父指针一直走，最终会到达根。
3. 同一组件内所有节点的根相同；不同组件的根不同。
4. `size[root]` 只在根节点上有意义，记录该组件的节点数。

`unite(a,b)` 先分别找到根 `root_a`、`root_b`。如果两个根相同，说明本来就在同一组件，合并返回 `false`。如果不同，就把小组件的根挂到大组件的根下面，并更新大根的 `size`。

`find(x)` 做路径压缩：在找到根以后，把沿途节点直接挂到根上。这个操作不改变连通性，只把未来查询路径变短。

## C++ 实现

接口：

```cpp
#pragma once
#include <cstddef>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace dsu {

class DisjointSet {
public:
    explicit DisjointSet(std::size_t n);
    std::size_t size() const;
    std::size_t find(std::size_t x);
    bool unite(std::size_t a, std::size_t b);
    bool same(std::size_t a, std::size_t b);
    std::size_t component_size(std::size_t x);
    std::vector<std::size_t> parents() const;
    std::vector<std::size_t> sizes() const;

private:
    void check_index(std::size_t x) const;
    std::vector<std::size_t> parent_;
    std::vector<std::size_t> size_;
};

}  // namespace dsu
```

实现：

```cpp
DisjointSet::DisjointSet(std::size_t n) : parent_(n), size_(n, 1) {
    std::iota(parent_.begin(), parent_.end(), 0);
}

void DisjointSet::check_index(std::size_t x) const {
    if (x >= parent_.size()) {
        throw std::out_of_range("disjoint-set index out of range");
    }
}

std::size_t DisjointSet::find(std::size_t x) {
    check_index(x);
    if (parent_[x] != x) {
        parent_[x] = find(parent_[x]);
    }
    return parent_[x];
}

bool DisjointSet::unite(std::size_t a, std::size_t b) {
    std::size_t root_a = find(a);
    std::size_t root_b = find(b);
    if (root_a == root_b) {
        return false;
    }
    if (size_[root_a] < size_[root_b]) {
        std::swap(root_a, root_b);
    }
    parent_[root_b] = root_a;
    size_[root_a] += size_[root_b];
    return true;
}

bool DisjointSet::same(std::size_t a, std::size_t b) {
    return find(a) == find(b);
}

std::size_t DisjointSet::component_size(std::size_t x) {
    return size_[find(x)];
}
```

`find()` 不是 `const`，因为路径压缩会修改 `parent_`。这是一种内部结构优化，不改变抽象连通性。`same()` 也不能是 `const`，因为它调用 `find()` 时可能触发压缩。

## 为什么 union by size 有用

如果每次都把大树挂到小树下面，树高可能不断增长，`find()` 会退化。union by size 的策略是把小树根挂到大树根下面。直观上，一个节点的深度每增加一次，它所在组件大小至少翻倍，因此单靠这个策略就能把树高控制在 `O(log n)`。

再加上路径压缩，摊还复杂度可以达到反阿克曼函数级别，通常记为 `O(α(n))`。在现实规模下，`α(n)` 极小，所以工程上常把并查集看成近似常数时间结构。这个说法的前提是同时使用路径压缩和按大小或按秩合并。

## 验证策略

固定测试先检查基本行为：初始化时每个节点自成一组；合并后连通性变化；重复合并返回 `false`；组件大小正确。

```cpp
void test_basic_components() {
    dsu::DisjointSet sets(6);
    for (std::size_t i = 0; i < 6; ++i) {
        require(sets.find(i) == i, "initial singleton root");
        require(sets.component_size(i) == 1, "initial singleton size");
    }
    require(sets.unite(0, 1), "merge 0-1");
    require(sets.unite(2, 3), "merge 2-3");
    require(sets.unite(1, 2), "merge components");
    require(!sets.unite(0, 3), "redundant merge returns false");
    require(sets.same(0, 3), "same after chain");
    require(!sets.same(0, 5), "different components");
    require(sets.component_size(2) == 4, "component size after unions");
}
```

越界输入应该显式失败，而不是访问未定义内存：

```cpp
void test_out_of_range() {
    dsu::DisjointSet sets(2);
    bool thrown = false;
    try {
        (void)sets.find(2);
    } catch (const std::out_of_range&) {
        thrown = true;
    }
    require(thrown, "out of range throws");
}
```

随机对照测试用一个朴素实现作为参考：朴素版本给每个元素存一个组件标签，合并时扫描整个数组改标签。它很慢，但逻辑直接，适合小规模验证。

```cpp
struct NaiveConnectivity {
    std::vector<int> label;
    explicit NaiveConnectivity(std::size_t n) : label(n) {
        for (std::size_t i = 0; i < n; ++i) {
            label[i] = static_cast<int>(i);
        }
    }
    bool unite(std::size_t a, std::size_t b) {
        if (label[a] == label[b]) {
            return false;
        }
        const int from = label[b];
        const int to = label[a];
        for (int& x : label) {
            if (x == from) {
                x = to;
            }
        }
        return true;
    }
    bool same(std::size_t a, std::size_t b) const {
        return label[a] == label[b];
    }
};
```

对照过程在 `n = 1..24` 的小规模上执行随机合并，每一步都比较所有点对的连通性和组件大小。这样做的目的不是测性能，而是防止父指针更新、组件大小更新或重复合并返回值出现偏差。

## 执行实验

构建并测试：

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build --output-on-failure
```

本地输出：

```text
100% tests passed, 0 tests failed out of 1
```

运行示例程序：

```bash
./build/dsu_demo
```

输出节选：

```text
union(0, 1) merged=true
union(2, 3) merged=true
union(1, 2) merged=true
union(5, 6) merged=true
union(6, 7) merged=true
node 0 root=0 component_size=4
node 3 root=0 component_size=4
node 5 root=5 component_size=3
node 7 root=5 component_size=3
same(0,3)=true
same(0,7)=false
```

这段输出说明 `0,1,2,3` 被合成一个组件，`5,6,7` 被合成另一个组件，节点 `4` 保持单独组件。`same(0,3)` 为真，`same(0,7)` 为假。

## 正确性理由

并查集的正确性来自根节点代表组件这一不变量。

初始化时，每个节点的父亲都是自己，因此每个节点都是单点组件的根。合并两个不同根时，只改变其中一个根的父指针，让它指向另一个根；这会把两棵树合成一棵树，不会影响其他树。组件大小只在新根上更新，表示两组元素数量之和。`find()` 的路径压缩只把节点改为直接指向原来的根，根没有变，所以连通性不变。

因此，两个元素在同一组件当且仅当 `find(a) == find(b)`。`unite()` 保持森林结构，`find()` 保持组件划分，查询就能稳定反映当前合并结果。

## 复杂度

- 初始化：`O(n)`。
- `find()` / `unite()` / `same()`：使用路径压缩和按大小合并后，摊还复杂度为 `O(α(n))`。
- 空间：`O(n)`，主要是 `parent` 和 `size` 两个数组。

如果去掉路径压缩或按大小合并，复杂度会变差。具体退化程度取决于合并顺序；最坏情况下，父指针链可以很长。

## 常见错误

**把 `size[x]` 当成任意节点的组件大小。** 只有根节点上的 `size[root]` 有意义。非根节点的旧 size 不一定清零，也不应该读取。

**`find()` 写成 const。** 路径压缩会修改父指针。可以设计只读版本，但默认高效实现通常让 `find()` 改变内部结构。

**认为并查集能直接删除边。** 标准并查集只擅长合并。删除边可能导致一个组件拆成多个组件，父指针森林没有足够信息直接恢复这种拆分。

**随机测试只查几个点对。** 连通性结构的错误可能藏在其他点对里。小规模随机对照应尽量检查所有点对和组件大小。

## 练习

1. 把 union by size 改成 union by rank，并说明 `rank` 和组件大小的区别。
2. 暂时去掉路径压缩，统计一批随机操作中 `find()` 的递归深度变化。
3. 用并查集实现 Kruskal 最小生成树，并用小图手算结果对照。
4. 思考如果操作中包含“撤销上一次合并”，标准并查集为什么不够用。

## 参考资料

- [cp-algorithms: Disjoint Set Union](https://cp-algorithms.com/data_structures/disjoint_set_union.html)
- Robert E. Tarjan, “Efficiency of a Good But Not Linear Set Union Algorithm”, *Journal of the ACM*, 1975.
- Thomas H. Cormen et al., *Introduction to Algorithms*, 4th edition, chapter on data structures for disjoint sets.
{% endraw %}
