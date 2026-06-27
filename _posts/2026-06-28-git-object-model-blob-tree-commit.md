---
layout: post
title: "Git 对象模型：blob、tree、commit 和哈希如何保存内容"
date: 2026-06-28 00:22:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 cat-file、ls-tree 和 rev-parse 看见 Git 提交背后的对象结构。"
tags: [git, object-model, blob, tree, commit, teaching]
---
{% raw %}

> 主题：Git 基础与协作 / 对象模型
> 本文是 Git 基础包的第二篇。实验只读取 lab 仓库自己的对象。

Git 的很多能力来自对象模型。文件内容进入 blob，目录快照进入 tree，提交说明、作者和父关系进入 commit。每个对象都有哈希 ID，引用和分支最终都指向这些对象。理解这层结构后，`cat-file`、`ls-tree` 和 `rev-parse` 就能帮助你从底层验证仓库状态。

## 学习目标

1. 说明 blob、tree、commit 分别保存什么。
2. 用 `git cat-file -t` 查看对象类型。
3. 用 `git ls-tree` 查看提交对应的目录快照。
4. 理解哈希 ID 与内容、元数据和历史关系的联系。

## 先修知识

需要知道 working tree、index 和 commit 的基本区别。

## 核心模型

![Git blob、tree、commit 对象模型](/assets/diagrams/git-object-model-blob-tree-commit.svg)

commit 指向一个 tree，tree 记录目录项和子 tree 或 blob，blob 保存文件内容。commit 还记录父 commit，因此提交之间形成历史图。

## 逐步实现

第一次提交之后，查看 `HEAD` 的对象类型：

```bash
git cat-file -t HEAD
git cat-file -t HEAD^{tree}
```

本地 transcript 中得到：

```text
commit
tree
```

`HEAD` 当前指向一个 commit。`HEAD^{tree}` 表示取出该提交指向的根 tree。再查看根 tree 的路径：

```bash
git ls-tree --name-only HEAD
```

输出：

```text
README.md
src
```

这说明提交保存的是项目快照。`README.md` 对应一个 blob，`src` 对应一个子 tree。继续查看完整 tree：

```bash
git ls-tree HEAD
```

你会看到模式、对象类型、对象 ID 和路径名。路径名位于 tree 中，文件内容位于 blob 中。

## 为什么对象模型重要

对象模型能解释三个常见现象：

1. 相同内容可能复用相同 blob。
2. 改动一个文件会产生新的 blob，并让相关 tree 和 commit 变化。
3. 分支切换本质上是让 working tree/index 对齐到另一个 commit 的快照。

在排查“这个文件在哪次提交中变了”时，理解对象模型能让 `log`、`show`、`diff` 的输出更清晰。

## 常见错误

1. **只把哈希看成随机编号。** 哈希是对象身份的一部分，和对象内容及格式相关。
2. **把 tree 当成文件内容。** tree 记录目录结构和对象引用，blob 保存文件内容。
3. **只看短哈希。** 短哈希便于阅读，脚本和审计场景应保留完整 ID。
4. **忽略父提交。** commit 的父关系决定历史图，单个快照无法表达完整演化过程。

## 练习或延伸

1. 对 `HEAD`、`HEAD^{tree}` 和某个 blob 分别运行 `git cat-file -t`。
2. 用 `git cat-file -p HEAD` 阅读 commit 内容。
3. 修改一个文件并提交，比较前后 `git ls-tree -r HEAD` 的对象 ID。

## 参考资料

- Git Book：[Git Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
- Git 文档：[git-cat-file](https://git-scm.com/docs/git-cat-file)
- Git 文档：[git-ls-tree](https://git-scm.com/docs/git-ls-tree)

{% endraw %}
