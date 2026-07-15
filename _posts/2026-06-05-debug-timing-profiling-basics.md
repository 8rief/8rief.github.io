---
layout: post
title: "计时和性能观察：先记录输入规模和测量边界"
date: 2026-06-05 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 /usr/bin/time、std::chrono 和 checksum workload 讲清性能观察不能脱离输入规模。"
tags: [performance, profiling, chrono, cpp, teaching]
---
{% raw %}

> 主题：调试与构建工具基础 / timing / profiling basics
> 本文 lab 已验证：CLI 记录 `rounds=200000`、checksum、`measured_ms`、`time_elapsed` 和 `max_rss_kb`。

性能问题不能只说“感觉慢”。最小可用证据至少包含输入规模、命令、环境、耗时边界和输出校验。本文不做复杂 profiler 教程，先建立最基础的测量纪律：同一输入、同一命令、可复跑输出。

## 为什么需要先记录测量边界

同一段代码在 Debug、Release、sanitizer、不同输入规模下的耗时可能差很多。只说“这次 0.2 秒”没有意义，因为不知道输入多大、命令是什么、是否真的执行了目标逻辑。

基础性能观察要先回答：测了哪段代码；输入规模是多少；输出如何证明工作没有被优化掉；外部进程耗时和内部片段耗时分别是多少。

## 学习目标

1. 区分 wall time、CPU 时间和程序内部计时。
2. 用 `/usr/bin/time` 记录进程级耗时和内存。
3. 用 `std::chrono` 记录代码片段耗时。
4. 避免从一次小输入测量得出过大的性能结论。

## 先修知识

需要会运行 CLI，并理解 Release/Debug、优化和 sanitizer 都会影响性能。

## 核心模型

![计时和性能观察模型](/assets/diagrams/debug-timing-profiling-basics.svg)

性能观察从固定输入开始。程序内部用 `std::chrono` 测量某段代码；外部用 `/usr/bin/time` 测量整个进程。输出 checksum 用来确认工作没有被优化掉或替换成空跑。

本 lab 的输入规模写成命令参数：

```text
rounds=200000
```

后续比较时，先改变 rounds，再观察耗时是否随规模变化，而不是从单点数字得出结论。

## 逐步实现

lab 中的工作负载：

```cpp
uint64_t checksum_workload(int rounds) {
    uint64_t state = 1469598103934665603ULL;
    for (int i = 0; i < rounds; ++i) {
        state ^= static_cast<uint64_t>(i * 2654435761U);
        state *= 1099511628211ULL;
        state ^= state >> 32;
    }
    return state;
}
```

内部计时：

```cpp
const auto start = chrono::steady_clock::now();
volatile uint64_t sink = checksum_workload(rounds);
const auto stop = chrono::steady_clock::now();
```

外部命令：

```bash
/usr/bin/time -f 'time_elapsed=%e max_rss_kb=%M' ./.lab_tmp/build-debug/debug_lab_cli timing 200000
```

输出示例：

```text
rounds=200000 checksum=7033538281016921374 measured_ms=0
time_elapsed=0.00 max_rss_kb=3680
```

## 如何解释输出

- `rounds=200000`：工作负载规模。
- `checksum=7033538281016921374`：输出校验，证明循环结果被使用。
- `measured_ms=0`：程序内部毫秒计时，在小输入下分辨率不足。
- `time_elapsed=0.00`：整个进程 wall time，同样过小，不能做性能结论。
- `max_rss_kb=3680`：进程峰值常驻内存约 3.6 MB。

这个样例的价值在于记录格式，不在于证明程序很快。要比较性能，应提高 rounds、重复运行，并用 Release 构建。

## 下一步如何加严谨度

入门阶段先保存一次可复跑输出。要形成性能结论，应至少增加三件事：固定机器和构建类型；每个输入规模运行多次取中位数；把结果写入 CSV 或 JSON，避免手工抄数字。需要定位热点时，再引入 profiler 或 benchmark 框架。

## 常见错误

1. **不记录输入规模。** 没有 `rounds`、数据大小或参数，耗时没有意义。
2. **只测 Debug 或 sanitizer 构建。** 这些构建适合定位问题，不代表发布性能。
3. **没有校验输出。** 编译器可能优化掉无用工作，或者程序根本没执行目标路径。
4. **一次测量就下结论。** 性能结论需要多次运行和稳定环境。
5. **只看内部计时。** 进程启动、IO 和初始化可能在外部时间里占比很高。

## 练习或延伸

1. 分别运行 `rounds=200000` 和 `rounds=2000000`，观察时间是否近似线性。
2. 配置 Release 构建，比较 Debug 和 Release 的耗时。
3. 把结果写成 CSV，为后续画图做准备。

## 参考资料

- GNU time 手册：[time invocation](https://www.gnu.org/software/time/)
- cppreference：[std::chrono](https://en.cppreference.com/w/cpp/chrono)
- Google Benchmark 文档：[User Guide](https://google.github.io/benchmark/user_guide.html)

{% endraw %}
