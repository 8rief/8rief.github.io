---
layout: post
title: "项目重试、幂等键与副作用边界：为什么失败后不能只再跑一次"
date: 2026-03-19 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用本地 SQLite 和模拟支付网关复现 crash-after-effect：朴素 retry 会重复扣款；幂等键、事务 outbox、稳定 event_id 和接收端去重各自解决不同边界。"
tags: [retry, idempotency, outbox, sqlite, side-effect, reliability, python, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-retry-idempotency-side-effect-boundary/README.md`](/assets/labs/project-retry-idempotency-side-effect-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
上一篇文章讨论的是同一个本地 JSON 状态被多个进程同时更新时，为什么原子替换仍然会丢更新。那类问题发生在本地状态内部，可以用完整临界区、版本检查和冲突重试处理。

这一篇把边界向外推一步：程序已经调用了外部系统，例如支付网关、邮件服务、短信服务、任务队列或第三方 API，然后自己在记录本地状态前崩溃。此时日志里只看到“请求失败”，直接重跑看起来很自然，但外部副作用可能已经发生。本文用本地 SQLite 和一个模拟支付网关复现这个问题，并逐层解释幂等键、事务 outbox、稳定 side-effect event ID、接收端去重和重试分类分别解决哪一段风险。

## 学习目标

完成本文后，你应该能够：

1. 解释为什么 crash-after-effect 后的重试会把一次业务请求变成两次外部副作用。
2. 用 idempotency key 让同一个请求重放同一份响应，并拒绝同一个 key 携带不同 payload。
3. 理解 transactional outbox 解决的是本地业务状态和待发送消息的原子提交，不直接等于外部副作用只发生一次。
4. 解释 dispatcher 在 send 之后、mark sent 之前崩溃时，为什么还需要稳定 event ID 和接收端去重。
5. 区分 transient error 和 permanent error：前者可有限重试，后者应停止并返回明确错误。

## 先修和实验边界

先修只需要 Python 3、SQLite 和基本命令行。本文的外部支付网关由另一个 SQLite 数据库模拟：应用数据库和网关数据库是两个独立连接，故意不做分布式事务。这样可以在本机复现外部副作用边界，同时避免真实支付、邮件或网络服务。

实验不会证明任意分布式系统的 exactly-once。它只证明这些局部事实：

- 一个请求入口可以用 idempotency key 去重。
- 本地数据库可以把业务状态和 outbox 事件放进同一个事务。
- 外部发送已经离开本地事务后，仍然可能出现重复 delivery。
- 接收端用稳定 event ID 去重后，重复 delivery 可以只应用一次。

## 为什么需要把重试和副作用分开

很多脚本和服务都会写出这样的逻辑：调用外部系统，失败就再跑一次。这个习惯在纯读请求、纯本地临时文件、可覆盖输出上通常可接受；一旦操作具有外部副作用，失败的含义就变复杂了。

一次失败可能落在四个不同位置：

| 位置 | 外部副作用 | 本地记录 | 直接重试的风险 |
| --- | --- | --- | --- |
| 调用前失败 | 未发生 | 未记录 | 通常安全，但仍要有限重试 |
| 调用中超时 | 不确定 | 未记录 | 可能已经发生，不能当作未发生 |
| 调用后、本地记录前崩溃 | 已发生 | 未记录 | 重试会重复副作用 |
| 本地记录后响应丢失 | 已发生 | 已记录 | 客户端重试需要返回同一结果 |

本文关注第三和第四种位置。核心问题是：**重试控制的是再次执行，幂等控制的是再次执行的可观察效果，副作用边界控制的是效果发生在哪个系统里。**

## 实验产物

本地 lab 生成三份报告：

```text
reports/retry_idempotency_probe.json
reports/transcript.md
reports/side_effect_summary.md
```

`transcript.md` 的关键结果是：

```text
NAIVE_EXTERNAL_EFFECTS=2
NAIVE_DUPLICATE_CHARGE=yes
REQUEST_REPLAY_SAME_RESPONSE=yes
REQUEST_CONFLICT_RC=74
OUTBOX_ONLY_EXTERNAL_EFFECTS=2
STABLE_EVENT_APPLIED_EFFECTS=1
STABLE_EVENT_DELIVERY_ATTEMPTS=2
TRANSIENT_ATTEMPTS=2
PERMANENT_ATTEMPTS=1
RUN_STATUS=ok
```

这些数字对应五组对照实验：朴素重试、请求幂等、outbox-only、稳定 event ID + 接收端去重、重试分类。

## 第一组：朴素重试怎样重复外部副作用

朴素实现先调用网关，再写本地 receipt：

```python
def naive_charge_request(app_db, gateway_db, request_id, attempt_id, amount_cents, crash_after_effect):
    apply_non_idempotent_effect(
        gateway_db,
        delivery_id=f"naive-{request_id}-{attempt_id}",
        logical_key=request_id,
        amount_cents=amount_cents,
    )
    if crash_after_effect:
        raise CrashAfterSideEffect()
    insert_local_receipt(app_db, request_id, amount_cents)
```

第一次执行在网关生效后崩溃，本地 receipt 没写入。调用方只看到失败，于是用同一个业务请求再试一次。第二次又调用网关，然后写入本地 receipt。

实验结果：

```text
NAIVE_EXTERNAL_EFFECTS=2
NAIVE_DUPLICATE_CHARGE=yes
```

本地应用只有一条 receipt，网关却有两条 non-idempotent effects。这是最危险的错觉：**应用状态看起来只有一次，外部系统已经执行两次。**

用时间线表示：

```text
attempt 1: send gateway charge -> gateway applied -> app crashes before receipt
attempt 2: send gateway charge -> gateway applied again -> app writes receipt
```

这里不能靠“再跑一次”修复，因为重跑本身就是第二次副作用的来源。

## 第二组：请求幂等键解决客户端重试入口

idempotency key 是客户端为一次逻辑请求生成的唯一 key。服务端收到请求后，把 key、请求指纹和响应写入本地表。之后同一个 key 带着同一个 payload 再来，服务端直接返回第一次响应；同一个 key 带着不同 payload 再来，服务端返回冲突。

本实验用三张应用表：

```sql
CREATE TABLE idempotency_requests (
    idempotency_key TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    response_json TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL
);

CREATE TABLE outbox (
    event_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    sent_at INTEGER
);
```

请求处理的关键步骤是一个数据库事务：

```python
fingerprint = request_fingerprint(customer_id, amount_cents)
row = select_idempotency_key(idempotency_key)
if row exists and row.fingerprint == fingerprint:
    return stored_response
if row exists and row.fingerprint != fingerprint:
    raise IdempotencyConflict()

insert_order(order_id, idempotency_key, customer_id, amount_cents)
insert_outbox(event_id, idempotency_key, "charge.requested", payload_json)
insert_idempotency_record(idempotency_key, fingerprint, response_json)
commit()
```

实验里，同一个 key 和同一个 payload 请求两次，结果是：

```text
REQUEST_REPLAY_SAME_RESPONSE=yes
```

同一个 key 改金额再请求，结果是：

```text
REQUEST_CONFLICT_RC=74
```

这个冲突很重要。没有 payload fingerprint，同一个 key 被误用于另一笔支付时，服务端可能错误复用旧响应。幂等键必须绑定“这一次请求到底是什么”。

## 第三组：outbox 解决本地事务，不覆盖发送边界

请求入口已经安全后，下一步是发送外部副作用。如果在处理请求的事务里直接调用网关，仍然会遇到 crash-after-effect。常见工程做法是 transactional outbox：请求事务只写本地 `orders` 和 `outbox`，另一个 dispatcher 读取 outbox 再发送。

这样做有两个直接好处：

1. 本地订单和“待发送事件”要么一起提交，要么一起回滚。
2. 客户端重试同一个 idempotency key 时，不会重复插入 outbox 事件。

但 outbox 自身只覆盖本地数据库边界。dispatcher 仍然可能在这个位置崩溃：

```text
read outbox event -> send gateway -> gateway applied -> crash before UPDATE outbox SET sent_at = 1
```

如果下次 dispatcher 用新的 delivery ID 再发给一个 non-idempotent receiver，网关会应用两次。实验结果正是这样：

```text
OUTBOX_ONLY_EXTERNAL_EFFECTS=2
```

所以 outbox 是必要层，但不是最终层。它把“业务状态与待发送消息”绑定在本地事务里；外部系统是否重复应用，还要看发送协议和接收端去重。

## 第四组：稳定 event ID 与接收端去重

稳定 event ID 的规则是：同一个 idempotency key、同一个 request fingerprint、同一种 side effect，生成同一个 `event_id`。dispatcher 每次重发都携带这个 event ID。接收端以 `event_id` 建唯一约束：第一次看到时应用副作用；后续重复 delivery 只记录一次重复投递，不再次应用。

接收端表结构如下：

```sql
CREATE TABLE idempotent_effects (
    event_id TEXT PRIMARY KEY,
    payload_hash TEXT NOT NULL,
    amount_cents INTEGER NOT NULL
);

CREATE TABLE idempotent_deliveries (
    delivery_no INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    applied_new INTEGER NOT NULL
);
```

实验仍然让 dispatcher 在发送后崩溃一次，然后重新发送同一个 outbox event。结果是：

```text
STABLE_EVENT_APPLIED_EFFECTS=1
STABLE_EVENT_DELIVERY_ATTEMPTS=2
```

这两个数字要一起读：delivery 确实发生了两次，所以网络层面没有 exactly-once；接收端应用效果只有一次，所以业务副作用被控制住了。工程上常说的“幂等发送”通常就是这个组合：稳定 key + 接收端存储 + payload fingerprint + 明确重复响应。

## 第五组：重试策略必须区分错误类型

重试策略还有一层容易被忽略：并非所有错误都值得重试。网络暂时不可用、短暂锁竞争、503、连接重置这类错误可以有限重试；请求参数错误、金额非法、认证失败、payload conflict 这类错误重复执行只会制造噪声。

实验中的重试器只重试 `TransientError`，遇到 `PermanentError` 立即停止：

```python
def retry_with_policy(operation, max_attempts=3):
    attempts = 0
    while True:
        attempts += 1
        try:
            return operation(), attempts
        except PermanentError:
            raise
        except TransientError:
            if attempts >= max_attempts:
                raise
```

结果：

```text
TRANSIENT_ATTEMPTS=2
PERMANENT_ATTEMPTS=1
```

这说明重试策略至少需要三件事：最大次数、退避节奏和错误分类。没有错误分类的 retry loop 会把永久失败放大成重复负载。

## 怎么复跑

进入实验包后运行：

```bash
./run_lab.sh
```

预期输出包括：

```text
Ran 5 tests
OK
NAIVE_EXTERNAL_EFFECTS=2
REQUEST_CONFLICT_RC=74
STABLE_EVENT_APPLIED_EFFECTS=1
PERMANENT_ATTEMPTS=1
RUN_STATUS=ok
```

如果只想看报告，可以运行：

```bash
python3 scripts/retry_probe.py
python3 -m json.tool reports/retry_idempotency_probe.json | sed -n '1,120p'
```

`retry_idempotency_probe.json` 中每个 scenario 都保留应用数据库和网关数据库的计数，便于对照“本地看到什么”和“外部实际发生什么”。

## 设计选择表

| 设计点 | 解决的问题 | 没解决的问题 |
| --- | --- | --- |
| idempotency key | 客户端超时或响应丢失后，可以重放同一请求结果 | dispatcher 发送后崩溃导致的重复 delivery |
| request fingerprint | 防止同一个 key 被不同 payload 复用 | 外部 receiver 是否会去重 |
| transactional outbox | 本地业务状态和待发送事件原子提交 | send 之后、mark sent 之前的崩溃窗口 |
| stable event ID | 重复发送时给 receiver 同一识别符 | receiver 没有持久化去重表时仍可能重复应用 |
| receiver dedupe | 多次 delivery 只应用一次业务效果 | 去重表过期策略、payload 冲突处理仍需设计 |
| retry classification | 暂时错误有限重试，永久错误停止 | 错误分类错误会导致过早失败或重复负载 |

## 常见错误

1. **只在客户端生成 UUID，没有服务端表。** key 必须落到服务端持久化存储中，并绑定请求指纹和响应。
2. **只比较 idempotency key，不比较 payload。** 同一个 key 携带不同金额、客户或参数时，应返回冲突。
3. **把 outbox 当成 exactly-once。** outbox 保证本地事务一致，不保证外部系统只应用一次。
4. **mark sent 早于 send。** 这样崩溃会丢消息；通常宁可重复发送，也不能静默丢副作用请求。
5. **没有去重过期策略。** 生产系统需要定义 key 保留多久、过期后如何处理重放。
6. **所有异常统一 retry。** permanent error 被重试会扩大负载，并掩盖真实参数或权限问题。

## 练习和扩展

1. 把 `idempotency_requests` 增加 `status` 字段，模拟 `in_progress` 请求再次到达时返回 409 或等待。
2. 给接收端重复 event ID 但不同 payload 的情况增加测试，要求返回冲突而不是静默忽略。
3. 给 retry loop 加指数退避和 jitter，把每次 attempt 记录到 JSONL 日志。
4. 给 outbox dispatcher 增加批处理，每批最多发送 10 条，并保证单条失败不会阻塞后续永久失败之外的事件。
5. 设计一个 key 过期策略：例如 24 小时后删除 idempotency record，同时说明过期后客户端重试的业务含义。

## 验收清单

一篇关于 retry/idempotency 的实现，至少要能回答：

- 同一个 idempotency key 和同一个 payload 是否返回同一响应？
- 同一个 key 和不同 payload 是否明确冲突？
- 业务状态和 outbox 是否处于同一个事务？
- dispatcher 在 send 之后崩溃时，下一次发送是否携带同一个 event ID？
- receiver 是否持久化 event ID 和 payload hash？
- transient/permanent 错误是否分开处理？
- 重试次数、退避和最终失败响应是否可观测？

## 参考资料

- RFC 9110：HTTP 方法幂等性语义：<https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods>
- IETF HTTPAPI Idempotency-Key draft：<https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/>
- Stripe idempotent requests：<https://docs.stripe.com/api/idempotent_requests>
- SQLite transactions：<https://www.sqlite.org/lang_transaction.html>
- SQLite conflict resolution：<https://www.sqlite.org/lang_conflict.html>
- Python sqlite3：<https://docs.python.org/3/library/sqlite3.html>
- Amazon Builders' Library: Making retries safe with idempotent APIs：<https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/>

{% endraw %}
