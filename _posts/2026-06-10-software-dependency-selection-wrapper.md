---
layout: post
title: "依赖选择：先问为什么需要库，再决定怎么包住它"
date: 2026-06-10 18:00:00 +0800
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

## 为什么要引入依赖边界

依赖边界要解决的核心问题是“外部 API 扩散”。一个库刚引入时通常只为了解决一个小问题，例如命令行解析、表格输出或 HTTP 请求；如果直接在所有模块里调用它，后续升级、替换、删除都会变成全项目修改。

判断依赖是否值得引入，可以先写一张需求表：

| 需求 | 标准库是否满足 | 引入第三方库的收益 | wrapper 位置 |
|---|---|---|---|
| 简单 CLI 子命令 | `argparse` 足够 | 复杂交互时才明显 | `cli.py` |
| JSON 本地状态 | `json` 足够 | schema 复杂后再考虑 | `storage.py` |
| 路径处理 | `pathlib` 足够 | 暂无 | `layout.py` |
| 单元测试 | `unittest` 足够 | fixture 大量复用时再考虑 | `tests/` |

这个表让“要不要加库”变成工程判断，而不是个人偏好。

## 标准库优先的可观察证据

本包 lab 使用标准库完成 CLI、存储、测试和报告。验证命令可以保持很短：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

健康输出中四个测试全部通过：

```text
test_cli_contract ... ok
test_domain_validation_and_summary ... ok
test_layout_creates_expected_directories ... ok
test_storage_round_trip ... ok
Ran 4 tests
OK
```

这说明当前需求没有触碰标准库的明显边界：CLI 参数简单，JSON schema 小，测试 fixture 可控，报告是 Markdown 文本。此时增加第三方库会提高安装和版本成本，却不会明显提升可维护性。

## 如果真的需要第三方库，先包一层

假设后续 CLI 需要自动补全、彩色帮助和复杂子命令，可以把第三方 CLI 库限制在入口层：

```python
# cli_adapter.py
from workflow_kit.domain import TaskCommand


def parse_args(argv: list[str]) -> TaskCommand:
    """把外部 CLI 库的解析结果转换成项目内部命令对象。"""
    ...
```

内部模块只认识 `TaskCommand`，不认识外部库对象。这样替换 CLI 库时，核心规则、storage 和测试用例不需要一起重写。

## 版本和许可证也属于技术边界

选择依赖时至少记录三项信息：

```text
版本边界：允许哪些 major/minor 版本
许可证：是否允许项目当前用途
替代方案：如果库不再维护，标准库或其他库能否接替
```

小项目常见的成熟做法是先保持零外部依赖；当需求增长到标准库会显著增加复杂度时，再引入一个经过 wrapper 隔离、测试覆盖、版本受控的依赖。

## 输出怎么读

如果 `python3 -m unittest` 已经覆盖 CLI、domain、layout 和 storage，且 README 的 demo 不需要额外安装步骤，那么“暂不引入依赖”是一个有证据的决定。相反，如果 README 开始出现大量手写解析、重复格式化、复杂网络重试逻辑，就说明标准库实现成本已经上升，需要重新评估。

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
