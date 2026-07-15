---
layout: post
title: "SELECT、WHERE 和 ORDER BY：先把问题读成行集合"
date: 2026-05-31 09:00:00 +0800
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

## 为什么需要先想行集合

页面上说“显示待处理工单”，数据库并不知道什么叫待处理。开发者要把它翻译成行条件：`status <> 'done'`。页面上说“优先处理重要的”，也要翻译成排序：`priority DESC, id ASC`。

这一步如果不清楚，后面很容易用 `SELECT *` 加一点应用层过滤凑结果。短期能显示，长期会让接口字段过宽、排序不稳定、分页结果重复或遗漏。

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

这里的开发需求是：看还需要处理的工单，优先级高的在前，同优先级按创建顺序稳定显示。`id ASC` 的作用是让相同优先级的输出顺序可复现。

lab 的完整报表会联表显示项目和负责人，本文先看核心结果：

```text
project        | id | title                    | status      | priority | assignee
---------------+----+--------------------------+-------------+----------+-----------
research-notes | 6  | Summarize baseline gap   | open        | 5        | unassigned
lab-runner     | 4  | Add transaction demo     | open        | 4        | Bo
research-notes | 9  | Check query plan note    | open        | 4        | unassigned
```

完整实验中未完成工单共有 7 条。注意其中包含 `in_progress`，因为条件写的是 `status <> 'done'`。如果需求只看 open 工单，就应改成 `status = 'open'`。

如果只想调试前三条，可以加 `LIMIT`：

```sql
SELECT id, title, priority
FROM tickets
WHERE status = 'open'
ORDER BY priority DESC, id ASC
LIMIT 3;
```

`LIMIT` 适合开发调试、后台列表预览和分页查询。它不应该替代业务过滤条件；如果忘记 `WHERE`，`LIMIT 10` 只是让错误结果变短。

另一个常见查询是“高优先级 open 工单”：

```sql
SELECT id, title, priority
FROM tickets
WHERE status = ? AND priority >= ?
ORDER BY priority DESC, id ASC;
```

应用层传入 `("open", 3)`。即使只是查询，也应养成参数绑定习惯，避免之后把用户输入拼进 SQL 字符串。

## 如何解释输出

看到一条读查询时，按这个顺序检查：

1. `FROM` 是否选对事实来源。
2. `WHERE` 是否表达了业务边界。
3. `SELECT` 是否只取后续需要的列。
4. `ORDER BY` 是否让结果稳定。
5. `LIMIT` 是否用于调试或分页；如果行集合本身过宽，应先修正 `WHERE`。

这个检查顺序能减少“页面上怎么多了旧数据”“为什么排序每次不一样”“为什么导出字段过多”的问题。

对上面的输出，可以这样解释：

- `research-notes` 的优先级 5 在最前，因为 `priority DESC`。
- 两条优先级 4 的记录按 `id ASC` 排列，所以 id 4 在 id 9 前。
- `unassigned` 是联表后对空负责人的显示值，并非 `tickets.status` 的取值。

## 调试时的最小步骤

1. 先写 `SELECT COUNT(*) FROM tickets;` 确认表里有数据。
2. 加 `WHERE status <> 'done'` 看行数是否符合预期。
3. 加 `ORDER BY` 检查第一行是否是业务上最应该出现的记录。
4. 最后再决定接口需要哪些列，避免一开始就导出所有字段。

## 常见错误

1. **默认顺序稳定。** 没有 `ORDER BY` 时，结果顺序不应被当作业务契约。
2. **用 `SELECT *` 写接口。** 开发调试可以临时使用，接口和导出应明确列名。
3. **把过滤写在应用代码里。** 能在 SQL 中表达的筛选应尽量靠近数据源。
4. **忘记 NULL。** `assignee_id` 这类可空字段参与条件时，要明确是否需要包含未分配记录。
5. **把 LIMIT 当过滤条件。** `LIMIT` 只截断结果，不证明前面的行集合正确。

## 练习或延伸

1. 写一个查询，只显示 `priority >= 4` 的未完成工单。
2. 把排序改成 `created_at ASC`，观察结果如何变化。
3. 给查询增加 `LIMIT 2`，解释它适合调试还是适合最终报表。

## 参考资料

- SQLite 文档：[SELECT](https://www.sqlite.org/lang_select.html)
- SQLite 文档：[ORDER BY](https://www.sqlite.org/syntax/ordering-term.html)
- SQLite 文档：[LIMIT clause](https://www.sqlite.org/lang_select.html#limitoffset)

{% endraw %}
