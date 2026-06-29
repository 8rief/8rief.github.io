---
layout: post
title: "最小复现：把失败输入缩到能解释的一行"
date: 2026-06-29 20:03:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 shrink_to_failing_case 演示如何从复杂输入缩小到最小触发样例并保留复跑命令。"
tags: [debugging, minimal-reproduction, testing, cpp, teaching]
---
{% raw %}

> 主题：调试与构建工具基础 / minimal reproduction
> 本文 lab 已验证：样例输入从 7 个值缩到 1 个仍能触发阈值问题。

遇到 bug 时，直接盯着完整项目状态很低效。更好的第一步是构造最小复现：保留能触发问题的最小输入、最短命令和最少环境假设。复现越小，调试时需要同时考虑的变量越少。

## 学习目标

1. 理解最小复现为什么能降低调试复杂度。
2. 用一个 shrinker 思路逐步删除无关输入。
3. 保存可以复跑的命令和预期输出。
4. 区分“复现 bug”和“修复 bug”两个阶段。

## 先修知识

需要会运行 CLI 命令和读测试输出。本文使用一个简单阈值触发条件作为例子。

## 核心模型

![最小复现缩减模型](/assets/diagrams/debug-minimal-reproduction-shrinking.svg)

完整失败输入先进入复现命令。shrinker 每次尝试删除一部分输入；如果删除后仍然失败，就保留更小输入。循环结束后，剩下的输入就是更容易解释的触发样例。

## 逐步实现

lab 中的失败条件是“存在一个值大于阈值”：

```cpp
optional<int> first_value_above(const vector<int>& values, int threshold);
```

缩减函数不断尝试删除元素：

```cpp
vector<int> shrink_to_failing_case(const vector<int>& values, int threshold) {
    vector<int> candidate = values;
    bool changed = true;
    while (changed && candidate.size() > 1) {
        changed = false;
        for (size_t i = 0; i < candidate.size(); ++i) {
            vector<int> trial = candidate;
            trial.erase(trial.begin() + static_cast<ptrdiff_t>(i));
            if (first_value_above(trial, threshold).has_value()) {
                candidate = move(trial);
                changed = true;
                break;
            }
        }
    }
    return candidate;
}
```

执行命令：

```bash
./.lab_tmp/build-debug/debug_lab_cli shrink
```

输出：

```text
original_size=7 shrunk_size=1 trigger=80
```

## 常见错误

1. **先改代码再固定复现。** 没有复现就不知道修复是否真的覆盖问题。
2. **复现步骤依赖本机隐含状态。** 命令、输入和环境应写进 transcript。
3. **复现太大。** 大输入中通常有大量无关噪音。
4. **只保存截图。** 文本命令和输出更容易被自动复跑和审查。

## 练习或延伸

1. 把触发条件改成“连续两个值之和超过阈值”，观察 shrinker 是否还正确。
2. 保存缩减后的输入到文件，并让 CLI 从文件读取。
3. 为一个真实失败测试写最小复现命令。

## 参考资料

- GCC 文档：[Bug Reporting](https://gcc.gnu.org/bugs/)
- LLVM 文档：[How to submit an LLVM bug report](https://llvm.org/docs/HowToSubmitABug.html)
- C-Reduce 项目：[C/C++ test case reduction](https://github.com/csmith-project/creduce)

{% endraw %}
