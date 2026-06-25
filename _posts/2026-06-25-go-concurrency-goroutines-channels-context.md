---
layout: post
title: "Go 并发：goroutine、channel 和 context 如何组成 worker 池"
date: 2026-06-25 19:35:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [go, concurrency, goroutine, channel, context, teaching]
---

## 学习目标

这一篇讲 Go 项目最核心的能力之一：受控并发。读完以后，你应该能解释：

1. 为什么批量检查适合 worker 池；
2. goroutine、channel、`sync.WaitGroup` 各自负责什么；
3. context 如何把取消信号传进每个请求。

## 先修知识

并发的目标是受控提高吞吐，而非盲目增加 goroutine。本地或远端服务都有连接数、CPU、磁盘和超时限制。教学项目用 `-workers` 参数控制并发上限。

## 核心模型

worker 池可以看成一个有界流水线：主 goroutine 投递任务，多个 worker 消费任务，结果按输入下标写回切片。

![Go worker 池并发模型](/assets/diagrams/go-concurrency-goroutines-channels-context.svg)

这里选择“按下标写回”：报告顺序应该稳定，不能由完成先后决定。稳定顺序让 transcript、测试和读者观察都更可靠。

## 逐步实现

入口函数接收目标列表和 worker 数：

```go
func CheckAll(ctx context.Context, client HTTPClient, targets []config.Target, workers int) []Result
```

先修正并发上限：

```go
if workers < 1 {
    workers = 1
}
if workers > len(targets) && len(targets) > 0 {
    workers = len(targets)
}
```

任务 channel 传递下标和目标：

```go
type job struct {
    index  int
    target config.Target
}
jobs := make(chan job)
results := make([]Result, len(targets))
```

每个 worker 从 channel 读取任务，然后把结果写回自己的下标：

```go
for range workers {
    wg.Add(1)
    go func() {
        defer wg.Done()
        for item := range jobs {
            results[item.index] = Check(ctx, client, item.target)
        }
    }()
}
```

主 goroutine 投递所有任务，关闭 channel，等待 worker 退出：

```go
for i, target := range targets {
    jobs <- job{index: i, target: target}
}
close(jobs)
wg.Wait()
```

本地实验里三个目标并发检查，慢目标耗时约 200ms，整体输出仍保持配置顺序：

```text
demo-ok   true  200
demo-fail false 500
demo-slow true  200
```

## 常见错误

1. **无限制地为每个目标启动 goroutine**：目标很多时会压垮本机或被检查服务。
2. **多个 goroutine 同时 append 同一个切片**：没有同步就会出现数据竞争；按下标写入预分配切片更简单。
3. **忘记关闭 jobs channel**：worker 会一直等待新任务，`WaitGroup` 也无法结束。

## 练习或延伸

- 把 `-workers` 从 1 改成 3，比较 demo-slow 对总耗时的影响。
- 给 `CheckAll` 增加一个测试：50 个目标、5 个 worker，结果顺序必须与输入一致。

## 参考资料

- [sync package](https://pkg.go.dev/sync)
- [context package](https://pkg.go.dev/context)
- [Go blog: Pipelines and cancellation](https://go.dev/blog/pipelines)
