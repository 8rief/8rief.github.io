---
layout: post
title: "C++ CLI11：用 scan 和 serve 子命令组织项目入口"
date: 2026-05-16 18:00:00 +0800
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

## 为什么需要子命令接口

同一个程序承担多个用户任务时，参数会迅速变乱。文件索引器至少有两个任务：`scan` 生成 JSON/CSV 报告，`serve` 把现有结果发布为本地 API。它们共享配置和日志路径，但输出文件参数、监听地址和运行方式不同。

把所有开关都放在顶层会让用户猜测哪些参数可以组合。子命令把任务边界写进 CLI 结构：先选择任务，再给任务传入对应参数。

CLI11 的价值在于让这个协议可声明、可打印、可失败。`--help` 是用户文档，解析错误是输入校验，子命令回调是入口层和核心库之间的转换点。核心库继续接收 `IndexerConfig` 和路径对象，不需要知道用户输入了哪些字符串。


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

## 输出怎么读

`--help` 是本篇最重要的输出之一。它应该同时展示全局选项和子命令：

```text
OPTIONS:
  --config TEXT [sample_config/indexer.json]
  --log TEXT [reports/file-indexer.log]

SUBCOMMANDS:
  scan   scan local files and write reports
  serve  serve reports through a local HTTP API
```

读这段输出时，先看默认值是否安全：配置指向样例文件，日志指向 `reports/`，服务默认绑定 loopback。再看任务边界是否清楚：生成报告走 `scan`，启动服务走 `serve`。

`scan` 命令的 transcript 出现 `files=3 bytes=304 lines=7 words=45`，说明 CLI 已经把字符串参数转换为配置并调用核心库。`serve` 命令出现 `/health 200` 和 `/api/summary 200`，说明另一个子命令复用了同一份索引结果。

如果用户说参数“不生效”，先用 `--help` 确认参数属于顶层还是子命令；再看 transcript 中的路径和日志；最后检查核心库收到的结构体。


## 子命令怎样连接核心库

入口层应该只做三件事：解析用户输入、转换成项目内部类型、调用核心函数。下面是 `scan` 的数据流。

```text
argv -> CLI11 parser -> config_path/json_path/csv_path -> IndexerConfig -> build_index -> reports
```

这个链路中，`argv` 和字符串路径属于用户接口；`IndexerConfig` 和 `IndexResult` 属于核心模型。分清这两个区域，后续才能给核心库写单元测试，也能给 CLI 写 smoke 测试。

如果把 `CLI::App` 对象传进 `build_index`，测试就必须构造命令行解析器，核心逻辑会被入口框架绑定。更稳妥的做法是让 `main` 函数在边界处完成转换。

可以把失败路径也纳入 transcript：

```bash
./build/file-indexer unknown-subcommand
```

预期 CLI11 给出非零退出码和帮助提示。这个检查能证明用户输错任务时，程序会在入口层失败，而不是进入核心库后才产生模糊错误。

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
