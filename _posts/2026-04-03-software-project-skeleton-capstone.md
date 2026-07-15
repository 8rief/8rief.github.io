---
layout: post
title: "结课项目：搭一个 release-ready 的小项目骨架"
date: 2026-04-03 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 workflow_kit 的 CLI、目录、模块、配置、测试、报告和 checklist 串起完整项目结构基础。"
tags: [software-engineering, capstone, project-structure, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/software-project-structure-foundations/README.md`](/assets/labs/software-project-structure-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

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

## 为什么要做这个结课骨架

结课骨架要解决的核心问题是“学了很多概念，但没有形成可交付闭环”。目录、模块、配置、测试和 README 单独看都容易理解；真正做项目时，难点在于让它们围绕同一个小需求协同工作。

`workflow_kit` 的目标刻意保持小：记录任务、修改状态、生成摘要、留下证据。它的价值在于展示一个项目从想法到可复查成果需要哪些最小部件。

## 从零到可展示的顺序

建议按下面顺序复现：

```bash
python3 -m workflow_kit.cli init --root demo_project --name release-ready-demo
python3 -m workflow_kit.cli add --root demo_project --owner product "write problem statement"
python3 -m workflow_kit.cli add --root demo_project --owner dev --status doing "separate domain and storage"
python3 -m workflow_kit.cli done --root demo_project 1
python3 -m workflow_kit.cli list --root demo_project
python3 -m workflow_kit.cli report --root demo_project
python3 -m unittest discover -s tests -v
```

这组命令覆盖项目生命周期：初始化、写入状态、修改状态、读取状态、生成报告、运行测试。

## 输出怎么读

任务列表：

```text
1    done    product    write problem statement
2    doing   dev        separate domain and storage
3    todo    qa         write CLI smoke test
```

第一列是稳定 id；第二列是状态机当前值；第三列是负责人；第四列是用户输入的标题。摘要输出：

```text
summary={'doing': 1, 'done': 1, 'todo': 1}
```

这说明 domain 的计数规则、storage 的读写、CLI 的展示和 report 的生成在同一份状态上达成一致。测试输出 `Ran 4 tests / OK` 则说明这些行为可以被自动复跑。

## 目录、模块和证据之间的关系

结课骨架不是简单创建一堆文件。每个文件都对应一个验收问题：

| 位置 | 回答的问题 | 验收证据 |
|---|---|---|
| `src/workflow_kit/domain.py` | 核心规则是什么 | domain 单元测试 |
| `src/workflow_kit/storage.py` | 状态如何持久化 | round-trip 测试 |
| `src/workflow_kit/cli.py` | 用户怎样操作 | CLI smoke test |
| `config/example.json` | 需要哪些可公开配置 | release checklist |
| `reports/summary.md` | 运行后产物在哪里 | demo transcript |
| `README.md` | 新读者如何开始 | 文档审查 |

这个表能帮助你判断新增文件是否有明确职责。

## 可扩展边界

完成骨架后，最安全的扩展方式是保持外部 contract 不变：

```text
JSON -> SQLite：list/report 输出不变，domain 测试不变
unittest -> pytest：行为断言不变，测试入口可变
本地 CLI -> Web API：domain 和 storage 先复用，再新增 HTTP adapter
```

只要现有 transcript 还能复跑，扩展就没有破坏基础闭环。

## 发布前自查

展示前可以按顺序检查：

```text
[ ] clean clone 或 clean temp dir 能运行 demo
[ ] README 命令与 transcript 一致
[ ] 测试输出包含成功用例和失败定位线索
[ ] 示例配置没有真实私有值
[ ] 报告能解释当前能力边界
```

这份自查比“项目差不多好了”更可靠，因为每一项都有可观察证据。

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
