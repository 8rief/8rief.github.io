---
layout: post
title: "SQLite 汇总：用 SQL 计算地区、月份和商品收入"
date: 2026-07-01 11:28:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把清洗 CSV 导入 SQLite，用 GROUP BY 生成稳定的报表指标。"
tags: [sqlite, sql, aggregation, data-processing, teaching]
---
{% raw %}
> 主题：数据处理与可视化 / SQLite / GROUP BY / reporting
> 本文 lab 已验证：SQLite 表中有 16 行，地区收入排序第一是 `East:202.25`。

当数据已经清洗成结构化表，汇总问题交给 SQL 更清晰。Python 负责读写文件和组织流程，SQLite 负责存表、分组和聚合。这个分工能让报告指标更容易复查。

## 学习目标

1. 把 clean CSV 行导入 SQLite 表。
2. 用 `GROUP BY` 和 `SUM` 生成收入汇总。
3. 理解 SQLite 文件在本地数据项目里的作用。

## 先修知识

知道 clean CSV 中已经有 `revenue` 字段。

## 核心模型

![SQLite 聚合报表](/assets/diagrams/data-sqlite-aggregation-reporting.svg)

clean 行进入 `sales` 表，SQL 查询输出按地区、月份、商品、渠道分组的指标。summary JSON 保存查询结果。

## 可信资料的关键结论

- Python `sqlite3` 文档说明该模块提供符合 DB-API 2.0 的 SQLite 接口。
- SQLite 官方文档定位它为嵌入式、文件型数据库，适合本地应用和小型数据处理。
- 参数化插入和固定表结构比拼接 SQL 更安全、更易维护。

## 逐步实现

建表：

```python
conn.execute("""
CREATE TABLE sales (
    order_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    month TEXT NOT NULL,
    region TEXT NOT NULL,
    channel TEXT NOT NULL,
    product TEXT NOT NULL,
    units INTEGER NOT NULL,
    revenue REAL NOT NULL
)
""")
```

插入数据：

```python
conn.executemany(
    "INSERT INTO sales(...) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    rows,
)
```

地区汇总：

```sql
SELECT region, ROUND(SUM(revenue), 2) AS revenue
FROM sales
GROUP BY region
ORDER BY revenue DESC, region;
```

lab 输出：

```text
region_revenue=East:202.25
region_revenue=South:197.25
region_revenue=West:171.50
region_revenue=North:165.30
sqlite_sales_rows=16
```

## 常见错误

1. **原始脏数据直接进报表表。** 先清洗，再入库。
2. **每个图表自己读 CSV 汇总。** SQL 层应统一产出指标。
3. **金额精度不说明。** 本包用 Decimal 计算金额，SQLite 存储用于报表汇总。
4. **没有排序规则。** 同分时加上名称排序，输出更稳定。

## 练习或延伸

1. 增加一个 `by_channel` 查询，比较 Web 和 Store 收入。
2. 给 `sales` 表增加索引，观察这个小数据集是否有明显差异。
3. 把 `ROUND(SUM(revenue), 2)` 改成 `SUM(units)`，生成销量汇总。

## 参考资料

- Python 文档：[sqlite3](https://docs.python.org/3/library/sqlite3.html)
- SQLite 官方文档：[SQLite Documentation](https://sqlite.org/docs.html)
- SQLite 官方文档：[Appropriate Uses For SQLite](https://sqlite.org/whentouse.html)

{% endraw %}
