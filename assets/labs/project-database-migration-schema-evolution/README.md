# project-database-migration-schema-evolution

配套文章：**数据库迁移与 schema 演化：expand、backfill、约束和 rollback 怎么做成证据**。

这个 lab 用 Python 标准库和 SQLite 演示实际开发里最容易出错的迁移边界：迁移表、checksum、`PRAGMA user_version`、expand/backfill/constraint 三阶段、旧查询兼容、回滚到上一版本、重复数据 preflight 和失败后不污染新版本。

## 运行

```bash
cd ~/8rief.github.io/assets/labs/project-database-migration-schema-evolution
bash run_lab.sh
```

成功时会看到：

```text
SCHEMA_VERSION=3
USER_VERSION=3
MIGRATIONS_APPLIED=3
USERS=3
DISPLAY_NAME_BACKFILLED=3
NORMALIZED_EMAILS_VALID=yes
UNIQUE_INDEX_PRESENT=yes
OLD_QUERY_COMPATIBLE=yes
REAPPLY_NOOP=yes
ROLLBACK_TO_2_REMOVED_EMAIL_NORMALIZED=yes
DUPLICATE_PREFLIGHT_FAILED=yes
DUPLICATE_STAYED_AT_VERSION_2=yes
RUN_STATUS=ok
database_migration_lab_status=ok
```

## 生成文件

- `reports/migration_probe.json`：机器可读的迁移、回滚和失败 preflight 摘要。
- `reports/migration_report.md`：给学习者阅读的报告。
- `reports/schema_after_v3.sql`：迁移到 v3 后的实际 schema。
- `reports/*.db`：本地实验数据库。

这些都是本地运行产物，不提交到公开仓库。
