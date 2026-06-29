---
layout: post
title: "测试策略：unit、round trip 和 CLI smoke 各自验证什么"
date: 2026-06-30 03:45:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 domain validation、storage round trip、layout 创建和 CLI contract 解释小项目如何组织可复跑测试。"
tags: [software-engineering, testing, unittest, cli, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / testing strategy
> 本文 lab 已验证：`python3 -m unittest discover -s tests -v` 运行 4 个测试并全部通过。

测试策略不是把所有东西都塞进一个端到端脚本。小项目也应该分层：纯函数和领域规则用 unit test；文件读写用 round trip；目录创建用临时目录 fixture；CLI 用 smoke test 验证用户可见 contract。

## 学习目标

1. 区分 unit test、round-trip test 和 CLI smoke test。
2. 用临时目录隔离文件系统副作用。
3. 让测试断言行为，而不是断言临时实现细节。
4. 把测试输出纳入发布检查。

## 先修知识

需要会运行 `python3 -m unittest`，知道临时目录可以避免污染真实项目。

## 核心模型

![小项目测试层次](/assets/diagrams/software-testing-strategy-pyramid.svg)

底层测试纯规则，中间测试适配器，顶层测试 CLI contract。release checklist 不替代测试，它把测试结果、demo transcript 和文档状态汇总成发布判断。

## 逐步实现

lab 的测试覆盖四类行为：

```text
test_domain_validation_and_summary ... ok
test_layout_creates_expected_directories ... ok
test_storage_round_trip ... ok
test_cli_contract ... ok
Ran 4 tests
OK
```

CLI contract 测试用真实命令执行 `init`、`add`、`done`、`report` 和 `list`。这比只调用内部函数更接近用户视角。storage round trip 则确认 JSON 写出后能按 schema 读回。

## 常见错误

1. **只测最终命令。** 失败时很难定位到 domain、storage 还是 CLI。
2. **只测内部函数。** 用户入口可能坏掉却没有被覆盖。
3. **测试写入真实目录。** 临时目录能降低污染和误删风险。
4. **断言输出全文。** 对稳定字段断言即可，避免文案小改导致大量测试失败。

## 练习或延伸

1. 给 `done` 命令的 missing id 错误写一个 CLI 测试。
2. 给 storage 加一个 schema_version 错误样例，确认它会失败。
3. 把 `reports/summary.md` 的关键字段加入 smoke test。

## 参考资料

- Python 文档：[unittest](https://docs.python.org/3/library/unittest.html)
- Python 文档：[tempfile](https://docs.python.org/3/library/tempfile.html)
- Google Testing Blog：[Testing on the Toilet: Flaky Tests](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html)

{% endraw %}
