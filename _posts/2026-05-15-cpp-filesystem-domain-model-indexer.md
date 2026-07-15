---
layout: post
title: "C++ filesystem 和领域模型：把本地文件索引写成可测试核心"
date: 2026-05-15 09:00:00 +0800
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

## 为什么需要领域模型

文件索引器看起来可以直接在 `main` 函数里遍历目录、打印结果、顺便写 JSON。这样写很快能跑出输出，但也很快暴露三个问题。

1. CLI、HTTP API 和测试都要复用同一套统计逻辑，散落在入口层会导致重复实现。
2. 公开 demo 需要稳定输出，文件系统遍历顺序、绝对路径和扩展名过滤都要被集中控制。
3. 测试应验证业务含义，例如文件数、字节数、行数和单词数，而不应依赖某个命令行字符串。

因此这里先定义 `FileEntry`、`IndexSummary` 和 `IndexResult`。它们把领域对象从 I/O 入口中抽出来：遍历器只负责产生结构体，JSON、CSV 和 HTTP 只是不同的呈现方式。

这个分层也让错误更容易定位。文件没有被扫描到时，先检查配置和遍历器；JSON 字段缺失时，检查转换函数；API 返回错误时，检查服务层是否正确使用 `IndexResult`。


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

## 输出怎么读

本次样例输出是：

```text
files=3 bytes=304 lines=7 words=45
```

这四个数字分别来自不同层次的状态变化。`files=3` 表示扩展名过滤后留下三个普通文件；`bytes=304` 来自 `std::filesystem::file_size` 的累计；`lines=7` 来自逐行读取；`words=45` 来自按空白切分后的累计。

JSON 报告中的三条明细说明相对路径已经被固定：

```json
{ "path": "intro.txt", "bytes": 91, "lines": 2, "words": 13 }
```

这里不使用绝对路径，是为了让 transcript 在不同机器上仍然可读。相对路径的基准是配置里的 `root`，所以测试应该检查 `intro.txt` 这样的结果，而不是检查本机目录。

如果数字不匹配，按顺序排查：样例文件是否被改动，扩展名列表是否包含 `.txt` 和 `.md`，遍历结果是否排序，最后再看分词规则是否变化。


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
