---
layout: post
title: "参数化查询和导入导出：把 SQL 接进 Python 项目"
date: 2026-06-28 17:47:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 Python sqlite3、占位符、CSV 导入和 JSON/CSV 导出，把 SQL 变成项目代码的一部分。"
tags: [sql, sqlite3, parameterized-query, csv, json, teaching]
---
{% raw %}

> 主题：SQL 实用开发 / Python sqlite3 / import-export  
> 本文 lab 已验证：包含英文单引号的标题能被参数化 INSERT 正确保存。

SQL 进入项目代码后，核心问题变成边界：用户输入如何进入查询，查询结果如何变成 JSON 或 CSV，导入文件如何被校验。参数化查询解决输入绑定，导入导出解决数据交换。它们比复杂数据库理论更贴近日常开发。

## 学习目标

1. 用 Python `sqlite3` 打开数据库并启用外键。
2. 用 `?` 占位符写参数化查询。
3. 从 CSV 导入工单数据。
4. 把同一份查询结果导出为 JSON 和 CSV。

## 先修知识

需要会使用 Python 文件读写，理解 SQL 的 `INSERT`、`SELECT` 和基本表结构。

## 核心模型

![参数化查询、导入和导出边界](/assets/diagrams/sql-parameterized-query-import-export-python.svg)

应用代码不把用户输入拼进 SQL 字符串，而是把 SQL 模板和参数分开交给数据库驱动。导入时，CSV 被解析成字段；导出时，查询结果被序列化成 JSON 和 CSV。每个边界都需要固定字段名和错误处理。

## 逐步实现

打开连接时设置 row factory 和外键：

```python
def connect(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

新增工单使用参数化 `INSERT`：

```python
conn.execute(
    """
    INSERT INTO tickets(project_id, assignee_id, title, status, priority, estimate_hours, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    (project_id, assignee_id, title, status, priority, estimate_hours, created_at),
)
```

lab 的测试传入标题：

```text
Reader's SQL note; no string concat
```

这行文本包含英文单引号和分号。参数化查询会把它当作普通字段值保存，而不是把它解释成 SQL 语法。

## CSV 导入

导入函数先检查表头：

```python
required = {"project", "title", "priority", "assignee"}
if set(reader.fieldnames or []) != required:
    raise ValueError(f"CSV header must be exactly {sorted(required)}")
```

然后逐行调用同一个 `add_ticket()`。这样 CSV 导入和普通新增共用同一套约束、外键和事件记录逻辑。

## JSON 和 CSV 导出

JSON 保存嵌套报表，CSV 保存明细表：

```python
report = {
    "project_summary": run_named_query(conn, "project_summary"),
    "workload": run_named_query(conn, "workload"),
    "open_tickets": run_named_query(conn, "open_tickets"),
}
```

同一份查询结果被写成 `report.json` 和 `open_tickets.csv`。这能避免 JSON 和 CSV 来自两套不同逻辑，导致数字对不上。

## 如何解释输出

capstone 输出：

```text
imported_tickets=3
json_export=reports/report.json
csv_export=reports/open_tickets.csv
```

这说明 CSV 导入增加了 3 条工单，并且导出阶段生成了两种格式。测试同时检查 JSON 中包含 `project_summary`，CSV 以固定表头开头。

## 常见错误

1. **字符串拼接 SQL。** 输入中有引号、分号或换行时容易出错，也会扩大注入风险。
2. **导入逻辑绕过业务函数。** 这样会绕开状态检查、事件记录或默认值。
3. **JSON 和 CSV 分别算一遍。** 两种导出格式应尽量来自同一份内存结果。
4. **导出绝对路径。** 公开报告中应避免暴露本机目录结构。

## 练习或延伸

1. 给导入 CSV 增加 `estimate_hours` 字段，并补充测试。
2. 把导出 JSON 改成只包含未完成工单，观察测试如何调整。
3. 传入包含逗号的标题，检查 CSV 是否仍能正确导出。

## 参考资料

- Python 文档：[sqlite3 placeholders](https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders)
- Python 文档：[csv — CSV File Reading and Writing](https://docs.python.org/3/library/csv.html)
- Python 文档：[json — JSON encoder and decoder](https://docs.python.org/3/library/json.html)
- SQLite 文档：[SQLite Keywords](https://www.sqlite.org/lang_keywords.html)

{% endraw %}
