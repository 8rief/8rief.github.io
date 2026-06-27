---
layout: post
title: "结课项目：Git repo lab、release tag 和协作检查表"
date: 2026-06-28 00:28:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个本地 Git lab 串起对象、分支、diff、merge、rebase、remote、tag 和 .gitignore。"
tags: [git, tag, gitignore, project, collaboration, teaching]
---
{% raw %}

> 主题：Git 基础与协作 / 结课项目
> 本文是 Git 基础包的第八篇。项目只使用本地仓库和本地 bare remote。

前七篇分别讲了状态模型、对象模型、分支引用、diff、merge 冲突、rebase 和 remote 协作。结课项目把这些动作串成一个本地 Git repo lab：从零创建仓库，制造并解决冲突，模拟同事协作，创建 release tag，并输出 Markdown/JSON 证据。

## 学习目标

1. 把 Git 基础命令组织成可复现实验。
2. 用 `.gitignore` 控制生成文件边界。
3. 用 annotated tag 标记一个可说明的发布点。
4. 形成协作前的检查表。

## 先修知识

建议先阅读本系列前七篇，理解 commit、branch、diff、merge、rebase 和 remote。

## 核心模型

![Git 结课 repo lab 结构](/assets/diagrams/git-release-tag-gitignore-capstone.svg)

lab 有三个仓库：`project` 是主工作仓库，`remote.git` 是本地 bare remote，`colleague` 是模拟同事 clone。脚本运行后生成 transcript、Markdown 报告和 JSON 观察结果。

## 逐步实现

### 项目结构

```text
git-foundations-collaboration/
├── README.md
├── run_lab.sh
├── src/
│   └── git_lab.py
├── tests/
│   └── test_git_lab.py
├── workspace/
└── reports/
```

`run_lab.sh` 先运行 unittest，再运行完整 Git 场景，最后打印关键图和报告片段。

### `.gitignore` 和 tag

lab 写入规则：

```gitignore
build/
*.tmp
```

这让生成目录和临时文件留在 working tree 外侧。随后创建发布标记：

```bash
git tag -a v0.1.0 -m 'Local report lab release'
git push origin v0.1.0
```

annotated tag 适合记录一个有说明的发布点。轻量 tag 更像一个简单名字；发布、教学和审计场景通常更偏向 annotated tag。

### 本地验证结果

本地 transcript 记录：

```text
Ran 2 tests in 0.201s
OK
```

最终历史图包含合并、rebase 后的本地提交、本地 tag 和同事提交：

```text
* d9d1d31 (HEAD -> main, origin/main) Add colleague checklist note
* 55b3a10 (tag: v0.1.0) Add ignore rules
* 8f8140a (topic/reword-readme) Add local note
* b932fe9 Add usage note
*   2eecc32 Resolve report status conflict
```

报告还记录了 `HEAD` 类型为 `commit`、根 tree 类型为 `tree`、冲突标记被检测到、rebase 前后哈希发生变化、`pull --ff-only` 后本地 `main` 与 `origin/main` 对齐。

## 协作前检查表

1. `git status --short` 干净，或只剩明确忽略的生成文件。
2. `git diff` 和 `git diff --staged` 已检查。
3. 最近提交信息能说明意图。
4. `git log --oneline --graph --decorate --all -n 12` 中历史关系符合预期。
5. 如有冲突，已运行必要测试或检查命令。
6. 推送前先 `git fetch`，确认本地分支和 remote 状态。
7. 发布点使用清楚的 tag，并在 README 或 release note 中说明边界。

## 常见错误

1. **把生成物混进提交。** `.gitignore` 应在项目早期建立。
2. **tag 没有说明。** 发布点需要解释用途、范围和验证状态。
3. **没有 transcript。** 可复现实验应保存命令、输出和环境版本。
4. **协作前不看历史图。** 分支关系不清楚时，push 和 pull 更容易引入混乱。

## 练习或延伸

1. 给 lab 增加第二个 tag `v0.2.0`，比较两个 tag 指向的提交。
2. 在 colleague clone 中制造一次非快进 push 失败，再用 fetch 和 merge 解决。
3. 把 `reports/observations.json` 中的最终图转换为 README 中的发布摘要。

## 参考资料

- Git 文档：[gitignore](https://git-scm.com/docs/gitignore)
- Git 文档：[git-tag](https://git-scm.com/docs/git-tag)
- Git Book：[Tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging)

{% endraw %}
