---
layout: post
title: "README、demo transcript 和 release checklist：让项目能被复查"
date: 2026-06-11 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 README、architecture note、demo output、project tree、summary report 和 release checklist 作为小项目收尾证据。"
tags: [software-engineering, documentation, release, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / documentation and release evidence
> 本文 lab 已验证：生成 `README.md`、`docs/architecture.md`、`reports/demo_output.txt`、`reports/project_tree.txt` 和 `reports/release_checklist.md`。

项目能运行还不够。别人接手时，需要知道项目解决什么问题、怎么运行、结构为什么这样放、demo 输出是什么、发布前检查是否通过。README、demo transcript 和 release checklist 共同构成收尾证据。

## 学习目标

1. 知道 README 应该回答哪些最小问题。
2. 用 demo transcript 证明命令真实运行过。
3. 用 architecture note 解释关键边界，而不是重复代码。
4. 用 release checklist 汇总测试、文档、配置和报告状态。

## 先修知识

需要理解目录结构、模块边界和测试策略。

## 核心模型

![项目收尾证据链](/assets/diagrams/software-readme-demo-release-evidence.svg)

README 是入口，architecture note 是设计说明，demo transcript 是运行证据，project tree 展示结构，summary report 展示产物，release checklist 把这些证据组织成发布判断。

## 逐步实现

lab 的 release checklist：

```text
- requirement slice: PASS
- directory layout: PASS
- module boundary: PASS
- config example without secrets: PASS
- JSON storage round trip: PASS
- CLI contract smoke: PASS
- unittest suite: see transcript
- README and architecture note: PASS
```

这份 checklist 不追求复杂流程，重点是把发布前最容易遗漏的事项固定下来。后续项目变大时，可以增加 changelog、版本号、CI、许可证、安装说明和兼容性说明。

## 为什么要引入证据链

证据链要解决的核心问题是“项目声称能运行，但读者无法复查”。README 写了命令，demo transcript 证明命令跑过，测试输出说明行为可重复，release checklist 把这些材料连接成发布判断。缺少其中任意一环，展示时都会留下疑问。

最小证据链可以写成：

```text
README usage -> demo transcript -> test output -> project tree -> release checklist
```

这条链让读者从“我应该怎么跑”一路走到“我看到的结果是否符合作者声明”。

## README 应该先回答的问题

小项目 README 不需要一开始就写得很长，但至少要回答：

```text
项目解决什么问题？
需要什么环境？
第一条命令是什么？
健康输出长什么样？
生成了哪些文件？
当前边界是什么？
```

一个可用的 usage 区块可以这样写：

````markdown
## Quick start

```bash
python3 -m workflow_kit.cli init --root demo_project --name release-ready-demo
python3 -m workflow_kit.cli add --root demo_project --owner product "write problem statement"
python3 -m workflow_kit.cli list --root demo_project
```

Expected output:

```text
1    todo    product    write problem statement
```
````

如果 README 没有 expected output，读者只能猜测命令成功时应该看到什么。

## transcript 的作用

transcript 是运行过程的证据，不是装饰性日志。它应该保留命令、关键输出和环境假设：

```text
python=Python 3.12.3
## create demo project
initialized=demo_project
added id=1 status=todo owner=product title=write problem statement
## unittest
Ran 4 tests
OK
```

读 transcript 时要看两点：第一，输出字段是否和 README 一致；第二，测试是否覆盖了 README 中承诺的行为。

## release checklist 该如何写

好的 checklist 应该引用证据，而不是只写主观判断：

```text
- requirement slice: PASS, see Quick start transcript
- config example without secrets: PASS, see config/example.json
- CLI contract smoke: PASS, see test_cli_contract
- unittest suite: PASS, see test_output.txt
```

这种写法能让后续审查者快速跳到对应文件。若 checklist 只写“文档已完善”“测试已通过”，它就无法帮助定位问题。

## 输出怎么读

项目树：

```text
demo_project/
  README.md
  config/example.json
  data/tasks.json
  docs/architecture.md
  reports/summary.md
```

这说明入口文档、公开配置、运行数据、设计说明和生成报告各自有位置。若报告声称生成了 `reports/summary.md`，项目树中就应该能看到该文件；若 README 提到配置字段，`config/example.json` 中就应该存在相应示例。

## 常见审查顺序

展示前可以按下面顺序看：

```text
1. README：能否在 2 分钟内找到第一条命令
2. transcript：命令是否真实跑过
3. test output：失败时能否定位
4. project tree：产物是否在文档声明的位置
5. checklist：是否还有发布前未完成项
```

这是一条面向读者的复查路径，比从源码文件逐个解释更有效。

## 常见错误

1. **README 只有一句口号。** 至少要有目标、安装/运行、示例输出和边界。
2. **文档重复代码细节。** 设计文档应该解释为什么这样分层。
3. **没有 transcript。** 读者无法判断命令是否真的跑过。
4. **release checklist 和测试脱节。** checklist 应引用具体测试和报告，而不是只写“已检查”。

## 练习或延伸

1. 为 `workflow_kit` 写一个更完整的 README usage 区块。
2. 给 checklist 增加 `changelog` 和 `version` 两项。
3. 比较两个开源项目 README，看哪个更容易让你复现第一个 demo。

## 参考资料

- GitHub Docs：[About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- Keep a Changelog：[keepachangelog.com](https://keepachangelog.com/en/1.1.0/)
- Python Packaging User Guide：[Writing your pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

{% endraw %}
