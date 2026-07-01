---
layout: post
title: "缓存从哪里来：cache-aside、命中、未命中和 TTL"
date: 2026-07-01 19:24:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地 TTLCache 模拟 cache-aside 模式，理解报表缓存的命中、未命中和过期。"
tags: [cache, ttl, database, teaching]
---
{% raw %}
> 主题：数据库/缓存实践 / cache-aside / TTL
> 本文 lab 已验证：报表缓存产生 1 次命中、3 次未命中、1 次 TTL 过期。

数据库查询结果常被重复读取，例如首页报表、商品分类统计、用户配置。缓存的需求来自“同一个结果短时间内反复用”。cache-aside 是最容易理解的模式：应用先查缓存，缓存没有再查数据库，并把结果写回缓存。

## 学习目标

1. 理解 cache-aside 的读取流程。
2. 实现一个最小 TTL 缓存。
3. 解释 hit、miss、expiration 三个计数。
4. 知道 TTL 只能限制陈旧时间，不能保证立即一致。

## 先修知识

需要知道字典可以按 key 保存值，时间戳可以用来判断是否过期。

## 核心模型

![缓存从哪里来：cache-aside、命中、未命中和 TTL](/assets/diagrams/db-cache-cache-aside-ttl.svg)

cache-aside 的主体是应用。缓存只保存可再生结果；数据库仍是权威来源。TTL 是缓存条目的有效期，到期后下一次读取会重新查数据库。

## 可信资料的关键结论

- Redis `EXPIRE` 为 key 设置生存时间，超时后 key 会被删除；这与本地 TTLCache 的概念一致。
- cache-aside 的关键是应用控制缓存读取和回填，数据库仍保存权威状态。
- TTL 适合限制最大陈旧窗口，但数据更新后的即时一致性需要额外失效动作。

## 逐步实现

缓存条目保存值和过期时间：

```python
@dataclass
class CacheEntry:
    value: object
    expires_at: float
```

读取时先判断三种情况：不存在、过期、命中。

```python
def get(self, key):
    entry = self.entries.get(key)
    if entry is None:
        self.misses += 1
        return None
    if entry.expires_at <= self.clock():
        self.expirations += 1
        self.misses += 1
        self.entries.pop(key, None)
        return None
    self.hits += 1
    return entry.value
```

报表读取函数采用 cache-aside：

```python
def get_category_report(conn, cache):
    cached = cache.get("category_report")
    if cached is not None:
        return cached
    report = category_report_from_db(conn)
    cache.set("category_report", report)
    return report
```

lab 输出：

```text
cache_hits=1
cache_misses=3
cache_expirations=1
```

这组数字对应四次读取：第一次 miss 后写缓存，第二次 hit；订单改变后手动失效，第三次 miss；时钟推进超过 TTL，第四次 miss 且记录 expiration。

## 常见错误

1. **把缓存当成权威数据源。** 缓存结果必须能从数据库重建。
2. **只记录 hit，不记录 miss 和 expiration。** 没有计数就无法解释缓存是否有效。
3. **TTL 设得越长越好。** TTL 越长，陈旧数据窗口也越长。
4. **在教学里直接上 Redis，却没有先讲清读取流程。** 本包先用本地类拆开机制。

## 练习或延伸

1. 把 TTL 从 5 秒改成 1 秒，观察 expiration 计数。
2. 为不同分类分别缓存 key，例如 `category_report:gear`。
3. 把 TTLCache 替换成 Redis，保持 `get_category_report` 的应用流程不变。

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
