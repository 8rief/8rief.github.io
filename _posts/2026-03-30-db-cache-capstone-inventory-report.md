---
layout: post
title: "结课项目：库存订单系统、报表缓存和 SVG 展示"
date: 2026-03-30 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 schema、CRUD、事务、索引、cache-aside、TTL、测试和报告合成一个可运行小项目。"
tags: [database, cache, sqlite, capstone, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/database-cache-practice/README.md`](/assets/labs/database-cache-practice/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：数据库/缓存实践 / capstone / inventory report
> 本文 lab 已验证：一条命令生成 SQLite 数据库、JSON 摘要、SVG 图表、Markdown 报告和 transcript。

这个结课项目把数据库和缓存放在同一个可运行例子里：商品存入 SQLite，订单通过事务写入，分类报表通过 SQL 聚合生成，cache-aside 缓存减少重复查询，TTL 和显式失效控制陈旧窗口，最后产出 JSON、SVG、Markdown 和 transcript。

## 学习目标

1. 从空目录运行一个数据库/缓存小项目。
2. 解释每个模块在系统中的位置。
3. 用输出指标说明项目已经完成。
4. 知道下一步如何迁移到 Web API 或真实 Redis。

## 先修知识

建议按顺序读完本包前七篇。需要 Python 3 和 shell。

## 核心模型

![结课项目：库存订单系统、报表缓存和 SVG 展示](/assets/diagrams/db-cache-capstone-inventory-report.svg)

项目主线是：迁移 schema → 写入种子商品 → 执行 CRUD → 下单事务 → 聚合报表 → 缓存报表 → 写出展示产物 → 跑测试和 transcript。每一步都有可见输出或可审计文件。

## 为什么需要结课项目

单独学习 schema、CRUD、事务、索引和缓存时，每个概念都能用很小的片段解释清楚。但真实开发不会按概念分文件运行；一个功能通常会同时写数据库、读报表、做缓存、生成输出并接受测试。结课项目的作用是把这些片段连成一条可执行数据流。

这个项目解决的核心问题是端到端可见性。你从空目录开始运行一条命令，最后得到 SQLite 数据库、结构化 JSON、Markdown 摘要、SVG 图表和 transcript。每个产物都对应一个开发场景：数据库供程序继续使用，JSON 供接口或测试消费，Markdown 给人读，SVG 能展示，transcript 记录复现过程。

它也给后续扩展留下稳定边界。要接 Web API，就把 `place_order` 和报表读取包成 HTTP 路由；要换 Redis，就保持 cache-aside 流程，替换 `TTLCache` 的存取实现；要接真实商品数据，就保留 schema 和测试，替换 seed 数据来源。

## 可信资料的关键结论

- SQLite 适合本地文件数据库和应用内存储场景；Python 标准库可直接访问它。
- 索引、事务和外键是数据库应用的基础工程能力，应该在小项目阶段就形成习惯。
- 缓存工程的第一原则是权威数据源清晰、缓存 key 依赖清晰、失效和 TTL 边界清晰。

## 逐步实现

运行完整 lab：

```bash
bash run_lab.sh
```

核心输出：

```text
schema_version=2
product_count=5
order_count=2
total_revenue_cents=17790
total_stock=158
cache_hits=1
cache_misses=3
cache_invalidations=1
cache_expirations=1
query_plan_uses_index=True
database_cache_status=ok
```

项目结构：

```text
database-cache-practice/
  scripts/app.py
  scripts/test_app.py
  data/app.sqlite3
  reports/summary.json
  reports/category_revenue.svg
  reports/report.md
  reports/transcript.txt
  run_lab.sh
  run_lab.cmd
```

`reports/report.md` 是给人看的摘要，`reports/summary.json` 是给程序和测试复用的结构化摘要，`reports/category_revenue.svg` 是可展示图表，`data/app.sqlite3` 是可审计数据库文件，`reports/transcript.txt` 保存运行证据。

当前报表按分类收入排序：

```text
bags        revenue=91.98  units_sold=2  stock_left=16
stationery  revenue=66.93  units_sold=7  stock_left=98
gear        revenue=18.99  units_sold=1  stock_left=44
```

这个项目可以作为后续 Web 后端、CLI 报表工具或 Redis 缓存实践的起点。

## 输出怎么读

结课项目的终端输出可以按四组理解：

```text
schema_version=2
product_count=5
order_count=2
```

第一组说明数据库结构和基础写入完成。第二组是业务结果：

```text
total_revenue_cents=17790
total_stock=158
```

收入和库存都来自订单事务，不是手写常量。第三组是缓存行为：

```text
cache_hits=1
cache_misses=3
cache_invalidations=1
cache_expirations=1
```

这说明 cache-aside、显式失效和 TTL 都被实际触发。第四组是访问路径和总状态：

```text
query_plan_uses_index=True
database_cache_status=ok
```

`query_plan_uses_index=True` 说明分类查询没有停留在“建了索引”的主观判断，代码实际检查了查询计划。`database_cache_status=ok` 是最后的完成标记；它只有在前面的数据库、缓存和文件生成流程全部跑完后才会出现。

## 常见错误

1. **只实现数据库，不给可展示结果。** 学习者需要看到最终效果。
2. **只实现缓存，不说明数据库权威来源。** 缓存结果必须能重新计算。
3. **把测试、transcript、图表分散到临时目录。** 结课项目应把证据集中到 reports。
4. **一开始就引入大型框架。** 0 基础阶段先把数据流跑通，再接 Web 或 Redis。

## 练习或延伸

1. 把项目封装成 CLI：`python scripts/app.py --root demo-out`。
2. 增加一个 `/reports/category_revenue.csv`，供电子表格打开。
3. 把 TTLCache 替换为 Redis，并保留同样的缓存统计字段。
4. 把下单函数暴露成一个最小 HTTP API，复用当前事务和失效逻辑。

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
