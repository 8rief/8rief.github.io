---
layout: post
title: "SELECT、WHERE 和 ORDER BY：先把问题读成行集合"
date: 2026-06-28 17:42:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从“我要看哪些行和哪些列”出发，学习 SELECT、WHERE、ORDER BY 和 LIMIT 的开发用法。"
tags: [sql, select, where, order-by, teaching]
---
{% raw %}

> 主题：SQL 实用开发 / SELECT / WHERE / ORDER BY  
> 本文 lab 已验证：样例库按优先级读出 7 条未完成工单。

项目里最常见的数据库动作是读数据。读数据的关键问题是先把需求翻译成行集合：我要哪些列、从哪张表读、保留哪些行、按什么顺序看、最多看多少条。`SELECT`、`WHERE`、`ORDER BY` 和 `LIMIT` 正好对应这条思路。

## 学习目标

1. 用 `SELECT` 指定结果列。
2. 用 `WHERE` 把行集合缩小到当前问题需要的范围。
3. 用 `ORDER BY` 让结果顺序稳定、可解释。
4. 理解 `LIMIT` 在调试和分页中的实际价值。

## 先修知识

需要知道表由行和列组成，工单表中有 `status`、`priority`、`title` 等字段。

## 核心模型

![SELECT、WHERE、ORDER BY、LIMIT 查询管线](/assets/diagrams/sql-select-where-order-limit.svg)

可以把一次查询看成管线：从表中取候选行，按 `WHERE` 过滤，再按 `ORDER BY` 排列，最后投影成结果列。实际数据库优化器可能调整执行顺序，但开发者写查询时先按这个逻辑理解，最容易检查需求是否表达完整。

## 逐步实现

先读出未完成工单：

```sql
SELECT id, title, status, priority
FROM tickets
WHERE status <> 'done'
ORDER BY priority DESC, id ASC;
```

这里的开发需求是：看还需要处理的工单，优先级高的在前，同优先级按创建顺序稳定显示。`id ASC` 不是装饰，它让相同优先级的输出顺序可复现。

lab 的完整报表会联表显示项目和负责人，本文先看核心结果：

```text
project        | id | title                    | status      | priority | assignee
---------------+----+--------------------------+-------------+----------+-----------
research-notes | 6  | Summarize baseline gap   | open        | 5        | unassigned
lab-runner     | 4  | Add transaction demo     | open        | 4        | Bo
research-notes | 9  | Check query plan note    | open        | 4        | unassigned
```

如果只想调试前三条，可以加 `LIMIT`：

```sql
SELECT id, title, priority
FROM tickets
WHERE status = 'open'
ORDER BY priority DESC, id ASC
LIMIT 3;
```

`LIMIT` 适合开发调试、后台列表预览和分页查询。它不应该替代业务过滤条件；如果忘记 `WHERE`，`LIMIT 10` 只是让错误结果变短。

## 如何解释输出

看到一条读查询时，按这个顺序检查：

1. `FROM` 是否选对事实来源。
2. `WHERE` 是否表达了业务边界。
3. `SELECT` 是否只取后续需要的列。
4. `ORDER BY` 是否让结果稳定。
5. `LIMIT` 是否用于调试或分页，而不是掩盖查询过宽。

这个检查顺序能减少“页面上怎么多了旧数据”“为什么排序每次不一样”“为什么导出字段过多”的问题。

## 常见错误

1. **默认顺序稳定。** 没有 `ORDER BY` 时，结果顺序不应被当作业务契约。
2. **用 `SELECT *` 写接口。** 开发调试可以临时使用，接口和导出应明确列名。
3. **把过滤写在应用代码里。** 能在 SQL 中表达的筛选应尽量靠近数据源。
4. **忘记 NULL。** `assignee_id` 这类可空字段参与条件时，要明确是否需要包含未分配记录。

## 练习或延伸

1. 写一个查询，只显示 `priority >= 4` 的未完成工单。
2. 把排序改成 `created_at ASC`，观察结果如何变化。
3. 给查询增加 `LIMIT 2`，解释它适合调试还是适合最终报表。

## 参考资料

- SQLite 文档：[SELECT](https://www.sqlite.org/lang_select.html)
- SQLite 文档：[ORDER BY](https://www.sqlite.org/syntax/ordering-term.html)
- SQLite 文档：[LIMIT clause](https://www.sqlite.org/lang_select.html#limitoffset)

{% endraw %}
