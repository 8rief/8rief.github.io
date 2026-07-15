---
layout: post
title: "数据库从表结构开始：用 SQLite user_version 管住迁移"
date: 2026-03-29 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从产品、订单和订单明细三张表开始，理解 schema、约束、外键和 user_version 迁移。"
tags: [database, sqlite, migration, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/database-cache-practice/README.md`](/assets/labs/database-cache-practice/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：数据库/缓存实践 / schema / migration
> 本文 lab 已验证：`PRAGMA user_version` 从 0 迁移到 2，生成 products、orders、order_items 三张表和两个索引。

应用数据一旦需要长期保存，第一件事就是把数据形状固定下来。表结构的作用是把“商品、订单、库存”这些业务词变成数据库能检查的列、类型、约束和关系。这个阶段不追求复杂建模，目标是让 0 基础读者能看懂一个最小库存系统为什么需要三张表，以及如何知道数据库已经处在正确版本。

## 学习目标

1. 解释表、列、主键、唯一约束、外键和检查约束的作用。
2. 用 `PRAGMA user_version` 保存当前 schema 版本。
3. 把迁移脚本写成可重复运行的函数。
4. 运行 lab 后确认 `schema_version=2`。

## 先修知识

只需要能运行 Python 3，并知道一行 CSV 或 JSON 记录可以表示一个对象。SQL 基础可以边看边补。

## 核心模型

![数据库从表结构开始：用 SQLite user_version 管住迁移](/assets/diagrams/db-cache-schema-migration-user-version.svg)

schema 是数据库的结构合同。应用先读取当前版本，再按版本号顺序补齐缺失结构，最后把版本号写回数据库文件。这样下一次启动时，程序能判断哪些迁移已经完成。

## 为什么需要 schema 版本

真实项目很少一次建完表后永远不动。第一个版本可能只有商品表，第二个版本需要订单表，第三个版本又要给查询加索引。如果每次启动都直接执行一整段 `CREATE TABLE`，旧数据库会因为对象已存在而失败；如果只靠人工记忆“这个数据库已经改到哪一步”，换机器、换同学、换部署环境时很快会失控。

`user_version` 解决的核心问题是可判定性。程序读取数据库文件里的整数版本，就能决定还需要执行哪些迁移。迁移脚本因此变成一个状态机：版本 0 进入版本 1，版本 1 进入版本 2。每个迁移只负责一小段结构变化，成功后再推进版本号。

这也让错误更容易定位。若运行后版本仍是 1，问题就落在第二段迁移；若版本是 2 但查询计划没有索引，就检查 `CREATE INDEX` 和目标 SQL 是否匹配。版本号把“数据库结构是否正确”变成可检查事实。

## 可信资料的关键结论

- Python `sqlite3` 连接的是 SQLite 文件数据库，适合小型本地数据持久化和原型开发。
- SQLite 的 PRAGMA 是 SQLite 专有控制接口，适合查询或设置数据库内部状态；`user_version` 常用于应用自管 schema 版本。
- 外键在 SQLite 中需要连接级启用，本 lab 在 `connect()` 里显式执行 `PRAGMA foreign_keys = ON`。

## 逐步实现

本包 lab 的三张表对应一个小库存系统：

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price_cents INTEGER NOT NULL CHECK(price_cents > 0),
    stock INTEGER NOT NULL CHECK(stock >= 0)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents > 0),
    PRIMARY KEY(order_id, product_id)
);
```

第一张表保存商品当前状态，第二张表保存一次购买行为，第三张表保存订单里买了哪些商品和当时单价。`unit_price_cents` 放在订单明细里，是为了订单历史不被后续商品改价影响。

迁移函数先读版本：

```python
def user_version(conn):
    return int(conn.execute("PRAGMA user_version").fetchone()[0])
```

然后按版本推进：

```python
if version < 1:
    conn.executescript("""
    CREATE TABLE products (...);
    CREATE TABLE orders (...);
    CREATE TABLE order_items (...);
    PRAGMA user_version = 1;
    """)

if version < 2:
    conn.executescript("""
    CREATE INDEX idx_products_category ON products(category, sku);
    CREATE INDEX idx_order_items_product_id ON order_items(product_id);
    PRAGMA user_version = 2;
    """)
```

运行：

```bash
bash run_lab.sh
```

你应该看到：

```text
schema_version=2
product_count=5
order_count=2
database_cache_status=ok
```

## 输出怎么读

`run_lab.sh` 会先删除旧的演示数据，再从空数据库重新迁移，所以输出是确定性的：

```text
schema_version=2
product_count=5
order_count=2
total_stock=158
```

`schema_version=2` 表示两段迁移都已经执行：第一段建表，第二段建索引。`product_count=5` 来自四个种子商品加一个新建的 `MG-777`。`order_count=2` 属于后续事务文章里的下单演示；它出现在这里，是为了证明同一套 schema 已经足够支撑订单写入。

还可以直接打开 SQLite 文件检查结构：

```sql
PRAGMA user_version;
SELECT name, type FROM sqlite_master WHERE type IN ('table', 'index') ORDER BY type, name;
```

你应该能看到 `products`、`orders`、`order_items` 三张表，以及 `idx_products_category`、`idx_order_items_product_id` 两个显式索引。若 `PRAGMA user_version` 返回 0，说明迁移函数没有运行；若没有索引，说明第二段迁移没有推进到版本 2。

## 常见错误

1. **把 schema 当成一次性脚本。** 实际项目会演进，需要版本号和顺序迁移。
2. **只在应用层检查库存和价格。** 数据库约束可以挡住一部分错误写入。
3. **忘记开启 SQLite 外键检查。** Python 连接后执行 `PRAGMA foreign_keys = ON`，让外键约束真正生效。
4. **把金额存成浮点数。** 本 lab 使用 cents 整数，避免小数精度问题。

## 练习或延伸

1. 给 `products` 增加 `description` 字段，把迁移版本推进到 3。
2. 尝试插入 `stock=-1` 的商品，观察 CHECK 约束如何报错。
3. 删除一个订单，确认 `order_items` 是否随外键级联删除。

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
