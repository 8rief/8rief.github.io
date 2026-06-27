---
layout: post
title: "Git 心智模型：working tree、index、commit 和 repository"
date: 2026-06-28 00:21:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从工作区、暂存区、提交和仓库四个状态建立 Git 的第一张图。"
tags: [git, version-control, working-tree, index, teaching]
---
{% raw %}

> 主题：Git 基础与协作 / 状态模型
> 本文是 Git 基础包的第一篇。实验只在本地临时仓库和本地 bare remote 中进行。

学习 Git 的第一个障碍通常是状态混在一起：文件已经改了、已经 `add`、已经 `commit`、已经推送，这四句话指向不同层次。清楚区分 working tree、index、commit 和 repository 后，`status`、`add`、`commit` 和 `log` 就能形成一条可解释的链路。

## 学习目标

1. 区分 working tree、index、commit 和 repository。
2. 解释 `git status --short` 中 `??` 和 `A` 的含义。
3. 理解 `git add` 改变的是暂存区，`git commit` 保存的是快照。
4. 能用一个最小仓库复现从未跟踪文件到第一次提交的过程。

## 先修知识

需要会在 Linux shell 中创建文件、进入目录、运行命令。本文不要求远程仓库或网络账号。

## 核心模型

![Git working tree、index、commit 模型](/assets/diagrams/git-working-tree-index-commit.svg)

working tree 是你正在编辑的文件目录。index 也叫暂存区，它记录下一次提交准备保存的内容。commit 是一次不可变的项目快照，带有作者、时间、提交说明和父提交关系。repository 保存对象、引用和配置。

## 逐步实现

创建一个本地仓库：

```bash
git init -b main project
cd project
git config user.name 'Git Lab Student'
git config user.email 'student@example.invalid'
printf '# local-report\n' > README.md
mkdir -p src
printf 'title: Local Report\nstatus: draft\n' > src/report.txt
```

此时运行：

```bash
git status --short
```

本地 transcript 中得到：

```text
?? README.md
?? src/
```

`??` 表示这些路径还没有被 Git 跟踪。执行：

```bash
git add README.md src/report.txt
git status --short
```

输出变成：

```text
A  README.md
A  src/report.txt
```

`A` 在左侧列，表示 index 中已经准备新增这两个路径。最后提交：

```bash
git commit -m 'Initial report skeleton'
git log --oneline -1
```

提交后，working tree 和 index 回到干净状态。你可以继续修改文件，重复“编辑、暂存、提交”的循环。

## 如何解释状态

遇到 Git 状态时，先问三个问题：

1. 文件内容是否只存在于 working tree。
2. 内容是否已经进入 index，准备参与下一次提交。
3. 内容是否已经成为某个 commit 的一部分。

这三个问题能解释大部分“为什么提交里没有我的修改”“为什么还有未提交内容”“为什么 reset 后文件变了”的初级问题。

## 常见错误

1. **把 `git add` 理解成上传。** `add` 只更新本地 index。
2. **把 commit 当成差异。** Git 的提交记录可以展示差异，但提交本身保存的是快照和父关系。
3. **修改后直接看 `log`。** `log` 只显示已有提交，未提交修改应看 `status` 和 `diff`。
4. **在真实项目里练习危险命令。** 初学阶段应使用受控临时仓库。

## 练习或延伸

1. 修改 `src/report.txt`，分别在 `git add` 前后运行 `git status --short`。
2. 用 `git restore --staged` 把已暂存内容移回 working tree，再观察状态。
3. 画出你当前仓库里一个文件从编辑到提交的路径。

## 参考资料

- Git Book：[Recording Changes to the Repository](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository)
- Git 文档：[git-status](https://git-scm.com/docs/git-status)
- Git 文档：[git-add](https://git-scm.com/docs/git-add)

{% endraw %}
