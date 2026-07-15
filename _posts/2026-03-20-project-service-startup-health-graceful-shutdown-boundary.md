---
layout: post
title: "项目服务启动、健康检查与优雅关闭边界：进程收到 SIGTERM 后怎么不丢请求"
date: 2026-03-20 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 Python 标准库实现一个本地 HTTP 服务，拆开 liveness、readiness、status、SIGTERM、drain、grace timeout 和 JSONL 生命周期日志各自解决的问题。"
tags: [service-lifecycle, health-check, graceful-shutdown, sigterm, http, observability, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-service-startup-health-graceful-shutdown-boundary/README.md`](/assets/labs/project-service-startup-health-graceful-shutdown-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
前面几篇文章把本地状态、并发写入、重试、幂等副作用和后台队列拆开了。队列能恢复任务以后，下一个问题很自然：真正部署时，worker 或 HTTP 服务本身怎么启动、怎么被探活、收到终止信号时怎么停下来？

很多初学项目会把服务写成这样：启动后立刻监听端口，健康检查固定返回 200，收到 `Ctrl+C` 或平台发来的 `SIGTERM` 后直接退出。这个版本在本机看起来能跑，在真实运行环境里会暴露三个故障：服务依赖还没初始化就接流量；进程正在退出时负载均衡还继续转发新请求；已经开始处理的请求或后台任务被直接截断。

本文用 Python 标准库写一个小 HTTP 服务，明确区分启动、探活、接收工作、收到终止信号、drain、退出这几段边界。文章关注服务生命周期的状态变化，不展开具体框架的封装 API。

## 学习目标

完成本文后，你应该能够：

1. 区分 liveness、readiness 和 status 三类接口各自回答的问题。
2. 解释为什么“端口已监听”不等于“服务已经可以接流量”。
3. 用 PID/port state file 让探针发现本地服务端点。
4. 设计 `starting -> ready -> draining -> stopping` 的服务状态机。
5. 解释 `SIGTERM` 到来后为什么要先关闭 readiness，再拒绝新工作，再等待 in-flight 工作完成。
6. 用 JSONL 日志还原服务启动、请求、终止和 drain 的证据链。

## 先修和实验边界

先修知识：Linux 进程和信号、HTTP 基本请求、上一节后台队列里的 worker 状态和 JSONL 观测方式。

实验边界：本文不引入 Flask、FastAPI、gunicorn、systemd、Docker 或 Kubernetes。实验只用 Python 标准库的 `ThreadingHTTPServer`、`signal` 和 `subprocess`。这样可以把问题压缩到最小：**进程什么时候算活着、什么时候算准备好、什么时候应该停止接新工作、什么时候可以退出**。

## 为什么需要引入服务生命周期契约

一个服务从启动到退出至少经历四个阶段：

| 阶段 | 外部现象 | 允许接新工作吗 | 需要记录什么 |
| --- | --- | --- | --- |
| starting | 进程启动，端口已绑定，依赖初始化中 | 不允许 | PID、端口、启动事件 |
| ready | 初始化完成，能够处理请求 | 允许 | ready 事件、请求计数 |
| draining | 收到终止信号，已有请求继续跑 | 不允许 | shutdown 事件、拒绝新请求、active 数 |
| stopping | drain 完成或超时，准备退出 | 不允许 | drain 结果、退出事件 |

端口监听只说明 socket 已经创建。服务可能还在加载配置、连接数据库、恢复队列租约、预热模型、加载缓存或执行迁移。把端口监听和 readiness 混成一个信号，会让上游过早把流量打进来。

退出也一样。`SIGTERM` 是平台给进程的“请停止”通知。正确的响应顺序应该是：

```text
SIGTERM -> ready=false -> refuse new work -> wait active work -> stop server -> exit
```

如果直接 `exit(0)`，正在处理的请求会中断；如果一直保持 ready，上游会在进程准备退出时继续发新请求。

## 实验产物

本地 lab 生成三份报告：

```text
reports/service_lifecycle_probe.json
reports/transcript.md
reports/service_status_report.md
```

`transcript.md` 的关键结果是：

```text
PID_PORT_FILE_VALID=yes
LIVE_BEFORE_READY=yes
READY_AFTER_STARTUP=yes
SIGTERM_READY_FALSE=yes
NEW_WORK_REFUSED_DURING_DRAIN=yes
INFLIGHT_COMPLETED_BEFORE_EXIT=yes
SERVICE_EXIT_CODE=0
REQUIRED_EVENTS_PRESENT=yes
JSONL_EVENTS_VALID=yes
EVENT_COUNT=8
RUN_STATUS=ok
```

这些结果对应本文的主线：服务先发布可发现的 PID/port，liveness 在 readiness 之前可用，初始化结束后 readiness 才变成 200，收到 `SIGTERM` 后 readiness 变成 503，新工作被拒绝，已经开始的工作在退出前完成，日志事件可解析。

## PID/port state file：让探针知道服务在哪里

本地测试经常让服务绑定随机端口 `--port 0`，避免与已有进程冲突。问题是：随机端口只有服务自己知道，测试进程需要一个可发现的入口。

实验服务启动后会写 `service_state.json`：

```json
{
  "host": "127.0.0.1",
  "log_file": "events.jsonl",
  "pid": 3188982,
  "port": 35719,
  "state_file": "service_state.json"
}
```

这个文件只记录公开的本地端点和进程号，不记录绝对工作目录、token、环境变量或私有配置。测试探针读取它以后，拼出：

```text
http://127.0.0.1:<port>/live
http://127.0.0.1:<port>/ready
http://127.0.0.1:<port>/status
http://127.0.0.1:<port>/work?seconds=0.8
```

这一步的价值在于把“服务已启动”变成可验证状态，而不是凭终端里有没有输出判断。

## liveness、readiness 和 status 分别回答什么

实验服务暴露四个 HTTP 路径：

| 路径 | 成功状态码 | 含义 | 典型使用者 |
| --- | --- | --- | --- |
| `/live` | 200 | 进程和 HTTP loop 能回答请求 | 进程管理器、容器平台 |
| `/ready` | 200 或 503 | 服务是否应该接收新工作 | 负载均衡、调度器 |
| `/status` | 200 | 当前状态和计数器 | 人和自动化排障脚本 |
| `/work?seconds=...` | 200 或 503 | 模拟一段业务工作 | 本文探针 |

`/live` 的语义要窄：只说明进程还活着、请求循环还能响应。`/ready` 的语义要严格：只有初始化完成并且没有进入 shutdown/drain 才返回 200。`/status` 不参与流量调度，负责暴露状态和计数器。

实验开始阶段，`/live` 已经返回 200，而 `/ready` 返回 503：

```text
LIVE_BEFORE_READY=yes
READY_AFTER_STARTUP=yes
```

这说明服务可以被探测到，但还没有承诺接收业务请求。

## 服务状态用一个对象维护

实验核心状态保存在 `LifecycleState`：

```python
@dataclass
class LifecycleState:
    host: str
    port: int
    pid: int
    started_at: float
    startup_complete: bool = False
    shutdown_requested: bool = False
    stopping: bool = False
    active_requests: int = 0
    accepted_requests: int = 0
    completed_requests: int = 0
    refused_requests: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)
