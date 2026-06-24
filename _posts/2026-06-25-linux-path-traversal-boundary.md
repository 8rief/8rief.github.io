---
layout: post
title: "目录穿越漏洞的本地复现：从 path join 到边界校验"
date: 2026-06-25 05:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个只监听 127.0.0.1 的 Python 服务复现 ../ 目录穿越，并用 resolve 与根目录边界检查修复。"
tags: [linux, web-security, defensive-security, python, path-traversal]
---
{% raw %}

> 主题：Web 安全基础 / 本地靶场 / 目录穿越 / 路径规范化  
> 本文命令已在 Ubuntu 24.04、Python 3.12.3、curl 8.5.0 环境下本地执行验证。实验服务只监听 `127.0.0.1`，漏洞请求只打本地玩具程序，用于理解防御边界。

网络和 HTTP 基础跑通以后，可以开始做第一类安全实验：把一个真实常见错误缩小到本地可复现的最小程序。目录穿越就是很适合入门的例子。它的表面形式是 URL 里出现 `../`，本质问题是服务端把用户输入直接拼到文件系统路径上，没有确认最终路径仍在允许目录内。

本文构造一个本地文件读取服务。`/unsafe` 端点直接 `web_root / name`，会读出 Web 根目录之外的文件；`/safe` 端点先解析真实路径，再检查它是否仍位于 Web 根目录下。本文聚焦服务端如何定义并验证文件访问边界。

## 安全边界

本文只访问本机 `127.0.0.1:18185` 上的临时服务。`secret.txt` 是实验脚本自己创建的本地演示文件，不包含真实秘密。不要把这里的请求用于未授权系统；学习目标是识别和修复路径边界错误。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释目录穿越为什么来自服务端路径边界缺失。
2. 复现一个最小的 `../` 越界读取。
3. 区分字符串拼接路径和规范化后的真实路径。
4. 用 `Path.resolve()` 与根目录包含关系检查阻止越界。
5. 写出文件下载、静态资源和附件读取功能的防御检查项。

## 核心模型

目录穿越问题可以画成一条边界线：

![目录穿越与路径边界校验](/assets/diagrams/linux-path-traversal-boundary.svg)

应用想开放的是 `web_root` 下的文件，例如 `www/index.txt`。用户输入 `../secret.txt` 后，如果服务端只做拼接，路径看起来是 `www/../secret.txt`，文件系统会把它解析到 `www` 外面。正确做法是先得到规范化绝对路径，再验证它是否仍在允许根目录内。

## 准备本地文件

实验创建两个文件：

```bash
mkdir -p www reports
printf 'public file inside web root\n' > www/index.txt
printf 'SECRET outside web root - local lab only\n' > secret.txt
find . -maxdepth 2 -type f | sort
```

输出：

```text
./path_server.py
./reports/transcript.txt
./run_lab.sh
./secret.txt
./www/index.txt
```

`www/index.txt` 是允许读取的公开文件，`secret.txt` 位于 Web 根目录外，模拟不该由静态文件接口暴露的文件。

## 不安全版本：直接拼路径

不安全端点的核心代码：

```python
if mode == 'unsafe':
    target = self.web_root / name
    self.send_text(200, f"UNSAFE read {target}\n" + target.read_text(encoding='utf-8'))
```

如果 `name=index.txt`，路径是 `www/index.txt`，看起来没有问题：

```bash
curl --noproxy '*' -sS 'http://127.0.0.1:18185/unsafe?name=index.txt'
```

输出：

```text
UNSAFE read www/index.txt
public file inside web root
```

但当输入变成 `../secret.txt`：

```bash
curl --noproxy '*' -sS 'http://127.0.0.1:18185/unsafe?name=../secret.txt'
```

输出：

```text
UNSAFE read www/../secret.txt
SECRET outside web root - local lab only
```

这就是越界。服务端以为自己从 `www` 下面读文件，文件系统实际解析到了 `www` 的父目录。

## 安全版本：先规范化，再检查边界

安全端点的关键代码：

```python
root = self.web_root.resolve()
target = (root / name).resolve()
if not target.is_relative_to(root) or not target.is_file():
    self.send_text(403, f"SAFE blocked name={name!r}\n")
    return
self.send_text(200, f"SAFE read {target.name}\n" + target.read_text(encoding='utf-8'))
```

`resolve()` 会消解 `..`、`.` 和符号链接影响，得到规范化绝对路径。`is_relative_to(root)` 检查规范化后的目标是否仍在允许根目录下。

再次请求越界路径：

```bash
curl --noproxy '*' -sS 'http://127.0.0.1:18185/safe?name=../secret.txt'
```

输出：

```text
SAFE blocked name='../secret.txt'
```

请求合法文件仍然成功：

```bash
curl --noproxy '*' -sS 'http://127.0.0.1:18185/safe?name=index.txt'
```

输出：

```text
SAFE read index.txt
public file inside web root
```

## 日志如何读

服务端日志节选：

```text
mode='unsafe' name='index.txt' peer=127.0.0.1:47756
mode='unsafe' name='../secret.txt' peer=127.0.0.1:47760
mode='safe' name='../secret.txt' peer=127.0.0.1:47768
mode='safe' name='index.txt' peer=127.0.0.1:47772
```

日志中的 `name` 是用户输入，不等于实际文件系统目标。排查这类问题时，既要记录原始输入，也要在调试环境中检查规范化后的目标路径。正式日志不应泄露过多本地绝对路径，但安全审计需要能判断越界尝试是否被阻断。

## 防御检查清单

文件下载、静态资源、附件预览、日志读取等功能都可以按下面顺序检查：

1. **定义允许根目录。** 先明确哪些目录可以被这个接口读取。
2. **拒绝绝对路径输入。** 用户输入应当是业务标识或相对名字；禁止把任意系统路径作为可读目标。
3. **规范化后再判断。** 检查 `(root / name).resolve()` 是否仍在 `root.resolve()` 内。
4. **处理符号链接。** 如果允许符号链接，要明确它们是否可以指向根目录外；不允许时要在部署或启动阶段检查。
5. **限制文件类型和大小。** 即使路径在根目录内，也要限制可读扩展名、MIME、大小和访问权限。
6. **最小权限运行。** 服务进程不应拥有读取无关敏感目录的权限。
7. **记录阻断事件。** 记录越界尝试的相对输入、来源和接口名，但不要把真实敏感路径回显给客户端。

## 常见错误

**只过滤字符串里的 `..`。** 攻击输入可能经过 URL 编码、重复编码、路径分隔符变体或符号链接绕过。稳妥边界应建立在规范化后的路径关系上。

**先打开文件再检查。** 边界检查要发生在读取之前。否则日志里看起来有检查，实际已经发生越界访问。

**把 404 当成安全策略。** 找不到文件不等于阻止越界。越界输入应该被明确识别并返回 403 或统一错误。

**服务权限过大。** 路径校验是应用层防线，进程权限是系统层防线。两者都需要。

## 练习

1. 尝试 `name=./index.txt`，观察安全版本是否允许。
2. 尝试 URL 编码形式 `name=..%2Fsecret.txt`，确认服务端解析后的 `name` 和阻断结果。
3. 在 `www` 里创建一个指向外部文件的符号链接，观察 `resolve()` 后的检查结果。
4. 把安全版本改成只允许 `.txt` 文件，并为不允许的扩展名返回 403。

## 参考资料

- [OWASP: Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [OWASP Cheat Sheet: File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html)
- [Python urllib.parse documentation](https://docs.python.org/3/library/urllib.parse.html)
{% endraw %}
