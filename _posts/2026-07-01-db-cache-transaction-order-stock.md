---
layout: post
title: "事务的真实用途：订单写入和库存扣减必须一起成功"
date: 2026-07-01 19:23:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个下单函数理解事务、回滚、库存检查和订单明细写入。"
tags: [database, sqlite, transaction, teaching]
---
{% raw %}
> 主题：数据库/缓存实践 / transaction / order flow
> 本文 lab 已验证：两个订单写入成功，库存扣减后 `total_stock=158`，订单明细共 4 行。

订单系统最怕半成品状态：订单头已经写入，库存没有扣；库存扣了，订单明细失败；某个商品不存在，前面几步却已经提交。事务解决的就是这一类“多步状态变化必须作为一个整体”的问题。

## 学习目标

1. 解释事务为什么服务于整体一致性。
2. 写出最小下单函数：创建订单、检查库存、扣库存、写明细。
3. 理解 Python `with conn:` 的提交和回滚边界。
4. 运行 lab 后核对订单、库存和收入。

## 先修知识

需要知道 INSERT 会新增行，UPDATE 会修改行，异常可以中断函数。

## 核心模型

![事务的真实用途：订单写入和库存扣减必须一起成功](/assets/diagrams/db-cache-transaction-order-stock.svg)

事务是数据库里的工作单元。事务内部的多条语句要么全部提交，要么在错误时回滚。应用把同一业务动作的数据库写入放到一个事务边界内。

## 可信资料的关键结论

- SQLite 事务通过 BEGIN、COMMIT、ROLLBACK 管理一组数据库变化；Python `sqlite3` 连接上下文管理器可用于提交或回滚事务。
- 事务边界应围绕业务动作，而不是围绕单条 SQL。
- 下单这类写路径的验证要同时检查订单、订单明细、库存和收入。

## 逐步实现

下单函数先把输入规范化，并拒绝空订单：

```python
normalized = [(sku, int(quantity)) for sku, quantity in items]
if not normalized:
    raise ValueError("order must contain at least one item")
```

然后进入事务边界：

```python
with conn:
    order_id = conn.execute("INSERT INTO orders(customer) VALUES (?)", (customer,)).lastrowid
    for sku, quantity in normalized:
        row = conn.execute(
            "SELECT id, price_cents, stock FROM products WHERE sku = ?",
            (sku,),
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown sku {sku}")
        if row["stock"] < quantity:
            raise ValueError(f"insufficient stock for {sku}")
        conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, row["id"]))
        conn.execute(
            "INSERT INTO order_items(order_id, product_id, quantity, unit_price_cents) VALUES (?, ?, ?, ?)",
            (order_id, row["id"], quantity, row["price_cents"]),
        )
```

lab 下了两个订单：

```text
order_count=2
sqlite_order_item_rows=4
total_revenue_cents=17790
total_stock=158
```

库存为什么是 158：初始四个商品库存 153，新建 Mug 后增加到 165，再补货 3 得到 168；两个订单一共卖出 10 件，最终 158。这个数字被测试固定下来。

## 常见错误

1. **每条 SQL 都单独提交。** 多步业务动作会暴露中间状态。
2. **只写订单，不复制成交单价。** 商品改价后历史订单会失真。
3. **错误时吞掉异常继续执行。** 事务边界需要让失败显式暴露。
4. **只看订单数，不核对库存和明细行。** 完整验证要覆盖相关表。

## 练习或延伸

1. 添加一个库存不足的订单测试，确认数据库没有留下半个订单。
2. 把 `unit_price_cents` 改成从 products 动态查询，思考历史订单会出现什么问题。
3. 给订单增加 `status` 字段，设计取消订单时如何回补库存。

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
