---
layout: post
title: "缓存失效和一致性：什么时候必须删掉旧报表"
date: 2026-07-01 19:25:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从订单写入后的报表变化出发，理解显式失效、TTL 和一致性边界。"
tags: [cache, consistency, database, teaching]
---
{% raw %}
> 主题：数据库/缓存实践 / invalidation / consistency
> 本文 lab 已验证：下单后显式失效一次，重新读取报表得到最新收入和库存。

缓存最容易出错的地方是旧结果的生命周期。分类收入报表由订单明细和库存共同决定。下单成功后，旧报表仍然存在于缓存中，如果继续读取它，用户看到的收入和库存都会落后。

## 学习目标

1. 识别哪些写操作会影响缓存结果。
2. 理解显式失效和 TTL 的分工。
3. 把缓存一致性边界写成可检查流程。
4. 知道小项目中如何选择简单可靠的失效策略。

## 先修知识

建议先阅读 cache-aside 和事务两篇。

## 核心模型

![缓存失效和一致性：什么时候必须删掉旧报表](/assets/diagrams/db-cache-invalidation-consistency.svg)

缓存一致性来自依赖关系。一个缓存结果依赖哪些表、哪些查询条件，相关写操作完成后就要失效对应 key。TTL 是兜底窗口，显式失效是写路径上的主动动作。

## 可信资料的关键结论

- Redis 等缓存系统提供 key 过期机制，但应用仍要设计写路径上的失效策略。
- 一致性边界应从缓存结果的数据依赖推导，而不是从缓存工具本身推导。
- 对 0 基础小项目，先用少量明确 key 和显式失效，比复杂缓存策略更可靠。

## 逐步实现

本 lab 的报表缓存 key 是：

```text
category_report
```

它依赖：

```text
products.stock
orders
order_items.quantity
order_items.unit_price_cents
```

下单会改变库存和订单明细，因此下单成功后要删除旧报表：

```python
order_one = place_order(conn, "alice", [("BK-200", 2), ("PN-010", 3)])
cache.invalidate("category_report")
order_two = place_order(conn, "bob", [("NB-001", 4), ("BT-404", 1)])
refreshed_report = get_category_report(conn, cache)
```

lab 输出：

```text
cache_invalidations=1
cache_misses=3
```

重新生成的报表里，bags 收入为 91.98，stationery 为 66.93，gear 为 18.99。这个结果来自数据库聚合，而不是缓存里旧值。

## 常见错误

1. **写操作完成后忘记失效。** 用户会看到旧报表。
2. **只靠 TTL。** TTL 到期前仍然可能返回陈旧结果。
3. **把所有缓存都清空。** 小系统可以这样做，系统变大后会造成不必要的 miss。
4. **缓存 key 没有表达依赖范围。** 后续很难判断该删哪个 key。

## 练习或延伸

1. 把 `place_order` 封装到服务函数里，让它在事务成功后统一失效缓存。
2. 增加 `product_detail:{sku}` 缓存，思考库存变更时应失效哪些 key。
3. 为报表增加 `cache_generated_at` 字段，让用户知道数据生成时间。

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
