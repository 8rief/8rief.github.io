---
layout: post
title: "Merge 冲突：复现、定位、解决和提交"
date: 2026-06-28 00:25:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用同一行状态字段的冲突实验，讲清 merge conflict 的证据链和解决步骤。"
tags: [git, merge, conflict, collaboration, teaching]
---
{% raw %}

> 主题：Git 基础与协作 / 合并冲突
> 本文是 Git 基础包的第五篇。实验在本地仓库中故意制造小型文本冲突。

合并冲突表示两条历史分支改动了同一块上下文，Git 需要人来决定最终内容。可靠的处理方式是先复现冲突，再读冲突标记和双方提交，最后写出明确的合并结果并提交。

## 学习目标

1. 解释为什么同一行被两条分支修改会产生冲突。
2. 读懂 `<<<<<<<`、`=======`、`>>>>>>>` 冲突标记。
3. 用 `git status` 找到未解决路径。
4. 通过编辑、`git add`、`git commit` 完成冲突解决。

## 先修知识

需要理解分支、提交和 diff。

## 核心模型

![Git merge conflict 解决模型](/assets/diagrams/git-merge-conflict-resolution.svg)

merge 会寻找共同祖先，再尝试把两边变化合并。两边改动同一段内容时，文件进入冲突状态。解决冲突的核心是确定最终文件内容，然后把解决后的文件放入 index。

## 逐步实现

在 feature 分支把状态改成 ready：

```bash
git switch -c feature/status-ready
python3 - <<'PY'
from pathlib import Path
p = Path('src/report.txt')
p.write_text(p.read_text().replace('status: draft', 'status: ready'))
PY
git add src/report.txt
git commit -m 'Mark report ready on feature'
```

回到 main，把同一行改成 review：

```bash
git switch main
python3 - <<'PY'
from pathlib import Path
p = Path('src/report.txt')
p.write_text(p.read_text().replace('status: draft', 'status: review'))
PY
git add src/report.txt
git commit -m 'Mark report under review'
```

合并 feature：

```bash
git merge feature/status-ready
```

lab 中这个命令返回非零状态，文件中出现冲突标记：

```text
<<<<<<< HEAD
status: review
=======
status: ready
>>>>>>> feature/status-ready
```

最终解决为：

```text
status: ready
review: completed
```

然后提交：

```bash
git add src/report.txt
git commit -m 'Resolve report status conflict'
```

## 冲突处理检查表

1. `git status --short` 找到冲突路径。
2. 打开文件，定位冲突标记。
3. 查 `git log --oneline --left-right --merge` 或相关提交，理解双方意图。
4. 编辑成最终内容，删除冲突标记。
5. 运行必要测试或检查命令。
6. `git add` 标记已解决，`git commit` 完成 merge。

## 常见错误

1. **直接删除其中一边内容。** 应先理解双方变更目的。
2. **保留冲突标记。** 标记进入提交会污染代码或文档。
3. **解决后忘记测试。** 文本能合并不代表语义正确。
4. **用强制命令掩盖冲突。** 初学阶段应完整走一遍证据链。

## 练习或延伸

1. 制造两个分支修改同一段 README 的冲突，按检查表解决。
2. 冲突时运行 `git diff`，观察 Git 如何展示双方内容。
3. 解决冲突后用 `git log --graph --oneline --decorate -n 8` 查看 merge commit。

## 参考资料

- Git Book：[Basic Merge Conflicts](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging#_basic_merge_conflicts)
- Git 文档：[git-merge](https://git-scm.com/docs/git-merge)
- Git 文档：[git-status](https://git-scm.com/docs/git-status)

{% endraw %}
