---
layout: post
title: "Python 环境和依赖管理：先让项目可复现"
date: 2026-06-25 16:30:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 python -m venv、pyproject.toml 和可复跑 lab 开始，把 Python 项目的解释器、依赖和命令入口固定下来。"
tags: [python, venv, packaging, pyproject, reproducibility]
---
{% raw %}


> 主题：Python 从0到可运行项目 / 环境 / 虚拟环境 / 依赖管理  
> 本文命令已在 Ubuntu 24.04、Python 3.12.3 环境下执行。配套 lab 的最终结果是 7 个 pytest 用例通过，并产出 CLI、API 和 JSON/CSV 报告的本地 transcript。

很多 Python 初学者会从一个单文件脚本开始，脚本在自己机器上能跑，换一台机器后依赖缺失、包版本漂移、命令入口找不到。工程化的第一步是先把运行边界固定：用哪个解释器、依赖装在哪里、项目如何被安装、命令如何被复跑。

## 学习目标

1. 用 `python -m venv` 建立项目独立环境。
2. 理解 `pyproject.toml` 在现代 Python 项目中的角色。
3. 用 editable install 把源码目录和命令入口接起来。
4. 解释为什么 transcript 比口头说明更适合作为复现实证。
5. 为后续 CLI、API、测试文章保留同一个项目骨架。

## 先修知识

你需要会进入 Linux 终端、执行 `python3 --version`、理解目录和文件的基本概念。还不需要掌握类、装饰器或 Web 框架。

## 核心模型

一个可复现 Python 项目可以先看成五层边界：

![Python 项目环境边界](/assets/diagrams/python-environment-venv-packaging.svg)

系统 Python 负责提供解释器。虚拟环境隔离项目依赖。`pyproject.toml` 描述项目元数据、依赖和命令入口。源码安装进虚拟环境后，CLI 和测试才能像真实用户那样调用项目。transcript 记录命令和观察结果，后续文章引用的是已经执行过的事实。

## 建立项目骨架

本文的 lab 项目叫 `local-evidence-kit`。它扫描一个本地目录，计算每个文件的大小和 SHA-256，导出 JSON/CSV，并在后续文章中增加 CLI、API 和测试。目录结构如下：

```text
local-evidence-kit/
├── pyproject.toml
├── run_lab.sh
├── sample_data/
├── scripts/
├── src/local_evidence/
└── tests/
```

核心配置放在 `pyproject.toml`：

```toml
[project]
name = "local-evidence-kit"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "typer>=0.12,<0.27",
  "fastapi>=0.116,<0.117",
  "httpx>=0.27,<0.29",
  "uvicorn>=0.30,<0.50",
]

[project.optional-dependencies]
dev = ["pytest>=8,<9"]

[project.scripts]
local-evidence = "local_evidence.cli:app"
```

这里有三个决策值得说明。

第一，`src/local_evidence/` 是项目源码目录。采用 `src` 布局可以减少一种常见误判：测试从当前目录直接导入源码，以为安装成功，实际打包后入口不可用。

第二，依赖使用范围约束。示例项目不追求锁死每一个补丁版本，但把主版本和关键小版本控制在可解释范围内，避免教程刚写完就因为依赖行为变化而失效。

第三，命令入口通过 `[project.scripts]` 暴露。安装项目后，读者可以执行 `local-evidence ...`，也可以执行 `python -m local_evidence.cli ...`。这比把脚本散放在目录里更接近真实项目。

## 从空环境到可运行

最小命令序列如下：

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

每条命令都有明确作用：

- `python3 --version` 先记录解释器版本，避免后来把语法错误误判为业务错误。
- `python3 -m venv .venv` 创建项目内虚拟环境。
- `source .venv/bin/activate` 让当前 shell 优先使用虚拟环境里的 `python` 和 `pip`。
- `python -m pip install -e ".[dev]"` 以 editable 模式安装当前项目，并安装开发依赖。
- `python -m pytest -q` 以测试结果确认安装后的项目能被导入和执行。

lab transcript 的关键结果如下：

```text
Python 3.12.3
Successfully installed fastapi-0.116.2 httpx-0.28.1 pytest-8.4.2 typer-0.26.7 ...
.......                                                                  [100%]
```

这段输出说明三件事：解释器版本已知，依赖安装完成，测试在安装后的项目环境里通过。

## 常见错误

1. **在系统环境里直接 pip install。** 这样会把多个项目的依赖混在一起，后续很难判断错误来自代码还是环境。
2. **只运行源码文件，不安装项目。** 这样看不到命令入口、包元数据和真实导入路径的问题。
3. **把 transcript 当成装饰。** transcript 的价值在于记录命令、版本和输出。没有执行证据的教程很难排查读者复现失败的原因。

## 练习

1. 把项目版本改成 `0.1.1`，重新执行 editable install，观察 `python -m pip show local-evidence-kit` 的输出。
2. 临时删除 `dev = ["pytest>=8,<9"]`，重新安装后执行 `python -m pytest -q`，观察失败原因。
3. 尝试在未激活虚拟环境时执行 `local-evidence`，比较命令是否可见。

## 参考资料

- Python 文档：[venv — Creation of virtual environments](https://docs.python.org/3/library/venv.html)
- PEP 621：[Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- pip docs source：[Local project installs](https://github.com/pypa/pip/blob/main/docs/html/topics/local-project-installs.md)


{% endraw %}
