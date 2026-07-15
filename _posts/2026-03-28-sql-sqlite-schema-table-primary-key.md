---
layout: post
title: "SQL 开发起点：用 SQLite 建一张能解释的表"
date: 2026-03-28 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从数据库文件、表、列、行和主键开始，用 SQLite 建立实际项目里的第一层 SQL 模型。"
tags: [sql, sqlite, schema, primary-key, teaching]
---
{% raw %}

> 主题：SQL 实用开发 / schema / table / primary key  
> 本文是 SQL 实用开发包的第一篇。实验使用 Python 标准库自带的 SQLite，不需要单独安装数据库服务。

很多人第一次接触 SQL 时直接背 `SELECT`，写项目时却不知道数据库文件里到底保存了什么。更稳的起点是先把数据形状定义清楚：一个数据库文件里有表，表由列组成，每一行是一条业务事实，主键给这条事实一个稳定身份。后续查询、更新、关联和报表都建立在这个形状上。

## 为什么需要先设计 schema

应用代码可以临时用字典、JSON 或 CSV 保存数据，但这些格式通常不会自动拒绝坏状态。工单状态写成 `blocked` 还是 `in_progress`，优先级能不能是 9，标题能不能是空字符串，都要靠 schema 说明并执行。

一个好的入门 schema 先把三件事说清楚：每行代表什么事实；哪些字段必须存在；哪些值属于非法写入。这样后面的 `SELECT`、`JOIN`、`GROUP BY` 和事务测试才有共同边界。

## 学习目标

1. 区分数据库文件、表、列、行和主键。
2. 用 `CREATE TABLE` 写出一个小型项目数据库的 schema。
3. 理解 `PRIMARY KEY`、`NOT NULL`、`UNIQUE` 和 `CHECK` 在开发中的作用。
4. 能解释为什么 SQL 表设计要先服务应用数据边界，再逐步引入更复杂的建模理论。

## 先修知识

需要会运行 Python 脚本、读写普通文本文件，并理解“项目、成员、工单”这类普通业务对象。本文不要求掌握数据库内核。

## 核心模型

![SQLite schema、table、row 和 primary key 模型](/assets/diagrams/sql-sqlite-schema-table-primary-key.svg)

SQLite 把数据库保存成一个普通文件。连接打开这个文件后，SQL 语句在文件中的表上执行。表的列规定每行有哪些字段；主键用于稳定定位一行；约束把明显不合法的数据挡在写入边界。

本包的 lab 使用一个小型工单系统：`projects` 保存项目，`members` 保存成员，`tickets` 保存工单，`ticket_events` 保存工单事件。这个模型足够小，但能覆盖实际开发常用的 SQL 动作。

一条工单行可以这样理解：

```text
id=2
project_id=1
assignee_id=1
title="Write SQL route"
status="open"
priority=3
estimate_hours=2.0
created_at="2026-06-28T08:00:00Z"
```

这里的 `id` 是这条事实的身份，`project_id` 和 `assignee_id` 是指向其他表的身份，`status/priority` 是受约束的业务状态。

## 逐步实现

创建项目表时，先写业务身份和必要约束：

```sql
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived'))
);
```

这里有四个开发上常见的边界：

1. `id INTEGER PRIMARY KEY` 给每个项目一条稳定记录身份。
2. `name TEXT NOT NULL UNIQUE` 表示项目名必须存在，而且不能重复。
3. `status` 有默认值，避免应用每次都重复填相同初始状态。
4. `CHECK` 限定状态枚举，避免把 `actvie` 这类拼写错误写进库。

成员表也类似：

```sql
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'developer'
);
```

工单表开始出现表之间的关系：

```sql
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assignee_id INTEGER REFERENCES members(id) ON DELETE SET NULL,
    title TEXT NOT NULL CHECK (length(title) > 0),
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'done')),
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    estimate_hours REAL NOT NULL DEFAULT 1.0 CHECK (estimate_hours >= 0),
    created_at TEXT NOT NULL
);
```

`project_id` 指向项目，`assignee_id` 指向成员。一个工单必须属于某个项目，但可以暂时没有负责人，所以前者 `NOT NULL`，后者允许为空。

把这些 SQL 放进迁移函数后，可以用下面的顺序验证：

```text
init schema -> seed sample data -> run report queries -> run constraint tests
```

如果 schema 没有守住边界，后面查询会被迫处理更多脏数据分支。

## 如何解释输出

lab 初始化后会创建数据库文件并写入样例数据。报告里记录了 SQLite 版本：

```text
sqlite_version=3.45.1
```

版本号让实验可以被复查。SQL 教学如果只贴语法不记录环境，后续遇到行为差异时很难定位。

本 lab 的约束测试会尝试插入非法状态：

```text
status='blocked'
```

结果是 SQLite 抛出完整性错误，测试 `test_constraints_reject_invalid_status` 通过。这个输出说明状态枚举已经成为数据库执行的写入规则。

## 实际开发中的取舍

- `INTEGER PRIMARY KEY` 在 SQLite 中适合作为小项目的自增身份；不要把可变的项目名当主键。
- `TEXT` 时间戳可用 ISO 8601 字符串保存，便于排序和导出；复杂时再引入更严格的时间处理约定。
- `CHECK` 适合守住简单枚举和数值范围；跨表规则要用外键或应用事务处理。
- `IF NOT EXISTS` 让初始化脚本可以复跑，但结构变更仍应有迁移版本记录。

## 常见错误

1. **先写查询，后想结构。** 查询依赖表结构，开发时应先让表的身份、字段和约束可解释。
2. **所有字段都允许为空。** `NULL` 有语义；没有想清楚时让它随处出现，会让查询和统计复杂化。
3. **把字符串当枚举随便写。** 状态字段应有固定集合，至少用 `CHECK` 守住拼写边界。
4. **只在应用层检查。** 应用代码可以有校验，但数据库约束是最后一道写入边界。
5. **把所有表合成一张大表。** 初学时看似简单，后续改项目名、成员名和事件历史时会出现重复和不一致。

## 练习或延伸

1. 给 `projects` 增加一个 `created_at` 字段，思考它是否应为 `NOT NULL`。
2. 给 `members.role` 加上 `CHECK`，限制为 `maintainer`、`developer`、`reviewer`。
3. 人为插入一个空标题工单，观察约束错误。

## 参考资料

- SQLite 文档：[CREATE TABLE](https://www.sqlite.org/lang_createtable.html)
- SQLite 文档：[Datatypes In SQLite](https://www.sqlite.org/datatype3.html)
- SQLite 文档：[SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html)
- Python 文档：[sqlite3 — DB-API 2.0 interface for SQLite databases](https://docs.python.org/3/library/sqlite3.html)

{% endraw %}