```

状态对象提供两个重要判断：

```python
def mode(self) -> str:
    if self.stopping:
        return "stopping"
    if self.shutdown_requested:
        return "draining"
    if not self.startup_complete:
        return "starting"
    return "ready"

def ready(self) -> bool:
    return self.startup_complete and not self.shutdown_requested and not self.stopping
```

这里有两个设计点：

1. `mode` 给人看，描述服务所处阶段。
2. `ready` 给调度逻辑看，只回答是否允许新工作进入。

不要把这两个概念合并。一个处于 `draining` 的服务仍然可以回答 `/live` 和 `/status`，但 readiness 必须变 false。

## `/work`：只在 ready 时接收新工作

`/work?seconds=0.8` 用 sleep 模拟正在执行的业务请求。进入处理前，服务会尝试接收工作：

```python
def try_accept_work(self) -> bool:
    with self.lock:
        if not self.startup_complete or self.shutdown_requested or self.stopping:
            self.refused_requests += 1
            return False
        self.active_requests += 1
        self.accepted_requests += 1
        return True
```

如果服务仍在启动、已经收到 shutdown，或正在停止，`/work` 返回 503，并写入 `request_refused` 事件。已经被接收的请求会把 `active_requests` 加 1；完成后再减 1，并增加 `completed_requests`。

这就是 drain 能成立的前提：服务必须知道当前有多少工作还在运行。

## SIGTERM 后先关 readiness

实验服务注册 `SIGTERM` 和 `SIGINT`：

```python
def on_signal(signum, _frame):
    if state.request_shutdown():
        logger.emit("shutdown_requested", signal=signum, **state.snapshot())
    shutdown_event.set()
