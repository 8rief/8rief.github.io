---
layout: post
title: "索引为什么会让查询变快：用 EXPLAIN QUERY PLAN 看证据"
date: 2026-06-21 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "给分类查询加索引，并用 SQLite 的查询计划确认查询走了索引。"
tags: [database, sqlite, index, query-plan, teaching]
---
{% raw %}
> 主题：数据库/缓存实践 / index / EXPLAIN QUERY PLAN
> 本文 lab 已验证：`EXPLAIN QUERY PLAN` 输出包含 `USING INDEX idx_products_category`。

索引的需求来自一个简单问题：数据越来越多时，数据库还要逐行扫描所有商品吗？分类查询的条件是 `WHERE category = ? ORDER BY sku`，如果我们经常这样查，就可以把 `category, sku` 建成索引，让数据库沿着更有序的数据结构定位结果。

## 学习目标

1. 理解索引服务于具体查询形状。
2. 创建组合索引 `idx_products_category`。
3. 用 `EXPLAIN QUERY PLAN` 验证查询计划。
4. 知道索引也有写入和维护成本。

## 先修知识

需要知道 `WHERE` 会筛选行，`ORDER BY` 会决定输出顺序。

## 核心模型

![索引为什么会让查询变快：用 EXPLAIN QUERY PLAN 看证据](/assets/diagrams/db-cache-index-explain-query-plan.svg)

索引像一本按关键词排序的目录。查询条件命中索引前缀时，数据库可以通过目录定位候选行，再按需要读取表数据。查询计划是数据库优化器选择访问路径的证据。

## 为什么需要查询计划

索引常被讲成“会让查询变快”，但初学阶段只看耗时容易误判。5 行数据无论扫描还是走索引都很快，操作系统缓存、解释器启动、一次性测量误差都会掩盖真正的访问路径。查询计划解决的核心问题是：数据库到底打算怎样取数据。

`EXPLAIN QUERY PLAN` 给出优化器选择的路径。看到 `SCAN products`，说明数据库倾向于扫描表；看到 `SEARCH products USING INDEX idx_products_category (category=?)`，说明分类条件命中了索引。它不能替代性能测试，也不能保证所有数据规模下都最优，但它能把索引是否被使用这件事变成可观察证据。

组合索引的列顺序也要从查询形状出发。本例查询先按 `category` 筛选，再按 `sku` 排序，所以 `(category, sku)` 同时服务筛选和输出顺序。若经常按 `sku` 查单个商品，就应该分析另一条查询，而不是指望同一个索引解决所有问题。

## 可信资料的关键结论

- SQLite 官方文档把 `EXPLAIN QUERY PLAN` 定位为交互式调试工具，适合观察 SELECT 使用了扫描还是索引搜索。
- SQLite 查询规划器会在可用访问路径之间选择成本较低的方案，索引是否使用取决于查询条件和统计信息。
- CREATE INDEX 创建的是额外数据结构，读路径可能变快，写路径需要维护索引。

## 逐步实现

本 lab 的第二个迁移创建索引：

```sql
CREATE INDEX idx_products_category ON products(category, sku);
```

它对应的查询是：

```sql
SELECT sku, name
FROM products
WHERE category = ?
ORDER BY sku;
```

用查询计划观察：

```python
rows = conn.execute(
    "EXPLAIN QUERY PLAN SELECT sku, name FROM products WHERE category = ? ORDER BY sku",
    ("gear",),
).fetchall()
plan = [str(row[3]) for row in rows]
```

lab 输出：

```text
query_plan=SEARCH products USING INDEX idx_products_category (category=?)
query_plan_uses_index=True
```

这条证据比“我觉得快”更有价值。当前数据只有 5 行，肉眼看不到性能差异；但查询计划说明数据库已经选择了我们为查询形状准备的访问路径。

## 输出怎么读

lab 会打印两层证据：原始查询计划和布尔断言。

```text
query_plan=SEARCH products USING INDEX idx_products_category (category=?)
query_plan_uses_index=True
```

第一行来自 SQLite 的计划描述。`SEARCH products` 表示按条件搜索表，`USING INDEX idx_products_category` 表示使用了我们创建的索引，`(category=?)` 表示绑定参数落在索引前缀上。第二行是测试友好的摘要：代码检查计划文本中是否包含索引名。

如果你把第二段迁移里的索引删除，再运行同样查询，常见输出会变成表扫描或使用其他可用索引。此时查询结果仍可能正确，只是访问路径不同。学习索引时要同时保留两个问题：结果是否正确，访问路径是否符合预期。

## 常见错误

1. **为所有列都建索引。** 索引会占空间，也会增加写入维护成本。
2. **脱离查询形状谈索引。** 先写出 WHERE、JOIN、ORDER BY，再决定索引。
3. **只测小数据耗时。** 小数据更适合看计划和解释机制，大数据再做耗时测量。
4. **看到索引名就结束分析。** 还要确认查询结果正确，索引只是访问路径。

## 练习或延伸

1. 删除 `idx_products_category` 后重新运行查询计划，对比输出。
2. 把查询改成 `WHERE sku = ?`，思考 UNIQUE 约束生成的索引是否会参与。
3. 把索引列顺序改成 `(sku, category)`，观察分类查询计划变化。

## 参考资料

- Python 文档：[sqlite3](https://docs.python.org/3/library/sqlite3.html)
- SQLite 文档：[PRAGMA](https://www.sqlite.org/pragma.html)
- SQLite 文档：[Foreign Key Support](https://www.sqlite.org/foreignkeys.html)
- SQLite 文档：[Transactions](https://www.sqlite.org/lang_transaction.html)
- SQLite 文档：[CREATE INDEX](https://www.sqlite.org/lang_createindex.html)
- SQLite 文档：[EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html)
- SQLite 文档：[Query Planner](https://www.sqlite.org/queryplanner.html)
- Redis 文档：[EXPIRE](https://redis.io/docs/latest/commands/expire/)

{% endraw %}
