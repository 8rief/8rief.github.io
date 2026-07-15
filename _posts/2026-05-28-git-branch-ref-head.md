---
layout: post
title: "Branch、ref 和 HEAD：分支名如何指向提交"
date: 2026-05-28 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 show-ref、switch 和 log --graph 解释分支、引用和 HEAD 的移动规则。"
tags: [git, branch, ref, head, teaching]
---
{% raw %}

> 主题：Git 基础与协作 / 分支和引用
> 本文是 Git 基础包的第三篇。实验只在本地仓库中创建和合并分支。

分支名是 Git 历史图上的命名入口。你在 `main` 上提交时，`main` 会向前移动；你切到 `feature/summary` 后提交，移动的是这个 feature 分支。`HEAD` 表示当前检出的提交或分支。把 branch、ref 和 HEAD 分清楚，才能读懂 `log --graph` 和合并结果。

## 为什么需要把分支看成引用

如果把分支想成一份独立目录，就很难解释为什么切换分支会改变工作区，也很难解释合并后 feature 分支名仍停在原提交。Git 分支的本质更简单：一个名字保存一个提交 ID。

提交发生时，当前分支名向前移动；`HEAD` 通常指向当前分支名。看懂这个关系后，`HEAD -> main`、`origin/main`、tag 和 feature 分支都只是历史图上的不同入口。

## 学习目标

1. 解释 branch 是指向提交的引用。
2. 区分 `HEAD`、本地分支和远程跟踪分支。
3. 用 `git switch` 创建并切换分支。
4. 用 `git log --graph --decorate --all` 观察历史图。

## 先修知识

需要理解 commit 保存快照并记录父提交。

## 核心模型

![Git branch、ref 和 HEAD 模型](/assets/diagrams/git-branch-ref-head.svg)

引用是名字到对象 ID 的映射。`refs/heads/main` 是本地分支，`refs/tags/v0.1.0` 是标签引用，`HEAD` 通常指向当前分支。提交后，当前分支引用移动到新 commit。

可以用两个底层命令观察：

```bash
git show-ref --heads
git symbolic-ref HEAD
```

前者列出本地分支名到提交 ID 的映射，后者通常输出 `refs/heads/main`，表示当前 HEAD 挂在 main 分支上。

## 逐步实现

从 `main` 创建 feature 分支：

```bash
git switch -c feature/summary
printf '\n## Summary\n\nThe report has an owner and a status line.\n' >> README.md
git add README.md
git commit -m 'Add summary section'
```

切回 `main` 并查看分支引用：

```bash
git switch main
git show-ref --heads
```

本地 lab 记录了两个 heads：一个指向 `main`，一个指向 `feature/summary`。合并后查看图：

```bash
git merge --no-ff feature/summary -m 'Merge summary section'
git log --oneline --graph --decorate --all -n 8
```

输出片段：

```text
*   0cfb16e (HEAD -> main) Merge summary section
|\
| * ecf4249 (feature/summary) Add summary section
|/
* 747ee6e Add report owner
* 8a74260 Initial report skeleton
```

这张图说明 `feature/summary` 的提交被保留下来，`main` 上新增了一个 merge commit。`HEAD -> main` 表示当前检出的是 `main` 分支。

merge commit 有两个父提交：一个来自合并前的 main，另一个来自 feature 分支。用 `--graph` 能看到这次分叉和合流；只看线性 `git log` 会丢掉结构信息。

## 如何读历史图

读 `log --graph` 时，建议按三层看：

1. 星号所在行代表 commit。
2. 线条表示父提交关系和分叉合流。
3. 括号里的 `HEAD`、分支名、标签名是引用。

分支名会移动，已有 commit 对象保持稳定。删除分支名不会自动删除已经被其他引用保留的提交。

实验后期还创建了标签 `v0.1.0`。标签也是引用，但它通常表示发布点，不会像分支那样随着新提交自动前进。

## 常见错误

1. **把分支名当成独立目录。** 分支名指向提交，切换分支会让工作区对齐到目标快照。
2. **忽略当前 HEAD。** 在错误分支提交，会让历史图偏离预期。
3. **只看线性日志。** 分支和合并需要用 `--graph --decorate --all` 观察。
4. **混淆本地分支和远程跟踪分支。** `main` 与 `origin/main` 是不同引用。
5. **只看当前分支。** 协作排错时应加 `--all`，否则看不到其他分支和远程跟踪分支的位置。

## 练习或延伸

1. 创建一个 `topic/readme` 分支，提交一行 README，再用 `show-ref --heads` 观察。
2. 在合并前后分别运行 `git log --graph --oneline --decorate --all`。
3. 用 `git branch --contains <commit>` 查看哪些分支包含某个提交。

## 参考资料

- Git Book：[Branches in a Nutshell](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell)
- Git 文档：[git-branch](https://git-scm.com/docs/git-branch)
- Git 文档：[git-switch](https://git-scm.com/docs/git-switch)

{% endraw %}
