---
layout: post
title: "依赖选择：先问为什么需要库，再决定怎么包住它"
date: 2026-06-30 03:44:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 stdlib-first、引入条件、版本边界和 wrapper 讲清小项目如何避免依赖失控。"
tags: [software-engineering, dependencies, packaging, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / dependency selection
> 本文 lab 已验证：capstone 使用 Python 标准库完成 CLI、JSON storage、测试和报告，证明当前需求不需要外部依赖。

引入依赖不是坏事，但每个依赖都会带来版本、API、许可证、构建和安全维护成本。小项目的原则是先问需求：标准库能否稳定满足？若需要第三方库，是否有清晰的 wrapper 边界和更新策略？

## 学习目标

1. 根据需求判断是否需要第三方库。
2. 识别依赖带来的 API、版本和维护成本。
3. 用 wrapper 把外部 API 限制在少数模块里。
4. 为依赖更新保留测试和发布检查。

## 先修知识

需要理解模块边界和测试。若已经读过 Python、Go、Rust 或 C++ 项目系列，可以把本文当作跨语言原则。

## 核心模型

![依赖引入决策路径](/assets/diagrams/software-dependency-selection-wrapper.svg)

从真实需求出发：若标准库足够，就先保持简单；若第三方库带来明确收益，就记录选择理由、版本边界和替代方案，并通过 wrapper 隔离外部 API。测试覆盖 wrapper 的行为契约。

## 逐步实现

capstone 只需要命令行、JSON、路径、时间和 unittest。标准库已经覆盖：

```python
import argparse
import json
from pathlib import Path
import unittest
```

若以后要把 CLI 改成更复杂的交互工具，可以考虑引入 Typer 或 Click；若要发布包，可以引入 packaging 工具链。引入前先写清：解决什么痛点、替换成本是什么、如何测试、如何锁定版本。

## 常见错误

1. **为了熟悉度引入库。** 依赖应该解决明确问题。
2. **外部 API 散落全项目。** 后续替换库时会变成大范围修改。
3. **没有版本边界。** 构建和运行结果会随时间漂移。
4. **用库替代设计。** 库能减少代码量，但不能替代清晰的输入输出契约。

## 练习或延伸

1. 判断 `workflow_kit` 是否需要第三方 CLI 库，并写出引入条件。
2. 为 JSON storage 写一个 `Storage` wrapper 接口，预留 SQLite 替换空间。
3. 给一个已有项目列出三项依赖，说明每项解决的具体需求。

## 参考资料

- Python Packaging User Guide：[Dependency specifiers](https://packaging.python.org/en/latest/specifications/dependency-specifiers/)
- Python 文档：[argparse](https://docs.python.org/3/library/argparse.html)
- Semantic Versioning：[semver.org](https://semver.org/)

{% endraw %}
