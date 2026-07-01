---
layout: post
title: "CRUD 不只是增删改查：参数化 SQL 和状态边界"
date: 2026-07-01 19:21:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用商品创建、库存更新和分类查询理解 CRUD，并把用户输入绑定为参数。"
tags: [database, sqlite, crud, teaching]
---
{% raw %}
> 主题：数据库/缓存实践 / CRUD / parameterized query
> 本文 lab 已验证：创建 `MG-777` 商品、库存增加 3、按 `gear` 分类查询得到 2 个商品。

数据库应用的大部分日常工作都落在 CRUD：Create、Read、Update、Delete。初学者常把 CRUD 看成四条 SQL 语句，但真正重要的是状态边界：哪些字段来自输入，哪些字段由数据库生成，哪些更新必须带条件，哪些查询结果可以交给后续业务逻辑。

## 学习目标

1. 写出最小商品创建、库存更新和分类查询。
2. 理解参数占位符 `?` 的作用。
3. 知道为什么更新库存要同时检查下界。
4. 把查询结果转成清晰的 Python 字典。

## 先修知识

需要知道 SQL 语句可以包含 `INSERT`、`UPDATE`、`SELECT`，以及 Python 函数可以接收参数。

## 核心模型

![CRUD 不只是增删改查：参数化 SQL 和状态边界](/assets/diagrams/db-cache-crud-parameterized-queries.svg)

CRUD 是应用和数据库之间的状态接口。应用决定意图，数据库负责持久化、约束和返回结果。参数化查询把 SQL 结构和输入值分开，让输入只作为值参与执行。

## 可信资料的关键结论

- Python `sqlite3` 文档明确推荐使用占位符绑定 Python 值，避免字符串格式化拼 SQL。
- DB-API 风格的 `?` 参数让 SQL 模板和输入值分离，适合绝大多数应用 CRUD。
- 约束、WHERE 条件和应用层异常应共同表达业务边界。

## 逐步实现

创建商品：

```python
def create_product(conn, sku, name, category, price_cents, stock):
    cur = conn.execute(
        "INSERT INTO products(sku, name, category, price_cents, stock) VALUES (?, ?, ?, ?, ?)",
        (sku, name, category, price_cents, stock),
    )
    conn.commit()
    return int(cur.lastrowid)
```

这里的 SQL 结构固定，`sku`、`name` 等值通过元组绑定。这样输入里的引号、空格或特殊字符只会作为字段值处理。

更新库存：

```python
def update_stock(conn, sku, delta):
    cur = conn.execute(
        "UPDATE products SET stock = stock + ? WHERE sku = ? AND stock + ? >= 0",
        (delta, sku, delta),
    )
    if cur.rowcount != 1:
        raise ValueError(f"stock update failed for {sku}")
    conn.commit()
```

`WHERE stock + ? >= 0` 是业务边界。它让数据库拒绝把库存改成负数。`rowcount` 不是装饰信息，它告诉应用这次更新是否真正影响了一行。

读取分类：

```python
def find_products_by_category(conn, category):
    rows = conn.execute(
        "SELECT sku, name, category, price_cents, stock FROM products WHERE category = ? ORDER BY sku",
        (category,),
    ).fetchall()
    return [dict(row) for row in rows]
```

运行 lab 后，`gear_product_count=2`，因为原始 `Bottle` 加上新建的 `Mug` 都属于 `gear`。

## 常见错误

1. **用字符串拼接 SQL。** 输入会混入 SQL 结构，安全性和正确性都会下降。
2. **更新后不检查 `rowcount`。** 应用会误以为更新成功。
3. **库存用“先查再无条件更新”的两步逻辑。** 并发或异常时更容易产生边界错误。
4. **查询结果直接在各处访问 tuple 下标。** 设置 `row_factory=sqlite3.Row` 后转成 dict，代码更清楚。

## 练习或延伸

1. 增加 `delete_product_by_sku`，只允许删除没有订单明细引用的商品。
2. 给 `find_products_by_category` 增加 `min_stock` 参数。
3. 故意把 `delta` 设为很小的负数，确认函数会抛出错误。

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
