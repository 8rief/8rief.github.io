---
layout: post
title: "Python 基础语法和数据模型：先把数据形状写清楚"
date: 2026-06-25 16:31:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 dataclass、类型标注、属性方法和不可变记录描述文件清单，建立项目数据流的核心模型。"
tags: [python, dataclass, typing, data-model, project-design]
---
{% raw %}


> 主题：Python 从0到可运行项目 / 语法 / 数据模型 / dataclass  
> 本文代码来自同一个本地 lab。相关测试覆盖清单排序、字节数统计和 SHA-256 值。

Python 语法很容易上手，工程难点常常出在数据形状不清楚：函数返回的是列表、字典、对象，还是混合结构？字段名在哪里统一？汇总值是临时计算还是写死保存？先把数据模型写清楚，后续文件、CLI、API 和测试都会稳定很多。

## 学习目标

1. 用 `dataclass` 表达领域记录。
2. 用类型标注说明函数输入输出。
3. 把文件条目、清单和汇总拆成三个层次。
4. 理解 `to_dict()` 为什么放在边界处。
5. 通过测试验证数据顺序和汇总逻辑。

## 先修知识

需要知道 Python 的函数、字符串、列表和字典。本文会用到类，重点放在项目里的数据结构如何保持清晰。

## 核心模型

文件扫描项目的数据流可以抽象成：文件系统路径进入扫描器，扫描器产出领域对象，领域对象在 CLI/API 边界转换成字典或 JSON。

![从文件到领域对象](/assets/diagrams/python-core-syntax-data-model.svg)

关键原则是：内部用有名字的对象表达含义，边界再转成通用格式。

## 定义文件条目

最小文件条目包含相对路径、字节数和 SHA-256：

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class FileEntry:
    path: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }
```

`frozen=True` 让对象创建后不能随意改字段。这个选择适合清单条目，因为扫描结果应当由输入文件决定，后续导出 JSON/CSV 时不应该偷偷修改条目。

## 把清单和汇总拆开

清单对象保存所有条目，汇总对象保存文件数和总字节数：

```python
@dataclass(frozen=True)
class ManifestSummary:
    file_count: int
    total_bytes: int

@dataclass(frozen=True)
class Manifest:
    root_name: str
    entries: tuple[FileEntry, ...]

    @property
    def summary(self) -> ManifestSummary:
        return ManifestSummary(
            file_count=len(self.entries),
            total_bytes=sum(entry.size_bytes for entry in self.entries),
        )
```

这里把 `entries` 设为 `tuple`，表达“扫描结束后这组条目就是一个结果”。`summary` 用属性方法计算，避免汇总值和条目列表不一致。

## 类型标注的实际作用

类型标注不会让 Python 变成静态语言，但它能帮助读者和工具理解边界。例如：

```python
def build_manifest(root: Path | str) -> Manifest:
    ...
```

这个签名说明调用者可以传 `Path` 或字符串，返回值一定是 `Manifest`。后续 CLI 可以直接读取 `manifest.summary.file_count`，API 可以调用 `manifest.to_dict()`。如果函数随手返回普通字典，调用者需要猜字段名和嵌套结构。

## 测试数据模型

lab 中的测试先创建两个临时文件，再检查顺序、汇总和哈希：

```python
def test_build_manifest_is_deterministic(tmp_path):
    (tmp_path / "b.txt").write_text("beta\n", encoding="utf-8")
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")

    manifest = build_manifest(tmp_path)

    assert [entry.path for entry in manifest.entries] == ["a.txt", "b.txt"]
    assert manifest.summary.file_count == 2
```

这个测试检验的是项目契约：同一目录每次扫描都按相对路径排序；汇总由条目计算；哈希来自文件内容。

## 常见错误

1. **到处传无结构字典。** 初期省事，后面字段改名时 CLI、API、测试一起坏。
2. **把汇总值保存成可变字段。** 条目变了但汇总没变，会造成隐蔽错误。
3. **把绝对路径写入公开清单。** 项目内部可以解析绝对路径，导出的清单应使用相对路径，避免泄露本机目录结构。

## 练习

1. 给 `FileEntry` 增加 `extension` 字段，并让测试验证 `.txt`、`.json`、`.csv` 三种扩展名。
2. 让 `Manifest.summary` 额外返回最大文件大小，思考这个值应不应该写入 `entries`。
3. 把 `entries` 从 `tuple` 改成 `list`，尝试在创建后追加条目，观察测试能否暴露风险。

## 参考资料

- Python 文档：[Data Classes](https://docs.python.org/3/library/dataclasses.html)
- Python 文档：[typing — Support for type hints](https://docs.python.org/3/library/typing.html)
- Python 文档：[Classes](https://docs.python.org/3/tutorial/classes.html)


{% endraw %}
