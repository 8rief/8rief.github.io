---
layout: post
title: "Rebase：在共享前整理本地历史的边界"
date: 2026-06-28 00:26:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地 topic 分支演示 rebase 如何重放提交，以及为什么共享后要谨慎改历史。"
tags: [git, rebase, history, branch, teaching]
---
{% raw %}

> 主题：Git 基础与协作 / rebase 边界
> 本文是 Git 基础包的第六篇。实验只 rebase 尚未共享的本地 topic 分支。

`git rebase` 的核心动作是把一组提交取出，放到新的基底上重新应用。这样可以让本地 topic 分支的历史更线性，也会改变被重放提交的哈希。边界很重要：适合整理尚未共享的本地历史；已经被他人基于其工作的公开历史，应谨慎改写。

## 学习目标

1. 解释 rebase 的“换基并重放提交”模型。
2. 观察 rebase 前后提交哈希变化。
3. 区分本地整理历史和共享历史改写。
4. 用 `merge --ff-only` 接收已经 rebase 到 main 上的 topic 分支。

## 先修知识

需要理解 branch、commit 哈希和父提交关系。

## 核心模型

![Git rebase 历史边界模型](/assets/diagrams/git-rebase-history-boundary.svg)

topic 分支从旧基底分出。main 前进后，rebase 会把 topic 的提交重放到新的 main 上。重放后的提交内容可能相同，父提交变了，commit ID 也会变化。

## 逐步实现

创建本地 topic 分支：

```bash
git switch -c topic/reword-readme
printf '\n## Local note\n\nThis branch will be rebased before sharing.\n' >> README.md
git add README.md
git commit -m 'Add local note'
git rev-parse HEAD
```

回到 `main`，让它先前进：

```bash
git switch main
mkdir -p docs
printf '# Usage\n\nRun the report script after cloning.\n' > docs/usage.md
git add docs/usage.md
git commit -m 'Add usage note'
```

再 rebase topic：

```bash
git switch topic/reword-readme
git rebase main
git rev-parse HEAD
```

lab 记录了：

```text
Hash changed by rebase: True
```

这说明 topic 的提交被重新创建到了新的父提交之上。随后 main 可以快进到 topic：

```bash
git switch main
git merge --ff-only topic/reword-readme
```

## 何时使用 rebase

推荐场景：

1. 个人本地 topic 分支还没有推送给其他人使用。
2. 想把 main 的最新提交作为新基底，减少后续合并噪声。
3. 想在提交前整理小步提交，使 review 更清楚。

谨慎场景：

1. 分支已经被多人基于其继续开发。
2. 远端分支受保护或团队约定保留 merge 历史。
3. 你需要保留真实合流过程作为审计记录。

## 常见错误

1. **共享后随意改写历史。** 会让他人的本地历史需要额外协调。
2. **rebase 中途不读冲突。** rebase 冲突也需要逐个提交地理解和解决。
3. **只追求线性图。** 历史可读性比形式更重要。
4. **混用 rebase 和 merge 规则。** 团队应在项目文档中写清默认策略。

## 练习或延伸

1. 在本地 topic 分支上提交两次，再 rebase 到 main，观察两个哈希如何变化。
2. 用 `git log --graph --oneline --decorate -n 8` 比较 rebase 前后历史图。
3. 阅读 `git rebase --abort` 和 `git rebase --continue` 的使用条件。

## 参考资料

- Git Book：[Rebasing](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)
- Git 文档：[git-rebase](https://git-scm.com/docs/git-rebase)
- Git 文档：[git-merge](https://git-scm.com/docs/git-merge)

{% endraw %}