```

信号处理函数只做两件事：把状态切到 shutdown requested，并设置一个 event。真正的等待、关闭 HTTP server 和退出，在主循环里完成。

收到 `SIGTERM` 后，`state.ready()` 立即变 false，所以 `/ready` 返回 503。此时 `/live` 和 `/status` 仍然可以回答，便于上游和排障脚本看到服务正在 drain。

探针验证了这个状态：

```text
SIGTERM_READY_FALSE=yes
NEW_WORK_REFUSED_DURING_DRAIN=yes
```

这两个结果分别说明：终止信号到来后，服务不会再被调度接新流量；如果仍有人调用 `/work`，服务会明确返回 503，而不是悄悄启动新任务。

## drain：等待已开始的工作完成

主循环收到 shutdown event 后，不马上退出，而是等待 active request 清零：

```python
deadline = now() + args.grace_timeout
while state.active_count() > 0 and now() < deadline:
    time.sleep(0.05)

if state.active_count() > 0:
    logger.emit("drain_timeout", remaining_active_requests=state.active_count())
else:
    logger.emit("drain_complete", remaining_active_requests=0)
```

实验里先发起一个 0.8 秒的 `/work`，等它进入 active 状态后再发送 `SIGTERM`。随后探针再尝试发一个新 `/work`，它会被拒绝；原来已经开始的请求继续完成；进程最后以 0 退出。

```text
INFLIGHT_COMPLETED_BEFORE_EXIT=yes
SERVICE_EXIT_CODE=0
```

这就是 graceful shutdown 的核心：终止信号不会承诺无限等待，只承诺在 grace timeout 内给已开始的工作一个完成机会。

## JSONL 生命周期日志

服务写入 `events.jsonl`，每行是一个独立 JSON 对象。探针最终看到 8 个关键事件：

```text
service_starting, service_ready, request_started, shutdown_requested,
request_refused, request_completed, drain_complete, service_stopped
```

这些事件能回答排障时最重要的问题：

| 问题 | 需要看的事件 |
| --- | --- |
| 服务有没有启动到 ready | `service_starting`、`service_ready` |
| SIGTERM 是什么时候到的 | `shutdown_requested` |
| shutdown 后还有没有新请求进来 | `request_refused` |
| 已开始请求是否完成 | `request_completed` |
| drain 是完成还是超时 | `drain_complete` 或 `drain_timeout` |
| 进程退出前是否收尾 | `service_stopped` |

日志使用 JSONL，是因为它既能被人 `cat`/`grep`，也能被脚本逐行解析。比起自由文本日志，JSONL 更适合自动化验收。

## 怎么复跑实验

在本地运行：

```bash
cd <LAB_ROOT>/project-service-startup-health-graceful-shutdown-boundary
./run_lab.sh
```

成功时会看到：

```text
Ran 4 tests in ...s
OK
PID_PORT_FILE_VALID=yes
LIVE_BEFORE_READY=yes
READY_AFTER_STARTUP=yes
SIGTERM_READY_FALSE=yes
NEW_WORK_REFUSED_DURING_DRAIN=yes
INFLIGHT_COMPLETED_BEFORE_EXIT=yes
SERVICE_EXIT_CODE=0
REQUIRED_EVENTS_PRESENT=yes
JSONL_EVENTS_VALID=yes
RUN_STATUS=ok
```

如果你只想观察服务，可以手动启动：

```bash
python3 src/service_lifecycle_demo.py --state-dir /tmp/service-demo --startup-delay 1 --grace-timeout 3
```

另开一个终端读取端口并探测：

```bash
cat /tmp/service-demo/service_state.json
curl -i http://127.0.0.1:<port>/live
curl -i http://127.0.0.1:<port>/ready
curl -i http://127.0.0.1:<port>/status
```

发送终止信号：

```bash
kill -TERM <pid>
cat /tmp/service-demo/events.jsonl
```

## 设计选择和原因

| 设计选择 | 原因 | 代价 |
| --- | --- | --- |
| `port=0` 后写 state file | 避免端口冲突，测试可发现真实端点 | 需要等待 state file 出现 |
| `/live` 和 `/ready` 分开 | 允许进程活着但暂不接流量 | 调用方必须理解两个接口 |
| SIGTERM 后 readiness 立即 false | 从调度层摘除服务 | 已有请求仍要靠 drain 管理 |
| active request 计数 | 判断 drain 何时结束 | 每个入口都必须正确加减计数 |
| grace timeout | 防止退出无限等待 | 超时时可能仍有工作被中断 |
| JSONL 事件 | 可脚本解析，可还原顺序 | 需要约定字段和事件名 |

这组选择背后的原则是：**先把服务生命周期变成可观测状态，再讨论框架和部署平台**。

## 常见错误

1. **健康检查永远返回 200。** 这会掩盖初始化失败和 shutdown draining。至少要区分 liveness 和 readiness。
2. **收到 SIGTERM 后继续接新请求。** 上游可能还没把服务摘掉，所以服务端也要拒绝新工作。
3. **没有 active work 计数。** 没有计数就无法判断 drain 是否完成，只能 sleep 一个固定时间。
4. **在信号处理函数里做复杂关闭。** 信号处理适合切状态和通知主循环，复杂 I/O 和等待应该放到正常控制流里。
5. **grace timeout 过长或过短。** 过短容易截断请求，过长会拖慢部署和扩缩容。真实项目要根据请求耗时分布决定。
6. **日志只有自然语言。** 自由文本适合读，结构化事件适合验收和报警。生命周期关键事件应该能被脚本解析。

## 练习和扩展

1. 给 `/work` 增加 `request_id`，在 JSONL 日志里把同一个请求的 start/complete/refuse 串起来。
2. 增加 `drain_timeout` 场景：让 `/work?seconds=5` 超过 `--grace-timeout 1`，观察退出码和日志。
3. 把 readiness 条件扩展成多个依赖：配置加载完成、数据库 ping 成功、队列恢复完成。
4. 为 `/status` 增加最近一次 shutdown 时间、最后一个错误和 uptime 秒数。
5. 把同样的生命周期契约改写到你熟悉的 Web 框架里，例如 FastAPI、Spring Boot、Go `net/http` 或 Rust axum。

## 验收清单

一个可部署服务至少应该回答：

- 启动后有没有可发现的 PID/port 或注册信息？
- liveness 和 readiness 是否分开？
- 初始化期间 readiness 是否保持 false？
- 收到 `SIGTERM` 后 readiness 是否立即 false？
- shutdown 后新工作是否被拒绝？
- 已开始工作是否有 drain 机会？
- drain 是否有最大等待时间？
- 关键生命周期事件是否有结构化日志？
- 本地是否有能复现这些状态变化的探针？

## 参考资料

- Python `http.server` 文档：解释标准库 HTTP server 的边界和适用场景。<https://docs.python.org/3/library/http.server.html>
- Python `signal` 文档：说明 Python 信号处理函数的执行模型。<https://docs.python.org/3/library/signal.html>
- Python `subprocess` 文档：本文测试用子进程启动和终止服务。<https://docs.python.org/3/library/subprocess.html>
- Kubernetes liveness/readiness/startup probes：真实平台中健康检查的常见语义。<https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/>
- Kubernetes Pod termination：说明终止信号和 grace period 的平台级流程。<https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination>
- systemd.service man page：Linux 服务管理器里启动、停止和信号的工程背景。<https://man7.org/linux/man-pages/man5/systemd.service.5.html>
- The Twelve-Factor App: Logs：把日志当事件流的经典工程约定。<https://12factor.net/logs>

{% endraw %}
