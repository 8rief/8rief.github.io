---
layout: post
title: "GROUP BY 和聚合：从明细行生成开发报表"
date: 2026-06-28 17:45:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 COUNT、SUM、CASE 和 GROUP BY 把工单明细转成项目汇总和成员工作量。"
tags: [sql, group-by, aggregate, reporting, teaching]
---
{% raw %}

> 主题：SQL 实用开发 / GROUP BY / aggregate report  
> 本文 lab 已验证：项目汇总、成员工作量和未完成工单报表来自同一个数据库快照。

项目里经常需要回答汇总问题：每个项目还有多少未完成工单？每个人手上有多少小时？这类问题不应该把所有明细读到应用里再手工循环。SQL 的聚合函数和 `GROUP BY` 可以直接把行集合折叠成报表。

## 学习目标

1. 用 `COUNT`、`SUM`、`ROUND` 生成汇总字段。
2. 用 `GROUP BY` 定义“按什么分组”。
3. 用 `CASE WHEN` 计算带条件的数量。
4. 理解报表查询为什么要从同一份明细数据生成。

## 先修知识

需要会写基本 `SELECT` 和 `JOIN`。本文沿用项目、成员、工单三张表。

## 核心模型

![GROUP BY 和聚合报表模型](/assets/diagrams/sql-group-by-aggregate-report.svg)

明细表是一行一条事实。`GROUP BY` 先把行按项目或负责人分组，聚合函数再对每组行计算数量、总和或平均值。结果行不再是一条工单，而是一组工单的摘要。

## 逐步实现

按项目统计总工单数、未完成数量和估算工时：

```sql
SELECT p.name AS project,
       COUNT(t.id) AS total_tickets,
       SUM(CASE WHEN t.status <> 'done' THEN 1 ELSE 0 END) AS open_tickets,
       ROUND(SUM(t.estimate_hours), 1) AS estimated_hours
FROM projects AS p
LEFT JOIN tickets AS t ON t.project_id = p.id
GROUP BY p.id, p.name
ORDER BY open_tickets DESC, p.name ASC;
```

`COUNT(t.id)` 统计每个项目下的工单行。`CASE WHEN` 把未完成工单变成 1，已完成变成 0，再用 `SUM` 得到未完成数量。这里使用 `LEFT JOIN`，是为了让没有工单的项目也能出现在报表里。

成员工作量报表：

```sql
SELECT COALESCE(m.name, 'unassigned') AS assignee,
       COUNT(t.id) AS active_tickets,
       ROUND(SUM(t.estimate_hours), 1) AS active_hours
FROM tickets AS t
LEFT JOIN members AS m ON m.id = t.assignee_id
WHERE t.status <> 'done'
GROUP BY m.id, m.name
ORDER BY active_hours DESC, assignee ASC;
```

这个查询只统计未完成工单，所以 `WHERE` 在分组前缩小行集合。

## 如何解释输出

lab 的 capstone 输出记录：

```text
project_summary_rows=3
workload_rows=4
```

项目汇总有 3 行，对应 3 个项目。工作量有 4 行，因为除 3 个成员外，还有 `unassigned` 这一组。这个结果说明分组键决定了报表粒度。

## 什么时候需要索引

聚合报表会扫描相关行。小表上先写对查询更重要；当报表变慢或数据量变大，再用 `EXPLAIN QUERY PLAN` 看是否需要索引。索引的解释应来自具体查询，例如“按 `status` 和 `priority` 找未完成高优先级工单”，而不是给每一列都建索引。

## 常见错误

1. **分组粒度不清楚。** `GROUP BY project` 和 `GROUP BY assignee` 回答的是不同问题。
2. **把明细列混进聚合结果。** 没有分组或聚合的列会让报表语义不稳定。
3. **忘记未分配分组。** 可空负责人应明确显示为 `unassigned`。
4. **过早优化索引。** 先用正确查询和测试数据验证结果，再根据计划和规模优化。

## 练习或延伸

1. 统计每个状态的工单数量。
2. 统计每个项目的平均估算工时。
3. 增加一个只看 `priority >= 4` 的项目风险报表。

## 参考资料

- SQLite 文档：[Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html)
- SQLite 文档：[SELECT — GROUP BY, HAVING and result-column processing](https://www.sqlite.org/lang_select.html#resultset)
- SQLite 文档：[EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)

{% endraw %}
