---
layout: post
title: "结课项目：调试和构建发布检查表"
date: 2026-04-01 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 warnings、CMake/Ninja、CTest、sanitizer、日志、计时和符号证据整理成一个可复跑检查包。"
tags: [debugging, build-system, release-checklist, cpp, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/debug-build-tooling-foundations/README.md`](/assets/labs/debug-build-tooling-foundations/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：调试与构建工具基础 / capstone / release checklist
> 本文 lab 已验证：Debug 构建、CTest、sanitizer、Ninja targets、symbol evidence、timing 和报告文件全部生成。

学完单个工具后，需要把它们组合成发布前检查。一个小型 C++ 项目至少应该能回答：用什么编译器和构建类型？哪些测试通过？sanitizer 有没有发现隐藏错误？构建目标是否清楚？性能观察记录了输入规模吗？诊断信息是否可读？

## 为什么需要检查表

单个工具通过并不等于项目可发布。编译通过不能证明行为正确，测试通过不能证明没有内存越界，sanitizer 失败也可能是教学用故意触发。检查表把每类证据放到固定位置，避免凭印象判断“应该没问题”。

检查表还要求写出未覆盖项。本次环境没有安装 gdb，所以报告只保留符号证据，不把单步调试纳入验收结论。

## 学习目标

1. 把调试和构建工具组织成固定验收流程。
2. 保存 transcript 和报告，避免只凭记忆判断。
3. 用符号工具把二进制地址关联回源码位置。
4. 知道当前包未覆盖 gdb 的原因和后续补充边界。

## 先修知识

建议读完本包前七篇，理解告警、CMake/Ninja、最小复现、sanitizer、CTest、日志和计时。

## 核心模型

![调试和构建发布检查表](/assets/diagrams/debug-build-capstone-release-checklist.svg)

发布检查由多个证据组成：构建 transcript 说明环境，CTest 说明回归行为，sanitizer 说明隐藏 bug 检测，Ninja target 说明构建图，日志和计时说明运行时观察，symbol evidence 说明调试符号能映射到源码。

本次报告摘要：

```text
compiler: g++ 13.3.0
cmake: 3.28.3
ninja: 1.11.1
gdb: not-installed
sanitizer statuses: ASan=1 UBSan=1
```

`ASan=1 UBSan=1` 是教学触发样例的预期失败状态；真实发布前应修复这类问题，让 sanitizer job 通过。

## 逐步实现

完整命令：

```bash
bash run_lab.sh
```

核心输出包括：

```text
100% tests passed, 0 tests failed out of 1
asan_status=1 ubsan_status=1
ERROR: AddressSanitizer: heap-buffer-overflow
runtime error: signed integer overflow
```

符号证据来自 `nm -C` 和 `addr2line`：

```text
buglab::running_mean(std::vector<int, std::allocator<int> > const&)
src/debug_lab.cpp:33
```

这说明 Debug 构建里的符号可以回到源码位置。本文 lab 环境未验证 gdb 单步调试，所以本包不把 gdb 作为已验收内容；后续如果安装 gdb，可以基于同一个 lab 继续扩展。

## 发布前可复跑顺序

1. 配置 Debug 构建并打开 warnings。
2. 构建库、CLI 和测试 target。
3. 运行 CTest，保存 `100% tests passed` 或失败输出。
4. 运行 sanitizer 构建，确认没有非预期报错。
5. 运行 CLI smoke、日志和 timing 命令。
6. 保存 transcript、报告和关键环境版本。

这个顺序先保证能构建，再看行为，再看隐藏运行时问题，最后整理证据。

## 本包生成了哪些证据

报告目录包含 transcript、CTest 输出、sanitizer 输出、timing 输出、Ninja targets、symbol evidence 和 Markdown 总结。交付时不需要把每个文件都贴进文章，但要能说明每个文件证明什么：测试证明行为，sanitizer 证明失败样例可定位，timing 证明测量边界，symbol evidence 证明调试符号可读。

## 如何判定可以交付

教学 lab 和真实发布的判定不同。本包为了讲解 sanitizer，会故意触发 ASan 和 UBSan，所以报告里的非零状态属于预期教学证据。真实项目发布前应把故障样例改成测试用例或独立 demo，并要求主构建、测试、sanitizer 和 smoke 命令全部通过。

可以把最终判定写成：

```text
build: pass
tests: pass
sanitizer: expected teaching failures captured
timing: measured with rounds=200000 and checksum
symbols: running_mean symbol visible
gdb: not covered in this environment
```

这样读者能区分已验证、故意失败和未覆盖三类状态。

## 常见错误

1. **只保留最终二进制，不保留 transcript。** 以后无法证明构建环境和命令。
2. **把 sanitizer 失败当发布失败。** 这里故意触发 sanitizer 来保留教学证据；真实项目中应修复后再发布。
3. **不区分工具用途。** CTest 验证行为，sanitizer 捕捉内存/UB，time 观察耗时，nm/addr2line 查符号。
4. **没有明确未覆盖项。** gdb 单步调试未在本文 lab 中验证，应明确边界，避免把未验证步骤写成结论。
5. **把教学故障样例当发布结果。** 教学中可故意触发 ASan/UBSan；真实发布清单中这些 job 应该是绿色。

## 练习或延伸

1. 安装 gdb 后，为 `running_mean` 设置断点并记录命令 transcript。
2. 增加一个 Release 构建和一个 sanitizer 构建的 CI matrix。
3. 把 `debug_build_report.md` 改成自动包含关键输出摘要。

## 参考资料

- GNU Binutils 文档：[addr2line](https://sourceware.org/binutils/docs/binutils/addr2line.html)
- GNU Binutils 文档：[nm](https://sourceware.org/binutils/docs/binutils/nm.html)
- CMake 文档：[CTest](https://cmake.org/cmake/help/latest/manual/ctest.1.html)

{% endraw %}
