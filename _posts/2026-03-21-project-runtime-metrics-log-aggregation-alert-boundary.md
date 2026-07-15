---
layout: post
title: "项目运行时指标、日志聚合与最小报警边界：什么时候该叫醒人"
date: 2026-03-21 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 JSONL 请求事件生成本地 metrics、report 和 alerts，拆开日志、指标、报警、小样本抑制和观测边界各自解决的问题。"
tags: [metrics, logs, alerting, observability, jsonl, reliability, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-runtime-metrics-log-aggregation-alert-boundary/README.md`](/assets/labs/project-runtime-metrics-log-aggregation-alert-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
上一篇文章把服务生命周期拆成 `starting -> ready -> draining -> stopping`，并用 JSONL 事件记录启动、请求、终止和 drain。服务能优雅退出以后，下一类问题会立刻出现：服务还在运行，但用户已经感到慢；错误正在变多，但终端日志还没有人看；某个接口偶尔失败，应该记录、汇总，还是立刻叫醒人？

很多项目一开始只有两种观测方式：人盯终端日志，或者出问题后 `grep` 日志。这个方式在本地调试时可用，进入长期运行后会失效。日志记录的是单个事实，系统状态需要从一段时间内的事实聚合出来；报警也不应该等同于“出现一条错误日志”，它应该是带阈值、样本量和处置意义的判断。

本文用一个本地 JSONL 事件文件做最小实验：先生成 12 条请求完成事件，再聚合出 counters、latency buckets、p50/p90、error rate、slow rate，最后根据阈值生成 alerts。实验保留原始日志、指标报告和报警 JSON，读者可以从报警一路追回原始事件。

## 学习目标

完成本文后，你应该能够：

1. 区分 logs、metrics 和 alerts 三层数据各自回答的问题。
2. 从 JSONL 请求事件聚合 request count、status family、endpoint count 和 error count。
3. 解释 latency bucket、p50、p90、slow rate 的含义和局限。
4. 用 error rate 和 p90 latency 写一个最小报警规则。
5. 解释为什么小样本窗口需要抑制阈值报警。
6. 复跑本地实验，并从 `runtime_events.jsonl` 追踪到 `metrics.json`、`alerts.json` 和 Markdown 报告。

## 先修和实验边界

先修知识：JSONL、一点 Python 文件读写、上一节服务生命周期中的结构化事件。

实验边界：本文不引入 Prometheus、Grafana、OpenTelemetry collector、云监控或告警平台，只用 Python 标准库处理本地文件。这样可以把核心边界讲清楚：**原始事件是什么，聚合指标是什么，报警规则什么时候有足够证据，什么时候只是样本不足**。

## 为什么需要引入 metrics 和 alerts

日志能回答“某个请求发生了什么”。例如：

```json
{"endpoint":"/api/report","event":"request_finished","latency_ms":510,"request_id":"req-010","status":502,"ts":9.0}
```

这一行说明 `req-010` 调用 `/api/report`，返回 502，耗时 510 ms。它不能直接回答这些问题：

- 最近一段窗口里一共有多少请求？
- 5xx 错误占比是多少？
- 慢请求集中在哪个 endpoint？
- p90 延迟是否超过阈值？
- 当前样本数是否足够支持报警？

metrics 把一组事件压缩成可比较的数值，alerts 把数值和规则结合成需要处理的状态。三层关系可以写成：

```text
JSONL logs -> aggregate window -> metrics -> evaluate rules -> alerts
```

这条链路的关键是可追溯。报警不能只写“服务异常”，它要说明触发规则、阈值、观测值、样本数和窗口来源。

## 实验产物

本地 lab 生成这些文件：

```text
reports/runtime_events.jsonl
reports/metrics.json
reports/alerts.json
reports/runtime_metrics_report.md
reports/metrics_probe.json
reports/transcript.md
```

`transcript.md` 的关键结果是：

```text
JSONL_EVENTS_VALID=yes
REQUEST_COUNT=12
ERRORS_5XX=3
ERROR_RATE=0.250
LATENCY_P90_MS=501.0
SLOW_RATE=0.333
HIGH_ERROR_RATE_ALERT=yes
HIGH_P90_LATENCY_ALERT=yes
SMALL_WINDOW_SUPPRESSED=yes
BUCKET_TOTAL_MATCHES=yes
ENDPOINT_REPORTED=yes
RUN_STATUS=ok
```

这些结果对应本文的验收点：事件可解析，指标总数正确，错误率和 p90 延迟能触发报警，小样本窗口不会产生误导性阈值报警，latency bucket 总数与请求数一致，endpoint 维度保留在报告里。

## 事件模型：每个请求一条事实

实验事件只保留最小字段：

```json
{
  "event": "request_finished",
  "ts": 7.0,
  "request_id": "req-008",
  "endpoint": "/api/report",
  "status": 503,
  "latency_ms": 420
}
```

字段含义：

| 字段 | 含义 | 为什么需要 |
| --- | --- | --- |
| `event` | 事件类型 | 让同一 JSONL 文件可以容纳多种事件 |
| `ts` | 窗口内时间 | 确定聚合窗口和事件顺序 |
| `request_id` | 单个请求标识 | 从指标回到原始请求时使用 |
| `endpoint` | 接口维度 | 判断哪个功能路径异常 |
| `status` | HTTP 状态码 | 计算 2xx/4xx/5xx 和错误率 |
| `latency_ms` | 请求耗时 | 计算延迟分布和慢请求 |

解析时先做输入校验：缺字段、非法 status、负延迟、非法 endpoint 都应失败。指标系统的输入边界不能默认日志永远正确；坏数据进入聚合后，错误会被包装成看似精确的图表。

## 指标一：计数器和状态码族

最基础的指标是 counter。实验把 12 条事件聚合成：

```json
{
  "request_count": 12,
  "status_family_counts": {
    "2xx": 9,
    "5xx": 3
  },
  "errors_5xx": 3,
  "error_rate": 0.25
}
```

`request_count` 是窗口内请求总数。`errors_5xx` 是服务端错误数。`error_rate` 的计算是：

```text
error_rate = errors_5xx / request_count = 3 / 12 = 0.25
```

这个指标适合回答“错误是否正在增多”。它不适合单独回答“用户是否一定受影响”，因为 5xx 的影响还取决于 endpoint、请求量、重试、缓存和用户路径。

## 指标二：endpoint 维度

只看全局 error rate 容易掩盖局部问题。实验保留 endpoint 计数：

```json
{
  "endpoint_counts": {
    "/api/report": 6,
    "/api/tasks": 6
  },
  "endpoint_error_counts": {
    "/api/report": 2,
    "/api/tasks": 1
  }
}
```

这个维度帮助排障：如果全局错误率上升，先看错误集中在哪个 endpoint，再回到对应 request_id 的日志。指标给出方向，日志提供证据。

维度不能无限增加。把 user_id、完整 URL、trace id 都做成指标标签，会让时间序列数量爆炸。本文只用 endpoint，是因为它能表达业务路径，又不会让本地实验变成标签管理课。

## 指标三：latency bucket 和 p90

平均延迟容易隐藏尾部慢请求。实验保留 bucket 和 p90：

```json
{
  "latency_buckets_ms": {
    "le_50ms": 1,
    "le_100ms": 6,
    "le_250ms": 2,
    "le_500ms": 1,
    "le_1000ms": 2,
    "gt_1000ms": 0
  },
  "latency_ms": {
    "min": 42,
    "p50": 88.5,
    "p90": 501.0,
    "max": 780
  }
}
```

bucket 回答“有多少请求落在各个耗时段”。p90 回答“90% 请求大约不超过多少毫秒”。如果 p90 明显高于 p50，说明尾部延迟正在拉开。

本文的 p90 使用固定小数据集上的线性插值，适合教学和本地验收。生产系统通常用直方图、滑动窗口或摘要结构估计分位数，具体实现要考虑样本量、窗口长度和存储成本。

## slow rate：把延迟阈值转成比例

除了 p90，实验还定义了 `slow_threshold_ms=250`：

```text
slow_requests = latency_ms > 250 的请求数
slow_rate = slow_requests / request_count
```

本次数据里 slow rate 是：

```text
SLOW_RATE=0.333
```

slow rate 的优点是解释直接：超过 250 ms 的请求占三分之一。它的边界也清楚：阈值必须来自用户体验目标或服务目标，不能随意选一个看起来顺眼的数。

## 报警规则：阈值、观测值和样本数

实验使用两个阈值：

```text
min_requests = 10
max_error_rate = 0.20
max_p90_ms = 300
```

窗口内有 12 个请求，满足最小样本数。聚合后：

```text
ERROR_RATE=0.250
LATENCY_P90_MS=501.0
```

因此两个报警触发：

```json
[
  {
    "name": "high_error_rate",
    "observed": 0.25,
    "sample_count": 12,
    "severity": "page",
    "state": "firing",
    "threshold": 0.2
  },
  {
    "name": "high_p90_latency",
    "observed": 501.0,
    "sample_count": 12,
    "severity": "ticket",
    "state": "firing",
    "threshold": 300.0
  }
]
```

报警事件要包含 `name`、`state`、`observed`、`threshold` 和 `sample_count`。没有这些字段，收到报警的人无法判断它是误报、趋势、单点异常，还是需要立即处理的故障。

## 小样本窗口为什么要抑制

如果窗口里只有 4 个请求，其中 1 个失败，error rate 也是 25%。机械套用阈值会触发同样的 high-error-rate 报警，但这个判断证据弱得多。

实验对前 4 条事件单独计算时，返回：

```json
[
  {
    "name": "insufficient_sample",
    "observed": 4,
    "reason": "not enough requests to evaluate rate/latency thresholds",
    "severity": "info",
    "state": "suppressed",
    "threshold": 10
  }
]
```

这一步的作用是把结论降级：当前窗口样本不足，不能用比例阈值得出强报警结论。真实系统可以选择扩大窗口、合并维度、或改用单次失败事件通知。

## 从 report 回到原始日志

`runtime_metrics_report.md` 给人读：

```text
| request_count | 12 | number of request_finished events in the window |
| errors_5xx | 3 | server-side failures |
| error_rate | 0.250 | errors_5xx / request_count |
| latency_p90_ms | 501.0 | high-tail observed latency |
```

`alerts.json` 给自动化系统读；`runtime_events.jsonl` 负责追溯。一个合理的排障路径是：

```text
high_p90_latency firing
-> 查看 metrics.json 的 endpoint_latency_p90_ms
-> 查看 /api/report 的慢请求
-> grep request_id 或 endpoint 回到 runtime_events.jsonl
```

指标越聚合，越需要回到日志确认具体事实。否则就会出现“图表看起来异常，但不知道哪个请求异常”的情况。

## 怎么复跑实验

在本地运行：

```bash
cd <LAB_ROOT>/project-runtime-metrics-log-aggregation-alert-boundary
./run_lab.sh
```

成功时会看到：

```text
Ran 5 tests in ...s
OK
JSONL_EVENTS_VALID=yes
REQUEST_COUNT=12
ERRORS_5XX=3
ERROR_RATE=0.250
LATENCY_P90_MS=501.0
SLOW_RATE=0.333
HIGH_ERROR_RATE_ALERT=yes
HIGH_P90_LATENCY_ALERT=yes
SMALL_WINDOW_SUPPRESSED=yes
BUCKET_TOTAL_MATCHES=yes
ENDPOINT_REPORTED=yes
RUN_STATUS=ok
```

也可以分两步运行：

```bash
python3 src/runtime_metrics_demo.py generate-events --output reports/runtime_events.jsonl
python3 src/runtime_metrics_demo.py aggregate --events reports/runtime_events.jsonl --out-dir reports
```

然后查看：

```bash
cat reports/metrics.json
cat reports/alerts.json
cat reports/runtime_metrics_report.md
```

## 设计选择和原因

| 设计选择 | 原因 | 代价 |
| --- | --- | --- |
| JSONL 作为输入 | 一行一个事件，容易追加和逐行解析 | 需要字段校验 |
| 固定窗口聚合 | 教学可复现，输出稳定 | 不能表达连续时间滚动趋势 |
| status family counter | 快速区分 2xx/4xx/5xx | 不能替代完整状态码分析 |
| latency bucket + p90 | 同时保留分布和尾部信号 | 小样本分位数不稳定 |
| min_requests 抑制 | 避免小样本比例误报 | 可能延迟发现低流量真实故障 |
| alerts JSON | 自动化可读，字段明确 | 需要后续平台承接通知和静默策略 |

这组选择适合初学项目：先把观测链路做完整，再引入 Prometheus、OpenTelemetry 或云监控平台。

## 常见错误

1. **把一条错误日志当成报警。** 单条日志适合排查事实，报警需要窗口、阈值、样本数和处置意义。
2. **只看平均延迟。** 平均值会掩盖尾部慢请求。至少要看 bucket 或 p90。
3. **没有样本数。** `error_rate=0.5` 在 2 个请求和 2000 个请求里含义完全不同。
4. **指标标签太细。** 把 request_id、user_id 做成指标标签会制造大量时间序列，降低可用性。
5. **报警没有 observed/threshold。** 没有观测值和阈值，值班人无法判断严重程度。
6. **只有 metrics，没有日志。** 指标告诉你哪里可能有问题，日志帮助你回到具体事实。

## 练习和扩展

1. 给事件增加 `method` 字段，把 GET/POST 分开统计。
2. 增加 `4xx_rate` 指标，并解释它和 5xx 对应的责任边界不同。
3. 把固定窗口改成按 `ts` 切成两个窗口，比较两个窗口的 error rate 和 p90。
4. 给 `alerts.json` 增加 `runbook` 字段，写出收到报警后第一步应该查什么。
5. 把 JSONL 输入换成上一节服务生命周期实验产生的真实 `request_started/request_completed` 事件。

## 验收清单

一个最小运行时观测包至少应该回答：

- 原始日志是否逐行可解析？
- 每条事件是否有 request id、endpoint、status、latency？
- 指标是否能从日志重新生成？
- request count、5xx count、error rate 是否一致？
- latency bucket 总数是否等于请求数？
- p90 和 slow rate 是否有明确阈值含义？
- 报警是否写出规则、阈值、观测值和样本数？
- 小样本窗口是否被单独处理？
- 报警能否追溯到 metrics，再追溯到原始日志？

## 参考资料

- Python `json` 文档：本文 JSONL 读写和校验的基础。<https://docs.python.org/3/library/json.html>
- Python `statistics` 文档：理解本地统计量和分位数实现时可参考。<https://docs.python.org/3/library/statistics.html>
- Prometheus metric types：介绍 counters、gauges、histograms 等常见指标类型。<https://prometheus.io/docs/concepts/metric_types/>
- Prometheus alerting rules：说明报警规则如何从指标表达式生成告警状态。<https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/>
- OpenTelemetry Metrics：解释现代可观测性体系中 metrics 的数据模型和语义。<https://opentelemetry.io/docs/concepts/signals/metrics/>
- Google SRE Book: Monitoring Distributed Systems：介绍监控目标、告警和四个黄金信号。<https://sre.google/sre-book/monitoring-distributed-systems/>
- The Twelve-Factor App: Logs：说明把日志作为事件流处理的工程背景。<https://12factor.net/logs>

{% endraw %}
