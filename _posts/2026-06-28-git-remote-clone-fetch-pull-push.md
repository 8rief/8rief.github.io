---
layout: post
title: "Remote 协作：bare remote、clone、fetch、pull、push"
date: 2026-06-28 00:27:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地 bare remote 模拟远程协作，讲清 clone、fetch、pull 和 push 的边界。"
tags: [git, remote, clone, fetch, pull, push, teaching]
---
{% raw %}

> 主题：Git 基础与协作 / remote 模型
> 本文是 Git 基础包的第七篇。实验使用本地 bare repository 模拟远端，不访问网络。

多人协作时，Git 需要一个共享位置交换引用和对象。这个位置可以是 GitHub，也可以是本机上的 bare repository。学习阶段用本地 bare remote 更安全：所有 clone、fetch、pull、push 行为都能复现，同时不会影响真实项目。

## 学习目标

1. 解释 bare remote 的作用。
2. 区分 clone、fetch、pull 和 push。
3. 理解 `origin/main` 是远程跟踪分支。
4. 用本地同事 clone 模拟协作更新。

## 先修知识

需要理解本地分支、提交和引用。

## 核心模型

![Git remote、clone、fetch、pull、push 模型](/assets/diagrams/git-remote-clone-fetch-pull-push.svg)

remote 保存共享引用和对象。`clone` 创建新的本地仓库。`push` 把本地提交和引用更新发送到 remote。`fetch` 只更新远程跟踪分支。`pull` 通常等于 fetch 后再把远端变化整合到当前分支。

## 逐步实现

创建本地 bare remote：

```bash
git init --bare ../remote.git
git remote add origin ../remote.git
git push -u origin main
```

此时 `origin/main` 记录 remote 中 `main` 的位置。再模拟同事 clone：

```bash
git clone ../remote.git ../colleague
cd ../colleague
git config user.name 'Git Lab Student'
git config user.email 'student@example.invalid'
printf '\nColleague adds one review checklist line.\n' >> docs/usage.md
git add docs/usage.md
git commit -m 'Add colleague checklist note'
git push origin main
```

回到原仓库：

```bash
git fetch origin
git rev-parse main
git rev-parse origin/main
git pull --ff-only
```

lab 中记录：

```text
Local before pull: 55b3a109f3279661c7d153fb0b07deb44490a0df
Origin/main after fetch: d9d1d31f6f7d81cddbefa3209f2102de99cafae1
Local after pull: d9d1d31f6f7d81cddbefa3209f2102de99cafae1
```

这说明 fetch 先更新了 `origin/main`，pull 快进本地 `main` 后，两者对齐。

## 命令边界

- `clone`：从 remote 创建一个新工作副本。
- `fetch`：取回对象和远端引用，当前分支内容通常不直接改变。
- `pull`：取回后整合到当前分支，可能快进、merge 或 rebase，取决于配置和参数。
- `push`：把本地引用更新发送到 remote，remote 是否接受取决于历史关系和权限规则。

这个边界能减少“为什么 fetch 后文件没变”“为什么 push 被拒绝”的困惑。

## 常见错误

1. **把 `origin/main` 当成本地 main。** 它是远程跟踪分支，代表上次 fetch 看到的 remote 状态。
2. **在不清楚策略时直接 pull。** 团队应明确使用 merge、rebase 还是 fast-forward only。
3. **push 前不看本地历史。** 先用 `log --graph` 检查即将共享的提交。
4. **用真实远端练习破坏性命令。** 学习 remote 行为时优先使用本地 bare remote。

## 练习或延伸

1. 用两个本地 clone 轮流提交并 push，观察另一个 clone 的 `fetch` 结果。
2. 在本地仓库运行 `git branch -vv`，查看分支跟踪关系。
3. 尝试 `git pull --ff-only` 在非快进场景下的失败提示。

## 参考资料

- Git Book：[Working with Remotes](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes)
- Git 文档：[git-fetch](https://git-scm.com/docs/git-fetch)
- Git 文档：[git-pull](https://git-scm.com/docs/git-pull)
- Git 文档：[git-push](https://git-scm.com/docs/git-push)

{% endraw %}
