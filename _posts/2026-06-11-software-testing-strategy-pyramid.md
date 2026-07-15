---
layout: post
title: "测试策略：unit、round trip 和 CLI smoke 各自验证什么"
date: 2026-06-11 09:00:00 +0800
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

## 失败样例如何帮助定位

可以刻意制造一个错误来理解测试层次。假设 `summary_by_status()` 忘记统计 `doing`，底层 domain 测试会先失败：

```text
FAIL: test_domain_validation_and_summary
AssertionError: {'done': 1, 'todo': 1} != {'doing': 1, 'done': 1, 'todo': 1}
```

这类失败说明错误在规则层，不需要先查 CLI 参数或文件路径。如果只有端到端测试，输出可能只是“report 不符合预期”，定位成本会高很多。

## 为什么测试要断言稳定行为

测试断言应该贴近用户和模块 contract。下面是稳定断言：

```python
self.assertIn("done", output)
self.assertIn("write problem statement", output)
self.assertEqual(summary["done"], 1)
```

容易脆弱的断言是检查临时实现细节，例如内部变量名、完整 help 文案、JSON 字段顺序。那些细节改动频繁，常常让测试在行为没坏时失败。

## 临时目录的状态变化

CLI smoke test 的关键步骤可以写成：

```text
TemporaryDirectory 创建空工作区
init 创建 config/data/docs/reports
add 写入 data/tasks.json
done 修改 task_id=1 的 status
report 写出 reports/summary.md
TemporaryDirectory 自动清理
```

临时目录让测试可以重复运行。每次测试从空目录开始，避免被上一次运行留下的数据污染。

## 测试层次和发布证据的关系

测试输出进入 release checklist 时，可以这样标注：

```text
unit/domain: PASS, 验证状态枚举和摘要计数
adapter/storage: PASS, 验证 JSON round trip
adapter/layout: PASS, 验证目录创建
contract/cli: PASS, 验证用户入口和输出字段
```

这比一句“测试通过”更有信息量。读者能看出哪些层被覆盖，哪些层还没有证据。

## 排查顺序

当测试失败时，不要立刻重写代码。先看失败层级：

```text
单元测试失败 -> 查纯规则和输入边界
round-trip 失败 -> 查序列化、schema、编码和原子写
layout 失败 -> 查路径、权限和目录命名
CLI smoke 失败 -> 查参数解析、退出码、stdout/stderr 和调用链
```

按层级排查能避免在无关模块里来回修改。

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


## 为什么要引入测试分层

测试分层解决的是定位问题：同样是失败，领域规则错、文件读写错、目录布局错、CLI 参数错，修复路径完全不同。把所有检查都塞进一个端到端脚本，失败时只能看到“整个系统坏了”，很难知道从哪里下手。

## 可复现实验

最小命令仍然是：

```bash
python3 -m unittest discover -s tests -v
```

一组健康输出应该类似：

```text
test_domain_validation_and_summary ... ok
test_layout_creates_expected_directories ... ok
test_storage_round_trip ... ok
test_cli_contract ... ok
Ran 4 tests
OK
```

## 输出怎么读

`domain_validation` 失败通常说明纯业务规则错；`storage_round_trip` 失败说明序列化或 schema 有问题；`cli_contract` 失败说明用户入口坏了。四类测试一起存在，才能把失败定位到具体层。

## 状态变化

一次 CLI smoke test 会经历：创建临时目录、初始化项目、写入任务、修改任务状态、生成报告、删除临时目录。临时目录是关键边界，它保证测试不污染真实工作区。

{% endraw %}
