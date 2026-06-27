---
layout: post
title: "路径穿越实验：从 unsafe join 到 canonical path 边界"
date: 2026-06-27 23:05:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "在本地 toy 服务中比较 unsafe 文件读取和 safe_resolve，解释 canonical path containment。"
tags: [linux, path-traversal, filesystem, defensive-security]
---
{% raw %}

> 主题：Linux 网络与授权安全基础 / 路径边界
> 本文的易错端点只读取 lab 自己创建的文件，用来说明修复方式。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

路径穿越问题的根源是把用户输入直接拼到文件路径上。攻击者可以用上级目录片段让路径离开预期目录。防护思路是先解析出 canonical path，再确认最终路径仍在允许的 document root 内。

## 学习目标

1. 解释路径拼接为什么会让文件边界失效。
2. 用本地 toy 服务复现 unsafe 与 safe 的差异。
3. 写出 `safe_resolve` 的关键检查顺序。
4. 将修复证据写入 `path_boundary.json`。

## 先修知识

需要知道相对路径、上级目录片段和文件根目录的含义。

## 核心模型

![路径穿越与 canonical path 边界](/assets/diagrams/linux-path-traversal-safe-resolve.svg)

unsafe join 直接把输入拼到根目录后面；safe resolve 会解码、拒绝绝对路径、解析真实路径，并检查结果仍在 document root 内。

## 逐步实现

lab 同时提供两个端点：

```text
/unsafe-file?name=../outside_area/private_note.txt
/safe-file?name=../outside_area/private_note.txt
```

本次证据：

```json
{
  "unsafe_status": 200,
  "safe_status": 400,
  "boundary": "unsafe endpoint can leave document root; safe endpoint rejects the same lab-owned path"
}
```

unsafe 端点能读到 document root 外的 lab-owned note。safe 端点对同一个输入返回 400，并说明路径离开 document root。

## safe_resolve 的检查顺序

```python
decoded = unquote(requested_name)
candidate = Path(decoded)
if candidate.is_absolute():
    raise PathBoundaryError()
resolved = (root / candidate).resolve()
if resolved != root and root not in resolved.parents:
    raise PathBoundaryError()
```

这个实现依赖标准库路径解析，核心是比较最终解析结果与允许根目录的关系。

## 常见错误

1. **只过滤字符串片段。** 编码、分隔符和符号链接会绕开简单字符串判断。
2. **先打开文件再检查。** 边界检查必须发生在文件读取前。
3. **只测试正常文件。** 应同时测试 public 文件和越界输入。
4. **把 vulnerable demo 暴露到外网。** 本文端点只用于本地教学。

## 练习或延伸

1. 给 safe 端点增加 allowlist，只允许 `readme.txt` 和 `nested/info.txt`。
2. 给测试增加 URL 编码形式的上级目录片段。
3. 把 path boundary evidence 写成修复报告模板。

## 参考资料

- OWASP：[Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- PortSwigger Web Security Academy：[File path traversal](https://portswigger.net/web-security/file-path-traversal)
- Python 文档：[pathlib](https://docs.python.org/3/library/pathlib.html)
- Python 文档：[urllib.parse](https://docs.python.org/3/library/urllib.parse.html)


{% endraw %}
