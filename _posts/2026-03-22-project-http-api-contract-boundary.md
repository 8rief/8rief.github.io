---
layout: post
title: "项目 HTTP/API 契约第一课：method、status、JSON 和幂等边界怎么定"
date: 2026-03-22 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个本地 task API，把 method、path、status code、JSON body、错误结构、Location、request id 和 Idempotency-Key 跑成可检查契约。"
tags: [http, api, json, status-code, idempotency, backend, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-http-api-contract-boundary/README.md`](/assets/labs/project-http-api-contract-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

前面的项目文章已经讲过配置、日志、原子写入、并发写、重试、队列、服务生命周期、运行时指标和测试金字塔。现在可以进入另一个每天都会遇到的边界：一个 HTTP API 到底应该承诺什么。

很多初学者写后端接口时会先想框架：用 Flask、FastAPI、Spring Boot、Gin、Axum，或者直接写 serverless function。框架当然重要，但 API 契约先于框架存在。客户端真正依赖的是 method、path、status code、header、JSON 请求体、JSON 响应体、错误结构和重复请求行为。只要这些没有固定，换框架、换语言、加缓存、加队列、加前端都会变成猜测。

这篇文章用一个本地 task API 说明最小契约：

```text
GET  /health          服务是否可用
GET  /tasks           列出任务
POST /tasks           创建任务，成功返回 201 和 Location
GET  /tasks/{id}      读取一个任务，不存在返回 404
PUT  /tasks/{id}      替换任务状态，重复相同请求不再次改变版本
```

## 为什么需要 API 契约

API 契约用来解决一个核心问题：调用方和服务方必须对同一件事有相同理解。`POST /tasks` 成功后返回什么状态？新资源地址在哪里？标题为空时是 `400` 还是 `500`？客户端重试创建请求时会不会重复创建两条任务？这些问题如果只写在口头约定里，测试、前端、文档和监控都会各自解释。

一个可运行的 API 契约至少包含七类证据：

| 契约项 | 要回答的问题 | 本 lab 的例子 |
| --- | --- | --- |
| method | 这个动作是读取、创建、替换还是局部修改 | `GET` 读，`POST` 创建，`PUT` 替换 |
| path | 资源是什么，集合和单个资源怎样区分 | `/tasks` 与 `/tasks/tsk-001` |
| status code | 客户端先看哪一类结果 | `201`、`400`、`404`、`409` |
| headers | body 之外还承诺什么元数据 | `Location`、`X-Request-Id`、`Idempotency-Replayed` |
| request JSON | 客户端应该提交哪些字段 | `{"title":"...","done":false}` |
| response JSON | 客户端可以读取哪些字段 | `task.id`、`task.version`、`changed` |
| error JSON | 失败时怎么定位和展示 | `error.code`、`error.message`、`error.request_id` |

## 先运行实验

如果你已经克隆过本站仓库：

```bash
cd ~/8rief.github.io
git pull --ff-only
cd assets/labs/project-http-api-contract-boundary
bash run_lab.sh
```

如果还没有克隆：

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/project-http-api-contract-boundary
bash run_lab.sh
```

这几条命令做了四件事：

1. 用 `py_compile` 检查 Python 源码语法。
2. 用 `unittest` 启动本地 HTTP server，验证 API 契约。
3. 用 probe 发送一组真实 HTTP 请求，记录请求/响应观察结果。
4. 生成 `reports/api_contract_probe.json`、`reports/api_events.jsonl` 和 `reports/api_contract_report.md`。

成功时会看到：

```text
unit/integration tests
Ran 5 tests in ...s
OK

contract probe
HEALTH_STATUS=200
LIST_STATUS=200
VALIDATION_STATUS=400
VALIDATION_ERROR_CODE=validation_error
CREATE_STATUS=201
CREATED_LOCATION=/tasks/tsk-001
CREATED_TASK_ID=tsk-001
REPLAY_STATUS=201
REPLAY_SAME_ID=yes
REPLAY_HEADER=yes
CONFLICT_STATUS=409
CONFLICT_ERROR_CODE=idempotency_conflict
GET_STATUS=200
PUT_STATUS=200
PUT_CHANGED=yes
PUT_REPEAT_CHANGED=no
NOT_FOUND_STATUS=404
NOT_FOUND_ERROR_CODE=not_found
REQUEST_IDS_PRESENT=yes
RUN_STATUS=ok
```

这段输出可以这样读：

- `CREATE_STATUS=201` 和 `CREATED_LOCATION=/tasks/tsk-001` 说明创建成功后，客户端知道新资源地址。
- `VALIDATION_STATUS=400` 说明客户端输入不合法，服务没有把它误报成服务器内部错误。
- `REPLAY_SAME_ID=yes` 说明同一个 `Idempotency-Key` 重放同一请求时没有重复创建任务。
- `CONFLICT_STATUS=409` 说明同一个幂等键配了不同请求体，服务会拒绝歧义。
- `PUT_REPEAT_CHANGED=no` 说明重复相同 `PUT` 没有继续改变版本。
- `REQUEST_IDS_PRESENT=yes` 说明每个响应都带了可追踪的请求 ID。

## 实验目录里有什么

```text
project-http-api-contract-boundary/
├── README.md
├── run_lab.sh
├── scripts/
│   └── api_contract_probe.py
├── src/
│   └── http_api_demo.py
└── tests/
    └── test_http_api_contract.py
```

`src/http_api_demo.py` 是服务端实现。它只用 Python 标准库里的 `http.server`、`http.HTTPStatus`、`json`、`urllib` 和线程工具，不依赖任何 Web 框架。这样做的目的是让初学者先看清框架通常帮你隐藏的边界；生产项目仍然应选择成熟 Web 框架。

`tests/test_http_api_contract.py` 会启动一个绑定在 `127.0.0.1` 随机端口上的 server，然后像真实客户端一样发请求。`scripts/api_contract_probe.py` 也会启动 server，但它的目标是生成学习报告。

## 机制一：method 和 path 先定义资源

HTTP API 的第一层设计是资源和动作。这个 lab 把任务集合和单个任务分开：

```text
/tasks          任务集合
/tasks/tsk-001  单个任务
```

动作由 method 表达：

```text
GET  /tasks        读取集合
POST /tasks        在集合里创建一个新任务
GET  /tasks/tsk-001 读取单个任务
PUT  /tasks/tsk-001 替换单个任务的状态
```

这比把所有动作写成 `/createTask`、`/updateTask`、`/getTask` 更容易形成统一规则。客户端看到 `GET` 就知道它应该是读取；看到 `POST` 就知道它可能产生新资源或副作用；看到 `PUT` 就知道目标资源路径已经在 URL 中。

实验里的 path 匹配很直接：

```python
def match_task_path(path: str) -> str | None:
    parts = [p for p in path.split("/") if p]
    if len(parts) == 2 and parts[0] == "tasks" and parts[1].startswith("tsk-"):
        return parts[1]
    return None
```

这段代码只接受 `/tasks/tsk-...`。路径不匹配时返回 `404`，避免把未定义接口误当成某个默认动作。

## 机制二：status code 是客户端的第一层分支

客户端拿到响应后，最先看到的通常是状态码。状态码不应该只是装饰，它决定客户端下一步怎么做。

本 lab 固定了几种最常用状态：

| 场景 | 状态码 | 客户端应该怎么理解 |
| --- | --- | --- |
| health 正常 | `200 OK` | 服务主路径可用 |
| 创建任务成功 | `201 Created` | 新资源已经创建，读取 `Location` |
| 请求 JSON 或字段错误 | `400 Bad Request` | 修改请求内容后再试 |
| 幂等键冲突 | `409 Conflict` | 同一个键关联了不同语义，不能自动重试 |
| 任务不存在 | `404 Not Found` | 资源地址无效或已消失 |

创建成功时，服务端返回：

```python
headers = {"Location": f"/tasks/{task_id}"}
return HTTPStatus.CREATED, headers, body
```

这条 `Location` 很重要。客户端不需要猜新任务 ID 怎么拼；它直接使用服务端给出的资源地址。

## 机制三：JSON body 要有稳定形状

成功响应使用一个明确对象：

```json
{
  "task": {
    "id": "tsk-001",
    "title": "write API contract",
    "done": false,
    "version": 1
  },
  "request_id": "probe-post-tasks"
}
```

错误响应也要有稳定对象：

```json
{
  "error": {
    "code": "validation_error",
    "message": "field 'title' must be a non-empty string",
    "request_id": "probe-post-tasks"
  }
}
```

这里的 `error.code` 比自然语言 `message` 更适合程序判断。前端可以根据 `validation_error` 高亮表单，根据 `not_found` 显示资源不存在，根据 `idempotency_conflict` 阻止自动重试。`message` 面向人读，可以改得更友好；`code` 一旦公开就要谨慎变更。

## 机制四：request id 让一次失败可以被追踪

本 lab 会接受客户端传来的 `X-Request-Id`，也会在缺失时生成一个短 ID：

```python
def request_id(self) -> str:
    incoming = self.headers.get("X-Request-Id")
    if incoming and all(ch.isalnum() or ch in "-_" for ch in incoming) and len(incoming) <= 80:
        return incoming
    return f"req-{uuid.uuid4().hex[:12]}"
```

响应 header 和错误 body 都会带这个 ID。这样客户端截图、服务端日志、测试报告和监控告警可以对到同一次请求。真实项目里还会把 request id 写入结构化日志，并在调用下游服务时继续传递。

## 机制五：POST 创建和幂等键

网络请求会失败。客户端可能没有收到响应，于是重试同一个创建请求。如果服务端每次 `POST /tasks` 都创建一条新记录，重试就会产生重复任务。

本 lab 使用 `Idempotency-Key` 说明一种常见工程做法：

```python
if idempotency_key and idempotency_key in self._idempotency:
    stored = self._idempotency[idempotency_key]
    if stored.fingerprint != fp:
        return HTTPStatus.CONFLICT, {}, error_body(...)
    headers = dict(stored.headers)
    headers["Idempotency-Replayed"] = "true"
    return stored.status, headers, dict(stored.body)
```

同一个 key 和同一个请求体会得到第一次创建的响应：

```text
REPLAY_STATUS=201
REPLAY_SAME_ID=yes
REPLAY_HEADER=yes
```

同一个 key 配了不同请求体会得到冲突：

```text
CONFLICT_STATUS=409
CONFLICT_ERROR_CODE=idempotency_conflict
```

这个实验只把幂等记录放在内存里。生产系统通常需要把 key、请求摘要、响应摘要和过期时间存在数据库或缓存里，并和真实副作用放在同一个一致性边界内。

## 机制六：PUT 的重复语义

`PUT /tasks/tsk-001` 在这个 lab 里表示替换任务状态。第一次把 `done` 改成 `true` 时，任务真的变化：

```text
PUT_CHANGED=yes
```

第二次发送完全相同的 `PUT`，资源已经处于目标状态：

```text
PUT_REPEAT_CHANGED=no
```

代码里只在状态改变时增加版本号：

```python
changed = old.title != title or old.done != payload["done"]
version = old.version + 1 if changed else old.version
```

这让客户端可以安全重放同一个替换请求。注意，这里说的是重复相同请求不会再次改变资源状态；它不等于所有 `PUT` 都没有副作用。真实系统仍然可能写日志、更新审计字段或触发下游同步，所以公开契约要写清楚哪些字段会变化。

## 测试应该覆盖哪些 API 边界

这篇文章接在测试金字塔之后。API 契约测试要站在客户端边界上检查，覆盖函数返回值之外的 HTTP 细节：

```python
status, headers, body = self.client.request(
    "POST", "/tasks", {"title": "write API contract"}, {"Idempotency-Key": "lesson-1"}
)
self.assertEqual(status, 201)
self.assertEqual(headers["Location"], "/tasks/tsk-001")
self.assertEqual(body["task"]["id"], "tsk-001")
```

这条测试同时检查了 HTTP status、header 和 JSON body。它比只测试 `TaskStore.create_task()` 更接近真实客户端，也比端到端浏览器测试更容易定位接口层问题。

建议最少覆盖这些边界：

1. 成功创建：状态码、`Location`、响应 JSON。
2. 输入错误：`400`、错误 code、request id。
3. 不存在资源：`404`、错误 code。
4. 重复请求：幂等 replay 和 conflict。
5. 替换请求：重复相同 `PUT` 的结果稳定。

## 常见错误

1. **所有失败都返回 `200`。** 客户端必须解析 body 才知道失败，会破坏缓存、监控和通用 HTTP 工具。
2. **把输入错误返回 `500`。** `500` 表示服务端内部错误。字段缺失、JSON 格式错误和类型错误应归到客户端请求问题。
3. **成功创建不返回资源位置。** 客户端只能从 body 猜 ID 或重新拉列表，接口耦合会变强。
4. **错误 body 每个接口都不一样。** 前端和调用方需要为每个错误写特殊解析逻辑。
5. **重试创建请求没有幂等边界。** 网络抖动后容易产生重复订单、重复任务或重复外部副作用。
6. **测试只调用内部函数。** 函数测试有价值，但不能证明 method、path、header、status 和 JSON 序列化都正确。

## 练习

1. 给 `GET /tasks` 增加 `?done=true` 过滤参数，并写一个 contract test 证明过滤只影响列表结果。
2. 给任务增加 `description` 字段。先写测试，再修改成功响应和错误校验。
3. 把错误响应改成 `application/problem+json` 风格，比较它和当前 `error.code` 结构的取舍。
4. 给 `PUT /tasks/{id}` 增加 `If-Match` 或 `version` 检查，避免两个客户端覆盖彼此更新。
5. 把内存里的 idempotency 记录改成 SQLite 表，思考它应该和任务创建放在一个事务里还是分开写。

## 参考资料

- IETF：[RFC 9110 — HTTP Semantics](https://datatracker.ietf.org/doc/html/rfc9110)
- IETF：[RFC 9112 — HTTP/1.1](https://datatracker.ietf.org/doc/html/rfc9112)
- IETF：[RFC 9457 — Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc9457)
- Python 文档：[http.server](https://docs.python.org/3/library/http.server.html)
- Python 文档：[urllib.request](https://docs.python.org/3/library/urllib.request.html)

{% endraw %}
