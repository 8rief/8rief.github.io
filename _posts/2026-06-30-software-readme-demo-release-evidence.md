---
layout: post
title: "README、demo transcript 和 release checklist：让项目能被复查"
date: 2026-06-30 03:46:00 +0800
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
