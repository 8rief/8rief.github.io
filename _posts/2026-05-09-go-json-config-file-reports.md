---
layout: post
title: "Go JSON 配置和文件报告：让输入输出可审计"
date: 2026-05-09 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [go, json, csv, files, teaching]
---

## 学习目标

这一篇处理项目的输入输出边界。读完以后，你应该能做到：

1. 用 `encoding/json` 读取目标配置；
2. 在读取配置时做本地实验边界校验；
3. 把检查结果写成 JSON 和 CSV 两种可审计报告。

## 先修知识

需要知道 JSON 是结构化文本，CSV 更适合表格工具查看。还需要知道文件写入可能失败，例如目录不存在、权限不足或中途写坏。

## 核心模型

文件边界有两个方向：读入配置、写出报告。

![Go JSON CSV 文件边界](/assets/diagrams/go-json-config-file-reports.svg)

读入时要把“不可信文本”转换成已验证的 `[]Target`；写出时要把内存里的 `[]Result` 转换成可以保存和复查的文件。这个过程不应隐藏错误。

## 为什么需要可审计的配置和报告

服务监控的输入如果只写在命令行里，目标多了以后很难复查；输出如果只打印日志，后续也难以被脚本、表格或 API 使用。JSON 配置和 JSON/CSV 报告解决的是可审计边界：输入可以被版本化、检查和复跑，输出可以被读取、比较和展示。

配置读取还要带本地实验边界。本 lab 明确只接受 `localhost` 和 loopback IP，避免读者复制示例后对第三方地址发起检查。这是教学项目的安全边界，也是让结果稳定的方式。

报告写入采用临时文件再 rename 的方式，解决半截文件问题。程序先把完整内容写进同目录临时文件，关闭后再替换目标路径；如果中途失败，旧报告不会被半个 JSON 覆盖。

## 逐步实现

样例配置只指向本机 loopback：

```json
[
  {"name": "demo-ok", "url": "http://127.0.0.1:18191/ok"},
  {"name": "demo-fail", "url": "http://127.0.0.1:18191/fail"},
  {"name": "demo-slow", "url": "http://127.0.0.1:18191/slow"}
]
```

读取函数做三件事：读文件、解析 JSON、验证目标。

```go
data, err := os.ReadFile(path)
if err != nil {
    return nil, fmt.Errorf("read config: %w", err)
}
var targets []Target
if err := json.Unmarshal(data, &targets); err != nil {
    return nil, fmt.Errorf("parse config json: %w", err)
}
```

教学 lab 有一个重要安全边界：配置只接受 `localhost` 或 loopback IP。这样读者复制命令时只会访问本地 demo 服务，不会意外对公网目标发起检查。

```go
if !isLoopbackHost(parsed.Hostname()) {
    return fmt.Errorf("host %q is outside the local lab boundary", parsed.Hostname())
}
```

报告输出提供 JSON 和 CSV 两种格式。JSON 保留类型结构，适合 API 和程序继续处理；CSV 适合人打开查看：

```text
name,url,ok,status_code,latency_ms,error,checked_at
demo-ok,http://127.0.0.1:18191/ok,true,200,1,,2026-07-03T14:21:00Z
demo-fail,http://127.0.0.1:18191/fail,false,500,1,,2026-07-03T14:21:00Z
demo-slow,http://127.0.0.1:18191/slow,true,200,201,,2026-07-03T14:21:00Z
```

写报告时先写临时文件，再 rename 到目标路径，可以减少半截文件被当作完整报告读取的风险：

```go
tmp, err := os.CreateTemp(filepath.Dir(path), ".tmp-*")
// write and close tmp
return os.Rename(tmpName, path)
```

## 输出怎么读

当前 CLI 检查后会先打印 JSON，再打印 CSV：

```text
-- csv --
name,url,ok,status_code,latency_ms,error,checked_at
demo-ok,http://127.0.0.1:18191/ok,true,200,1,,2026-07-03T14:21:00Z
demo-fail,http://127.0.0.1:18191/fail,false,500,0,,2026-07-03T14:21:00Z
demo-slow,http://127.0.0.1:18191/slow,true,200,201,,2026-07-03T14:21:00Z
```

三行对应配置里的三个目标。`demo-ok` 是正常接口，`demo-fail` 返回 500 所以 `ok=false`，`demo-slow` 返回 200 但延迟约 200ms。`error` 列为空，说明这些请求都成功拿到了 HTTP 响应；不健康来自状态码，而不是 Go 请求错误。

如果配置里把 URL 改成外部 host，`LoadTargets` 会在启动阶段报错，报告文件不会生成。这个失败比运行一半后才发现更容易定位。

如果报告文件生成了但内容不符合预期，先检查输入配置顺序，再检查 `Result` 字段。CSV 的行顺序应该和 JSON 数组顺序一致；这能证明报告层没有重新排序结果，也方便你把两个文件对照起来。

## 常见错误

1. **JSON 解析后不验证字段**：空名字、重复名字和外部 host 会在后续步骤产生更难定位的问题。
2. **只输出人类可读文本**：文本日志不适合作为后续程序输入，JSON/CSV 才能稳定复查。
3. **直接覆盖目标文件**：如果进程中途失败，报告可能变成半个 JSON。临时文件加 rename 的模式更稳。

## 练习或延伸

- 给配置增加 `method` 字段，并限制当前版本只接受 `GET`。
- 给 CSV 增加 `category` 列，把 HTTP 状态失败和请求失败区分开。

## 参考资料

- [encoding/json package](https://pkg.go.dev/encoding/json)
- [encoding/csv package](https://pkg.go.dev/encoding/csv)
- [os package](https://pkg.go.dev/os)
