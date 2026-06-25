---
layout: post
title: "Trie 和 Aho-Corasick：从前缀树到多模式匹配"
date: 2026-06-25 14:20:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "用 Trie 共享前缀，再加入失败链接和输出继承，解释 Aho-Corasick 如何在线性扫描中完成多模式匹配。"
tags: [algorithm, trie, aho-corasick, string-matching, cplusplus]
---
{% raw %}
> 主题：Trie / Aho-Corasick / 多模式匹配 / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含 Trie 查询、重叠模式匹配和朴素搜索对照。

Trie 把一组字符串压进同一棵前缀树。共享前缀的词只保存一份路径，因此它适合字典查询、自动补全和前缀统计。Aho-Corasick 在 Trie 上加入失败链接，让多模式匹配只扫描文本一遍。

失败链接的含义是：当前节点代表某个前缀 `s`，如果下一个字符无法继续匹配，就跳到 `s` 的最长真后缀对应的节点。构建完成后，每读入一个文本字符，自动机就能移动到当前文本后缀所能匹配的最长模式前缀。

## 学习目标

1. 实现 Trie 的插入、完整词查询和前缀查询。
2. 理解失败链接和 KMP prefix function 的相似点。
3. 构建 Aho-Corasick 自动机，并继承输出列表。
4. 找出重叠匹配和后缀模式匹配。
5. 用朴素多模式搜索验证结果。

## 核心模型

![Trie 到 Aho-Corasick 自动机](/assets/diagrams/algorithm-trie-aho-corasick.svg)

Trie 负责共享前缀，失败链接负责在失配时保留可用后缀，输出继承负责发现“某个模式是另一个模式后缀”的情况。

## C++ 实现片段

```cpp
struct Node {
    array<int, 26> next;
    int link = 0;
    vector<int> out;
    Node() { next.fill(-1); }
};

void build() {
    queue<int> q;
    for (int c = 0; c < 26; ++c) {
        int v = t[0].next[c];
        if (v == -1) t[0].next[c] = 0;
        else q.push(v);
    }
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int id : t[t[u].link].out) t[u].out.push_back(id);
        for (int c = 0; c < 26; ++c) {
            int v = t[u].next[c];
            if (v == -1) {
                t[u].next[c] = t[t[u].link].next[c];
            } else {
                t[v].link = t[t[u].link].next[c];
                q.push(v);
            }
        }
    }
}
```

这段构建把缺失转移也补齐。因此搜索时可以直接 `u = t[u].next[c]`，无需在文本扫描过程中写 while 回退循环。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
matches in ushers: (she@1) (he@2) (hers@2)
```

`ushers` 中同时出现 `she`、`he` 和 `hers`。其中 `he` 是 `she` 的后缀路径上的输出，`hers` 又从同一位置继续向后匹配。实验还构造了 `a`、`aa`、`aaa` 这类高度重叠模式，用朴素搜索逐位置对照。

## 正确性思路

构建 BFS 按深度从浅到深处理节点。处理节点 `u` 时，它的失败链接已经正确；对字符 `c` 的缺失转移可以复用失败链接节点的转移，存在子节点时则把子节点失败链接设为该复用转移。

搜索过程中，当前状态始终代表“文本当前前缀的某个后缀，同时也是 Trie 中的最长可用前缀”。节点的 `out` 列表加上失败链继承的输出，覆盖所有以当前位置结尾的模式。

## 复杂度

- 构建 Trie：所有模式总长度为 `L` 时，时间 `O(L · alphabet_transition_cost)`。本文固定小写字母数组，转移处理为 `O(26L)`。
- 搜索：文本长度为 `T`，时间 `O(T + matches)`。
- 空间：Trie 节点数 `O(L)`，每个节点保存固定字母表转移。

## 常见错误

**没有继承失败链接的输出。** 这会漏掉后缀模式，例如匹配到 `she` 时也应报告 `he`。

**根节点缺失转移没有补成 0。** 搜索时遇到首字符失配会访问非法下标。

**忽略字符集边界。** 固定 `a-z` 的实现需要在输入边界做校验；生产环境常用映射表或哈希转移。

## 练习

1. 支持任意 ASCII 字符，把 `array<int,26>` 改成 `unordered_map<char,int>`。
2. 返回每个模式的出现次数，而非每个位置。
3. 用 Aho-Corasick 实现敏感词高亮，处理重叠区间合并。
4. 比较 KMP、Trie 和 Aho-Corasick 的适用场景。

## 参考资料

- [cp-algorithms: Aho-Corasick algorithm](https://cp-algorithms.com/string/aho_corasick.html)
- [Princeton Algorithms: Tries](https://algs4.cs.princeton.edu/52trie/)
- [cppreference: std::array](https://en.cppreference.com/w/cpp/container/array)
{% endraw %}
