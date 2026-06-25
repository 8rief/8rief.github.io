---
layout: post
title: "C++ filesystem 和领域模型：把本地文件索引写成可测试核心"
date: 2026-06-25 21:01:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, filesystem, domain-model, teaching]
---

## 学习目标

这一篇讲文件索引器的核心模型。读完以后，你应该能解释：

1. 如何用 `std::filesystem` 遍历本地样例目录；
2. 为什么 `FileEntry`、`IndexSummary`、`IndexResult` 要分开；
3. 入口层和核心层怎样通过结构体传递稳定数据。

## 先修知识

需要知道目录、文件扩展名、相对路径和文本文件的基本概念。项目默认只扫描样例目录，不扫描用户主目录或系统目录。

## 核心模型

文件索引器的核心路径是：配置给出 root 和扩展名，遍历器找出文件，检查器统计 bytes、lines、words，汇总器生成结果。

![C++ filesystem 领域模型](/assets/diagrams/cpp-filesystem-domain-model-indexer.svg)

这条路径里没有 CLI 参数、HTTP 请求或日志输出。核心逻辑保持纯粹，测试才容易覆盖。

## 逐步实现

领域结构体放在头文件里：

```cpp
struct FileEntry {
    std::string path;
    std::uintmax_t bytes{};
    std::size_t lines{};
    std::size_t words{};
};

struct IndexSummary {
    std::size_t files{};
    std::uintmax_t bytes{};
    std::size_t lines{};
    std::size_t words{};
};
```

`IndexResult` 把汇总和明细放在一起：

```cpp
struct IndexResult {
    IndexSummary summary;
    std::vector<FileEntry> files;
};
```

遍历目录时只处理普通文件和允许的扩展名：

```cpp
for (const auto& item : std::filesystem::recursive_directory_iterator(config.root)) {
    if (!item.is_regular_file() || !has_allowed_extension(item.path(), allowed)) {
        continue;
    }
    result.files.push_back(inspect_file(config.root, item.path()));
}
```

单个文件的统计使用普通输入流：

```cpp
while (std::getline(input, line)) {
    ++entry.lines;
    std::istringstream words(line);
    entry.words += std::distance(std::istream_iterator<std::string>{words}, {});
}
```

实验样例目录有 3 个文件，CLI 输出：

```text
files=3 bytes=304 lines=7 words=45
```

这个结果同时进入 JSON、CSV 和 HTTP API，说明核心模型没有被不同入口重复实现。

## 常见错误

1. **把完整绝对路径写进报告**：公开报告使用相对路径，输出更稳定，也不暴露工作目录。
2. **边遍历边输出**：先构造 `IndexResult`，后续 JSON/CSV/API 可以复用同一份结果。
3. **不排序文件列表**：文件系统遍历顺序可能变化，排序后 transcript 和测试更稳定。

## 练习或延伸

- 增加 `max_depth` 配置，只扫描有限层级。
- 把 word 统计换成更严格的分词逻辑，说明空白分词和真实语言分词的差异。

## 参考资料

- [std::filesystem](https://en.cppreference.com/w/cpp/filesystem)
- [recursive_directory_iterator](https://en.cppreference.com/w/cpp/filesystem/recursive_directory_iterator)
- [std::istream_iterator](https://en.cppreference.com/w/cpp/iterator/istream_iterator)
