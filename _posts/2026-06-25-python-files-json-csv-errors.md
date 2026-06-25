---
layout: post
title: "Python 文件、JSON、CSV 和异常：项目输入输出的边界"
date: 2026-06-25 16:32:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 pathlib、hashlib、json、csv 和原子写入，把文件扫描项目的输入、输出和错误边界讲清楚。"
tags: [python, pathlib, json, csv, exceptions, hashlib]
---
{% raw %}


> 主题：Python 从0到可运行项目 / pathlib / JSON / CSV / 异常边界  
> 本文 lab 已验证：固定样例目录扫描出 3 个文件、119 字节，并导出 JSON/CSV。

脚本阶段常见写法是“读一个文件，print 一个结果”。项目阶段要回答更多问题：输入路径不存在怎么办？传进来的是文件还是目录？输出写到一半失败怎么办？JSON 和 CSV 谁负责字段顺序？这些问题都属于输入输出边界。

## 学习目标

1. 用 `pathlib.Path` 管理目录、相对路径和文件写入。
2. 用 `hashlib.sha256()` 分块计算文件哈希。
3. 用 `json` 和 `csv` 导出同一份领域数据。
4. 区分可恢复的输入错误和程序内部错误。
5. 理解原子写入在报告文件中的价值。

## 先修知识

需要会使用路径、目录和文本文件。理解上一讲的 `FileEntry` 和 `Manifest` 会更顺畅。

## 核心模型

项目的文件边界可以拆成五步：先确认 root 是目录，再枚举普通文件，然后计算内容摘要，最后把同一份 manifest 导出为 JSON 和 CSV。

![文件输入输出边界](/assets/diagrams/python-files-json-csv-errors.svg)

这样拆分后，扫描逻辑不需要知道 CLI 参数名，导出逻辑也不需要重新遍历文件系统。

## 扫描目录

扫描器先把输入解析成绝对路径，再检查存在性和类型：

```python
class ScanBoundaryError(ValueError):
    """Raised when a requested scan root cannot be treated as a directory."""


def build_manifest(root: Path | str) -> Manifest:
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"scan root does not exist: {root_path}")
    if not root_path.is_dir():
        raise ScanBoundaryError(f"scan root is not a directory: {root_path}")
    ...
```

`FileNotFoundError` 是 Python 已有异常，适合表达路径不存在。`ScanBoundaryError` 是项目自己的边界错误，适合表达“存在，但不符合本项目输入契约”。

## 枚举和哈希

枚举文件时跳过符号链接，并按相对路径排序：

```python
def iter_regular_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())
```

排序让输出稳定。跳过符号链接可以避免扫描不小心离开用户指定的目录。哈希用分块读取，避免大文件一次性读入内存：

```python
def hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

## 导出 JSON 和 CSV

JSON 适合保留嵌套结构，CSV 适合用表格工具检查条目列表。它们应来自同一个 `Manifest`：

```python
def write_manifest_json(manifest: Manifest, path: Path | str) -> None:
    destination = Path(path)
    content = json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    _atomic_write_text(destination, content + "\n")
```

CSV 使用固定字段名：

```python
with tmp.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["path", "size_bytes", "sha256"])
    writer.writeheader()
    for entry in manifest.entries:
        writer.writerow(entry.to_dict())
```

`newline=""` 是 CSV 写入时的重要细节，避免在不同平台出现多余空行。

## 本地执行结果

lab 对样例目录执行扫描后，CLI 输出：

```text
scanned root=sample_data files=3 bytes=119
manifest root=sample_data files=3 bytes=119
```

JSON 摘要片段如下：

```json
{
  "root_name": "sample_data",
  "summary": {
    "file_count": 3,
    "total_bytes": 119
  }
}
```

这说明 JSON、CSV、CLI summary 读到的是同一份 manifest。

## 常见错误

1. **导出绝对路径。** 公共报告中优先使用相对路径。
2. **不排序就输出。** 文件系统遍历顺序可能变化，测试和 diff 会变得不稳定。
3. **写报告时直接覆盖目标文件。** 中途失败可能留下半个 JSON；先写临时文件再 `replace` 更安全。
4. **吞掉所有异常。** 输入错误应该被明确报告，不能把失败伪装成空结果。

## 练习

1. 增加一个 `--min-size` 过滤参数，只导出不小于指定字节数的文件。
2. 给 CSV 增加 `extension` 字段，并补充测试。
3. 人为传入一个普通文件路径，观察 `ScanBoundaryError` 如何被测试捕获。

## 参考资料

- Python 文档：[pathlib — Object-oriented filesystem paths](https://docs.python.org/3/library/pathlib.html)
- Python 文档：[hashlib — Secure hashes and message digests](https://docs.python.org/3/library/hashlib.html)
- Python 文档：[json — JSON encoder and decoder](https://docs.python.org/3/library/json.html)
- Python 文档：[csv — CSV File Reading and Writing](https://docs.python.org/3/library/csv.html)


{% endraw %}
