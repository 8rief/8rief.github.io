---
layout: post
title: "项目后台任务、队列与可观测性边界：worker 崩溃后任务怎么恢复"
date: 2026-03-20 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 SQLite 实现一个本地后台任务队列，证明原子 lease、visibility timeout、heartbeat、重试、dead-letter 和 JSONL 可观测性各自解决的边界。"
tags: [background-job, queue, worker, sqlite, observability, retry, dead-letter, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-background-jobs-queue-observability-boundary/README.md`](/assets/labs/project-background-jobs-queue-observability-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
前两篇文章已经把“失败后能不能再跑一次”拆成两层：本地状态更新需要锁和版本冲突；外部副作用需要幂等键、outbox 和接收端去重。实际项目里还有第三层：耗时任务通常不会在 HTTP 请求里同步完成，而是进入后台队列，由 worker 慢慢处理。

后台任务看起来简单：表里插一行，worker `while true` 查询一行，做完后标记成功。真正的问题出现在 worker 崩溃、进程被 kill、机器重启、任务暂时失败或永久失败时。如果没有明确的队列状态机和可观测日志，任务可能被两个 worker 同时处理，也可能永远卡在 running，还可能失败很多次却没人知道。

本文用一个本地 SQLite 队列表和确定性逻辑时间，构造一个最小后台任务系统：原子领取任务、visibility timeout、heartbeat 延长租约、transient retry、dead-letter queue、JSONL 事件日志和状态报告。

## 学习目标

完成本文后，你应该能够：

1. 解释为什么后台任务不能只靠 `while true` + `SELECT pending LIMIT 1`。
2. 设计 `pending`、`running`、`succeeded`、`dead` 这几种核心 job state。
3. 用一个事务把“选择任务”和“写入 lease”变成原子操作。
4. 解释 visibility timeout 和 heartbeat 的区别。
5. 区分暂时失败重试、永久失败 dead-letter、达到最大次数 dead-letter。
6. 用 JSONL 事件和 status report 判断 worker 系统现在发生了什么。

## 先修和实验边界

先修知识：SQLite 事务、上一组文章里的 retry/idempotency/outbox 思路、基本 Python 命令行。

实验边界：本文不引入 Redis、RabbitMQ、SQS、Celery 或 Kubernetes，只用 SQLite 模拟队列核心状态。这样做的目的，是用最小环境拆开后台任务最容易混淆的机制：**任务所有权、租约过期、重试时间、死亡队列、日志证据**。

## 为什么需要队列状态机

后台任务通常来自这些场景：图片压缩、报表生成、邮件发送、模型推理、Webhook 投递、日志归档、批量导入。它们共同特点是耗时、不稳定、可能失败、需要异步返回。

一个最小可维护队列至少要回答六个问题：

| 问题 | 没有明确设计时的结果 | 本文采用的机制 |
| --- | --- | --- |
| 谁拿到了任务 | 两个 worker 同时处理同一行 | 原子 lease |
| worker 崩溃后怎么办 | job 永远停在 running | visibility timeout |
| worker 还活着但任务很慢 | 任务被过早抢走 | heartbeat 延长 lease |
| 临时错误怎么办 | 要么丢任务，要么无限重试 | backoff + max_attempts |
| 参数错误怎么办 | 重试很多次仍然失败 | permanent error 进入 dead |
| 现在系统状态是什么 | 只能猜日志 | JSONL event + status report |

队列不是一张任务表那么简单。它是一个状态机，加上一组可观测事件。

## 实验产物

本地 lab 生成三份报告：

```text
reports/queue_probe.json
reports/transcript.md
reports/queue_status_report.md
```

`transcript.md` 的关键结果是：

```text
READY_JOB_CLAIMED_ONCE=yes
EXPIRED_JOB_RECLAIMED=yes
HEARTBEAT_PREVENTED_EARLY_RECLAIM=yes
TRANSIENT_RETRY_FINAL_STATE=succeeded
TRANSIENT_RETRY_ATTEMPTS=2
PERMANENT_DEAD_LETTER=yes
MAX_ATTEMPTS_DEAD_LETTER=yes
EVENT_COUNT=24
JSONL_EVENTS_VALID=yes
RUN_STATUS=ok
```

这些结果分别对应：同一任务只能被一个 worker 领取、过期租约可以被回收、heartbeat 可以阻止过早回收、暂时失败能重试成功、永久失败和耗尽次数会进入 dead-letter、事件日志能被解析。

## 队列表怎么设计

实验里的核心表是 `jobs`：

```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    state TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL,
    available_at INTEGER NOT NULL,
    lease_until INTEGER,
    locked_by TEXT,
    heartbeat_at INTEGER,
    last_error TEXT,
    result_json TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
```

几个字段要一起理解：

- `state` 表示任务当前状态：`pending`、`running`、`succeeded`、`dead`。
- `attempts` 是已经被 worker 领取过的次数，不是失败次数。
- `available_at` 表示 pending 任务何时可以再次被领取；重试 backoff 会改它。
- `lease_until` 表示 running 任务租约何时过期；过期后可被别的 worker 回收。
- `locked_by` 和 `heartbeat_at` 用于诊断当前 worker 是否还在工作。
- `last_error` 和 `result_json` 用于最终状态解释。

这张表同时承担任务状态和诊断证据。真实项目可以拆成 `jobs`、`job_attempts`、`job_events` 多张表；本文先保留一个容易复现的最小版本。

## 原子 lease：选择和占有必须在一个事务里

错误写法是先 `SELECT` 一行 pending job，再 `UPDATE` 它为 running。两个 worker 并发时可能都选到同一行。

本文的领取逻辑放进 `BEGIN IMMEDIATE` 事务：

```python
con.execute("BEGIN IMMEDIATE")
row = con.execute("""
    SELECT * FROM jobs
    WHERE attempts < max_attempts
      AND (
        (state = 'pending' AND available_at <= ?)
        OR (state = 'running' AND lease_until <= ?)
      )
    ORDER BY created_at, job_id
    LIMIT 1
""", (now, now)).fetchone()

if row is not None:
    update_to_running(row.job_id, attempts + 1, worker_id, now + lease_seconds)
con.commit()
```

实验结果：

```text
READY_JOB_CLAIMED_ONCE=yes
```

含义是：同一个逻辑时间下，worker A 领取后，worker B 再尝试领取不到同一任务。队列的第一条边界是任务所有权：一个 ready job 在一个 lease 周期内只能有一个 owner。

## visibility timeout：worker 崩溃后的恢复边界

worker 领取任务后崩溃，数据库里会留下 `state='running'`。如果永远相信 running 状态，任务会卡死；如果立即让别人拿走，慢任务会被重复处理。

visibility timeout 的折中方案是：running job 带有 `lease_until`。在租约过期前，其他 worker 不能拿；过期后，其他 worker 可以 reclaim。

实验时间线：

```text
t=0   worker-a leases job-reclaim, lease_until=10
t=5   worker-b tries, gets none
t=11  worker-b reclaims the expired running job, attempts=2
```

对应结果：

```text
EXPIRED_JOB_RECLAIMED=yes
```

这里的 reclaim 不代表原 worker 一定死了，只代表它没有在约定时间内证明自己还持有任务。生产系统里 lease 长度要根据任务耗时分布设置，太短会重复处理，太长会拖慢恢复。

## heartbeat：慢任务如何证明自己还活着

visibility timeout 只靠固定时间会误伤慢任务。worker 仍在运行，只是任务耗时超过最初 lease，此时应该定期 heartbeat，更新 `lease_until` 和 `heartbeat_at`。

实验时间线：

```text
t=0   worker-a leases job-heartbeat, lease_until=10
t=7   worker-a heartbeats, lease_until=17
t=12  worker-b tries, gets none
t=18  worker-b can reclaim after the extended lease expires
```

结果：

```text
HEARTBEAT_PREVENTED_EARLY_RECLAIM=yes
```

heartbeat 不是装饰日志。它改变任务所有权边界：只要 worker 按时续租，其他 worker 就不应该抢任务。状态报告里的 `heartbeat_at` 能帮助定位“worker 卡住”和“任务确实还在跑”的差异。

## transient retry：暂时失败怎样重新进入 pending

暂时失败包括短暂网络问题、依赖服务 503、临时锁竞争、限流等。它们可以重试，但不能立即无限重试。本文的策略是：失败后把 job 从 `running` 改回 `pending`，同时把 `available_at` 设到未来。

代码逻辑：

```python
if transient and attempts < max_attempts:
    state = 'pending'
    available_at = now + base_backoff_seconds * attempts
else:
    state = 'dead'
```

实验中，第一次执行失败并安排到 `t=6` 才能重试：

```text
t=0  attempts=1, worker-a leases
t=1  transient failure, available_at=6
t=5  worker-b tries, gets none
t=6  worker-b leases, attempts=2
t=7  worker-b completes successfully
```

结果：

```text
TRANSIENT_RETRY_FINAL_STATE=succeeded
TRANSIENT_RETRY_ATTEMPTS=2
```

这说明 retry 的本质是一次新的调度：任务重新进入 pending，同时携带下一次可用时间和 attempts 计数。

## dead-letter：永久失败和耗尽次数要显式收尾

永久失败包括 payload 格式错误、权限错误、不可恢复的业务校验失败。继续重试只会制造噪声。另一类情况是 transient error 反复出现，超过 `max_attempts` 后也应该停止自动重试。

实验包含两条 dead-letter 路径：

```text
PERMANENT_DEAD_LETTER=yes
MAX_ATTEMPTS_DEAD_LETTER=yes
```

状态报告中 dead-letter 场景最终是：

```text
pending=0, running=0, succeeded=0, dead=2
```

`dead` 不是“丢掉”。它是一个可审计终态：保留 `last_error`、`attempts`、payload 和时间字段，后续可以人工修复、重新入队或确认丢弃。

## JSONL 事件：队列需要可观测性

每个关键状态变化都写一行 JSONL：

```json
{"event":"job_enqueued","job_id":"job-exclusive","kind":"demo","max_attempts":3,"now":0,"schema_version":1}
{"attempts":1,"event":"job_leased","job_id":"job-exclusive","lease_until":10,"now":0,"reclaimed":false,"schema_version":1,"worker_id":"worker-a"}
{"event":"job_succeeded","job_id":"job-status","now":1,"schema_version":1,"worker_id":"worker-a"}
```

实验验证：

```text
EVENT_COUNT=24
JSONL_EVENTS_VALID=yes
```

这些事件服务于三个问题：

1. 单个任务为什么进入当前状态？
2. worker 是否有持续 heartbeat？
3. 系统现在积压在哪里：ready、delayed、running expired、dead？

只看最终表状态很难定位历史路径；只看普通文本日志又难以统计。JSONL 是一个低成本折中：人能读，脚本也能聚合。

## 怎么复跑

进入实验包后运行：

```bash
./run_lab.sh
```

预期输出包括：

```text
Ran 7 tests
OK
READY_JOB_CLAIMED_ONCE=yes
EXPIRED_JOB_RECLAIMED=yes
HEARTBEAT_PREVENTED_EARLY_RECLAIM=yes
TRANSIENT_RETRY_FINAL_STATE=succeeded
PERMANENT_DEAD_LETTER=yes
RUN_STATUS=ok
```

如果只想看报告：

```bash
python3 scripts/queue_probe.py
python3 -m json.tool reports/queue_probe.json | sed -n '1,160p'
cat reports/queue_status_report.md
```

## 设计选择表

| 设计点 | 解决的问题 | 边界 |
| --- | --- | --- |
| 原子 lease | 避免同一 ready job 被两个 worker 同时拿走 | handler 本身仍需幂等 |
| visibility timeout | worker 崩溃后任务能被回收 | lease 太短会导致重复处理 |
| heartbeat | 慢任务续租，避免过早回收 | worker 卡死但仍 heartbeat 会延迟恢复 |
| available_at | transient failure 延迟重试 | backoff 策略需要按系统压力调整 |
| max_attempts | 防止无限重试 | 次数耗尽后需要人工或自动补偿流程 |
| dead-letter | 保留不可自动恢复的任务 | dead 任务需要明确处理责任 |
| JSONL events | 状态变化可审计、可聚合 | 生产系统还需要指标、trace、告警 |

## 常见错误

1. **只用 `SELECT pending LIMIT 1`，再单独 `UPDATE`。** 选择和占有不在一个事务里，会产生重复领取。
2. **没有 visibility timeout。** worker 崩溃后 running job 永远卡住。
3. **visibility timeout 太短且没有 heartbeat。** 长任务会被别的 worker 抢走，产生重复处理。
4. **所有失败立即重试。** 短时间内会打爆依赖服务，也看不出永久失败。
5. **没有 dead-letter。** 失败任务混在 pending 里反复出现，系统看似忙碌却没有进展。
6. **日志只有自然语言。** 出问题时无法按 job_id、worker_id、state、attempts 做聚合。
7. **handler 不幂等。** 即使队列 lease 设计正确，过期 reclaim 后仍可能重复执行外部副作用。

## 练习和扩展

1. 给 `jobs` 增加 `priority` 字段，验证高优先级任务先被 lease。
2. 把 `job_events` 从 JSONL 文件改成 SQLite 表，写一个按 `job_id` 输出时间线的 CLI。
3. 给 heartbeat 增加 worker 进程 pid 或 hostname，生成 worker 健康报告。
4. 实现指数 backoff：`available_at = now + min(max_delay, base * 2 ** (attempts - 1))`。
5. 给 dead-letter 增加 `requeue` 命令，但要求必须写入一条人工原因。
6. 在 handler 里复用上一篇文章的 idempotency/event ID 机制，证明 lease 过期后的重复处理不会重复外部副作用。

## 验收清单

一个可发布的后台任务系统至少要能回答：

- worker 领取任务是否是原子操作？
- running job 在 worker 崩溃后多久可以恢复？
- 长任务如何续租？
- 暂时失败如何安排下一次执行？
- 永久失败和耗尽次数如何进入 dead-letter？
- 每次状态变化是否有结构化事件？
- 状态报告能否区分 ready、delayed、running expired、dead？
- handler 是否具备幂等或补偿设计？

## 参考资料

- Python sqlite3：<https://docs.python.org/3/library/sqlite3.html>
- SQLite transactions：<https://www.sqlite.org/lang_transaction.html>
- SQLite isolation：<https://www.sqlite.org/isolation.html>
- Python logging：<https://docs.python.org/3/library/logging.html>
- Amazon SQS visibility timeout：<https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html>
- RabbitMQ Work Queues tutorial：<https://www.rabbitmq.com/tutorials/tutorial-two-python>
- Celery task retry：<https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying>

{% endraw %}
