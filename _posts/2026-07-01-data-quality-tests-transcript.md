---
layout: post
title: "数据项目怎么验收：测试、行数、关键指标和 transcript"
date: 2026-07-01 11:42:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把数据清洗和图表生成变成可复查流程，而不只是一张看起来正确的图。"
tags: [data-quality, testing, transcript, teaching]
---
{% raw %}
> 主题：数据处理与可视化 / tests / transcript / acceptance
> 本文 lab 已验证：`unittest` 通过，summary、SQLite、SVG 和 Markdown 报告都存在。

数据项目的验收不能只看图表。图表很容易“看起来对”，但真正需要检查的是：原始行数、清洗行数、拒收原因、关键指标、数据库行数、图表文件和报告文件是否都能从同一条命令链路生成。

## 学习目标

1. 为数据流水线写最小测试。
2. 用 transcript 保存命令、环境和关键输出。
3. 区分“文件存在”和“内容正确”。

## 先修知识

已经知道流水线会生成 clean CSV、reject CSV、SQLite、JSON、SVG 和 Markdown。

## 核心模型

![数据项目验收证据链](/assets/diagrams/data-quality-tests-transcript.svg)

验收从原始输入开始，一直检查到最终图表和报告。测试断言关键数字，transcript 记录完整执行过程。

## 可信资料的关键结论

- Python `unittest` 是标准库测试框架，适合写轻量回归测试。
- `py_compile` 可以检查 Python 文件语法，不能替代行为测试。
- 对数据处理任务，测试应覆盖行数、拒收原因、关键汇总和产物存在性。

## 逐步实现

运行语法检查：

```bash
python3 -m py_compile scripts/pipeline.py scripts/test_pipeline.py
```

运行测试：

```bash
PYTHONPATH=scripts python3 -m unittest scripts/test_pipeline.py
```

测试断言：

```python
self.assertEqual(summary["raw_rows"], 20)
self.assertEqual(summary["clean_rows"], 16)
self.assertEqual(summary["rejected_rows"], 4)
self.assertAlmostEqual(summary["total_revenue"], 736.30, places=2)
self.assertEqual(summary["by_region"][0], {"region": "East", "revenue": 202.25})
```

完整 transcript 保存在：

```text
reports/transcript.txt
```

关键输出：

```text
Ran 1 test in ...
OK
chart_ready=reports/region_revenue.svg
report_ready=reports/report.md
pipeline_status=ok
```

## 常见错误

1. **只检查文件存在。** 空文件也会存在，必须检查关键内容。
2. **只测总收入。** 拒收原因和分组指标也需要固定。
3. **不记录 Python 版本。** 标准库行为通常稳定，但环境仍应记录。
4. **手工跑多个命令不保存。** 后续无法判断报告是否由当前脚本生成。

## 练习或延伸

1. 给 `by_channel` 增加测试断言。
2. 故意修改一行金额，观察测试失败。
3. 把测试结果写入单独的 `reports/test-output.txt`。

## 参考资料

- Python 文档：[unittest](https://docs.python.org/3/library/unittest.html)
- Python 文档：[py_compile](https://docs.python.org/3/library/py_compile.html)

{% endraw %}
