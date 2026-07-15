---
layout: post
title: "数据库迁移与 schema 演化：expand、backfill、约束和 rollback 怎么做成证据"
date: 2026-03-23 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个 SQLite 用户表，把 schema_migrations、checksum、user_version、expand/backfill/constraint、兼容查询、rollback 和失败 preflight 跑成证据。"
tags: [sqlite, database, migration, schema-evolution, rollback, data-repair, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-database-migration-schema-evolution/README.md`](/assets/labs/project-database-migration-schema-evolution/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

前面的文章已经讲过 SQL 基础、数据库缓存、原子写入、HTTP/API 契约和测试金字塔。真实项目继续向前走时，会遇到一个更危险的问题：数据库结构变了，旧代码、旧数据和新约束怎样同时活下来。

很多人第一次写数据库迁移时，会把它理解成“执行几条 `ALTER TABLE`”。这只是最表层。迁移真正要解决的是状态演化：线上已经有数据，旧版本代码可能还在运行，新版本代码需要新字段，约束迟早要收紧，失败时还要知道停在了哪里。

这篇文章用 SQLite 做一个用户表迁移实验：

```text
v1  users(id, email, full_name)
v2  expand: add display_name, then backfill from full_name
v3  repair + constraint: add email_normalized, backfill lower(trim(email)), then add unique index
```

## 为什么需要迁移证据

数据库迁移用来解决一个核心问题：schema、数据和代码发布节奏不同步。代码可以回滚到旧版本，数据库里已经写入的数据却不能像 Git commit 一样随便撤销。一个可发布迁移必须回答：哪些版本已经执行？执行内容有没有被改过？旧查询还能不能工作？新约束加之前数据是否满足条件？失败后数据库停在哪个版本？

本 lab 把这些问题变成可检查输出：

```text
SCHEMA_VERSION=3
USER_VERSION=3
MIGRATIONS_APPLIED=3
DISPLAY_NAME_BACKFILLED=3
NORMALIZED_EMAILS_VALID=yes
UNIQUE_INDEX_PRESENT=yes
OLD_QUERY_COMPATIBLE=yes
REAPPLY_NOOP=yes
ROLLBACK_TO_2_REMOVED_EMAIL_NORMALIZED=yes
DUPLICATE_PREFLIGHT_FAILED=yes
DUPLICATE_STAYED_AT_VERSION_2=yes
MIGRATION_003_ABSENT_AFTER_FAILURE=yes
RUN_STATUS=ok
```

这些 marker 的意思是：迁移到 v3 成功，旧查询仍然能读 `id,email,full_name`，重复运行迁移不会再次改库，回滚到 v2 会移除 v3 的列和索引，重复 email 的坏数据会在进入 v3 前被拦住，并且失败后不会把迁移表写成已完成。

## 先运行实验

如果你已经克隆过本站仓库：

```bash
cd ~/8rief.github.io
git pull --ff-only
cd assets/labs/project-database-migration-schema-evolution
bash run_lab.sh
```

如果还没有克隆：

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/project-database-migration-schema-evolution
bash run_lab.sh
```

脚本会做五件事：

1. 清理本地 `reports/` 和 Python cache。
2. 编译检查 `src/migration_demo.py` 和 `scripts/migration_probe.py`。
3. 运行 5 个 `unittest`，覆盖幂等迁移、旧查询兼容、rollback、重复数据 preflight 和 checksum mismatch。
4. 运行 probe，生成迁移、回滚和失败场景的报告。
5. 检查稳定 marker，确认输出不是上一轮运行遗留物。

## 实验目录里有什么

```text
project-database-migration-schema-evolution/
├── README.md
├── fixtures/
│   ├── users_v1.csv
│   └── users_duplicate_email.csv
├── run_lab.sh
├── scripts/
│   └── migration_probe.py
├── src/
│   └── migration_demo.py
└── tests/
    └── test_migration_demo.py
```

`fixtures/users_v1.csv` 是正常旧数据：

```csv
email,full_name
 Alice@Example.COM ,Alice Zhang
bob@example.com,Bob Lee
carol@example.com,Carol Ng
```

`fixtures/users_duplicate_email.csv` 是坏数据：

```csv
email,full_name
BOB@example.com,Bob One
 bob@example.com ,Bob Two
alice@example.com,Alice One
```

这份坏数据用来证明：如果 v3 想加 `lower(trim(email))` 的唯一索引，迁移必须先发现重复，而不是建索引失败后留下半截状态。

## 机制一：schema_migrations 表记录事实

实验先创建迁移表：

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
```

这张表回答三个问题：

1. 当前已经执行到哪个版本。
2. 每个版本的名字是什么。
3. 当初执行的迁移内容摘要是什么。

checksum 的意义是防止“已经执行过的迁移文件后来被改了”。实验里 checksum 来自版本号、迁移名和 statement id：

```python
@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    statement_id: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(
            f"{self.version}:{self.name}:{self.statement_id}".encode("utf-8")
        ).hexdigest()
```

真实项目可以把 SQL 文件内容、迁移脚本内容或构建产物 hash 进去。关键是：执行过的迁移不能被无声替换。

## 机制二：PRAGMA user_version 是数据库自己的版本标记

SQLite 有一个很轻量的版本位置：

```sql
PRAGMA user_version = 3;
```

本 lab 同时维护 `schema_migrations` 和 `PRAGMA user_version`。前者记录每一步迁移，后者让工具或程序快速知道当前库的整体版本。probe 输出里两个值都应该是 3：

```text
SCHEMA_VERSION=3
USER_VERSION=3
```

如果它们不一致，说明迁移记录和数据库元信息至少有一个环节出了问题。

## 机制三：每个迁移都要独立事务

迁移 runner 对每一步执行：

```python
def run_transaction(conn, func):
    try:
        conn.execute("BEGIN")
        func()
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
```

这不是形式。v3 迁移会先 preflight 重复 email，再加列、回填、建唯一索引。任何一步失败，都不能把 `schema_migrations` 写成 v3 已完成。坏数据 probe 证明了这一点：

```text
DUPLICATE_PREFLIGHT_FAILED=yes
DUPLICATE_STAYED_AT_VERSION_2=yes
MIGRATION_003_ABSENT_AFTER_FAILURE=yes
```

这里的语义是：v1 和 v2 已经完成，v3 因为重复 normalized email 被拒绝，数据库仍停在 v2，迁移表没有 v3 记录。

## 机制四：expand 先兼容旧代码

v2 做的是 expand：

```sql
ALTER TABLE users ADD COLUMN display_name TEXT;
UPDATE users SET display_name = full_name WHERE display_name IS NULL;
```

为什么先允许 `display_name` 为空，然后再 backfill？因为上线过程中旧代码可能还只写 `email` 和 `full_name`。如果一上来就加一个没有默认值的 `NOT NULL` 字段，旧代码写入会失败。

expand 阶段的目标是让新旧代码都能运行：

- 旧代码继续读写 `id,email,full_name`。
- 新代码可以开始读 `display_name`。
- backfill 让旧数据也拥有新字段值。

实验用 `OLD_QUERY_COMPATIBLE=yes` 固定这个边界：

```python
rows = conn.execute("SELECT id, email, full_name FROM users ORDER BY id").fetchall()
```

只要这个查询仍然可用，旧读路径就没有被 v2/v3 破坏。

## 机制五：backfill 和 constraint 分开

v3 的目标是让 email 比较不再受大小写和空格影响：

```sql
ALTER TABLE users ADD COLUMN email_normalized TEXT;
UPDATE users SET email_normalized = lower(trim(email));
CREATE UNIQUE INDEX idx_users_email_normalized ON users(email_normalized);
```

注意顺序：

1. 先检查旧数据里有没有重复 normalized email。
2. 再加列。
3. 再 backfill。
4. 最后建唯一索引。

如果把唯一索引放在最前面，失败时你只知道“建索引失败”，不知道是哪几条数据冲突。实验里的 preflight 查询会直接找出问题：

```sql
SELECT lower(trim(email)) AS email_normalized, count(*) AS count
FROM users
GROUP BY lower(trim(email))
HAVING count(*) > 1;
```

这就是数据修复脚本的作用：先把旧数据修成满足新约束的状态，再把约束加上去。

## 机制六：rollback 是边界，不是魔法

实验支持从 v3 回滚到 v2：

```text
ROLLBACK_TO_2_REMOVED_EMAIL_NORMALIZED=yes
ROLLBACK_TO_2_KEPT_DISPLAY_NAME=yes
ROLLBACK_TO_2_REMOVED_UNIQUE_INDEX=yes
```

v3 回滚做两件事：

1. 删除 `idx_users_email_normalized`。
2. 重建 `users` 表，只保留 `id,email,full_name,display_name`。

SQLite 支持的 `ALTER TABLE` 能力有限，所以 lab 用重建表的方式表达列删除：

```python
ALTER TABLE users RENAME TO users_old;
CREATE TABLE users (...);
INSERT INTO users (...) SELECT ... FROM users_old;
DROP TABLE users_old;
```

真实生产环境里，rollback 需要更谨慎。删除列、删除索引、数据格式转换和外部副作用都可能不可逆。工程上常见做法是优先保证代码可回滚，数据库迁移尽量走兼容式 expand/contract，而不是指望所有迁移都有完美 down 脚本。

## 机制七：重复运行必须是 no-op

迁移脚本经常会被 CI、本地、部署系统重复调用。已经执行过的版本必须跳过：

```python
if migration.version in applied_migrations(conn):
    continue
```

probe 里固定了这个结果：

```text
REAPPLY_NOOP=yes
```

这条检查能防止另一类事故：同一个迁移重复插入数据、重复创建索引、重复 backfill 造成不可预测状态。

## 测试应该覆盖哪些迁移边界

这个 lab 的 5 个测试分别覆盖：

1. 迁移到最新版本后，重复迁移是 no-op，旧查询仍然工作。
2. 坏数据触发 duplicate preflight，v3 不会写入迁移表。
3. rollback 到 v2 会移除 v3 列和索引，但保留 v2 的 `display_name`。
4. 已执行迁移的 checksum 被篡改后，后续迁移会停止。
5. dump 出来的 schema 里能看到迁移表和唯一索引。

这些测试比只检查“脚本执行成功”更有价值，因为它们固定了迁移系统真正要承诺的状态变化。

## 常见错误

1. **直接在生产库上试 `ALTER TABLE`。** 迁移必须先在复制数据或本地 fixture 上跑出证据。
2. **新字段一开始就设成强约束。** 旧代码还在写旧字段时，强约束会把发布切成硬断点。
3. **backfill 和约束混在一起。** 出错时不知道是数据坏、脚本坏，还是约束设计错。
4. **没有迁移表或 checksum。** 无法判断某个环境执行到了哪一步，也无法发现迁移脚本被改过。
5. **失败后仍写迁移成功。** 迁移表必须和实际 schema/data 状态一致。
6. **rollback 讲得太轻松。** 删除数据、压缩字段、合并表、外部副作用通常不能简单回滚。
7. **测试只看版本号。** 版本号正确不代表旧查询兼容、索引存在、数据已 backfill。

## 练习

1. 给 `users` 增加 `created_at` 字段。先用 expand 方式添加 nullable/default，再写 backfill 检查。
2. 把 `full_name` 拆成 `first_name` 和 `last_name`。写一个 preflight，找出无法拆分的数据。
3. 给 `email_normalized` 增加查询路径，证明旧查询和新查询可以并存一段时间。
4. 修改 fixture，让 duplicate preflight 失败；写一份数据修复脚本，把重复 email 修成可迁移状态。
5. 给 migration runner 加一个 `--dry-run`，只输出待执行迁移和 preflight 结果，不修改数据库。

## 参考资料

- SQLite 文档：[ALTER TABLE](https://www.sqlite.org/lang_altertable.html)
- SQLite 文档：[PRAGMA user_version](https://www.sqlite.org/pragma.html#pragma_user_version)
- SQLite 文档：[CREATE INDEX](https://www.sqlite.org/lang_createindex.html)
- SQLite 文档：[Transactions](https://www.sqlite.org/lang_transaction.html)
- Python 文档：[sqlite3](https://docs.python.org/3/library/sqlite3.html)

{% endraw %}
