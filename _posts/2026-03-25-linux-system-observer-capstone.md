---
layout: post
title: "结课项目：写一个本地 system observer，把进程和文件证据整理成报告"
date: 2026-03-25 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个本地观察工具串起文件、描述符、进程、环境、权限、信号和文本流水线。"
tags: [linux, project, observability, python, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/os-linux-process-files/README.md`](/assets/labs/os-linux-process-files/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：操作系统与 Linux 基础 / 结课项目
> 本文是 OS/Linux 进程与文件基础包的第八篇。项目只观察本机和 lab 创建的文件，不读取敏感目录。

前七篇分别讲了文件系统、文件描述符、进程、环境、权限、信号和文本流水线。结课项目把这些知识串成一个本地 system observer：创建受控 workspace，收集每类证据，写出 Markdown 报告和 JSON 文件，再用 unittest 保证核心行为可复跑。

## 学习目标

1. 把零散命令组织成可复现实验项目。
2. 用 Python 标准库收集本地文件和进程观察结果。
3. 保存人能读的 Markdown 报告和机器可读的 JSON 证据。
4. 用测试和 transcript 说明项目确实跑过。

## 先修知识

需要读过本系列前七篇，知道如何运行 Python 脚本和 shell 命令。

## 为什么需要结课观察器

单条命令能证明一个瞬时现象，却很难说明实验输入是怎样准备的、输出保存在哪里、换一台机器后哪些差异可接受。结课项目用一个可重跑入口把这些零散证据收束起来，让学习结果成为可检查的产物。

这个项目还刻意保留了机器差异。PID、inode、运行时间和 WSL 挂载权限可以变；测试检查结构关系、字段类型和关键结果，不把动态数字写死。这是系统实验可复现性的核心做法。

## 核心模型

![system observer 结课项目结构](/assets/diagrams/linux-system-observer-capstone.svg)

项目分为四层：workspace 负责受控输入，collector 负责采集系统观察，reporter 负责输出 Markdown 和 JSON，tests/transcript 负责证明行为可复现。

## 逐步实现

### 项目结构

```text
os-linux-process-files/
├── README.md
├── run_lab.sh
├── src/
│   └── system_observer.py
├── tests/
│   └── test_system_observer.py
├── workspace/
└── reports/
```

`run_lab.sh` 做三件事：先运行测试，再运行观察器，最后把关键命令和报告片段写进 transcript。

### 关键实现

观察器的主流程可以概括成：

```python
paths = prepare_workspace(workspace)
observations = {
    "filesystem": filesystem_observations(paths),
    "file_descriptors": descriptor_demo(paths["generated"]),
    "process": process_observation(),
    "environment_variables": environment_observation(),
    "permissions": permission_observation(paths["generated"]),
    "signals": signal_observation(),
    "text_pipeline": pipeline_observation(paths["logs"] / "events.log"),
}
write_json_and_markdown(observations)
```

这里没有复杂框架，因为教学目标是清楚地看到系统边界。路径用 `pathlib` 管理，命令用参数列表调用，输出同时写入 Markdown 和 JSON。

### 本地验证结果

本地 transcript 记录了测试结果：

```text
Ran 7 tests in 0.091s
OK
```

观察器生成了两类输出：

```text
wrote reports/system_observer_report.md
wrote reports/observations.json
```

报告里包含文件元数据、文件描述符写入结果、当前进程 `/proc` 片段、环境变量继承、`umask` 权限实验、`SIGTERM` 结束状态和日志流水线统计。权限实验额外记录了 WSL Windows 挂载目录可能显示 `777` 的现象，并用 Linux `/tmp` 中的结果作为 POSIX 权限教学证据。

### 输出怎么读

本轮实验的稳定关键结果是：

```text
fd demo: written through original fd; written through duplicated fd
environment child: visible-to-child
permission demo: requested 0o666 with umask 0o027 produced 0o640
signal wait_status=143
log levels: ERROR=1 INFO=3 WARN=2
users: alice=2 bob=3 carol=1
```

这些行分别对应五条可验证关系：复制的文件描述符共享打开文件状态；子进程收到已导出环境；`umask` 屏蔽创建请求；Bash 把 `SIGTERM` 终止表示为 143；文本流水线对固定输入生成固定聚合。PID 和 inode 数字可变，所以不在验收条件中比较具体值。

从证据链看，`observations.json` 适合自动测试与二次处理，Markdown 报告适合人工审阅，transcript 记录生成两者的实际命令。三者用途不同，合在一起才能回答“代码检查了什么”和“这次真的跑出了什么”。

## 为什么这个项目适合收尾

这个项目定位为基础教学观察器，范围控制在受控 workspace、当前进程和短生命周期子进程。它的价值在于把基础概念压到一个可复跑闭环中：每个概念都有命令或代码证据，每份证据都有保存位置，每次修改都能通过测试和 transcript 复查。后续学习 Git、构建系统、数据库或网络时，也应保持这种证据链习惯。

完成标准可以直接检查：7 个测试全部通过，两个报告文件生成，七类观察都有字段，transcript 包含实际运行记录。观察器不做持续监控、系统全量盘点或敏感目录扫描；这些需求会引入权限、性能、数据保留和隐私设计，已超出本项目的基础教学边界。

## 常见错误

1. **只写文章不保留实验。** 教学内容有命令时，应能在本地重跑。
2. **把真实系统目录当练习对象。** 初学阶段应使用受控 workspace，避免误改重要文件。
3. **只保存 Markdown，不保存结构化数据。** JSON 便于后续脚本检查和对比。
4. **忽略平台差异。** WSL、容器、macOS 和原生 Linux 的某些观察结果会不同，报告要写清边界。

## 练习或延伸

1. 给 JSON 增加 `uname -a` 和 Python 版本字段。
2. 增加一个测试，验证日志级别统计包含 `INFO`、`WARN`、`ERROR`。
3. 把报告中的表格转成 CSV，再写一个小脚本比较两次运行的差异。

## 参考资料

- Python 文档：[pathlib](https://docs.python.org/3/library/pathlib.html)
- Python 文档：[subprocess](https://docs.python.org/3/library/subprocess.html)
- Python 文档：[json](https://docs.python.org/3/library/json.html)

{% endraw %}
