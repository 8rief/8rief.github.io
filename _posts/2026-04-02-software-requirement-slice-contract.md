---
layout: post
title: "需求切片：先把“要做一个项目”改写成可验收行为"
date: 2026-04-02 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用问题陈述、用户可见行为、CLI contract 和验收样例，把模糊项目目标切成能开发和测试的最小闭环。"
tags: [software-engineering, requirements, cli, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / requirement slicing
> 本文 lab 已验证：demo CLI 创建项目、添加任务、标记完成、列出任务并生成摘要报告。

“做一个项目”不是可执行需求。工程开始时，先把目标切成一个能被用户观察、能被命令复跑、能被测试验证的行为闭环。切片越小，越容易判断目录、模块、配置和测试应该怎么放。

## 学习目标

1. 把模糊需求改写成用户可见行为。
2. 给每个切片写出输入、输出和验收命令。
3. 区分功能边界、数据边界和发布边界。
4. 用 capstone lab 的 CLI contract 作为小项目起点。

## 先修知识

需要会运行命令行，并理解测试应该验证行为，而不是只检查实现细节。

## 核心模型

![从需求到可验收切片](/assets/diagrams/software-requirement-slice-contract.svg)

需求切片的路径是：先写问题陈述，再写用户会执行什么操作，然后固定 CLI 或 API contract，最后用输入输出样例和验收命令证明它可以工作。

## 逐步实现

capstone lab 的第一个切片是“创建一个可记录任务的项目骨架”。验收命令如下：

```bash
python3 -m workflow_kit.cli init --root demo_project --name release-ready-demo
python3 -m workflow_kit.cli add --root demo_project --owner product "write problem statement"
python3 -m workflow_kit.cli list --root demo_project
```

transcript 中的可见行为：

```text
initialized=demo_project
added id=1 status=todo owner=product title=write problem statement
1	done	product	write problem statement
```

这个切片很小，但已经覆盖了项目根目录、数据文件、CLI 输出、任务状态和用户验收方式。后续目录结构和模块拆分都围绕这些行为服务。

## 为什么要引入需求切片

需求切片要解决的核心问题是“项目目标无法被验证”。一句“做一个任务管理工具”没有输入、输出、失败边界和验收方式，开发时很容易先写目录、先选库、先做界面，最后才发现最基本的用户行为没有闭环。

可执行切片至少包含四件事：

```text
用户是谁 -> 执行什么操作 -> 看到什么结果 -> 用什么命令复查
```

本文的第一个切片可以写成：

```text
作为项目维护者，我可以初始化一个工作目录，添加一条任务，并通过 list 看到这条任务的编号、状态、负责人和标题。
验收命令：init -> add -> list。
验收结果：list 输出包含 id=1、status=todo、owner=product、title=write problem statement。
```

这个写法把讨论从“工具大概长什么样”推进到“第一条行为是否跑通”。

## 输入、输出和状态变化

上面的三条命令产生了三类状态变化：

```text
init  -> 创建项目目录、README、config、data、docs、reports
add   -> 在 data/tasks.json 中追加一条任务记录
list  -> 读取 data/tasks.json，并把稳定字段打印给用户
```

任务状态文件可以抽象成下面结构：

```json
{
  "schema_version": 1,
  "tasks": [
    {"task_id": 1, "title": "write problem statement", "status": "todo", "owner": "product"}
  ]
}
```

读输出时要看字段是否支撑验收：

```text
1    done    product    write problem statement
```

`1` 说明后续命令可以定位任务；`done` 说明状态枚举已经进入输出 contract；`product` 说明负责人字段没有在存储或展示时丢失；标题说明用户输入能被完整保存。只要这四项稳定，需求切片就能继续往测试、README 和发布检查里传递。

## 把模糊目标切成开发顺序

一个小项目可以按下面顺序切：

| 顺序 | 行为 | 验收方式 | 暂时不做的内容 |
|---:|---|---|---|
| 1 | 初始化目录并添加任务 | `init -> add -> list` | 登录、同步、多用户 |
| 2 | 标记任务完成 | `done 1 -> list` | 复杂工作流 |
| 3 | 生成摘要报告 | `report` 输出状态计数 | 图表和网页 |
| 4 | 发布检查 | 测试、transcript、README 一致 | 自动 CI |

这个顺序的好处是每一步都能独立展示。下一步开发失败时，上一条切片仍然是可运行成果。

## 检查清单

写需求切片时，可以逐项检查：

```text
[ ] 用户能从命令或页面入口触发行为
[ ] 输入参数和错误输入已列出
[ ] 输出包含稳定字段，而非临时调试信息
[ ] 状态变化能从文件、数据库或报告中复查
[ ] 至少有一条自动测试或 transcript 证明它跑过
```

如果其中一项缺失，这条需求还停留在想法阶段。

## 常见错误

1. **先搭复杂目录，再补需求。** 目录应该服务于行为闭环。
2. **只写“支持任务管理”。** 需要写清楚用户输入、输出和失败边界。
3. **没有验收命令。** 需求无法复跑时，讨论会停留在主观判断。
4. **把一次性脚本当成项目。** 项目至少要有可维护的入口、数据边界、测试和文档。

## 练习或延伸

1. 给 `workflow_kit` 增加一个 `archive` 行为，先写验收命令，再写代码。
2. 把“生成报告”切成输入、输出、错误和验收样例。
3. 为一个你自己的小工具写三条用户可见行为。

## 参考资料

- Python 文档：[argparse](https://docs.python.org/3/library/argparse.html)
- Python 文档：[subprocess](https://docs.python.org/3/library/subprocess.html)
- GitHub Docs：[About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)

{% endraw %}
