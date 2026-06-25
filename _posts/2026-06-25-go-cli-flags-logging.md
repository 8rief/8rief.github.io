---
layout: post
title: "Go CLI 和日志：让服务检查可以被脚本复用"
date: 2026-06-25 19:34:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [go, cli, flags, logging, teaching]
---

## 学习目标

这一篇把库代码包装成可复用命令。读完以后，你应该能完成：

1. 用标准库 `flag` 写出 `check`、`serve`、`demo` 三个子命令；
2. 理解 CLI 参数怎样进入配置、并发数、超时和报告路径；
3. 用结构化日志记录关键结果，而不把业务数据混进不可解析的长文本。

## 先修知识

需要知道命令行参数由字符串组成，程序需要把它们解析成路径、整数和时间长度。还需要知道标准错误流适合放日志，标准输出适合放机器可读结果或简短输出。

## 核心模型

入口层只做四件事：解析命令、调用业务包、写日志、返回退出状态。

![Go CLI flags 日志入口](/assets/diagrams/go-cli-flags-logging.svg)

业务逻辑不应该知道 `os.Args`，否则测试会被全局进程状态污染。入口层也不应该重写检查规则，否则 CLI、API 和测试会出现三套语义。

## 逐步实现

`main` 只创建 logger 并调用 `run`：

```go
func main() {
    logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
    if err := run(os.Args[1:], logger); err != nil {
        logger.Error("command failed", "error", err)
        os.Exit(1)
    }
}
```

`run` 根据第一个参数分发子命令：

```go
switch args[0] {
case "check":
    return runCheck(args[1:], logger)
case "serve":
    return runServe(args[1:], logger)
case "demo":
    return runDemo(args[1:], logger)
}
```

`check` 子命令解析这些参数：

```bash
./bin/healthmon check   -config sample_config/targets.json   -workers 3   -timeout 900ms   -json reports/results.json   -csv reports/results.csv
```

一次成功运行会输出结构化日志：

```text
level=INFO msg="checks finished" ok=2 total=3 json=reports/results.json csv=reports/results.csv
```

这条日志的价值在于字段清楚：`ok=2`、`total=3`、报告路径都能被人和脚本读懂。报告详情仍然放在 JSON/CSV 文件里，日志只承担摘要和定位作用。

## 常见错误

1. **在业务包里直接读 `os.Args`**：这样 API handler 或测试调用同一逻辑时会被 CLI 参数污染。
2. **日志只写自然语言句子**：自然语言适合解释，结构化日志更适合定位和过滤。
3. **把失败详情只写在日志里**：真正需要复查的结果应该进入 JSON/CSV 报告。

## 练习或延伸

- 给 `check` 增加 `-summary` 参数，只在终端打印健康目标数量。
- 给 `serve` 增加 `-log-level`，比较 info 和 debug 两种输出对排错的帮助。

## 参考资料

- [flag package](https://pkg.go.dev/flag)
- [log/slog package](https://pkg.go.dev/log/slog)
- [os package](https://pkg.go.dev/os)
