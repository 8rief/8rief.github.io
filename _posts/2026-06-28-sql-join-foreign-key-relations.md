---
layout: post
title: "JOIN 和外键：把项目、成员和工单连成一张结果"
date: 2026-06-28 17:44:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用项目、成员、工单三张表讲清 JOIN、外键和 LEFT JOIN 在实际开发中的边界。"
tags: [sql, join, foreign-key, left-join, teaching]
---
{% raw %}

> 主题：SQL 实用开发 / JOIN / foreign key  
> 本文 lab 已验证：未分配工单通过 `LEFT JOIN` 显示为 `unassigned`。

真实项目很少只靠一张表。工单属于项目，工单可以分配给成员，事件属于工单。如果把项目名和成员名重复写进每条工单，修改名字时就会出现多处状态不一致。外键和 `JOIN` 的价值是把事实分开保存，在读取时组合成需要的结果。

## 学习目标

1. 理解外键列保存的是被关联表的主键。
2. 用 `JOIN` 读取必须存在的关联数据。
3. 用 `LEFT JOIN` 保留可选关联缺失的行。
4. 能判断哪些字段应该存一份，哪些字段应该通过关联读取。

## 先修知识

需要理解 `projects.id`、`members.id` 和 `tickets.project_id`、`tickets.assignee_id` 的对应关系。

## 核心模型

![JOIN 和外键关系模型](/assets/diagrams/sql-join-foreign-key-relations.svg)

`tickets.project_id` 指向 `projects.id`，所以每条工单必须能找到所属项目。`tickets.assignee_id` 指向 `members.id`，但它允许为空，表示工单暂时未分配。

## 逐步实现

读取未完成工单时，把项目名和负责人名一起带出来：

```sql
SELECT p.name AS project,
       t.id,
       t.title,
       t.status,
       t.priority,
       COALESCE(m.name, 'unassigned') AS assignee
FROM tickets AS t
JOIN projects AS p ON p.id = t.project_id
LEFT JOIN members AS m ON m.id = t.assignee_id
WHERE t.status <> 'done'
ORDER BY t.priority DESC, t.id ASC;
```

这里有两个不同的连接：

1. `JOIN projects`：工单必须属于项目，缺项目就是数据错误。
2. `LEFT JOIN members`：工单可以没有负责人，缺负责人仍然要显示。

`COALESCE(m.name, 'unassigned')` 把空负责人转成报表中可读的词。这样导出的 CSV 不会让读者分不清是缺字段还是未分配。

## 如何解释输出

lab 输出中有这样的行：

```text
research-notes | 6 | Summarize baseline gap | open | 5 | unassigned
```

这条工单没有负责人，但它仍然出现在结果里，因为成员表使用的是 `LEFT JOIN`。如果把它改成普通 `JOIN`，未分配工单会从结果中消失，报表会错误地低估待处理工作。

## 外键的开发价值

外键不只是“关系数据库的概念”。它在开发中直接解决三个问题：

1. 防止工单指向不存在的项目。
2. 删除项目时让相关工单按规则处理。
3. 让读查询能用主键关系组合数据，而不是靠字符串猜测。

SQLite 中需要对连接执行 `PRAGMA foreign_keys = ON`。lab 的 `connect()` 每次打开数据库都会设置它，避免测试和 CLI 行为不一致。

## 常见错误

1. **把 `LEFT JOIN` 都写成 `JOIN`。** 可选关系会被误删出结果集。
2. **用名字当关联字段。** 名字可能改，主键更适合做关联身份。
3. **忘记打开 SQLite 外键检查。** SQLite 需要显式启用外键约束。
4. **把重复字段当缓存。** 除非有明确性能和一致性方案，否则优先通过 JOIN 读取。

## 练习或延伸

1. 查询每条工单的最近一条事件，需要连接 `ticket_events`。
2. 把 `LEFT JOIN members` 改成 `JOIN members`，观察未分配工单是否还在。
3. 尝试插入 `project_id = 999999` 的工单，解释外键错误。

## 参考资料

- SQLite 文档：[JOIN clause](https://www.sqlite.org/syntax/join-clause.html)
- SQLite 文档：[SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html)
- SQLite 文档：[Core functions — coalesce](https://www.sqlite.org/lang_corefunc.html#coalesce)

{% endraw %}
