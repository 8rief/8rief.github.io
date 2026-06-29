---
layout: post
title: "模块边界：把 domain、storage、config 和 CLI 分开"
date: 2026-06-30 03:42:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 workflow_kit 的 domain/storage/config/layout/cli 拆分解释为什么核心逻辑应该少依赖边界细节。"
tags: [software-engineering, modules, architecture, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / module boundaries
> 本文 lab 已验证：domain validation、layout 创建、storage round trip 和 CLI contract 都有 unittest 覆盖。

项目变大后，最容易混乱的是模块职责。一个可维护的小项目通常把核心规则和外部边界分开：domain 负责业务对象和规则，storage 负责读写，config 负责配置校验，CLI 负责把用户输入转成函数调用。

## 学习目标

1. 区分核心逻辑和边界适配器。
2. 理解为什么 domain 模块应该尽量少依赖文件系统和命令行。
3. 用测试覆盖模块边界，而不是只测最终脚本。
4. 能为一个小项目画出模块调用方向。

## 先修知识

需要理解函数、模块和单元测试。本文示例使用 Python，但边界思想适用于 Java、Go、C++ 和 Rust 项目。

## 核心模型

![核心逻辑和边界适配器](/assets/diagrams/software-module-boundaries-domain-adapters.svg)

`domain` 在中间，定义 `Task`、状态和摘要规则；`storage` 把对象保存成 JSON；`config` 校验项目根和名称；`layout` 创建目录；`cli` 把命令行参数传给这些模块。测试可以分别验证每条边界。

## 逐步实现

核心对象：

```python
@dataclass(frozen=True)
class Task:
    task_id: int
    title: str
    status: str = "todo"
    owner: str = "unassigned"
```

存储边界：

```python
def save_state(path: Path, state: dict[str, object]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
```

CLI 不直接拼 JSON，不直接实现业务规则；它只解析参数、调用模块、输出结果。这样改 storage 时不用改 domain，改 CLI 文案时不用改核心规则。

## 常见错误

1. **CLI 里堆所有逻辑。** 后续测试、复用和迁移都会困难。
2. **domain 依赖本地路径。** 纯规则应能在内存中测试。
3. **storage 静默吞错。** schema 版本、字段类型和文件格式错误应该显式失败。
4. **循环依赖。** 模块之间互相导入会让边界失效。

## 练习或延伸

1. 给 `Task` 增加 `priority` 字段，判断要改哪些模块。
2. 把 JSON storage 替换成 CSV storage，尽量保持 domain 测试不变。
3. 为 CLI 的错误输出增加一条测试。

## 参考资料

- Python 文档：[dataclasses](https://docs.python.org/3/library/dataclasses.html)
- Python 文档：[json](https://docs.python.org/3/library/json.html)
- Python 文档：[os.replace](https://docs.python.org/3/library/os.html#os.replace)

{% endraw %}
