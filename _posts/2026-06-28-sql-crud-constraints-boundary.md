---
layout: post
title: "INSERT、UPDATE、DELETE 和约束：让数据修改有边界"
date: 2026-06-28 17:43:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用新增、修改、删除和数据库约束理解项目数据为什么需要写入边界。"
tags: [sql, insert, update, delete, constraints, teaching]
---
{% raw %}

> 主题：SQL 实用开发 / CRUD / constraints  
> 本文 lab 已验证：非法状态会被 `CHECK` 约束拒绝，状态更新会留下事件记录。

读查询解决“看什么”，写查询解决“改变什么”。项目事故经常发生在写入边界：空标题被写入、状态拼错、优先级超出范围、删除时留下孤立数据。`INSERT`、`UPDATE`、`DELETE` 必须和约束一起理解，才能让数据修改可控。

## 学习目标

1. 用 `INSERT` 新增一条业务记录。
2. 用 `UPDATE` 修改有限字段，并检查影响行数。
3. 用 `DELETE` 删除明确范围内的行。
4. 理解 `NOT NULL`、`CHECK`、外键动作对写入质量的保护。

## 先修知识

需要理解主键、状态字段和优先级字段。建议先读本包第一篇 schema 文章。

## 核心模型

![CRUD 写入和约束边界](/assets/diagrams/sql-crud-constraints-boundary.svg)

应用发出写入请求，数据库先检查表结构和约束。通过检查的行进入表；违反约束的写入失败，并把错误返回给调用者。开发代码应该把这种失败当作边界反馈，而不是吞掉错误。

## 逐步实现

新增工单：

```sql
INSERT INTO tickets(project_id, assignee_id, title, status, priority, estimate_hours, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?);
```

这里用 `?` 占位，是为了后续参数化查询。实际值由应用层绑定，不拼接进 SQL 字符串。

修改工单状态：

```sql
UPDATE tickets
SET status = ?
WHERE id = ?;
```

应用代码要检查影响行数。lab 中如果 `rowcount != 1`，会报告 `ticket not found`。这样可以避免“看似更新成功，其实没有匹配任何行”。

删除已完成工单：

```sql
DELETE FROM tickets
WHERE status = 'done';
```

删除语句必须有明确范围。开发中可以先把 `DELETE` 改写成 `SELECT id, title FROM ...` 预览目标行，再执行真正删除。

## 约束如何工作

lab 的测试故意写入非法状态：

```sql
INSERT INTO tickets(project_id, title, status, priority, estimate_hours, created_at)
VALUES (1, 'bad status', 'blocked', 3, 1.0, '2026-06-28T00:00:00Z');
```

由于 `status` 只允许 `open`、`in_progress`、`done`，SQLite 会抛出 `IntegrityError`。这说明错误没有进入数据表，后续查询也不需要为未知状态写额外分支。

## 如何解释输出

本地测试记录：

```text
test_constraints_reject_invalid_status ... ok
test_status_update_records_event ... ok
```

第一条说明非法状态被挡住；第二条说明状态更新不仅改变 `tickets.status`，还会向 `ticket_events` 写入一条事件。项目里的写操作通常不只改一列，还需要留下可审计轨迹。

## 常见错误

1. **写 `UPDATE` 不带 `WHERE`。** 这会修改整张表，是最常见的破坏性错误之一。
2. **删除前不预览。** 先用同样条件 `SELECT` 一次，可以减少误删。
3. **只靠前端校验。** 前端、后端和数据库约束分别服务不同边界，不能互相替代。
4. **忽略影响行数。** `UPDATE` 没报错不代表真的改到目标行。

## 练习或延伸

1. 把某条工单从 `open` 改为 `done`，再查询事件表。
2. 尝试插入 `priority = 9`，解释失败来自哪个约束。
3. 先 `SELECT` 再 `DELETE` 所有已完成工单，记录删除数量。

## 参考资料

- SQLite 文档：[INSERT](https://www.sqlite.org/lang_insert.html)
- SQLite 文档：[UPDATE](https://www.sqlite.org/lang_update.html)
- SQLite 文档：[DELETE](https://www.sqlite.org/lang_delete.html)
- SQLite 文档：[CHECK constraints](https://www.sqlite.org/lang_createtable.html#ckconst)

{% endraw %}
