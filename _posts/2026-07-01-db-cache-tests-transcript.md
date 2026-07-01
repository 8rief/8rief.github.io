---
layout: post
title: "数据库项目怎么验收：测试、transcript 和可展示输出"
date: 2026-07-01 19:26:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把数据库状态、缓存计数、查询计划和报告文件固定为可复查证据。"
tags: [database, testing, transcript, teaching]
---
{% raw %}
> 主题：数据库/缓存实践 / tests / transcript
> 本文 lab 已验证：`unittest` 通过，transcript 保存完整命令输出，报告产物存在。

数据库项目的结果藏在文件和表里，单看终端一句“OK”不够。验收应该覆盖四类证据：数据库关键状态、缓存行为、查询计划、可展示文件。这样以后改代码时，能快速发现库存、收入、索引或报告是否被破坏。

## 学习目标

1. 用 unittest 固定关键业务指标。
2. 保存 transcript 作为命令级复现证据。
3. 检查 SQLite 表行数和查询计划。
4. 区分可展示产物和可审计产物。

## 先修知识

需要知道测试断言的含义：实际结果必须等于预期结果。

## 核心模型

![数据库项目怎么验收：测试、transcript 和可展示输出](/assets/diagrams/db-cache-tests-transcript.svg)

验收链路是“运行命令 → 生成数据库和报告 → 测试读取产物 → transcript 记录过程”。测试不是替代文档，transcript 也不是替代测试；两者合在一起说明结果能复现且被断言。

## 可信资料的关键结论

- Python `unittest` 适合固定确定性输出；数据库教学 lab 应优先断言稳定业务指标。
- SQLite 的查询计划输出可以作为索引教学证据，但不能替代结果正确性测试。
- 可复现实验应保留输入、输出、运行命令和环境假设。

## 逐步实现

测试直接调用 demo，并断言关键结果：

```python
payload = app.run_demo(root)
summary = payload["summary"]
cache = payload["cache_stats"]

self.assertEqual(summary["schema_version"], 2)
self.assertEqual(summary["product_count"], 5)
self.assertEqual(summary["order_count"], 2)
self.assertEqual(summary["total_revenue_cents"], 17790)
self.assertEqual(summary["total_stock"], 158)
self.assertTrue(payload["query_plan_uses_index"])
self.assertEqual(cache["hits"], 1)
self.assertEqual(cache["invalidations"], 1)
self.assertEqual(cache["expirations"], 1)
```

运行：

```bash
bash run_lab.sh
```

关键输出：

```text
run tests
.
----------------------------------------------------------------------
Ran 1 test in 0.082s

OK

visible result markers
summary_ready=reports/summary.json
chart_ready=reports/category_revenue.svg
report_ready=reports/report.md
database_cache_status=ok
```

可展示产物：

```text
reports/report.md
reports/category_revenue.svg
reports/summary.json
```

可审计产物：

```text
data/app.sqlite3
reports/transcript.txt
```

## 常见错误

1. **只断言文件存在。** 文件存在不能说明数字正确。
2. **测试预期和业务计算不一致。** 本包把总库存推导后固定为 158。
3. **把 transcript 当作随手日志。** 它应保存足够的环境、命令和输出。
4. **忽略查询计划。** 索引相关教学需要证据证明查询使用了索引。

## 练习或延伸

1. 增加一个测试，读取 `reports/summary.json` 并断言 category_report 第一项是 bags。
2. 让测试故意期待错误库存，观察失败信息如何帮助定位。
3. 增加一个 `python -m sqlite3` 或 `sqlite3` CLI 检查步骤，输出表结构。

## 参考资料

- Python 文档：[sqlite3](https://docs.python.org/3/library/sqlite3.html)
- SQLite 文档：[PRAGMA](https://www.sqlite.org/pragma.html)
- SQLite 文档：[Foreign Key Support](https://www.sqlite.org/foreignkeys.html)
- SQLite 文档：[Transactions](https://www.sqlite.org/lang_transaction.html)
- SQLite 文档：[CREATE INDEX](https://www.sqlite.org/lang_createindex.html)
- SQLite 文档：[EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)
- SQLite 文档：[Query Planner](https://www.sqlite.org/queryplanner.html)
- Redis 文档：[EXPIRE](https://redis.io/docs/latest/commands/expire/)

{% endraw %}
