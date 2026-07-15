---
layout: post
title: "Go CLI 和日志：让服务检查可以被脚本复用"
date: 2026-05-10 18:00:00 +0800
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

## 为什么需要 CLI flags 和结构化日志

同一套检查逻辑需要被脚本、人工命令和 CI 复用。把配置路径、worker 数、timeout、JSON/CSV 输出路径写死在代码里，会让每次场景变化都变成改源码。CLI flags 解决的是运行参数边界：代码保持不变，运行者通过参数选择输入、输出和资源上限。

结构化日志解决的是定位问题。自然语言日志读起来顺，但脚本很难稳定提取字段；`slog` 输出 `ok=2 total=3 json=... csv=...` 这类键值对，人能读，工具也能过滤。详细业务结果进入报告文件，日志保留摘要和路径。

入口层还负责退出码。业务包返回错误，入口层决定打印日志并 `os.Exit(1)`；业务包本身不直接退出进程。这样测试和 API 都能复用业务逻辑，而不会被 CLI 行为打断。

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

## 输出怎么读

CLI 检查命令的关键参数是：

```bash
./bin/healthmon check -config sample_config/targets.json -workers 3 -timeout 900ms -json reports/results.json -csv reports/results.csv
```

`-config` 指向输入，`-workers` 控制并发上限，`-timeout` 控制请求时间边界，`-json` 和 `-csv` 指向两个报告产物。成功后日志类似：

```text
time=2026-07-03T22:21:00.246+08:00 level=INFO msg="checks finished" ok=2 total=3 json=reports/results.json csv=reports/results.csv
```

`ok=2 total=3` 表示三个目标中两个健康，一个不健康。日志里的时间是本地时区，报告里的 `checked_at` 是 UTC；两者用途不同，不要用字符串完全相等来做测试。

排查 CLI 时也按参数边界看。`-config` 报错通常是文件路径或 JSON 校验问题；`-workers` 异常会影响并发上限；`-timeout` 太短会把慢目标推入错误路径；`-json` 或 `-csv` 报错多半来自目录权限或路径不存在。把这些边界写成 flags，比在代码里改常量更容易复现实验。

结构化日志适合保留摘要，详细结果仍以文件为准。若日志显示 `ok=2 total=3`，下一步就打开 `reports/results.json` 或 `reports/results.csv` 看是哪一个目标失败，而不是继续从日志里猜。

给 CLI 增加新参数时，先回答三个问题：

```text
这个参数影响输入、输出，还是资源上限？
默认值能否在本地 lab 稳定复现？
错误值应该在入口层报错，还是交给业务包处理？
```

这三个问题能防止入口层膨胀成业务逻辑。

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
