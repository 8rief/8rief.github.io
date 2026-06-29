---
layout: post
title: "日志和错误信息：把诊断线索写给未来的自己"
date: 2026-06-29 20:06:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用结构化诊断行区分用户输出、错误输出和可审计日志线索。"
tags: [logging, debugging, error-handling, cpp, teaching]
---
{% raw %}

> 主题：调试与构建工具基础 / logging / error messages
> 本文 lab 已验证：CLI 输出 `level=info component=parser` 和 `level=warn component=parser` 两类诊断行。

很多调试时间浪费在“当时到底发生了什么”。日志和错误信息的任务是把关键状态留下来：哪个组件、什么级别、发生了什么、是否影响用户。好的诊断信息不需要很花哨，但必须稳定、可搜索、不过度暴露敏感信息。

## 学习目标

1. 区分用户输出、错误输出和诊断日志。
2. 写出稳定的结构化诊断行。
3. 避免在日志中泄露路径、密钥或大段输入。
4. 让错误消息指向可操作的下一步。

## 先修知识

需要会运行 CLI，并知道 stdout 和 stderr 的区别。

## 核心模型

![日志和错误信息边界模型](/assets/diagrams/debug-logging-error-message-boundary.svg)

用户输出面向正常结果；错误输出面向当前失败；日志面向后续诊断。三者可以同时存在，但不要混成一堆不可解析文本。稳定字段如 `level`、`component`、`message` 能让 grep 和脚本更容易处理。

## 逐步实现

lab 的诊断行函数：

```cpp
string diagnostic_line(string_view level, string_view component, string_view message) {
    ostringstream out;
    out << "level=" << level << " component=" << component
        << " message=\"" << message << "\"";
    return out.str();
}
```

运行：

```bash
./.lab_tmp/build-debug/debug_lab_cli log
```

输出：

```text
level=info component=parser message="accepted input batch"
level=warn component=parser message="rejected non-positive token"
```

这样的日志行可以直接用 `grep 'level=warn'` 找警告，也可以按 `component=parser` 聚合。

## 常见错误

1. **日志只写“failed”。** 没有组件、输入边界和下一步，很难定位。
2. **把密钥或本机路径写进公开日志。** 日志是持久证据，必须有公开安全意识。
3. **正常输出和调试输出混在一起。** 机器读取 CLI 输出时会被干扰。
4. **错误消息不可操作。** “invalid input” 不如 “not positive: -2”。

## 练习或延伸

1. 把 parse 命令的错误写到 stderr，把正常摘要写到 stdout。
2. 给诊断行增加 `input_count` 字段，但不要打印完整输入。
3. 写一个脚本统计 transcript 中 warn 行数量。

## 参考资料

- Twelve-Factor App：[Logs](https://12factor.net/logs)
- IETF RFC 5424：[The Syslog Protocol](https://www.rfc-editor.org/rfc/rfc5424)
- cppreference：[std::ostringstream](https://en.cppreference.com/w/cpp/io/basic_ostringstream)

{% endraw %}
