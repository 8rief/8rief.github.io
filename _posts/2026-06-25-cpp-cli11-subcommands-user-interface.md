---
layout: post
title: "C++ CLI11：用 scan 和 serve 子命令组织项目入口"
date: 2026-06-25 21:04:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, cli11, cli, teaching]
---

## 学习目标

这一篇讲用户入口。读完以后，你应该能完成：

1. 用 CLI11 定义全局选项和子命令；
2. 把 `scan` 和 `serve` 分成两个清楚的用户任务；
3. 让 CLI 参数只存在入口层，核心库继续保持可测试。

## 先修知识

需要知道命令行选项通常是字符串，程序要把它们转换成路径、端口和其他类型。一个项目达到可展示状态时，`--help` 必须有清楚输出。

## 核心模型

CLI 是用户和核心库之间的协议层。

![C++ CLI11 子命令模型](/assets/diagrams/cpp-cli11-subcommands-user-interface.svg)

`scan` 生成文件报告；`serve` 启动本地 API。两个子命令共享配置和日志选项，但输出路径和监听参数各自独立。

## 逐步实现

顶层 app：

```cpp
CLI::App app{"Local file indexer CLI and API"};
app.add_option("--config", config_path, "JSON config path")->capture_default_str();
app.add_option("--log", log_path, "log file path")->capture_default_str();
```

`scan` 子命令负责报告路径：

```cpp
auto* scan = app.add_subcommand("scan", "scan local files and write reports");
scan->add_option("--json", json_path, "JSON report path")->capture_default_str();
scan->add_option("--csv", csv_path, "CSV report path")->capture_default_str();
```

`serve` 子命令负责监听地址：

```cpp
auto* serve = app.add_subcommand("serve", "serve reports through a local HTTP API");
serve->add_option("--host", host, "listen host")->capture_default_str();
serve->add_option("--port", port, "listen port")->capture_default_str();
```

实验命令：

```bash
./build/file-indexer   --config sample_config/indexer.json   --log reports/file-indexer.log   scan   --json reports/index.json   --csv reports/index.csv
```

`--help` 输出列出全局选项和子命令：

```text
SUBCOMMANDS:
  scan   scan local files and write reports
  serve  serve reports through a local HTTP API
```

这说明 CLI 已经具备稳定接口，可以作为工具被复用。

## 常见错误

1. **把 scan 和 serve 混成大量布尔选项**：子命令更能表达互斥任务。
2. **核心库读取 CLI 参数**：核心库应该接收结构体或路径，不应知道用户怎样传参。
3. **没有 `--help` 验证**：用户入口本身也是交付物，需要进 transcript。

## 练习或延伸

- 增加 `validate` 子命令，只检查配置和根目录，不写报告。
- 给 `serve` 增加 `--once` 选项，启动后处理一次请求再退出，方便自动化测试。

## 参考资料

- [CLI11 documentation](https://cliutils.github.io/CLI11/book/)
- [CLI11 GitHub repository](https://github.com/CLIUtils/CLI11)
- [Command line interface guidelines](https://clig.dev/)
