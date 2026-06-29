---
layout: post
title: "计时和性能观察：先记录输入规模和测量边界"
date: 2026-06-29 20:07:00 +0800
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

## 常见错误

1. **不记录输入规模。** 没有 `rounds`、数据大小或参数，耗时没有意义。
2. **只测 Debug 或 sanitizer 构建。** 这些构建适合定位问题，不代表发布性能。
3. **没有校验输出。** 编译器可能优化掉无用工作，或者程序根本没执行目标路径。
4. **一次测量就下结论。** 性能结论需要多次运行和稳定环境。

## 练习或延伸

1. 分别运行 `rounds=200000` 和 `rounds=2000000`，观察时间是否近似线性。
2. 配置 Release 构建，比较 Debug 和 Release 的耗时。
3. 把结果写成 CSV，为后续画图做准备。

## 参考资料

- GNU time 手册：[time invocation](https://www.gnu.org/software/time/)
- cppreference：[std::chrono](https://en.cppreference.com/w/cpp/chrono)
- Google Benchmark 文档：[User Guide](https://google.github.io/benchmark/user_guide.html)

{% endraw %}
