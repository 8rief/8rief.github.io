---
layout: post
title: "结课项目：SQLite 报表 CLI、索引证据和发布检查"
date: 2026-06-28 17:48:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 schema、CRUD、JOIN、GROUP BY、事务、参数化查询和导出整理成一个可测试的 SQLite 报表 CLI。"
tags: [sql, sqlite, cli, explain-query-plan, capstone, teaching]
---
{% raw %}

> 主题：SQL 实用开发 / capstone / EXPLAIN QUERY PLAN  
> 本文 lab 已验证：7 个单元测试通过，查询计划使用 `idx_tickets_status_priority`。

学完 SQL 语法后，需要把它收束成一个能运行、能测试、能导出证据的小项目。本包的结课项目是一个 SQLite 报表 CLI：初始化数据库、迁移 schema、导入 CSV、运行报表、导出 JSON/CSV、检查事务回滚、用查询计划确认索引是否服务实际查询。

## 学习目标

1. 把前面几篇的 SQL 操作组合成一个 CLI 项目。
2. 用测试验证 schema、CRUD、事务、导入导出和查询计划。
3. 用 `EXPLAIN QUERY PLAN` 解释索引是否被使用。
4. 建立发布前检查清单，避免只凭代码阅读判断正确性。

## 先修知识

建议已经读过本包前七篇，知道表结构、查询、写入、连接、聚合、事务和参数化查询。

## 核心模型

![SQLite 报表 CLI 结课项目模型](/assets/diagrams/sql-report-cli-index-explain-capstone.svg)

CLI 是用户入口，SQLite 数据库是状态边界，SQL 查询生成报表，测试和 transcript 提供可复查证据。`EXPLAIN QUERY PLAN` 不替代性能测试，但可以说明某个查询是否走到了预期索引。

## 项目结构

lab 的核心文件如下：

```text
src/sql_practical_lab.py
sample_import/new_tickets.csv
tests/test_sql_practical_lab.py
run_lab.sh
reports/transcript.txt
reports/report.json
reports/open_tickets.csv
reports/sql_lab_report.md
```

脚本只依赖 Python 标准库。这样可以降低复现门槛，先把 SQL 工作流讲清楚。

## 本地执行结果

完整执行会先跑测试，再运行 capstone：

```text
Ran 7 tests in 0.497s
OK
```

capstone 输出关键行：

```text
sqlite_version=3.45.1
imported_tickets=3
open_tickets=7
project_summary_rows=3
workload_rows=4
rollback_before=9 rollback_after=9 rolled_back=True
query_plan=SEARCH tickets USING INDEX idx_tickets_status_priority (status=? AND priority>?)
```

这些行分别证明：

1. 实验环境记录了 SQLite 版本。
2. CSV 导入确实写入 3 条工单。
3. 未完成工单报表有 7 行。
4. 项目汇总和工作量报表都有结果。
5. 事务失败后行数保持不变。
6. 优先级查询使用了为 `status, priority` 建立的索引。

## 索引如何从需求出发

本项目只建少量索引：

```sql
CREATE INDEX IF NOT EXISTS idx_tickets_status_priority
    ON tickets(status, priority DESC, id);
```

它服务的查询是：找出 `status = 'open'` 且 `priority >= 3` 的工单，并按优先级排序。查询计划显示：

```text
SEARCH tickets USING INDEX idx_tickets_status_priority (status=? AND priority>?)
```

这说明索引和查询需求对齐。文章不展开 B-tree 内部细节，因为当前目标是开发者能判断“这个索引是否服务我的查询”。当数据规模和延迟目标明确后，再进入更深入的索引和查询优化。

## 发布检查清单

这个 SQL 小项目的发布检查包括：

1. `python3 -m unittest discover -s tests -v` 通过。
2. transcript 记录 Python 和 SQLite 版本。
3. JSON/CSV 导出来自同一组查询函数。
4. 事务失败路径有测试和输出证据。
5. 参数化查询测试覆盖带单引号的标题。
6. 查询计划说明索引服务哪条需求。
7. README 说明如何复跑。

## 常见错误

1. **只写 SQL 片段，没有可运行项目。** 语法理解需要落到脚本、输入、输出和测试。
2. **索引没有对应查询。** 没有需求的索引会增加写入成本和维护成本。
3. **只看成功输出。** 失败路径、回滚和约束错误同样需要验证。
4. **导出结果没有来源说明。** 报表应能追溯到具体查询和数据库快照。

## 练习或延伸

1. 增加一个 `--min-priority` 参数，导出高优先级未完成工单。
2. 新增一个 `idx_tickets_assignee_status` 索引，再写查询计划说明它服务的需求。
3. 把 `run_lab.sh` 放到新的临时目录复跑，确认不依赖旧输出。

## 参考资料

- SQLite 文档：[EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)
- SQLite 文档：[Query Planning](https://www.sqlite.org/queryplanner.html)
- SQLite 文档：[CREATE INDEX](https://www.sqlite.org/lang_createindex.html)
- Python 文档：[unittest — Unit testing framework](https://docs.python.org/3/library/unittest.html)

{% endraw %}
