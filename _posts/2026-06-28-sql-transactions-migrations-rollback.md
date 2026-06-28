---
layout: post
title: "事务和迁移：让多步修改要么完成要么回滚"
date: 2026-06-28 17:46:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从失败回滚和 schema_migrations 表理解事务、迁移和可审计数据库变更。"
tags: [sql, transaction, migration, rollback, teaching]
---
{% raw %}

> 主题：SQL 实用开发 / transaction / migration  
> 本文 lab 已验证：外键失败会触发事务回滚，工单数量保持 9 → 9。

很多数据修改不是一步完成的。创建工单后要写事件，导入 CSV 时要写多条工单，升级 schema 时要记录迁移版本。事务解决的问题是：一组修改要么全部完成，要么失败后回到修改前状态。迁移解决的问题是：数据库结构如何可追踪地演进。

## 学习目标

1. 理解事务的 `BEGIN`、`COMMIT`、`ROLLBACK` 语义。
2. 解释为什么多步写入需要事务保护。
3. 用 `schema_migrations` 表记录结构版本。
4. 能读懂失败回滚的测试结果。

## 先修知识

需要会写 `INSERT`，并理解外键约束失败会抛出错误。

## 核心模型

![事务提交、回滚和迁移版本模型](/assets/diagrams/sql-transactions-migrations-rollback.svg)

事务把多条语句放进同一个边界。全部成功时提交；其中一步失败时回滚。迁移表记录结构变更版本，让应用知道数据库是否已经执行过某次 schema 更新。

## 逐步实现

lab 的 schema 初始化会创建迁移表：

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
```

执行建表后写入版本记录：

```sql
INSERT OR IGNORE INTO schema_migrations(version, applied_at)
VALUES (1, ?);
```

这不是完整迁移框架，但它建立了一个重要习惯：数据库结构变化需要被记录，而不是靠“我记得运行过脚本”。

事务回滚实验先插入一条正常工单，再插入一条外键错误工单：

```sql
INSERT INTO tickets(project_id, title, status, priority, estimate_hours, created_at)
VALUES (1, 'Temporary transaction ticket', 'open', 3, 1.0, ?);

INSERT INTO tickets(project_id, title, status, priority, estimate_hours, created_at)
VALUES (999999, 'Broken foreign key', 'open', 3, 1.0, ?);
```

第二条违反外键。由于两条语句在同一个事务中，第一条也会被回滚。

## 如何解释输出

capstone 输出：

```text
rollback_before=9 rollback_after=9 rolled_back=True
```

这里的 9 是导入 CSV 后的工单数量。回滚前后数量相同，说明临时工单没有残留。这个证据比“代码看起来用了事务”更有价值，因为它直接验证了失败路径。

## 迁移的实践边界

小项目可以从一个 `migrate()` 函数开始。项目变大后，迁移通常拆成按版本编号的脚本。无论工具如何变化，都要保留三个原则：

1. 每次结构变化有版本号。
2. 迁移脚本可以在新环境复跑。
3. 失败时不留下半套结构。

## 常见错误

1. **多步写入没有事务。** 中途失败会留下部分状态。
2. **把迁移当一次性手工操作。** 手工改库难以复现，环境之间容易漂移。
3. **只测试成功路径。** 数据库错误最需要测试失败路径和回滚结果。
4. **混合业务数据和结构变更。** schema 迁移应尽量清楚边界和回滚策略。

## 练习或延伸

1. 给 `members` 表增加一个 `active` 字段，并写入迁移版本 2。
2. 写一个事务：新增工单并新增事件，故意让事件插入失败，观察工单是否回滚。
3. 查询 `schema_migrations`，确认版本记录存在。

## 参考资料

- SQLite 文档：[Transaction](https://www.sqlite.org/lang_transaction.html)
- SQLite 文档：[BEGIN TRANSACTION](https://www.sqlite.org/lang_transaction.html)
- SQLite 文档：[CREATE TABLE](https://www.sqlite.org/lang_createtable.html)
- Python 文档：[sqlite3 transaction control](https://docs.python.org/3/library/sqlite3.html#transaction-control)

{% endraw %}
