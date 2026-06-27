---
layout: post
title: "Diff 和 patch：未暂存、已暂存和已提交变化怎么比较"
date: 2026-06-28 00:24:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 git diff、git diff --staged 和提交差异理解 Git 的变化边界。"
tags: [git, diff, patch, index, teaching]
---
{% raw %}

> 主题：Git 基础与协作 / 差异边界
> 本文是 Git 基础包的第四篇。实验只比较 lab 仓库中的小文本文件。

Git 的 diff 输出是一种补丁语言：哪些行被删除，哪些行被新增，变更发生在文件的哪个上下文中。关键在于明确比较对象。`git diff` 比较 working tree 和 index，`git diff --staged` 比较 index 和 HEAD，提交之间的 diff 比较两个历史快照。

## 学习目标

1. 解释 diff 输出中的文件头、上下文和新增行。
2. 区分 unstaged diff 和 staged diff。
3. 理解 patch 是可审查、可传递的变化描述。
4. 在提交前用 diff 检查即将保存的内容。

## 先修知识

需要理解 working tree、index 和 commit 三层状态。

## 核心模型

![Git diff 和 patch 边界模型](/assets/diagrams/git-diff-patch-staged.svg)

同一个文件修改，在 `git add` 前位于 working tree；`git diff` 能看到它。执行 `git add` 后，修改进入 index；此时 `git diff --staged` 能看到下一次提交将包含的 patch。

## 逐步实现

修改一个文件：

```bash
printf 'owner: team-a\n' >> src/report.txt
git diff -- src/report.txt
```

本地 lab 的 unstaged diff：

```diff
diff --git a/src/report.txt b/src/report.txt
index 7d6f9db..ded425c 100644
--- a/src/report.txt
+++ b/src/report.txt
@@ -1,2 +1,3 @@
 title: Local Report
 status: draft
+owner: team-a
```

`+owner: team-a` 表示新增行。`@@` 行描述变更块的位置和上下文范围。执行暂存：

```bash
git add src/report.txt
git diff --staged -- src/report.txt
```

这时 staged diff 显示同一段 patch，说明 index 中已经准备保存这次变化。提交后：

```bash
git commit -m 'Add report owner'
```

再运行 `git diff` 通常没有输出，因为 working tree 和 index 已经与 `HEAD` 对齐。

## 审查 diff 的顺序

提交前建议按这个顺序看：

1. `git status --short` 看有哪些路径变化。
2. `git diff` 看尚未暂存的内容。
3. `git diff --staged` 看即将进入提交的内容。
4. `git show --stat --oneline HEAD` 看最近一次提交概况。

这个流程能减少把调试输出、临时文件或无关格式化变更带入提交的概率。

## 常见错误

1. **提交前不看 staged diff。** `git add .` 后容易把无关文件放进 index。
2. **只看文件名。** 文件名变化无法说明内容是否正确。
3. **忽略上下文。** patch 中的上下文行能帮助判断变更是否落在正确位置。
4. **把生成文件一起提交。** 应通过 `.gitignore` 或更明确的路径选择控制边界。

## 练习或延伸

1. 修改两个文件，只暂存其中一个，再比较 `git diff` 和 `git diff --staged`。
2. 用 `git diff --word-diff` 查看一行内部的词级变化。
3. 将 diff 保存到文件：`git diff --staged > review.patch`，打开阅读。

## 参考资料

- Git 文档：[git-diff](https://git-scm.com/docs/git-diff)
- Git Book：[Viewing the Commit History](https://git-scm.com/book/en/v2/Git-Basics-Viewing-the-Commit-History)
- Git 文档：[git-show](https://git-scm.com/docs/git-show)

{% endraw %}
