---
layout: post
title: "路径穿越实验：从 unsafe join 到 canonical path 边界"
date: 2026-05-24 09:00:00 +0800
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

## 为什么需要 canonical path 边界

应用看到的是 URL 参数，文件系统最终处理的是解析后的路径。两者之间可能经过百分号解码、分隔符处理、`.`/`..` 归一化和符号链接解析。只搜索字符串 `../` 会把防护绑定在某一种写法上，无法表达真正的不变量。

这里需要维护的不变量是：**最终要打开的 regular file 必须位于解析后的 document root 中。** 这个条件直接对应文件系统对象，不依赖输入最初怎样拼写。

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

保持本地教学服务运行，在 lab 根目录生成边界报告：

```bash
PYTHONPATH=src python3 -m local_netsec_lab.cli path-boundary \
  --base-url http://127.0.0.1:18480 \
  --output reports/path_boundary.json
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

请求中的 query 由 HTTP 层解析一次。编码形式也进入同一拒绝路径：

```text
/safe-file?name=%2e%2e%2foutside_area%2fprivate_note.txt
-> decoded name: ../outside_area/private_note.txt
-> HTTP 400
```

生产代码要明确哪一层负责解码，避免网关、框架和业务代码对同一值反复解码。当前 helper 接受已经解码的文件名，职责边界保持单一。

## safe_resolve 的检查顺序

```python
root = document_root.resolve()
candidate = Path(requested_name)
if not requested_name or candidate.is_absolute():
    raise PathBoundaryError("empty or absolute paths are not allowed")

resolved = (root / candidate).resolve()
if resolved != root and root not in resolved.parents:
    raise PathBoundaryError("requested path leaves document root")
if not resolved.is_file():
    raise PathBoundaryError("requested path is not a regular file")
```

`Path.resolve()` 会消除 `..` 并解析符号链接。父子关系用 `Path` 对象比较，没有使用容易误判 `/srv/public-copy` 的字符串前缀判断。最后的 regular-file 检查还会拒绝目录和不存在的路径。

## 三条路径手算

假设 root 是 `/lab/sample_public`：

```text
readme.txt
  -> /lab/sample_public/readme.txt       -> 接受

nested/../readme.txt
  -> /lab/sample_public/readme.txt       -> 接受

../outside_area/private_note.txt
  -> /lab/outside_area/private_note.txt  -> 拒绝
```

第二条说明 `..` 字面量并非自动等于攻击；安全条件取决于解析后的目标是否仍在 root 内。第三条越过 root，必须在打开文件之前停止。

## 当前实现仍有的边界

resolve→检查→read 之间存在时间窗口。如果不可信本地用户能在这几步之间替换符号链接，可能形成 TOCTOU 竞态。这个单进程本地 lab 的目录不会并发改变，因此适合解释 canonical containment；高对抗环境应使用目录文件描述符、`openat`/`openat2` 一类更强的内核边界，并根据平台能力设计。

Python 官方文档还说明 `http.server` 的简单文件 handler 会跟随符号链接。当前 lab 自己实现 safe handler，且只监听 loopback；它仍然不是生产文件服务器。

## 常见错误

1. **只过滤字符串片段。** 编码、分隔符和符号链接会绕开简单字符串判断。
2. **先打开文件再检查。** 边界检查必须发生在文件读取前。
3. **只测试正常文件。** 应同时测试 public 文件和越界输入。
4. **把 vulnerable demo 暴露到外网。** 本文端点只用于本地教学。

## 练习或延伸

1. 给 safe 端点增加 allowlist，只允许 `readme.txt` 和 `nested/info.txt`。
2. 给测试增加 URL 编码形式的上级目录片段。
3. 把 path boundary evidence 写成修复报告模板。
4. 建立一个指向 root 外部的符号链接，确认当前 containment 检查拒绝它。

## 参考资料

- OWASP：[Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- PortSwigger Web Security Academy：[File path traversal](https://portswigger.net/web-security/file-path-traversal)
- Python 文档：[`Path.resolve`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve)
- Python 文档：[urllib.parse](https://docs.python.org/3/library/urllib.parse.html)
- Linux man-pages：[openat2(2)](https://man7.org/linux/man-pages/man2/openat2.2.html)


{% endraw %}
