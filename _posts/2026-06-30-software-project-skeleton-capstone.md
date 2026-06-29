---
layout: post
title: "结课项目：搭一个 release-ready 的小项目骨架"
date: 2026-06-30 03:47:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 workflow_kit 的 CLI、目录、模块、配置、测试、报告和 checklist 串起完整项目结构基础。"
tags: [software-engineering, capstone, project-structure, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / capstone / project skeleton
> 本文 lab 已验证：CLI demo 生成 3 条任务、1 条 done、summary 为 `doing=1, done=1, todo=1`，unittest 4/4 通过。

这个结课项目把前七篇合在一起：从一个任务记录工具的最小需求出发，搭出目录、模块、配置、存储、CLI、测试、demo transcript 和 release checklist。目标是掌握小项目从零到可交付的结构闭环，复杂产品能力留给后续扩展。

## 学习目标

1. 从零创建一个有清晰结构的小项目骨架。
2. 让 CLI、JSON storage、domain rules 和 config validation 各在自己的模块里。
3. 用 tests 和 transcript 证明项目可运行。
4. 用 release checklist 判断是否可以展示或继续扩展。

## 先修知识

建议读完本包前七篇，并具备 Python 基础、Git 基础和命令行基础。

## 核心模型

![Release-ready 小项目骨架](/assets/diagrams/software-project-skeleton-capstone.svg)

一个小项目的收尾闭环包括：需求切片明确，目录结构可理解，模块边界稳定，配置边界安全，测试证据可复跑，发布检查能说明当前状态。

## 逐步实现

运行：

```bash
bash run_lab.sh
```

核心输出：

```text
1	done	product	write problem statement
2	doing	dev	separate domain and storage
3	todo	qa	write CLI smoke test
summary={'doing': 1, 'done': 1, 'todo': 1}
Ran 4 tests
OK
```

项目树：

```text
demo_project/
  .gitignore
  README.md
  config/example.json
  data/tasks.json
  docs/architecture.md
  reports/summary.md
```

这个骨架已经能展示、测试和继续扩展。下一步可以把 CLI 包装成安装命令，增加版本号和 changelog，或者把 JSON storage 替换成 SQLite，同时保持 domain 测试不变。

## 常见错误

1. **把 capstone 做成大而全产品。** 结课项目应优先证明结构闭环。
2. **报告没有原始命令支撑。** transcript 是可复查证据。
3. **模块边界只停留在图上。** 测试需要覆盖实际边界。
4. **发布前不检查公开安全。** README、报告和示例配置都不能包含本机私有值。

## 练习或延伸

1. 增加 `workflow_kit.cli export --format csv`，并补一个 CLI smoke test。
2. 把 `data/tasks.json` 替换成 SQLite storage，保持 CLI 输出不变。
3. 为这个项目写一个 `CHANGELOG.md`，记录第一个可展示版本。

## 参考资料

- Python 文档：[argparse](https://docs.python.org/3/library/argparse.html)
- Python 文档：[unittest](https://docs.python.org/3/library/unittest.html)
- Python Packaging User Guide：[Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

{% endraw %}
