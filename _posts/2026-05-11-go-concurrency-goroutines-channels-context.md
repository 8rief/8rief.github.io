---
layout: post
title: "Go 并发：goroutine、channel 和 context 如何组成 worker 池"
date: 2026-05-11 09:00:00 +0800
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

## 为什么需要受控并发

批量健康检查天然适合并发：多个目标之间没有依赖，等待一个慢目标时可以检查其他目标。但并发不是越多越好。无限制 goroutine 会增加内存、连接数和被检查服务压力；结果按完成顺序输出还会让报告每次顺序不同。

worker 池解决的是吞吐和可控性的平衡。`-workers` 给出上限，channel 分发任务，`WaitGroup` 等待 worker 结束，预分配结果切片按输入下标写回。这样既能并发，又能保持报告顺序稳定。

context 解决取消传播。上层设置一轮检查的超时，`Check` 用 `NewRequestWithContext` 把取消信号绑定到 HTTP 请求。超时发生时，请求能尽快结束，worker 也能回到队列或退出。

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

## 输出怎么读

当前配置只有三个目标，使用 `-workers 3` 后三个检查可以同时进行。报告顺序仍是配置顺序：

```text
demo-ok   true  200
demo-fail false 500
demo-slow true  200
```

这个顺序由 `results[item.index] = ...` 保证，和完成先后无关。慢目标可能最后完成，但仍出现在第三行，因为它在配置中第三个。

如果把 `-workers` 改成 1，整体耗时更容易被 `/slow` 的 200ms 延迟拖住；如果把目标增加到很多个，worker 上限可以防止一次性打开过多连接。测试应同时检查“并发后结果完整”和“顺序保持输入顺序”。

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
