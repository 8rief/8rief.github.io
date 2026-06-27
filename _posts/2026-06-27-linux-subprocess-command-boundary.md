---
layout: post
title: "命令执行边界：用 argv、校验和 loopback 范围替代 shell 拼接"
date: 2026-06-27 23:06:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地命令边界 demo 说明输入校验、argv list 和 shell metacharacter 拒绝。"
tags: [linux, subprocess, input-validation, defensive-security]
---
{% raw %}

> 主题：Linux 网络与授权安全基础 / subprocess boundary
> 本文只演示本地 loopback IP 校验，不执行用户提供的 shell 字符串。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

很多安全问题来自把用户输入拼进 shell 字符串。更稳的方式是先把输入限制成明确数据类型，再用 argv list 调用子进程，并避免 `shell=True`。lab 用 IP literal 校验演示这个边界。

## 学习目标

1. 区分 shell 字符串和 argv list。
2. 用 `ipaddress` 校验 loopback IP literal。
3. 拒绝包含 shell 元字符的输入。
4. 把命令边界证据写入 JSON。

## 先修知识

需要知道 Linux 命令通常由程序名和参数组成。

## 核心模型

![命令执行边界](/assets/diagrams/linux-subprocess-command-boundary.svg)

输入先进入类型校验，校验通过后生成 argv list，子进程不经过 shell。校验失败时没有 argv，也没有执行。

## 逐步实现

运行：

```bash
python3 -m local_netsec_lab.cli command-boundary   --output reports/command_boundary.json
```

本次证据：

```json
{
  "safe_accepted": true,
  "rejected_accepted": false,
  "rejected_reason": "value must be an IP literal"
}
```

安全输入 `127.0.0.1` 被解析为 loopback IP，命令以 argv list 运行。带 shell 元字符的输入无法解析为 IP literal，因此被拒绝，`argv` 为空。

## 代码边界

核心函数只返回参数数组：

```python
return [sys.executable, "-c", "import sys; print(sys.argv[1])", str(ip)]
```

这段代码没有拼接 shell 字符串，也没有把未经校验的输入交给 shell。真实项目还要限制可执行程序、工作目录、环境变量、超时和输出大小。

## 常见错误

1. **把字符串校验写在执行之后。** 校验必须发生在生成命令前。
2. **以为 argv list 自动安全。** argv list 仍需要参数语义校验。
3. **允许任意主机。** 本 lab 只允许 loopback，避免越界探测。
4. **忽略 timeout。** 子进程和网络操作都需要超时边界。

## 练习或延伸

1. 把校验改成只允许 `127.0.0.1`，拒绝 `::1`，观察测试怎样调整。
2. 给 subprocess 增加 timeout 参数。
3. 记录 rejected 输入的原因，但避免把完整用户输入写进公开日志。

## 参考资料

- Python 文档：[subprocess](https://docs.python.org/3/library/subprocess.html)
- Python 文档：[ipaddress](https://docs.python.org/3/library/ipaddress.html)
- OWASP Cheat Sheet Series：[项目首页](https://owasp.org/www-project-cheat-sheets/)


{% endraw %}
