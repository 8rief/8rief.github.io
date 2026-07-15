---
layout: post
title: "SQLite 汇总：用 SQL 计算地区、月份和商品收入"
date: 2026-06-19 18:00:00 +0800
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

## 为什么需要 SQLite

只用 Python 字典也能做分组求和，但 SQL 更适合表达报表问题。`GROUP BY region`、`GROUP BY month` 这样的语句能直接说明指标口径，也便于以后把本地数据迁移到更大的数据库。SQLite 的优势是不用启动服务，一个文件就能保存表和查询结果，非常适合入门数据项目和本地报告。

本包的分工很明确：

1. Python 负责文件读写、校验和流程控制。
2. SQLite 负责把 clean 行保存成表。
3. SQL 查询负责分组、求和、排序。
4. JSON 保存查询结果，供展示层使用。

这种分工让汇总口径集中在少数 SQL 语句里，而不是散落在多个脚本函数中。

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

## 输出怎么读

`sqlite_sales_rows=16` 必须和 `clean_rows=16` 对上，说明只有清洗后的有效行进入了报表表。四行地区收入按收入倒序排列：

```text
East  202.25
South 197.25
West  171.50
North 165.30
```

这个顺序由 SQL 的 `ORDER BY revenue DESC, region` 决定，图表脚本只读取已经排好的结果。第二个排序键 `region` 用来处理收入相同时的稳定顺序，避免每次运行输出顺序不同。

`ROUND(SUM(revenue), 2)` 表示按两位小数输出报表值。本 lab 的金额计算在 Python 中使用 `Decimal`，SQLite 负责报表汇总和展示口径。

## 查询到报告的状态变化

地区汇总的状态变化可以写成：

```text
sales 表 16 行
-> 按 region 分组
-> 每组 SUM(revenue)
-> ROUND 到两位小数
-> 按 revenue 倒序
-> 写入 summary["by_region"]
```

如果报告中的 top region 不对，先查 SQL 输出，再查 summary，而不是直接改 SVG。

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
